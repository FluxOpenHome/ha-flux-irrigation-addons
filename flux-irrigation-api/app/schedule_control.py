"""
Flux Open Home - Schedule Control
===================================
Shared helpers for disabling/enabling ESPHome schedule programs.

When the system is paused (manual, weather, or API), the actual ESPHome
schedule enable switches must be turned off to prevent the controller
from starting watering runs autonomously. On resume, they are restored
to their prior state.

The saved schedule states are stored in /data/schedules.json under the
key "saved_schedule_states" so they survive add-on restarts.
"""

import re
import ha_client
from config import get_config


# Pattern to identify schedule enable switches:
#   - Must be a switch.* entity
#   - Must contain "schedule" and "enable"
#   - Must NOT contain day names (those are day-of-week toggles)
#   - Must NOT contain "enable_zone" (those are zone enable toggles)
_DAY_PATTERN = re.compile(
    r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)", re.IGNORECASE
)


def _is_schedule_enable(entity_id: str) -> bool:
    """Check if an entity_id is a schedule program enable switch."""
    if not entity_id.startswith("switch."):
        return False
    lower = entity_id.lower()
    if "schedule" not in lower:
        return False
    if "enable" not in lower:
        return False
    if "enable_zone" in lower:
        return False
    if _DAY_PATTERN.search(lower):
        return False
    return True


def get_schedule_enable_entities() -> list[str]:
    """Return all schedule enable switch entity_ids from the config."""
    config = get_config()
    return [
        eid for eid in config.allowed_control_entities
        if _is_schedule_enable(eid)
    ]


async def disable_schedules() -> dict[str, str]:
    """Disable all schedule programs by turning off their enable switches.

    Returns a dict of {entity_id: previous_state} so they can be restored.
    The caller is responsible for saving this to schedules.json.
    """
    schedule_entities = get_schedule_enable_entities()
    if not schedule_entities:
        print("[SCHED_CTRL] No schedule enable entities found — nothing to disable")
        return {}

    # Get current states before disabling
    states = await ha_client.get_entities_by_ids(schedule_entities)
    saved_states = {}

    for entity in states:
        entity_id = entity["entity_id"]
        current_state = entity.get("state", "unknown")
        saved_states[entity_id] = current_state

        if current_state == "on":
            success = await ha_client.call_service(
                "switch", "turn_off", {"entity_id": entity_id}
            )
            if success:
                print(f"[SCHED_CTRL] Disabled schedule: {entity_id}")
            else:
                print(f"[SCHED_CTRL] Failed to disable schedule: {entity_id}")

    print(f"[SCHED_CTRL] Disabled {len(saved_states)} schedule(s): {saved_states}")
    return saved_states


async def restore_schedules(saved_states: dict[str, str]):
    """Restore schedule programs to their saved states.

    Args:
        saved_states: Dict of {entity_id: state} from a previous disable_schedules() call.
                      Only entities that were "on" before will be turned back on.
    """
    if not saved_states:
        # Fallback: no saved states were persisted (e.g. entity discovery failed
        # during pause, or states were lost).  Turn ON all schedule enable entities
        # to ensure the schedule is never left permanently disabled.
        all_entities = get_schedule_enable_entities()
        if not all_entities:
            print("[SCHED_CTRL] No saved states AND no schedule enable entities found")
            return
        print(f"[SCHED_CTRL] No saved states — fallback: turning ON "
              f"{len(all_entities)} schedule enable(s)")
        for eid in all_entities:
            success = await ha_client.call_service(
                "switch", "turn_on", {"entity_id": eid}
            )
            if success:
                print(f"[SCHED_CTRL] Fallback restored: {eid}")
            else:
                print(f"[SCHED_CTRL] Fallback FAILED: {eid}")
        return

    restored = []
    for entity_id, previous_state in saved_states.items():
        if previous_state == "on":
            success = await ha_client.call_service(
                "switch", "turn_on", {"entity_id": entity_id}
            )
            if success:
                restored.append(entity_id)
                print(f"[SCHED_CTRL] Restored schedule: {entity_id}")
            else:
                print(f"[SCHED_CTRL] Failed to restore schedule: {entity_id}")

    print(f"[SCHED_CTRL] Restored {len(restored)} schedule(s)")
