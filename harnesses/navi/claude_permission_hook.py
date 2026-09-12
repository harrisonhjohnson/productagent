#!/usr/bin/env python3
"""
PreToolUse hook for Claude Code — routes permission checks to Telegram via NAVI bot.

Claude Code calls this before every tool execution. We:
  1. Pass through pre-approved safe tools immediately.
  2. For risky tools: send a Telegram notification with inline keyboard buttons.
  3. Poll ~/.navi/permissions/<req_id>.decision (written by telegram_bot.py).
  4. Exit 0 to allow, exit 2 to block.

If Telegram is unreachable or NAVI's .env is missing, we pass through (fail open)
so Claude Code sessions don't freeze. Unhandled exceptions also fail open.
"""
import sys
import json
import os
import re
import secrets
import time
import urllib.request

PERM_DIR = os.path.join(os.path.expanduser("~"), ".navi", "permissions")
NAVI_ENV = os.path.expanduser("~/tools/navi/.env")

# Tools that always pass through without any notification
SILENT_TOOLS = {
    "Read", "LS", "Glob", "Grep", "NotebookRead", "TodoWrite",
    "WebSearch", "WebFetch", "ListMcpResourcesTool", "ReadMcpResourceTool",
    "ToolSearch", "TaskCreate", "TaskUpdate", "TaskGet", "TaskList",
}

# Bash command prefixes that always pass through silently
SILENT_BASH_PREFIXES = (
    "git status", "git diff", "git log", "git branch", "git show",
    "git stash list", "git fetch", "git remote", "git rev-parse",
    "git symbolic-ref", "git describe", "git tag -l", "git ls-files",
    "ls", "cat ", "rg ", "find ", "tree", "which ", "echo ", "printf ",
    "pwd", "wc ", "head ", "tail ", "sort ", "uniq ", "cut ",
    "grep ", "sed ", "awk ", "jq ", "python3 -c ", "python3 -m pytest",
    "python3 -m py_compile", "node -e ", "node --version",
    "npm test", "npm run test", "npm run lint", "npm run typecheck",
    "cargo test", "cargo check", "cargo build", "go test", "go build",
    "uv run pytest", "uv run ruff",
    # Venture iteration fleet — safe, high-frequency, non-destructive.
    # Default-branch pushes are still gated by Claude Code's auto-mode classifier.
    "git add", "git commit", "git checkout", "git switch", "git restore",
    "git rm", "git mv", "git pull", "git push", "git merge --ff-only",
    "git clone",
    "gh pr ", "gh api ", "gh repo view", "gh run ",
    "npm run ", "npm ci", "npm install", "npm i ",
    "pnpm ", "bun ", "yarn ",
    "pip install", "pip3 install", "uv pip install", "uv add ",
    "mkdir ", "cp ", "sips ", "stat ", "diff ",
    "chmod +x", "launchctl list", "claude mcp",
)

# Directories trusted to run without remote approval. Edit/Write under these
# roots pass silently, as do `cd <root> && ...` commands. Anything OUTSIDE these
# roots (system paths like /etc, /usr, /Library) still pings Telegram. Set to the
# whole home dir for low-friction local work; hard-block patterns are the floor.
TRUSTED_ROOTS = (os.path.realpath(os.path.expanduser("~")),)

# Patterns that should be hard-blocked (never sent to Telegram for approval)
HARD_BLOCK_PATTERNS = (
    "rm -rf /", "rm -rf ~", "rm -rf $HOME",
    ":(){ :|:& };:", "dd if=/dev/zero",
)


def init_perm_dir() -> None:
    """Create the IPC directory with owner-only permissions, tightening if it already existed."""
    os.makedirs(PERM_DIR, mode=0o700, exist_ok=True)
    os.chmod(PERM_DIR, 0o700)


def write_file_exclusive(path: str, content: str) -> None:
    """Write content to path using O_EXCL so a pre-planted file causes an error."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(content)


def read_decision_file(path: str) -> str:
    """Read a decision file, rejecting it if it isn't owned by us or has loose permissions."""
    st = os.stat(path)
    if st.st_uid != os.getuid():
        raise PermissionError(f"decision file owned by uid {st.st_uid}, expected {os.getuid()}")
    if st.st_mode & 0o077:
        raise PermissionError(f"decision file has group/other bits set: {oct(st.st_mode)}")
    with open(path) as f:
        return f.read().strip()


def load_env():
    if not os.path.exists(NAVI_ENV):
        return
    with open(NAVI_ENV) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k and k not in os.environ:
                os.environ[k] = v


def send_telegram(token: str, chat_id: str, text: str, reply_markup=None) -> bool:
    payload = {"chat_id": int(chat_id), "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception:
        return False


def under_trusted_root(path: str) -> bool:
    """True if path resolves to within a trusted root. realpath collapses '..' so
    `cd ~/../../etc` resolves to /etc and is correctly judged untrusted."""
    if not path:
        return False
    rp = os.path.realpath(os.path.expanduser(path))
    return any(rp == root or rp.startswith(root + os.sep) for root in TRUSTED_ROOTS)


# Leading `cd <dir>` followed by end-of-command / newline / && / ; / || — captures
# the target (quoted or bare). The newline form silences multi-line scripts that
# start by cd-ing into a trusted root, same trust as `cd <root> && ...` (use [ \t]*
# so the newline isn't swallowed before the alternation can match it).
_CD_PREFIX = re.compile(r"""^cd\s+('[^']*'|"[^"]*"|[^\s&;|]+)[ \t]*(?:$|\n|&&|;|\|\|)""")


def bash_is_silent(cmd: str) -> bool:
    cmd = cmd.strip()
    if any(cmd.startswith(p) for p in SILENT_BASH_PREFIXES):
        return True
    # `cd <trusted dir> && <anything>` — the user opted to trust runs anywhere
    # under home, so the whole command passes once we confirm the cd target.
    m = _CD_PREFIX.match(cmd)
    if m:
        target = m.group(1).strip("'\"")
        if under_trusted_root(target):
            return True
    return False


def is_silent(tool_name: str, tool_input: dict) -> bool:
    if tool_name in SILENT_TOOLS:
        return True
    if tool_name == "Bash":
        return bash_is_silent(tool_input.get("command") or "")
    if tool_name in ("Edit", "Write", "NotebookEdit"):
        path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
        return under_trusted_root(path)
    return False


def is_hard_blocked(tool_name: str, tool_input: dict) -> bool:
    if tool_name != "Bash":
        return False
    cmd = (tool_input.get("command") or "").strip()
    return any(p in cmd for p in HARD_BLOCK_PATTERNS)


def format_tool_description(tool_name: str, tool_input: dict) -> str:
    if tool_name == "Bash":
        cmd = (tool_input.get("command") or "").strip()
        desc = tool_input.get("description", "")
        if desc:
            return f"$ {cmd[:250]}\n({desc[:100]})"
        return f"$ {cmd[:300]}"
    if tool_name in ("Edit", "Write"):
        path = tool_input.get("file_path", "?")
        return f"{tool_name} → {path}"
    if tool_name == "Agent":
        label = tool_input.get("description", "")
        prompt = (tool_input.get("prompt") or "")[:120]
        return f"Spawn agent: {label}\n{prompt}"
    snippet = json.dumps(tool_input)[:200]
    return f"{tool_name}: {snippet}"


def main():
    init_perm_dir()
    load_env()

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_USER_ID")

    try:
        hook_input = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    if is_hard_blocked(tool_name, tool_input):
        print("Blocked: dangerous command pattern detected.")
        sys.exit(2)

    if is_silent(tool_name, tool_input):
        sys.exit(0)

    if not token or not chat_id:
        sys.exit(0)

    req_id = secrets.token_hex(16)  # 128 bits of CSPRNG → 32 hex chars
    cwd = os.getcwd()
    project = os.path.basename(cwd)
    tool_desc = format_tool_description(tool_name, tool_input)

    msg = (
        f"\U0001f512 Claude Code permission\n"
        f"Project: {project}\n\n"
        f"{tool_desc}\n\n"
        f"Allow? Tap below or reply:\n"
        f"y {req_id}  /  n {req_id}"
    )

    reply_markup = {
        "inline_keyboard": [[
            {"text": "✅ Allow", "callback_data": f"allow_{req_id}"},
            {"text": "❌ Deny", "callback_data": f"deny_{req_id}"},
        ]]
    }

    pending_path = os.path.join(PERM_DIR, f"{req_id}.pending")
    try:
        write_file_exclusive(pending_path, json.dumps({"tool": tool_name, "input": tool_input, "cwd": cwd}))
    except FileExistsError:
        print(f"Pending file collision for {req_id}. Denied.")
        sys.exit(2)

    if not send_telegram(token, chat_id, msg, reply_markup):
        try:
            os.unlink(pending_path)
        except OSError:
            pass
        sys.exit(0)

    decision_path = os.path.join(PERM_DIR, f"{req_id}.decision")
    deadline = time.time() + 300

    while time.time() < deadline:
        if os.path.exists(decision_path):
            try:
                decision = read_decision_file(decision_path)
                os.unlink(decision_path)
            except (OSError, PermissionError) as e:
                print(f"Decision file rejected ({e}). Denied.")
                for p in (decision_path, pending_path):
                    try:
                        os.unlink(p)
                    except OSError:
                        pass
                sys.exit(2)
            try:
                os.unlink(pending_path)
            except OSError:
                pass
            if decision == "y":
                sys.exit(0)
            print(f"Denied via Telegram (request {req_id})")
            sys.exit(2)
        time.sleep(1)

    for p in (pending_path, decision_path):
        try:
            os.unlink(p)
        except OSError:
            pass
    print(f"Timed out waiting for Telegram reply ({req_id}). Denied.")
    sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
