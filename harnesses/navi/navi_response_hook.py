#!/usr/bin/env python3
"""Stop hook — NAVI mobile mode (no tmux).

Fires when a Claude Code tab finishes a turn. If THIS tab is on mobile
(a ~/.navi/mobile/on_<session_id> flag exists), it:
  1. forwards the final assistant message to the single Telegram chat,
  2. records message_id -> session_id (so a Telegram reply maps back here),
  3. BLOCKS, polling for the user's reply, then feeds it back as the next turn
     via {"decision":"block","reason": <reply>} on stdout.

Reply of __EXIT__ / "/desktop" / "stop" (or timeout) hands the tab back to the
keyboard (exit 0, no block). Desktop tabs are a fast no-op. Fails silent.

Timeout is NAVI_MOBILE_TIMEOUT seconds (default 600); if Claude Code kills the
hook sooner, the turn simply returns to the keyboard (safe).
"""
import sys
import os
import json
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
NAVI_ENV = os.path.join(HERE, ".env")
POLL_TIMEOUT = int(os.environ.get("NAVI_MOBILE_TIMEOUT", "600"))
EXIT_WORDS = {"__EXIT__", "/desktop", "desktop", "stop", "exit"}


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


def last_assistant_text(transcript_path):
    try:
        lines = open(transcript_path, encoding="utf-8").read().splitlines()
    except OSError:
        return ""
    text = ""
    for ln in lines:
        try:
            o = json.loads(ln)
        except Exception:
            continue
        if o.get("type") != "assistant" and o.get("role") != "assistant":
            continue
        content = (o.get("message") or {}).get("content")
        blocks = []
        if isinstance(content, list):
            for b in content:
                if isinstance(b, dict) and b.get("type") == "text" and b.get("text"):
                    blocks.append(b["text"])
        elif isinstance(content, str):
            blocks.append(content)
        if blocks:
            text = "\n".join(blocks)
    return text.strip()


def chunk_text(text, limit=3500, max_chunks=8):
    """Split on paragraph, then line, then hard boundaries. Telegram caps a
    message at 4096 chars; we leave headroom for the header and part marker."""
    if len(text) <= limit:
        return [text]
    chunks, buf = [], ""

    def flush():
        nonlocal buf
        if buf:
            chunks.append(buf)
            buf = ""

    for para in text.split("\n\n"):
        if len(para) > limit:
            flush()
            for line in para.split("\n"):
                while len(line) > limit:
                    chunks.append(line[:limit])
                    line = line[limit:]
                if not buf:
                    buf = line
                elif len(buf) + 1 + len(line) <= limit:
                    buf += "\n" + line
                else:
                    flush()
                    buf = line
            continue
        if not buf:
            buf = para
        elif len(buf) + 2 + len(para) <= limit:
            buf += "\n\n" + para
        else:
            flush()
            buf = para
    flush()

    if len(chunks) > max_chunks:
        dropped = len(chunks) - max_chunks
        chunks = chunks[:max_chunks]
        chunks[-1] += (
            "\n\n…(%d more part%s suppressed — read the full reply on desktop)"
            % (dropped, "" if dropped == 1 else "s")
        )
    return chunks


def send_telegram(token, chat_id, text):
    data = json.dumps({"chat_id": int(chat_id), "text": text}).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=data, headers={"Content-Type": "application/json"},
    )
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read().decode()).get("result", {}).get("message_id")
    except Exception:
        return None


def main():
    try:
        hook = json.load(sys.stdin)
    except Exception:
        return

    sid = hook.get("session_id") or os.environ.get("CLAUDE_CODE_SESSION_ID")

    try:
        import mobile_mode
    except Exception:
        return
    if not sid or not mobile_mode.session_on(sid):
        return  # desktop tab -> no-op

    load_env()
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_USER_ID")
    if not token or not chat_id:
        return

    resp = last_assistant_text(hook.get("transcript_path") or "")
    if not resp:
        return  # tool-only turn; nothing to mirror, don't block

    cwd = hook.get("cwd") or os.getcwd()
    project = os.path.basename(cwd) or "session"
    sh = mobile_mode.short(sid)
    parts = chunk_text(resp)
    total = len(parts)
    for i, part in enumerate(parts, 1):
        marker = f" ({i}/{total})" if total > 1 else ""
        mid = send_telegram(
            token, chat_id, f"\U0001f4f1 {project} · {sh}{marker}\n\n{part}"
        )
        # Map every part back to this session, so replying to any of them lands here.
        if mid:
            try:
                mobile_mode.record_forward(mid, sid)
            except Exception:
                pass

    # Block until the user replies from Telegram (or times out).
    deadline = time.time() + POLL_TIMEOUT
    while time.time() < deadline:
        reply = mobile_mode.take_reply(sid)
        if reply is not None:
            r = reply.strip()
            if r in EXIT_WORDS or r.lower() in EXIT_WORDS:
                mobile_mode.set_session(sid, False)
                send_telegram(token, chat_id, f"\U0001f5a5 tab {sh} released to keyboard.")
                return  # exit 0 -> back to keyboard
            # Feed the reply back as this tab's next turn.
            print(json.dumps({
                "decision": "block",
                "reason": reply,
                "systemMessage": f"\U0001f4f1 via Telegram → {sh}",
            }))
            return
        time.sleep(2)

    # Timed out waiting for a reply.
    mobile_mode.set_session(sid, False)
    send_telegram(token, chat_id,
                  f"⏳ tab {sh} idle {POLL_TIMEOUT // 60}m — released to keyboard. /navi-mobile to resume.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
