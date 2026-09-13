"""NAVI mobile mode — per-tab response mirroring + Telegram-driven turns.

No tmux. Each Claude Code tab is identified by its CLAUDE_CODE_SESSION_ID
(== the Stop hook's `session_id`). A tab opts in by running the /navi-mobile
skill (-> navi_tab.py on), which drops a per-session flag here. While the flag
is set, the Stop hook (navi_response_hook.py) forwards that tab's responses to
the single Telegram chat and BLOCKS waiting for the user's reply, which it feeds
back as the tab's next turn ({"decision":"block","reason": <reply>}).

State under ~/.navi/mobile:
  on_<sid>          -> flag file (presence = tab is on mobile); JSON {label,cwd,ts}
  reply_<sid>.txt   -> the bot writes the user's reply here; the hook consumes it
  msg_<message_id>.json -> {"sid": ...} so a Telegram *reply* maps to its tab
  last_session      -> most recently forwarded sid (for plain, non-reply texts)

Correlation mirrors the permission gate's req_id pattern, so one chat cleanly
spans many concurrent tabs: reply to a tab's message -> drives that exact tab.
"""
from __future__ import annotations

import os
import json
import time

NAVI_DIR = os.path.join(os.path.expanduser("~"), ".navi")
MOBILE_DIR = os.path.join(NAVI_DIR, "mobile")
EXIT_SENTINEL = "__EXIT__"


def _ensure() -> None:
    os.makedirs(MOBILE_DIR, mode=0o700, exist_ok=True)


def short(sid) -> str:
    return (sid or "")[:6] or "tab"


def _flag(sid):
    return os.path.join(MOBILE_DIR, f"on_{sid}")


def _reply(sid):
    return os.path.join(MOBILE_DIR, f"reply_{sid}.txt")


def _msg(mid):
    return os.path.join(MOBILE_DIR, f"msg_{mid}.json")


# ---- per-session mobile flag --------------------------------------------

def session_on(sid) -> bool:
    return bool(sid) and os.path.exists(_flag(sid))


def set_session(sid, on: bool, label: str = "", cwd: str = "") -> None:
    if not sid:
        return
    _ensure()
    if on:
        with open(_flag(sid), "w") as f:
            json.dump({"label": label, "cwd": cwd, "ts": time.time()}, f)
    else:
        try:
            os.unlink(_flag(sid))
        except OSError:
            pass


def session_info(sid) -> dict:
    try:
        with open(_flag(sid)) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def list_sessions() -> list:
    out = []
    try:
        for fn in os.listdir(MOBILE_DIR):
            if fn.startswith("on_"):
                sid = fn[3:]
                info = session_info(sid)
                out.append({"sid": sid, "label": info.get("label", ""), "cwd": info.get("cwd", "")})
    except OSError:
        pass
    return out


# ---- message <-> session mapping ----------------------------------------

def record_forward(message_id, sid) -> None:
    _ensure()
    with open(_msg(message_id), "w") as f:
        json.dump({"sid": sid, "ts": time.time()}, f)
    with open(os.path.join(MOBILE_DIR, "last_session"), "w") as f:
        f.write(sid)
    _prune()


def session_for_message(message_id):
    try:
        with open(_msg(message_id)) as f:
            return json.load(f).get("sid")
    except (OSError, ValueError):
        return None


def last_session():
    try:
        with open(os.path.join(MOBILE_DIR, "last_session")) as f:
            return f.read().strip() or None
    except OSError:
        return None


# ---- reply channel (bot writes, hook consumes) --------------------------

def write_reply(sid, text) -> None:
    _ensure()
    p = _reply(sid)
    tmp = p + ".tmp"
    with open(tmp, "w") as f:
        f.write(text)
    os.replace(tmp, p)


def take_reply(sid):
    """Read and delete the pending reply for a session (hook side)."""
    p = _reply(sid)
    try:
        with open(p) as f:
            t = f.read()
        os.unlink(p)
        return t
    except OSError:
        return None


def release(sid) -> None:
    """Phone side: unblock a waiting hook and turn the tab's flag off."""
    write_reply(sid, EXIT_SENTINEL)
    set_session(sid, False)


def _prune(max_age: int = 86400) -> None:
    try:
        now = time.time()
        for fn in os.listdir(MOBILE_DIR):
            if fn.startswith("msg_") and fn.endswith(".json"):
                fp = os.path.join(MOBILE_DIR, fn)
                try:
                    if now - os.path.getmtime(fp) > max_age:
                        os.unlink(fp)
                except OSError:
                    pass
    except OSError:
        pass


# ---- Telegram entry points (called from telegram_bot.py main loop) -------

def handle_mobile_command(text, chat_id, send_message) -> bool:
    """/tabs, /desktop [id], /mobile (help), /mode. Returns True if handled."""
    t = (text or "").strip()
    parts = t.split()
    cmd = parts[0].lower() if parts else ""
    if cmd not in ("/tabs", "/desktop", "/mobile", "/mode"):
        return False

    if cmd in ("/tabs", "/mode"):
        ss = list_sessions()
        if not ss:
            send_message(chat_id, "No tabs on mobile. Run /navi-mobile inside a Claude tab to enable one.")
            return True
        lines = ["\U0001f4f1 Tabs on mobile:"]
        for s in ss:
            lbl = s["label"] or os.path.basename(s["cwd"] or "")
            lines.append(f"• {short(s['sid'])}  {lbl}")
        lines.append("\nReply to a tab's message to drive it. /desktop <id> to release (or /desktop for all).")
        send_message(chat_id, "\n".join(lines))
        return True

    if cmd == "/mobile":
        send_message(chat_id,
                     "To put a tab on mobile, run /navi-mobile *inside that Claude tab*.\n"
                     "Then reply here to drive it. /tabs to list · /desktop to release.")
        return True

    if cmd == "/desktop":
        target = parts[1] if len(parts) > 1 else None
        ss = list_sessions()
        if not ss:
            send_message(chat_id, "No tabs on mobile.")
            return True
        released = []
        for s in ss:
            if target is None or s["sid"].startswith(target):
                release(s["sid"])
                released.append(short(s["sid"]))
        if released:
            send_message(chat_id, "\U0001f5a5 Released to keyboard: " + ", ".join(released))
        else:
            send_message(chat_id, f"No tab matching '{target}'.")
        return True

    return False


def handle_mobile_reply(msg, text, chat_id, send_message) -> bool:
    """Route a Telegram reply to its tab's reply channel. True if consumed."""
    if not text or text.startswith("/"):
        return False

    sid = None
    reply_to = (msg.get("reply_to_message") or {}).get("message_id")
    if reply_to is not None:
        sid = session_for_message(reply_to)
    if not sid:
        # plain text: route to the most-recent tab, only if some tab is on mobile
        if list_sessions():
            sid = last_session()
    if not sid or not session_on(sid):
        return False

    write_reply(sid, text)
    send_message(chat_id, f"➡️ tab {short(sid)}")
    return True
