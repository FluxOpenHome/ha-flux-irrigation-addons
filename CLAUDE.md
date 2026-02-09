# CLAUDE.md

## Critical Rules

### Python Triple-Quoted Strings with JavaScript onclick Handlers

**CRITICAL: In Python triple-quoted strings (`"""`), the escape `\'` produces a plain single quote `'` — it does NOT produce a backslash-quote `\'` in the output.**

When building JavaScript `onclick` handlers inside HTML that's embedded in a Python triple-quoted string, you MUST use `\\'` (backslash-backslash-quote) to produce `\'` in the JS output.

**WRONG (causes JS parse error — kills entire script block silently):**
```python
html += '<button onclick="myFunc(\'' + val + '\')">Click</button>';
```
Output: `onclick="myFunc('' + val + '')"` — JS sees empty strings, syntax error.

**CORRECT:**
```python
html += '<button onclick="myFunc(\\'' + val + '\\')">Click</button>';
```
Output: `onclick="myFunc(\'' + val + '\')"` — JS sees proper escaped quotes.

This applies to ALL files: `management_ui.py`, `admin.py`, `homeowner_ui.py`.

Similarly, `\d` in a Python triple-quoted string is an invalid escape sequence (SyntaxWarning in Python 3.12+). Use `\\d` to produce `\d` for JS regex patterns.

**General rule: Any backslash intended for the JS/HTML output must be doubled (`\\`) in the Python source.**


### Gophr ESPHome Deep Sleep — Sensor Value Retention

**CRITICAL: Gophr moisture probes sleep between readings. While asleep, Home Assistant marks ALL entities as `"unavailable"`. This includes depth sensors (shallow/mid/deep), device sensors (wifi, battery, sleep_duration), schedule times, and all other entities.**

**You MUST NEVER show zero, null, "—", or empty values when the device is sleeping.** The system maintains a **sensor value cache** (`_sensor_cache` in `moisture.py`, persisted to `/data/moisture_sensor_cache.json`) that stores the last valid numeric reading for every sensor entity.

**Rules:**
1. **Every API endpoint** that returns sensor values must use the sensor cache as a fallback when HA returns `"unavailable"` or `"unknown"`. This includes the probe detail endpoint (`GET /probes`), the multiplier calculation, and any other endpoint that reads sensor states.
2. **The UI must always show the last known value** with a `(retained)` indicator when the value is from cache. Bars should display at the retained percentage, not zero.
3. **The Awake/Sleeping status** uses a **write-probe** approach, NOT sensor state checks. HA retains ESPHome entity values long after the device sleeps, so checking `live_raw_state` is unreliable. Instead, the system attempts a harmless write to `min_awake_minutes` (toggleing between 1.0 and 1.5). If the write succeeds → awake. If HA returns an error → sleeping. A background poller (`_awake_poll_loop`) runs every 5 seconds to keep `_probe_awake_cache` fresh. The `is_awake` field in the probe API response comes from this cache.
4. **The sensor cache must be updated** whenever a good reading comes in (numeric value, not unavailable/unknown) and persisted to disk so it survives add-on restarts.
5. **Never reset multipliers to 1.0x** during sleep cycles. The cached readings ensure the moisture algorithm continues to use the last valid data.

**Pattern for any new endpoint that reads sensors:**
```python
_load_sensor_cache()
# ... fetch from HA ...
if raw in ("unavailable", "unknown") and eid in _sensor_cache:
    # Use cached value
    result = _sensor_cache[eid]
else:
    # Use live value, update cache
    _sensor_cache[eid] = {"state": numeric_val, ...}
```

### Gophr Sleep Duration Unit: MINUTES

**The Gophr ESPHome device uses MINUTES for its `sleep_duration` entity, NOT seconds.** All code that reads or writes sleep durations must use minutes:
- `_set_probe_sleep_duration(probe_id, minutes)` — writes minutes to the HA number entity
- `pending_sleep_duration` — stored in minutes
- `_original_sleep_durations` — stored in minutes (read from sensor which reports minutes)
- UI input — min 1, max 120, step 1, labeled "min"
- API endpoint `PUT /probes/{probe_id}/sleep-duration` — accepts `{ "minutes": N }`

### Enable Zone Switch for Skip Zones

**The enable_zone switch approach for skipping zones WORKS CORRECTLY.** `_find_enable_zone_switch()` finds switches in `config.allowed_control_entities` because enable_zone switches are classified in the "other" category by `ha_client.get_device_entities()`. Do NOT revert to setting `adjusted_value = 0.0` for skip — the enable switch approach properly disables/re-enables zone hardware.
