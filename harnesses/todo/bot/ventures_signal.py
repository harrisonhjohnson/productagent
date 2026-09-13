"""
Ventures signal — the PM system's Navi transport (ventures standup #8 accord, 2026-08-24).

Navi carries SIGNALS from ~/ventures (lane states, queue, alerts) and executes the
bounded verbs — ack / pause / resume / decide / standup-request — as the operator's own
unfenced process. It never holds ventures state and never runs the meeting.

Contract (pm/LOG.md, 2026-08-24 evening entry): one machine, same gates, any channel —
every action here lands in a ventures file, dated, marked "via Navi". Orders and TODOs
stay separate systems.
"""

import hashlib
import json
import logging
import os
import re
from datetime import date, datetime
try:
    from config import USER_NAME
except ImportError:  # pragma: no cover
    USER_NAME = "you"

logger = logging.getLogger(__name__)

_STATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ventures_state.json")

LANES = ("night", "day")


def _root():
    try:
        import config
        root = getattr(config, "VENTURES_ROOT", None)
    except Exception:
        root = None
    return root or os.path.expanduser("~/ventures")


def _lane_dir(lane):
    return os.path.join(_root(), "00-ops", lane)


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


# ---- readers ---------------------------------------------------------------

def read_lane(lane):
    """One lane's run-state + standing alert. Never raises."""
    out = {"lane": lane, "state": None, "alert": None}
    try:
        with open(os.path.join(_lane_dir(lane), "run-state.json")) as f:
            out["state"] = json.load(f)
    except Exception:
        pass
    try:
        alert_path = os.path.join(_lane_dir(lane), "ALERT.md")
        if os.path.isfile(alert_path):
            with open(alert_path) as f:
                lines = f.read().strip().splitlines()
            out["alert"] = lines[2] if len(lines) > 2 else (lines[0] if lines else "(empty)")
    except Exception:
        pass
    return out


def pending_orders():
    """Count unchecked '- [ ]' lines in ORDERS.md '## Tonight' section (mirrors the
    night wrapper's awk). Returns int or None on read failure."""
    try:
        with open(os.path.join(_root(), "pm", "ORDERS.md")) as f:
            lines = f.read().splitlines()
        n, inside = 0, False
        for line in lines:
            if line.startswith("## Tonight"):
                inside = True
                continue
            if re.match(r"^## ", line):
                inside = False
            if inside and line.startswith("- [ ]"):
                n += 1
        return n
    except Exception:
        return None


def capture_info():
    out = {"last_ac": None, "paused": False}
    cap = os.path.join(_root(), "00-ops", "capture")
    try:
        with open(os.path.join(cap, "last-ac")) as f:
            out["last_ac"] = f.read().strip()
    except Exception:
        pass
    out["paused"] = os.path.isfile(os.path.join(cap, "PAUSED"))
    return out


def _day_word(iso_date):
    try:
        d = date.fromisoformat(iso_date)
    except Exception:
        return iso_date or "never"
    delta = (date.today() - d).days
    return {0: "today", 1: "yesterday"}.get(delta, f"{iso_date} ({delta}d ago)")


def _lane_line(info):
    s = info["state"]
    if not s:
        return f"  {info['lane']}: no state file"
    cost = s.get("cost_usd", 0)
    return (f"  {info['lane']}: {s.get('status', '?')} {_day_word(s.get('date', ''))}"
            f" (${cost:.2f})" if isinstance(cost, (int, float)) else
            f"  {info['lane']}: {s.get('status', '?')} {_day_word(s.get('date', ''))}")


# ---- renderer --------------------------------------------------------------

def render_section(kind="status"):
    """Message lines for the ventures signal. kind: 'morning' | 'evening' | 'status'.
    Returns [] only on total failure — callers may append directly."""
    try:
        lanes = [read_lane(l) for l in LANES]
        cap = capture_info()
        q = pending_orders()
        alerts = [i for i in lanes if i["alert"]]

        header = {"morning": "🏭 VENTURES — dawn read-back:",
                  "evening": "🏭 VENTURES — dusk queue check:",
                  "status": "🏭 VENTURES:"}[kind]
        parts = [header]
        if cap["paused"]:
            parts.append("  ⏸ capture PAUSED (resume with: /ventures resume)")
        for i in lanes:
            parts.append(_lane_line(i))
        for i in alerts:
            parts.append(f"  🔴 {i['lane']} ALERT standing: {i['alert']}")
            parts.append(f"     ack with: /ventures ack {i['lane']}")

        if kind == "evening":
            if q is None:
                parts.append("  queue: ORDERS.md unreadable")
            elif q == 0:
                parts.append("  queue: empty for tonight (a valid answer)")
            else:
                parts.append(f"  queue: {q} order(s) armed for the next capture window")
            if alerts:
                parts.append("  ⚠️ queue contract: no NEW orders while an alert stands — read back first")
        elif kind == "morning":
            bad = [i for i in lanes if i["state"] and i["state"].get("status")
                   not in ("ok", "no-orders")]
            if alerts or bad:
                parts.append("  → read-back due: convene standup at the desk")
            else:
                parts.append("  → both lanes clean; nothing to decide is a complete meeting")
        else:  # status
            if q is not None:
                parts.append(f"  queue: {q} unchecked Tonight order(s)")
            if cap["last_ac"]:
                parts.append(f"  last AC window: {_day_word(cap['last_ac'])}")
        return parts
    except Exception as e:
        logger.error(f"ventures render failed: {e}")
        return []


# ---- immediate alert relay -------------------------------------------------

def _load_seen():
    try:
        with open(_STATE_PATH) as f:
            return json.load(f)
    except Exception:
        return {}


def _save_seen(seen):
    try:
        with open(_STATE_PATH, "w") as f:
            json.dump(seen, f)
    except Exception as e:
        logger.error(f"ventures state save failed: {e}")


def scan_alerts():
    """Return push strings for new/changed ALERT.md files; dedup persisted across
    restarts. An alert deleted (acked) and later rewritten pushes again."""
    pushes = []
    seen = _load_seen()
    changed = False
    for lane in LANES:
        path = os.path.join(_lane_dir(lane), "ALERT.md")
        key = f"alert:{lane}"
        try:
            if os.path.isfile(path):
                with open(path) as f:
                    content = f.read()
                digest = hashlib.sha1(content.encode()).hexdigest()
                if seen.get(key) != digest:
                    body = "\n".join(content.strip().splitlines()[:12])
                    pushes.append(f"🔴 VENTURES {lane.upper()} ALERT\n\n{body}\n\n"
                                  f"ack with: /ventures ack {lane}")
                    seen[key] = digest
                    changed = True
            elif key in seen:
                del seen[key]
                changed = True
        except Exception as e:
            logger.error(f"ventures alert scan ({lane}): {e}")
    if changed:
        _save_seen(seen)
    return pushes


# ---- bounded verbs ---------------------------------------------------------

def ack(lane):
    if lane not in LANES:
        return f"Unknown lane '{lane}'. Lanes: night, day."
    path = os.path.join(_lane_dir(lane), "ALERT.md")
    if not os.path.isfile(path):
        return f"No standing {lane} alert."
    try:
        with open(path) as f:
            lines = f.read().strip().splitlines()
        headline = lines[2] if len(lines) > 2 else "(unreadable)"
        log_path = os.path.join(_lane_dir(lane), "logs", f"{date.today().isoformat()}.log")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a") as f:
            f.write(f"[navi] {_now()} ALERT acknowledged by {USER_NAME} via Telegram"
                    f" — was: {headline}\n")
        os.remove(path)
        return f"Acked {lane} alert: {headline}\n(logged to the lane's daily log)"
    except Exception as e:
        return f"Ack failed: {e}"


def pause():
    path = os.path.join(_root(), "00-ops", "capture", "PAUSED")
    try:
        with open(path, "w") as f:
            f.write(f"paused by {USER_NAME} via Navi {_now()}\n")
        return "⏸ Capture paused — no lane fires until /ventures resume."
    except Exception as e:
        return f"Pause failed: {e}"


def resume():
    path = os.path.join(_root(), "00-ops", "capture", "PAUSED")
    try:
        if os.path.isfile(path):
            os.remove(path)
            return "▶️ Capture resumed — next poll may fire within 10 min if on AC."
        return "Capture wasn't paused."
    except Exception as e:
        return f"Resume failed: {e}"


def decide(text):
    """Append a charter-defined directive line to pm/LOG.md — the next standup applies
    it and notes the change (pm/CHARTER.md defines this mechanism)."""
    if not text.strip():
        return "Usage: /ventures decide <one-line decision>"
    try:
        log_path = os.path.join(_root(), "pm", "LOG.md")
        with open(log_path) as f:
            lines = f.read().splitlines(keepends=False)
        directive = f"> directive: {text.strip()} ({USER_NAME} via Navi, {_now()})"
        for i, line in enumerate(lines):
            if line.strip() == "---":
                lines.insert(i + 1, "")
                lines.insert(i + 2, directive)
                break
        else:
            lines.append(directive)
        with open(log_path, "w") as f:
            f.write("\n".join(lines) + "\n")
        return f"Pinned for the next standup:\n{directive}"
    except Exception as e:
        return f"Decide failed: {e}"


def standup_request():
    msg = decide("convene standup — requested via Navi")
    return (f"{msg}\n\nThe meeting runs at the desk by default (evidence gets graded "
            f"against diffs there). From the phone: open a desk tab in navi-mobile "
            f"mode and type 'standup' — flagged as a Navi-driven meeting.")


# ---- command surface -------------------------------------------------------

def handle_ventures_command(text, chat_id, user_id):
    """'/ventures [status|ack <lane>|pause|resume|decide <text>|standup]' -> reply str."""
    parts = text.split()
    sub = parts[1].lower() if len(parts) > 1 else "status"
    if sub == "status":
        return "\n".join(render_section("status")) or "ventures signal unavailable"
    if sub == "ack":
        if len(parts) < 3:
            return "Usage: /ventures ack night|day"
        return ack(parts[2].lower())
    if sub == "pause":
        return pause()
    if sub == "resume":
        return resume()
    if sub == "decide":
        return decide(text.split(None, 2)[2] if len(parts) > 2 else "")
    if sub == "standup":
        return standup_request()
    return ("Unknown ventures command. Available: status · ack night|day · pause · "
            "resume · decide <text> · standup")
