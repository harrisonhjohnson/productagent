# Navi - Telegram Claude Bot

A Telegram bot that forwards messages to Claude CLI and returns responses.

## Setup

1. **Install dependencies:**
   ```bash
   pip install requests
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your Telegram bot token
   ```

3. **Run the bot:**
   ```bash
   # Load environment variables and run
   export $(cat .env | xargs) && python telegram_bot.py

   # Or use python-dotenv (install with: pip install python-dotenv)
   # Then add to the script: from dotenv import load_dotenv; load_dotenv()
   ```

## Usage

Send messages to **@YourNaviBot** on Telegram to interact with Claude CLI from anywhere.

### Basic Usage
- Send any question or task to the bot
- The bot forwards it to Claude CLI
- Receives and returns Claude's response

### Working with Your TODO List
Navi has access to your personal TODO list at `~/TODO.md`:

**Example messages:**
- "What's on my TODO list?"
- "Add 'Review Q1 budget' to my work section"
- "Mark the Canada data update as complete"
- "Show me my personal tasks"

### Working with Files & Projects
Since Navi runs from your home directory, be specific with paths:

**Example messages:**
- "Check my TODO list and prioritize tasks"
- "Review the code in projects/my-app"
- "List my active projects in ~/active/"
- "What projects am I working on?"

## What Navi does

Navi started as "forward Telegram messages to `claude -p`". It is now a small
phone-side harness around Claude Code:

- **Chat bridge** — any message goes to Claude CLI with a rolling per-user session
  (`session.py`); long replies are chunked to Telegram's 4096-char limit
  (`utils/formatting.py`, see `FORMATTING_GUIDE.md`).
- **Mobile mode for a live tab** — `navi_tab.py on` inside a Claude Code tab marks
  that tab mobile; the `navi_response_hook.py` Stop hook streams each of the tab's
  responses to Telegram and feeds your reply back as the tab's next turn. Multiple
  tabs, keyed by `CLAUDE_CODE_SESSION_ID`, can be mobile at once (`/tabs`,
  `/desktop <id>`). The `navi-mobile/SKILL.md` skill wraps the on/off command.
- **Permission gate** — `claude_permission_hook.py` is a PreToolUse hook that asks
  you on Telegram to approve or deny a tool call before it runs.
- **TODO manager** — reads and writes `~/TODO.md` in a fixed format with short IDs
  (`todo_manager.py`); `mcp_server.py` exposes the same list as MCP tools so any
  Claude session can query it; `agent_executor.py` + `prework_engine.py` run
  background agents on individual TODOs and draft the follow-up message for you.
- **Scheduler** — morning/evening summaries, weekly review, war-room hard
  questions (`scheduler.py`, `warroom_*.py`); state survives restarts
  (`scheduler_state.py`).
- **Voice** — voice notes transcribed via Whisper (`voice_handler.py`, see
  `VOICE_SETUP.md`).
- **Ventures signal** — `ventures_signal.py` relays alerts from an unattended
  night-run machine (see the `night-orders` harness) and accepts a handful of
  bounded verbs (`/ventures ack|pause|resume|decide|standup`) from the phone.
- **Knowledge graph hook** — optional `integrations/karma_client.py`.

Everything is gated to the Telegram user IDs in `config.AUTHORIZED_USERS`; set
`NAVI_USER_NAME` so prompts speak in your name.

## Security notes (read before running)

This is a personal bot published as a reference, not a hardened product. Known tradeoffs you should
decide on before running it on your own machine:

- **Skipped permissions in background runs.** `agent_executor.py` and the inbox-fetch path in
  `telegram_bot.py` launch `claude -p --dangerously-skip-permissions` so unattended runs can use
  MCP tools without a human in the loop. That means untrusted content (an email body, a web page)
  can drive tool calls unchecked. Safer options: drop the flag and let `claude_permission_hook.py`
  gate the run over Telegram, or restrict those runs with `--allowedTools` to read-only tools.
- **Prefix allowlist in the permission hook.** `SILENT_BASH_PREFIXES` in `claude_permission_hook.py`
  auto-approves commands by prefix, so `git status; rm -rf ~` would pass. Reject any command
  containing `;`, `&&`, `||`, `|`, backticks, or `$(` before prefix matching if you keep the hook.
- **Local HTTP server has no auth.** `hyrule_server.py` binds to 127.0.0.1 but allows any origin
  with credentials, so a page in your browser could add or complete TODOs. Restrict `allow_origins`
  to the served origin and add a startup token if you expose it.
- **MCP server over SSE.** `mcp_server.py` runs without authentication when started as an SSE
  server. Only expose it behind something that authenticates (Cloudflare Access, a bearer token
  check), never on a bare tunnel URL.

## Features

- Comprehensive error handling
- Graceful shutdown (Ctrl+C)
- Request timeouts
- Automatic retry logic
- Logging for monitoring
- Secure token management

## Requirements

- Python 3.7+
- Claude CLI installed and configured
- Telegram bot token
- `requests` library

## Running as Background Service

The bot is configured to run as a macOS LaunchAgent service that starts automatically when you log in.

### Management Commands

Use the management script to control the service:

```bash
cd ~/tools/navi

# Start the bot
./manage_bot.sh start

# Stop the bot
./manage_bot.sh stop

# Restart the bot
./manage_bot.sh restart

# Check status
./manage_bot.sh status

# View logs
./manage_bot.sh logs

# View errors
./manage_bot.sh errors

# Follow logs in real-time
./manage_bot.sh follow
```

### Service Details

- **Service File:** `~/Library/LaunchAgents/com.navi.telegrambot.plist`
- **Bot Location:** `~/tools/navi/`
- **Working Directory:** `~/` (full access to all your projects)
- **Logs:** `~/tools/navi/bot.log`
- **Errors:** `~/tools/navi/bot.error.log`
- **Auto-start:** Enabled (starts on login)
- **Auto-restart:** Enabled (restarts if crashed)

### Manual Run

If you prefer to run the bot manually without the service:

```bash
cd ~/tools/navi
export TELEGRAM_BOT_TOKEN="your_token_here"
python3 telegram_bot.py
```

Press `Ctrl+C` to stop gracefully.
