"""
Navi Bot Configuration

Security settings and authorized users
"""
import os

# Authorized Telegram User IDs
# To find your user ID: message @userinfobot on Telegram
AUTHORIZED_USERS = [
    int(os.environ.get("TELEGRAM_USER_ID", "0")),  # authorized user
]

# Display name used in prompts ("reply in <name>'s voice", "helping <name>")
USER_NAME = os.environ.get("NAVI_USER_NAME", "you")
SLACK_USER_NAME = USER_NAME

# Bot Settings
MAX_MESSAGE_LENGTH = 4096  # Telegram's limit
CLAUDE_TIMEOUT = 120  # seconds

# Retry Settings
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 2  # seconds
MAX_RETRY_DELAY = 30  # seconds
RETRY_BACKOFF_MULTIPLIER = 2  # exponential backoff

# 409 Conflict Handling
CONFLICT_WAIT_TIME = 35  # seconds (Telegram's long polling timeout is 30s)

# Logging
LOG_UNAUTHORIZED_ATTEMPTS = True
LOG_FILE_MAX_BYTES = 10 * 1024 * 1024  # 10MB
LOG_FILE_BACKUP_COUNT = 5  # Keep 5 old log files

# Session/Context Settings
SESSION_TIMEOUT_MINUTES = 30  # Clear context after 30 min of inactivity
MAX_CONTEXT_MESSAGES = 10  # Number of recent messages to include in context
CLEANUP_INTERVAL_SECONDS = 300  # Clean up expired sessions every 5 minutes

# TODO Integration
TODO_PATH = None  # None = default to ~/TODO.md
TODO_AUTO_UPDATE_DATE = True  # Automatically update "Last Updated" date

# Scheduler Settings
SCHEDULER_TIMEZONE = 'America/New_York'  # Your timezone
SCHEDULER_ENABLED = True  # Enable scheduled jobs
DEFAULT_TODO_SUMMARY_TIME = (8, 0)  # Daily TODO summary at 8:00am (hour, minute)
DEFAULT_EVENING_SUMMARY_TIME = (17, 0)  # Evening summary at 5:00pm (hour, minute)
DEFAULT_WEEKLY_REVIEW_DAY = 'fri'  # Weekly review on Friday
DEFAULT_WEEKLY_REVIEW_TIME = (17, 0)  # Weekly review at 5:00pm
MORNING_TOP_PRIORITIES = 3  # Number of top priorities to show in morning summary
CATCHUP_SUMMARY_ENABLED = False  # Send catch-up summary when user messages after missed scheduled summary

# War Room Settings
WARROOM_ENABLED = True  # Enable War Room feature
WARROOM_QUESTIONS_HOUR = 8  # Hour to generate daily hard questions (24h format)
WARROOM_QUESTIONS_MINUTE = 30  # Minute to generate daily hard questions
WARROOM_ROOT = None  # None = default to ~/work/warrooms

# Claude Code Agent Inbox
# Background agents write completion summaries here; Navi sends them to Telegram
AGENT_INBOX_ENABLED = True
AGENT_INBOX_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'inbox')
AGENT_INBOX_POLL_SECONDS = 10  # Check inbox every 10 seconds

# Karma Knowledge Graph Integration
KARMA_ENABLED = True
KARMA_DIR = os.path.expanduser("~/Documents/GitHub/karma")

# Ventures PM signal (standup #8 accord, 2026-08-24)
# Navi transports ~/ventures signals + executes bounded verbs; see ventures_signal.py
VENTURES_ENABLED = True
VENTURES_ROOT = None  # None = default to ~/ventures
VENTURES_MORNING_TIME = (8, 5)  # dawn read-back push (after the 8:00 briefing)
VENTURES_ALERT_POLL_SECONDS = 30  # immediate ALERT.md relay check in the main loop


def _csv(name: str, default: str) -> list:
    return [x.strip() for x in os.environ.get(name, default).split(",") if x.strip()]


# --- Permissions for background Claude runs ---------------------------------
# Comma-separated Claude Code tool patterns passed as --allowedTools. Anything
# not listed goes to the PreToolUse permission hook (Telegram approve/deny) or is
# denied when no hook is configured. Never use --dangerously-skip-permissions.
EXECUTOR_ALLOWED_TOOLS = os.environ.get("NAVI_EXECUTOR_ALLOWED_TOOLS", "Read,Glob,Grep,Edit,Write")
INBOX_ALLOWED_TOOLS = os.environ.get("NAVI_INBOX_ALLOWED_TOOLS", "mcp__gmail__*,Write")

# --- Inbox rules (personal; set in .env) --------------------------------------
INBOX_RECEIPTS_LABEL = os.environ.get("NAVI_INBOX_RECEIPTS_LABEL", "Receipts")
INBOX_PROTECTED_SENDERS = _csv("NAVI_INBOX_PROTECTED_SENDERS", "")      # exact domains, never archived
INBOX_PROTECTED_PARTIAL = _csv("NAVI_INBOX_PROTECTED_PARTIAL", "")      # substrings, never archived
INBOX_FINANCE_SENDERS = _csv("NAVI_INBOX_FINANCE_SENDERS", "paypal,stripe,square,shopify,amazon")
