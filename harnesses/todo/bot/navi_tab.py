#!/usr/bin/env python3
"""navi_tab.py — flip the CURRENT Claude Code tab into / out of NAVI mobile mode.

Run *inside* a Claude Code tab (by the /navi-mobile skill, or manually). Keys off
CLAUDE_CODE_SESSION_ID, which is present in the tab's tool environment and equals
the Stop hook's session_id.

  python3 navi_tab.py on       # this tab -> mobile (responses stream to Telegram)
  python3 navi_tab.py off      # this tab -> desktop
  python3 navi_tab.py status
"""
import sys
import os
import json
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
NAVI_ENV = os.path.join(HERE, ".env")


def load_env():
    if not os.path.exists(NAVI_ENV):
        return
    for line in open(NAVI_ENV):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def tg(text):
    load_env()
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_USER_ID")
    if not token or not chat_id:
        return
    data = json.dumps({"chat_id": int(chat_id), "text": text}).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=data, headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception:
        pass


def current_sid():
    return os.environ.get("CLAUDE_CODE_SESSION_ID") or os.environ.get("TERM_SESSION_ID") or ""


def main():
    import mobile_mode as m

    action = (sys.argv[1] if len(sys.argv) > 1 else "on").lower()
    sid = current_sid()
    if not sid:
        print("No CLAUDE_CODE_SESSION_ID — run this inside a Claude Code tab.")
        return 1

    cwd = os.getcwd()
    label = os.path.basename(cwd) or "session"
    sh = m.short(sid)

    if action == "on":
        m.set_session(sid, True, label=label, cwd=cwd)
        tg(f"\U0001f4f1 Mobile ON — tab {sh} ({label}).\n"
           f"This tab's responses stream here; reply to drive it. "
           f"/desktop {sh} to release (or Ctrl-C in the tab).")
        print(f"Mobile mode ON for this tab (id {sh}). Responses now stream to Telegram; "
              f"reply there to continue this tab. Send /desktop from Telegram (or Ctrl-C here) "
              f"to hand control back to the keyboard.")
    elif action == "off":
        m.set_session(sid, False)
        tg(f"\U0001f5a5 Mobile OFF — tab {sh} back to keyboard.")
        print(f"Mobile mode OFF for this tab (id {sh}).")
    elif action == "status":
        print(f"{'mobile' if m.session_on(sid) else 'desktop'} | tab {sh} | {label}")
    else:
        print(f"Unknown action: {action} (use on|off|status)")
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"navi_tab error: {e}")
        sys.exit(1)
