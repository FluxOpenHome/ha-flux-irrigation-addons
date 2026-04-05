#!/usr/bin/env python3
"""
ESP32 Irrigation Controller Serial Monitor
Auto-reconnects, timestamps, color-codes, detects crashes, logs to file.

Usage:
    python3 monitor_esp32.py [--port /dev/cu.wchusbserial10] [--baud 115200] [--log irrigation.log]

Press Ctrl+C to exit. Press 'r' + Enter to reset the device.
"""

import serial
import serial.tools.list_ports
import time
import re
import sys
import os
import argparse
from datetime import datetime

# ANSI colors for terminal
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
CYAN = "\033[96m"
GRAY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Patterns that indicate crashes
CRASH_PATTERNS = [
    r"Guru Meditation Error",
    r"abort\(\)",
    r"Backtrace:",
    r"assert failed",
    r"LoadProhibited",
    r"StoreProhibited",
    r"InstrFetchProhibited",
    r"IllegalInstruction",
    r"rst:0x",
    r"CRITICAL HEAP",
    r"panic_abort",
    r"stack overflow",
    r"Task watchdog got triggered",
    r"Brownout detector",
    r"safe_mode.*invoke",
]

HEAP_PATTERN = re.compile(r"Heap:\s*(\d+)\s*free")
CRASH_RE = re.compile("|".join(CRASH_PATTERNS), re.IGNORECASE)
ESPHOME_ANSI = re.compile(r"\x1b\[[0-9;]*m")

# Heap tracking
heap_history = []
min_heap_seen = float("inf")
crash_count = 0
boot_count = 0
last_boot_time = None


def find_esp32_port():
    """Auto-detect ESP32 USB serial port."""
    ports = serial.tools.list_ports.comports()
    for p in ports:
        desc = (p.description or "").lower()
        hwid = (p.hwid or "").lower()
        if any(
            k in desc or k in hwid
            for k in ["ch340", "cp210", "ftdi", "usb", "wch", "serial"]
        ):
            if "bluetooth" not in desc and "debug" not in desc:
                return p.device
    # Fallback to known macOS names
    for name in [
        "/dev/cu.wchusbserial10",
        "/dev/cu.usbserial-0001",
        "/dev/cu.SLAB_USBtoUART",
    ]:
        if os.path.exists(name):
            return name
    return None


def format_line(raw_line):
    """Strip ESPHome ANSI codes and add our own color coding."""
    clean = ESPHOME_ANSI.sub("", raw_line).strip()
    if not clean:
        return None, None

    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]

    # Detect crash patterns
    if CRASH_RE.search(clean):
        colored = f"{RED}{BOLD}[{ts}] !!! {clean}{RESET}"
        return colored, clean

    # Color by ESPHome log level
    if "[E]" in clean or "ERROR" in clean:
        colored = f"{RED}[{ts}] {clean}{RESET}"
    elif "[W]" in clean or "WARNING" in clean:
        colored = f"{YELLOW}[{ts}] {clean}{RESET}"
    elif "[I]" in clean:
        colored = f"{GREEN}[{ts}] {clean}{RESET}"
    elif "[D]" in clean:
        colored = f"{GRAY}[{ts}] {clean}{RESET}"
    elif "[V]" in clean:
        colored = f"{GRAY}[{ts}] {clean}{RESET}"
    elif "boot" in clean.lower() or "IRRIGATION BOOT" in clean:
        colored = f"{CYAN}{BOLD}[{ts}] {clean}{RESET}"
    else:
        colored = f"[{ts}] {clean}"

    return colored, clean


def track_heap(clean_line):
    """Track heap values from log lines."""
    global min_heap_seen
    match = HEAP_PATTERN.search(clean_line)
    if match:
        heap_val = int(match.group(1))
        heap_history.append((time.time(), heap_val))
        if heap_val < min_heap_seen:
            min_heap_seen = heap_val
        # Keep last 1000 readings
        if len(heap_history) > 1000:
            heap_history.pop(0)
        return heap_val
    return None


def print_status():
    """Print current monitoring status."""
    global crash_count, boot_count, min_heap_seen
    print(f"\n{CYAN}{'='*60}")
    print(f"  Monitor Status @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Boots: {boot_count} | Crashes detected: {crash_count}")
    if min_heap_seen < float("inf"):
        print(f"  Min heap seen: {min_heap_seen} bytes")
    if heap_history:
        latest = heap_history[-1][1]
        print(f"  Current heap: {latest} bytes")
        if latest < 20000:
            print(f"  {RED}{BOLD}  WARNING: Heap critically low!{RESET}{CYAN}")
    if last_boot_time:
        uptime = time.time() - last_boot_time
        m, s = divmod(int(uptime), 60)
        h, m = divmod(m, 60)
        print(f"  Uptime since last boot: {h}h {m}m {s}s")
    print(f"{'='*60}{RESET}\n")


def reset_device(ser):
    """Reset ESP32 via DTR/RTS."""
    print(f"{YELLOW}>>> Resetting ESP32...{RESET}")
    ser.dtr = False
    ser.rts = True
    time.sleep(0.3)
    ser.rts = False
    time.sleep(0.1)
    print(f"{GREEN}>>> Reset pulse sent{RESET}")


def monitor(port, baud, logfile_path):
    """Main monitoring loop with auto-reconnect."""
    global crash_count, boot_count, last_boot_time

    logfile = None
    if logfile_path:
        logfile = open(logfile_path, "a", encoding="utf-8")
        logfile.write(
            f"\n{'='*60}\nSession started: {datetime.now().isoformat()}\n{'='*60}\n"
        )

    print(f"{CYAN}{BOLD}")
    print(f"  ESP32 Irrigation Serial Monitor")
    print(f"  Port: {port} @ {baud} baud")
    if logfile_path:
        print(f"  Log:  {logfile_path}")
    print(f"  Ctrl+C to exit")
    print(f"{RESET}")

    while True:
        try:
            print(f"{GREEN}Connecting to {port}...{RESET}")
            ser = serial.Serial(port, baud, timeout=1, dsrdtr=False, rtscts=False)
            ser.reset_input_buffer()
            print(f"{GREEN}Connected! Waiting for output...{RESET}\n")

            # Do an initial reset to get fresh boot log
            reset_device(ser)

            line_buf = b""
            status_timer = time.time()

            while True:
                # Read available data
                avail = ser.in_waiting
                if avail > 0:
                    data = ser.read(avail)
                elif ser.in_waiting == 0:
                    data = ser.read(1)
                else:
                    data = b""

                if data:
                    line_buf += data
                    # Process complete lines
                    while b"\n" in line_buf:
                        line, line_buf = line_buf.split(b"\n", 1)
                        raw = line.decode("utf-8", errors="replace")
                        colored, clean = format_line(raw)

                        if colored and clean:
                            print(colored)

                            # Log to file
                            if logfile:
                                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[
                                    :-3
                                ]
                                logfile.write(f"[{ts}] {clean}\n")
                                logfile.flush()

                            # Track crashes
                            if CRASH_RE.search(clean):
                                crash_count += 1
                                print(
                                    f"{RED}{BOLD}>>> CRASH #{crash_count} DETECTED <<<{RESET}"
                                )

                            # Track boots
                            if "IRRIGATION BOOT" in clean:
                                boot_count += 1
                                last_boot_time = time.time()
                                print(
                                    f"{CYAN}{BOLD}>>> Boot #{boot_count} detected <<<{RESET}"
                                )

                            # Track heap
                            track_heap(clean)

                # Print status every 5 minutes
                if time.time() - status_timer > 300:
                    print_status()
                    status_timer = time.time()

        except serial.SerialException as e:
            print(f"{RED}Serial error: {e}{RESET}")
            print(f"{YELLOW}Reconnecting in 3 seconds...{RESET}")
            time.sleep(3)
        except KeyboardInterrupt:
            print(f"\n{YELLOW}Exiting monitor...{RESET}")
            print_status()
            if logfile:
                logfile.close()
            try:
                ser.close()
            except Exception:
                pass
            return
        except Exception as e:
            print(f"{RED}Error: {e}{RESET}")
            print(f"{YELLOW}Retrying in 3 seconds...{RESET}")
            time.sleep(3)


def main():
    parser = argparse.ArgumentParser(description="ESP32 Irrigation Serial Monitor")
    parser.add_argument(
        "--port", default=None, help="Serial port (auto-detected if not specified)"
    )
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate")
    parser.add_argument(
        "--log",
        default="irrigation_serial.log",
        help="Log file path (default: irrigation_serial.log)",
    )
    args = parser.parse_args()

    port = args.port or find_esp32_port()
    if not port:
        print(f"{RED}No ESP32 USB serial port found!{RESET}")
        print("Available ports:")
        for p in serial.tools.list_ports.comports():
            print(f"  {p.device} - {p.description}")
        sys.exit(1)

    monitor(port, args.baud, args.log)


if __name__ == "__main__":
    main()
