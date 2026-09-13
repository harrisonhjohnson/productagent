"""
Mac-native behavioral state inference for NAVI.

Reads ambient macOS signals to predict one of 5 behavioral states,
used by the scheduler to decide whether to send a message now or defer it.
"""
import subprocess
import re
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# Import known SSIDs from config — leave None to skip SSID-based detection
try:
    import config as _config
    HOME_SSID = getattr(_config, 'BEHAVIOR_HOME_SSID', None)
    OFFICE_SSID = getattr(_config, 'BEHAVIOR_OFFICE_SSID', None)
except ImportError:
    HOME_SSID = None
    OFFICE_SSID = None


def _run(cmd: list, timeout: int = 3) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout
    except Exception:
        return ""


def get_wifi_ssid() -> Optional[str]:
    out = _run(["networksetup", "-getairportnetwork", "en0"])
    m = re.search(r"Current Wi-Fi Network: (.+)", out)
    return m.group(1).strip() if m else None


def get_battery() -> dict:
    out = _run(["pmset", "-g", "batt"])
    pct_m = re.search(r"(\d+)%", out)
    return {
        "percent": int(pct_m.group(1)) if pct_m else 50,
        "charging": "AC Power" in out or "charging" in out.lower(),
    }


def get_screen_idle_seconds() -> int:
    """Returns seconds since last user input, or -1 on failure."""
    out = _run(["ioreg", "-c", "IOHIDSystem"])
    m = re.search(r'"HIDIdleTime"\s*=\s*(\d+)', out)
    if m:
        return int(m.group(1)) // 1_000_000_000
    return -1


def get_state() -> str:
    """
    Infer behavioral state from macOS ambient signals.
    Returns one of: HEADS_DOWN, ON_THE_MOVE, OFF_THE_CLOCK, AWAY, AVAILABLE
    """
    now = datetime.now()
    hour = now.hour
    is_weekend = now.weekday() >= 5

    ssid = get_wifi_ssid()
    battery = get_battery()
    idle_s = get_screen_idle_seconds()

    at_home = bool(HOME_SSID and ssid == HOME_SSID)
    at_office = bool(OFFICE_SSID and ssid == OFFICE_SSID)
    ssids_configured = bool(HOME_SSID or OFFICE_SSID)
    at_known = (at_home or at_office) if ssids_configured else True

    is_sleep_hours = hour < 7 or hour >= 23
    is_work_hours = not is_weekend and 8 <= hour < 19
    is_evening = 19 <= hour < 23
    screen_idle = idle_s > 300 if idle_s >= 0 else False       # 5 min
    screen_deep_idle = idle_s > 1800 if idle_s >= 0 else False  # 30 min

    if is_sleep_hours or screen_deep_idle:
        return "AWAY"

    if not at_known:
        return "ON_THE_MOVE"

    if is_evening and (at_home or not ssids_configured):
        return "OFF_THE_CLOCK"

    if is_work_hours and at_known and not screen_idle and battery["charging"]:
        return "HEADS_DOWN"

    if is_work_hours and at_known:
        return "AVAILABLE"

    return "AVAILABLE"


def is_good_time_to_interrupt() -> bool:
    """True when it's appropriate to fire a scheduled push message."""
    try:
        state = get_state()
        return state in ("AVAILABLE", "HEADS_DOWN")
    except Exception as e:
        logger.warning(f"behavior_state check failed, defaulting to True: {e}")
        return True
