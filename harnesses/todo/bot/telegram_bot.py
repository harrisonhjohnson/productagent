import re
import subprocess
import requests
import signal
import sys
import logging
from logging.handlers import RotatingFileHandler
import time
import os
import random
from typing import Optional, List
import config
from session import SessionManager
from todo_manager import TodoManager
from scheduler import JobScheduler, BuiltInJobs

# Mobile mode — response mirroring + tmux reply routing (optional)
try:
    import mobile_mode
    MOBILE_AVAILABLE = True
except Exception as _e:
    MOBILE_AVAILABLE = False
    print(f"Mobile mode not available: {_e}")

# Import draft generator (optional - may not be installed yet)
try:
    from draft_generator import (
        get_pending_drafts,
        get_draft_by_id,
        mark_draft_sent,
        identify_quick_wins,
        format_drafts_summary,
        generate_all_drafts,
        execute_draft,
        skip_draft
    )
    DRAFTS_AVAILABLE = True
except ImportError:
    DRAFTS_AVAILABLE = False
from scheduler_state import SchedulerState
from voice_handler import VoiceHandler

# Import War Room manager
try:
    from warroom_manager import WarRoomManager
    from warroom_questions import generate_hard_questions, save_questions, get_todays_questions
    WARROOM_AVAILABLE = True
except ImportError as e:
    WARROOM_AVAILABLE = False
    print(f"War Room system not available: {e}")

# Import agent executor and prework engine
try:
    from agent_executor import AgentExecutor
    from prework_engine import PreworkEngine, run_prework_for_new_todo
    import slack_registry
    AGENT_AVAILABLE = True
except ImportError as e:
    AGENT_AVAILABLE = False
    print(f"Agent system not available: {e}")

# Import Gmail client (optional - requires google API libraries)
try:
    from integrations.email_client import GmailClient
    EMAIL_AVAILABLE = True
except ImportError as e:
    EMAIL_AVAILABLE = False
    print(f"Email system not available: {e}")

# Import ventures PM signal (standup #8 accord — see ventures_signal.py)
try:
    import ventures_signal
    VENTURES_AVAILABLE = True
except ImportError as e:
    VENTURES_AVAILABLE = False
    print(f"Ventures signal not available: {e}")

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    print("Error: TELEGRAM_BOT_TOKEN environment variable not set")
    sys.exit(1)

# Claude CLI path - configurable via environment variable
CLAUDE_PATH = os.getenv("CLAUDE_PATH", os.path.expanduser("~/.local/bin/claude"))

# Pinned so bot runs never inherit the interactive /model (which may be a
# capped premium tier). Override with CLAUDE_MODEL for a one-off.
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5")

API = f"https://api.telegram.org/bot{TOKEN}"

# Set up logging with rotation
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

# Rotating file handler
log_file = os.path.join(os.path.dirname(__file__), 'bot.error.log')
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=config.LOG_FILE_MAX_BYTES,
    backupCount=config.LOG_FILE_BACKUP_COUNT
)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Initialize session manager
session_manager = SessionManager()

# Initialize TODO manager
try:
    todo_manager = TodoManager(config.TODO_PATH)
    logger.info("TODO manager initialized successfully")
except FileNotFoundError as e:
    logger.warning(f"TODO manager initialization failed: {e}")
    todo_manager = None

# Initialize scheduler
job_scheduler = None
scheduler_state = None
if config.SCHEDULER_ENABLED:
    try:
        job_scheduler = JobScheduler(timezone=config.SCHEDULER_TIMEZONE)
        scheduler_state = SchedulerState()
        logger.info("Job scheduler initialized successfully")
    except Exception as e:
        logger.warning(f"Job scheduler initialization failed: {e}")
        job_scheduler = None
        scheduler_state = None

# Initialize voice handler
try:
    voice_handler = VoiceHandler(telegram_token=TOKEN)
except Exception as e:
    logger.warning(f"Voice handler initialization failed: {e}")
    voice_handler = None

# Initialize Gmail client (before agent/prework so they can use it)
gmail_client = None
if EMAIL_AVAILABLE and getattr(config, 'EMAIL_ENABLED', True):
    try:
        gmail_client = GmailClient()
        if gmail_client.is_configured():
            logger.info("Gmail client initialized")
        else:
            logger.warning("Gmail client not configured - missing token or OAuth client files")
            gmail_client = None
    except Exception as e:
        logger.warning(f"Gmail client initialization failed: {e}")
        gmail_client = None

# Initialize agent executor and prework engine
agent_executor = None
prework_engine = None
if AGENT_AVAILABLE and todo_manager:
    try:
        # Try to get slack_context from todo_manager if available
        slack_context = getattr(todo_manager, 'slack_context', None)
        agent_executor = AgentExecutor(
            todo_manager=todo_manager,
            slack_registry=slack_registry,
            slack_context=slack_context,
            gmail_client=gmail_client,
        )
        prework_engine = PreworkEngine(
            todo_manager=todo_manager,
            slack_context=slack_context,
            slack_registry=slack_registry,
            gmail_client=gmail_client,
        )
        logger.info("Agent executor and prework engine initialized")
    except Exception as e:
        logger.warning(f"Agent system initialization failed: {e}")
        agent_executor = None
        prework_engine = None

# Quick win session state - tracks pending actions for send/skip
# Format: {user_id: {1: {"todo_id": "TXXX", "suggestion": "...", "result": PreworkResult}, ...}}
pending_qw_actions = {}

# Initialize War Room manager
warroom_manager = None
if WARROOM_AVAILABLE and getattr(config, 'WARROOM_ENABLED', True):
    try:
        warroom_root = getattr(config, 'WARROOM_ROOT', None)
        warroom_manager = WarRoomManager(root_dir=warroom_root)
        logger.info("War Room manager initialized")
    except Exception as e:
        logger.warning(f"War Room manager initialization failed: {e}")
        warroom_manager = None

# Pending email send confirmations: {user_id: {"to": ..., "subject": ..., "body": ..., ...}}
pending_email_sends = {}

# Pending email triage state: {user_id: {1: {email_data}, 2: {...}}}
pending_email_triage = {}
pending_email_search = {}  # {user_id: {'results': {1: {email_data}}, 'state': 'list'|'reading'|'drafting', 'draft': {...}}}


running = True

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global running
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    running = False

    # Shutdown scheduler if running
    if job_scheduler:
        try:
            job_scheduler.shutdown()
            logger.info("Scheduler shut down successfully")
        except Exception as e:
            logger.error(f"Error shutting down scheduler: {e}")

def get_updates(offset: Optional[int] = None, timeout: int = 30) -> list:
    """Fetch updates from Telegram with error handling and 409 conflict recovery"""
    try:
        r = requests.get(
            f"{API}/getUpdates",
            params={"offset": offset, "timeout": timeout},
            timeout=timeout + 5
        )
        r.raise_for_status()
        return r.json().get("result", [])
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 409:
            # Conflict error - another instance is polling
            logger.warning(f"409 Conflict: Another bot instance is polling. Waiting {config.CONFLICT_WAIT_TIME}s...")
            time.sleep(config.CONFLICT_WAIT_TIME)
            return []
        logger.error(f"HTTP error fetching updates: {e}")
        time.sleep(5)
        return []
    except requests.exceptions.Timeout:
        logger.warning("Request to Telegram API timed out")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching updates: {e}")
        time.sleep(5)
        return []
    except Exception as e:
        logger.error(f"Unexpected error in get_updates: {e}")
        return []

def send_message(chat_id: int, text: str, retry_count: int = 0) -> bool:
    """Send message to Telegram with retry logic and exponential backoff"""
    try:
        r = requests.post(
            f"{API}/sendMessage",
            json={"chat_id": chat_id, "text": text[:config.MAX_MESSAGE_LENGTH]},
            timeout=10
        )
        r.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        if retry_count < config.MAX_RETRIES:
            # Calculate exponential backoff with jitter
            delay = min(
                config.INITIAL_RETRY_DELAY * (config.RETRY_BACKOFF_MULTIPLIER ** retry_count),
                config.MAX_RETRY_DELAY
            )
            # Add jitter (random 0-25% of delay)
            jitter = random.uniform(0, delay * 0.25)
            total_delay = delay + jitter

            logger.warning(f"Failed to send message to chat {chat_id}, retrying in {total_delay:.1f}s (attempt {retry_count + 1}/{config.MAX_RETRIES}): {e}")
            time.sleep(total_delay)
            return send_message(chat_id, text, retry_count + 1)
        else:
            logger.error(f"Failed to send message to chat {chat_id} after {config.MAX_RETRIES} retries: {e}")
            return False
    except Exception as e:
        logger.error(f"Unexpected error in send_message: {e}")
        return False

# --- Claude Code permission gate ---

PERM_DIR = os.path.join(os.path.expanduser("~"), ".navi", "permissions")
os.makedirs(PERM_DIR, mode=0o700, exist_ok=True)
os.chmod(PERM_DIR, 0o700)


def answer_callback_query(callback_id: str, text: str = "") -> None:
    """Acknowledge a Telegram inline-keyboard button press (removes the spinner)."""
    try:
        requests.post(
            f"{API}/answerCallbackQuery",
            json={"callback_query_id": callback_id, "text": text},
            timeout=5,
        )
    except Exception as e:
        logger.warning(f"Failed to answer callback query: {e}")


def edit_message_reply_markup(chat_id: int, message_id: int, text: str) -> None:
    """Replace the inline keyboard with plain text showing the decision."""
    try:
        requests.post(
            f"{API}/editMessageText",
            json={
                "chat_id": chat_id,
                "message_id": message_id,
                "text": text,
            },
            timeout=5,
        )
    except Exception as e:
        logger.warning(f"Failed to edit message: {e}")


def resolve_permission(req_id: str, decision: str) -> bool:
    """Write a decision file for a pending permission request. Returns True if the
    pending file existed (i.e. the request was still open)."""
    pending_path = os.path.join(PERM_DIR, f"{req_id}.pending")
    decision_path = os.path.join(PERM_DIR, f"{req_id}.decision")
    if not os.path.exists(pending_path):
        return False
    fd = os.open(decision_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(decision)
    try:
        os.unlink(pending_path)
    except OSError:
        pass
    return True


def handle_permission_callback(callback: dict) -> None:
    """Handle an inline-keyboard button press for a Claude Code permission request."""
    callback_id = callback.get("id", "")
    data = callback.get("data", "")
    msg = callback.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    message_id = msg.get("message_id")
    user_id = callback.get("from", {}).get("id")

    if not is_authorized(user_id):
        answer_callback_query(callback_id, text="Unauthorized")
        return

    if not (data.startswith("allow_") or data.startswith("deny_")):
        return

    action, req_id = data.split("_", 1)
    decision = "y" if action == "allow" else "n"
    found = resolve_permission(req_id, decision)

    if found:
        label = "✅ Allowed" if decision == "y" else "❌ Denied"
        answer_callback_query(callback_id, text=label)
        if chat_id and message_id:
            original = msg.get("text", "")
            # Strip the "Allow? Tap below…" footer and append decision
            body = original.split("\n\nAllow?")[0]
            edit_message_reply_markup(chat_id, message_id, f"{body}\n\n{label}")
        logger.info(f"Permission {req_id}: {label} by user {user_id}")
    else:
        answer_callback_query(callback_id, text="Request expired or not found")


def handle_permission_text_reply(text: str, chat_id: int, user_id: int) -> bool:
    """Handle 'y <req_id>' / 'n <req_id>' text replies. Returns True if handled."""
    m = re.match(r'^([yn])\s+([0-9a-f]{32})$', text.strip(), re.IGNORECASE)
    if not m:
        return False
    decision = m.group(1).lower()
    req_id = m.group(2).lower()
    found = resolve_permission(req_id, decision)
    if found:
        label = "✅ Allowed" if decision == "y" else "❌ Denied"
        send_message(chat_id, f"{label} (request {req_id})")
        logger.info(f"Permission {req_id}: {label} via text from user {user_id}")
    else:
        send_message(chat_id, f"Request {req_id} not found (may have expired).")
    return True


# --- end permission gate ---


def split_long_message(text: str, max_length: int = config.MAX_MESSAGE_LENGTH) -> List[str]:
    """Split long messages into chunks that fit Telegram's limit"""
    if len(text) <= max_length:
        return [text]

    chunks = []
    current_chunk = ""

    # Split by lines first to avoid breaking mid-sentence
    lines = text.split('\n')

    for line in lines:
        # If a single line is longer than max_length, split it by words
        if len(line) > max_length:
            words = line.split(' ')
            for word in words:
                if len(current_chunk) + len(word) + 1 <= max_length:
                    current_chunk += word + ' '
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = word + ' '
        else:
            # Check if adding this line would exceed the limit
            if len(current_chunk) + len(line) + 1 <= max_length:
                current_chunk += line + '\n'
            else:
                # Save current chunk and start a new one
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = line + '\n'

    # Add the last chunk
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

def send_long_message(chat_id: int, text: str) -> bool:
    """Send potentially long message, splitting if necessary"""
    chunks = split_long_message(text)

    if len(chunks) == 1:
        return send_message(chat_id, chunks[0])

    # Multiple chunks - send with indicators
    logger.info(f"Splitting long message into {len(chunks)} parts for chat {chat_id}")
    success = True

    for i, chunk in enumerate(chunks, 1):
        header = f"📝 Part {i}/{len(chunks)}\n\n"
        message = header + chunk if i > 1 else chunk

        if not send_message(chat_id, message):
            success = False
            logger.error(f"Failed to send part {i}/{len(chunks)} to chat {chat_id}")

        # Brief delay between messages to avoid rate limiting
        if i < len(chunks):
            time.sleep(0.5)

    return success

def is_authorized(user_id: int) -> bool:
    """Check if user is authorized to use the bot"""
    return user_id in config.AUTHORIZED_USERS


def get_suggestion_footer(todos: List = None, context: str = "") -> str:
    """
    Generate contextual suggestion footer based on current state.

    Args:
        todos: List of TODOs for context
        context: What command was just run

    Returns:
        Suggestion string like "/prework TXYZ | /qw"
    """
    if not todos:
        return ""

    suggestions = []

    # Get summary for smart suggestions
    if todo_manager:
        summary = todo_manager.get_grouping_summary()

        if context == "todo":
            if summary['overdue_count'] > 0:
                overdue = todo_manager.get_overdue_todos()
                if overdue:
                    first_id = overdue[0].get('id', '')
                    suggestions.append(f"/prework {first_id}")
            elif summary['quick_win_count'] > 0:
                suggestions.append("/qw")

        elif context == "now":
            quick_wins = todo_manager.get_quick_win_todos()
            if quick_wins:
                suggestions.append("/qw")

        elif context == "status":
            if summary['overdue_count'] > 0:
                suggestions.append("/now")

    return " | ".join(suggestions) if suggestions else ""


def handle_now_command(chat_id: int, user_id: int) -> str:
    """
    Smart 'what next' command showing overdue, due today, and quick wins.
    """
    if not todo_manager:
        return "TODO manager not available."

    from datetime import datetime, date
    today = date.today()
    day_name = today.strftime("%a %b %d")

    lines = [f"Now ({day_name})", ""]

    # Get overdue
    overdue = todo_manager.get_overdue_todos()
    if overdue:
        lines.append(f"OVERDUE ({len(overdue)})")
        for todo in overdue[:3]:
            todo_id = todo.get('id', '?')
            text = todo.get('text', '')[:50]
            lines.append(f"[{todo_id}] {text}")
        if len(overdue) > 3:
            lines.append(f"  ... +{len(overdue) - 3} more")
        lines.append("")

    # Get due today
    due_today = todo_manager.get_due_today_todos()
    if due_today:
        lines.append(f"DUE TODAY ({len(due_today)})")
        for todo in due_today[:3]:
            todo_id = todo.get('id', '?')
            text = todo.get('text', '')[:50]
            lines.append(f"[{todo_id}] {text}")
        if len(due_today) > 3:
            lines.append(f"  ... +{len(due_today) - 3} more")
        lines.append("")

    # Get quick wins
    quick_wins = todo_manager.get_quick_win_todos()
    if quick_wins:
        lines.append(f"QUICK WINS ({len(quick_wins)})")
        for todo in quick_wins[:3]:
            todo_id = todo.get('id', '?')
            text = todo.get('text', '')[:50]
            lines.append(f"[{todo_id}] {text}")
        if len(quick_wins) > 3:
            lines.append(f"  ... +{len(quick_wins) - 3} more")
        lines.append("")

    # Add suggestion
    if not overdue and not due_today and not quick_wins:
        lines.append("All clear! No urgent items.")
    else:
        first_item = (overdue or due_today or quick_wins)[0]
        first_id = first_item.get('id', '')
        lines.append(f"Start: /prework {first_id} | /qw")

    return "\n".join(lines)


def handle_by_person_command(person: str, chat_id: int) -> str:
    """
    Show TODOs for a specific person.
    """
    if not todo_manager:
        return "TODO manager not available."

    if not AGENT_AVAILABLE:
        return "Slack registry not available."

    todos = todo_manager.get_todos(include_completed=False)
    by_person = slack_registry.get_todos_by_person(todos)

    # Find matching person (case insensitive)
    person_lower = person.lower()
    matched_person = None
    for p in by_person.keys():
        if p.lower() == person_lower or p.lower().startswith(person_lower):
            matched_person = p
            break

    if not matched_person:
        # List available people
        if by_person:
            available = ", ".join(by_person.keys())
            return f"No TODOs found for '{person}'.\n\nAvailable: {available}"
        return f"No TODOs found for '{person}'."

    person_todos = by_person[matched_person]
    return slack_registry.format_person_todos_compact(matched_person, person_todos)


def handle_by_project_command(project: str, chat_id: int) -> str:
    """
    Show TODOs for a specific project.
    """
    if not todo_manager:
        return "TODO manager not available."

    if not AGENT_AVAILABLE:
        return "Slack registry not available."

    todos = todo_manager.get_todos(include_completed=False)
    by_project = slack_registry.get_todos_by_project(todos)

    # Find matching project (case insensitive)
    project_lower = project.lower().replace('-', '').replace('_', '')
    matched_project = None
    for p in by_project.keys():
        p_normalized = p.lower().replace('-', '').replace('_', '')
        if p_normalized == project_lower or p_normalized.startswith(project_lower):
            matched_project = p
            break

    if not matched_project:
        # List available projects
        if by_project:
            available = ", ".join(by_project.keys())
            return f"No TODOs found for '{project}'.\n\nAvailable: {available}"
        return f"No TODOs found for '{project}'."

    project_todos = by_project[matched_project]
    return slack_registry.format_project_todos_compact(matched_project, project_todos)


def handle_status_compact(chat_id: int, user_id: int) -> str:
    """
    Compact status overview with grouping counts.
    """
    if not todo_manager:
        return "TODO manager not available."

    summary = todo_manager.get_grouping_summary()

    lines = ["Status", ""]

    # Main counts
    counts = []
    counts.append(f"{summary['total']} open")
    if summary['due_today_count']:
        counts.append(f"{summary['due_today_count']} due today")
    if summary['overdue_count']:
        counts.append(f"{summary['overdue_count']} overdue")
    lines.append(" | ".join(counts))

    # By person (top 3)
    if summary['by_person']:
        sorted_people = sorted(summary['by_person'].items(), key=lambda x: x[1], reverse=True)[:3]
        person_str = " ".join([f"{p}({c})" for p, c in sorted_people])
        lines.append(f"By person: {person_str}")

    # By project (top 3)
    if summary['by_project']:
        sorted_projects = sorted(summary['by_project'].items(), key=lambda x: x[1], reverse=True)[:3]
        project_str = " ".join([f"{p}({c})" for p, c in sorted_projects])
        lines.append(f"By project: {project_str}")

    # Quick wins
    if summary['quick_win_count']:
        lines.append(f"Quick wins: {summary['quick_win_count']} ready")

    # Suggestions
    suggestions = []
    if summary['overdue_count'] or summary['due_today_count']:
        suggestions.append("/now")
    if summary['by_person']:
        top_person = sorted(summary['by_person'].items(), key=lambda x: x[1], reverse=True)[0][0]
        suggestions.append(f"/by {top_person}")
    if summary['quick_win_count']:
        suggestions.append("/qw")

    if suggestions:
        lines.extend(["", " | ".join(suggestions)])

    return "\n".join(lines)


def handle_qw_command(chat_id: int, user_id: int) -> str:
    """
    Quick wins with inline send/skip options.
    """
    global pending_qw_actions

    if not todo_manager:
        return "TODO manager not available."

    if not prework_engine:
        return "Prework engine not available."

    # Get quick win TODOs
    quick_wins = todo_manager.get_quick_win_todos()

    if not quick_wins:
        return "No quick wins found.\n\nQuick wins are items with 'reply', 'confirm', 'follow up' keywords."

    # Run batch prework to get suggestions
    send_message(chat_id, f"Analyzing {min(len(quick_wins), 5)} quick wins...")
    results = prework_engine.run_batch_prework(quick_wins, limit=5)

    if not results:
        return "No actionable quick wins found.\n\nTry /prework [ID] for individual analysis."

    # Store pending actions for this user
    pending_qw_actions[user_id] = {}

    lines = [f"Quick Wins ({len(results)})", ""]

    for i, result in enumerate(results, 1):
        todo = next((t for t in quick_wins if t.get('id') == result.todo_id), None)
        if not todo:
            continue

        text = todo.get('text', '')[:50]

        lines.append(f"{i}. [{result.todo_id}] {text}")

        if result.suggestion:
            suggestion_preview = result.suggestion.command[:80]
            if len(result.suggestion.command) > 80:
                suggestion_preview += "..."
            lines.append(f'   -> "{suggestion_preview}"')
            lines.append(f"   send {i} | skip {i}")

            # Store for later execution
            pending_qw_actions[user_id][i] = {
                "todo_id": result.todo_id,
                "suggestion": result.suggestion,
                "todo": todo
            }
        lines.append("")

    lines.append("done all | skip all")

    return "\n".join(lines)


def handle_morning_command(chat_id: int, user_id: int) -> str:
    """
    On-demand morning briefing.
    """
    if not todo_manager:
        return "TODO manager not available."

    from datetime import datetime

    lines = ["Good morning!", ""]

    # Summary
    summary = todo_manager.get_summary()
    lines.append(summary)
    lines.append("")

    # Overdue
    overdue = todo_manager.get_overdue_todos()
    if overdue:
        lines.append(f"OVERDUE ({len(overdue)})")
        for todo in overdue[:3]:
            lines.append(f"  [{todo.get('id', '?')}] {todo.get('text', '')[:50]}")
        lines.append("")

    # Due today
    due_today = todo_manager.get_due_today_todos()
    if due_today:
        lines.append(f"DUE TODAY ({len(due_today)})")
        for todo in due_today[:3]:
            lines.append(f"  [{todo.get('id', '?')}] {todo.get('text', '')[:50]}")
        lines.append("")

    # Top priorities
    priorities = todo_manager.get_todos_by_priority(limit=3)
    if priorities:
        lines.append("TOP PRIORITIES")
        for todo in priorities:
            lines.append(f"  [{todo.get('id', '?')}] {todo.get('text', '')[:50]}")
        lines.append("")

    # Suggestion
    if overdue:
        first_id = overdue[0].get('id', '')
        lines.append(f"Start: /prework {first_id}")
    elif due_today:
        first_id = due_today[0].get('id', '')
        lines.append(f"Start: /prework {first_id}")
    else:
        lines.append("/now | /status | /qw")

    return "\n".join(lines)


def handle_qw_action(action: str, user_id: int, chat_id: int) -> Optional[str]:
    """
    Handle quick win actions (send N, skip N, done all, skip all).

    Returns response string or None if not a QW action.
    """
    global pending_qw_actions

    if user_id not in pending_qw_actions or not pending_qw_actions[user_id]:
        return None

    action_lower = action.lower().strip()

    # Parse action

    # "send N" - execute and mark complete
    send_match = re.match(r'send\s+(\d+)', action_lower)
    if send_match:
        num = int(send_match.group(1))
        if num not in pending_qw_actions[user_id]:
            return f"No pending action #{num}."

        item = pending_qw_actions[user_id][num]
        suggestion = item['suggestion']
        todo = item['todo']
        todo_id = item['todo_id']

        # Execute the suggestion
        if prework_engine:
            success, result_msg = prework_engine.execute_one_shot(suggestion, todo)
            if success:
                # Mark TODO complete
                todo_manager.mark_complete(todo_id)
                del pending_qw_actions[user_id][num]
                return f"Sent and completed [{todo_id}]!\n{result_msg}"
            else:
                return f"Failed to send: {result_msg}"

    # "skip N" - remove from pending without action
    skip_match = re.match(r'skip\s+(\d+)', action_lower)
    if skip_match:
        num = int(skip_match.group(1))
        if num not in pending_qw_actions[user_id]:
            return f"No pending action #{num}."

        item = pending_qw_actions[user_id][num]
        todo_id = item['todo_id']
        del pending_qw_actions[user_id][num]
        return f"Skipped [{todo_id}]."

    # "done all" - execute all pending
    if action_lower in ['done all', 'send all']:
        results = []
        items = list(pending_qw_actions[user_id].items())
        for num, item in items:
            suggestion = item['suggestion']
            todo = item['todo']
            todo_id = item['todo_id']

            if prework_engine:
                success, _ = prework_engine.execute_one_shot(suggestion, todo)
                if success:
                    todo_manager.mark_complete(todo_id)
                    results.append(f"[{todo_id}] sent")
                else:
                    results.append(f"[{todo_id}] failed")

        pending_qw_actions[user_id] = {}
        return "Done all:\n" + "\n".join(results)

    # "skip all" - clear pending without action
    if action_lower == 'skip all':
        count = len(pending_qw_actions[user_id])
        pending_qw_actions[user_id] = {}
        return f"Skipped {count} quick wins."

    return None


def handle_warroom_command(text: str, chat_id: int, user_id: int) -> str:
    """
    Handle /warroom commands.

    Commands:
    - /warroom - List active war rooms
    - /warroom create "Name" --target YYYY-MM-DD --tags tag1,tag2
    - /warroom <slug> - Show status
    - /warroom <slug> blocker <id> <status> [note]
    - /warroom <slug> owner <id> <person>
    - /warroom <slug> confidence <id> <level>
    - /warroom <slug> planb <id> <plan>
    - /warroom <slug> park <id> <reason>
    - /warroom <slug> unpark <id>
    - /warroom <slug> questions
    - /warroom <slug> standup
    - /warroom <slug> close
    """
    if not warroom_manager:
        return "War Room system not available."

    from datetime import date

    parts = text.split()

    # /warroom - list active
    if len(parts) == 1:
        return warroom_manager.list_active_summary()

    subcommand = parts[1].lower()

    # /warroom create "Name" --target YYYY-MM-DD
    if subcommand == 'create':
        # Parse: /warroom create "Project A" --target 2026-03-01 --tags a
        rest = ' '.join(parts[2:])

        # Extract name (quoted or first word)
        name_match = re.search(r'"([^"]+)"', rest)
        if name_match:
            name = name_match.group(1)
            rest = rest.replace(f'"{name}"', '').strip()
        else:
            # Take first word as name
            name_parts = rest.split('--')[0].strip().split()
            name = name_parts[0] if name_parts else 'Unnamed'
            rest = rest.replace(name, '', 1).strip()

        # Extract target date
        target_match = re.search(r'--target\s+(\d{4}-\d{2}-\d{2})', rest)
        if not target_match:
            return "Usage: /warroom create \"Name\" --target YYYY-MM-DD [--tags tag1,tag2]"

        try:
            target_date = date.fromisoformat(target_match.group(1))
        except ValueError:
            return "Invalid date format. Use YYYY-MM-DD."

        # Extract tags
        tags = []
        tags_match = re.search(r'--tags\s+([^\s]+)', rest)
        if tags_match:
            tags = [t.strip() for t in tags_match.group(1).split(',')]

        try:
            warroom = warroom_manager.create(name, target_date, tags)
            days = (target_date - date.today()).days
            return f"Created War Room: {name}\nTarget: {target_date} (T-{days})\nTags: {', '.join(tags) if tags else 'none'}\n\n/warroom {warroom.slug}"
        except ValueError as e:
            return f"Error: {str(e)}"

    # Otherwise, first arg is war room slug
    slug = subcommand
    warroom = warroom_manager.get(slug)
    if not warroom:
        return f"War room '{slug}' not found.\n\nActive war rooms:\n{warroom_manager.list_active_summary()}"

    # /warroom <slug> - show status
    if len(parts) == 2:
        return warroom_manager.get_status_summary(slug)

    action = parts[2].lower()

    # /warroom <slug> blocker <id> <status> [note]
    if action == 'blocker':
        if len(parts) < 5:
            return "Usage: /warroom <slug> blocker <todo_id> <red|yellow|green> [note]"

        todo_id = parts[3].upper()
        status = parts[4].lower()

        if status not in ['red', 'yellow', 'green']:
            return "Status must be: red, yellow, or green"

        note = ' '.join(parts[5:]) if len(parts) > 5 else None

        # Check if blocker exists
        existing = next((b for b in warroom.blockers if b.id == todo_id), None)

        if existing:
            success = warroom_manager.update_blocker(slug, todo_id, status=status, note=note)
            if success:
                return f"Updated {todo_id} -> {status.upper()}{' - ' + note if note else ''}"
        else:
            # Add new blocker
            item_text = f"TODO {todo_id}"  # Default, could be fetched from TODO.md
            if todo_manager:
                todos = todo_manager.get_todos(include_completed=False)
                todo = next((t for t in todos if t.get('id') == todo_id), None)
                if todo:
                    item_text = todo.get('text', '')[:60]

            success = warroom_manager.add_blocker(slug, todo_id, item_text, status=status, note=note)
            if success:
                return f"Added blocker {todo_id} ({status.upper()})"

        return f"Failed to update blocker {todo_id}"

    # /warroom <slug> owner <id> <person>
    if action == 'owner':
        if len(parts) < 5:
            return "Usage: /warroom <slug> owner <todo_id> <person>"

        todo_id = parts[3].upper()
        owner = ' '.join(parts[4:])

        success = warroom_manager.update_blocker(slug, todo_id, owner=owner)
        if success:
            return f"Set owner of {todo_id} -> {owner}"
        return f"Blocker {todo_id} not found. Add it first with: /warroom {slug} blocker {todo_id} yellow"

    # /warroom <slug> confidence <id> <level>
    if action == 'confidence':
        if len(parts) < 5:
            return "Usage: /warroom <slug> confidence <todo_id> <high|medium|low>"

        todo_id = parts[3].upper()
        confidence = parts[4].lower()

        if confidence not in ['high', 'medium', 'low']:
            return "Confidence must be: high, medium, or low"

        success = warroom_manager.update_blocker(slug, todo_id, confidence=confidence)
        if success:
            return f"Set confidence of {todo_id} -> {confidence}"
        return f"Blocker {todo_id} not found."

    # /warroom <slug> planb <id> <plan>
    if action == 'planb':
        if len(parts) < 5:
            return "Usage: /warroom <slug> planb <todo_id> <fallback plan>"

        todo_id = parts[3].upper()
        plan_b = ' '.join(parts[4:])

        success = warroom_manager.set_plan_b(slug, todo_id, plan_b)
        if success:
            return f"Set Plan B for {todo_id}: {plan_b}"
        return f"Blocker {todo_id} not found."

    # /warroom <slug> park <id> <reason>
    if action == 'park':
        if len(parts) < 5:
            return "Usage: /warroom <slug> park <todo_id> <reason>"

        todo_id = parts[3].upper()
        reason = ' '.join(parts[4:])

        # Get item text from TODO.md
        item_text = f"TODO {todo_id}"
        if todo_manager:
            todos = todo_manager.get_todos(include_completed=False)
            todo = next((t for t in todos if t.get('id') == todo_id), None)
            if todo:
                item_text = todo.get('text', '')[:60]

        success = warroom_manager.park_item(slug, todo_id, item_text, reason)
        if success:
            return f"Parked {todo_id}: {reason}\n\nWill restore after {warroom.target_date.strftime('%b %d')}"
        return f"Failed to park {todo_id}"

    # /warroom <slug> unpark <id>
    if action == 'unpark':
        if len(parts) < 4:
            return "Usage: /warroom <slug> unpark <todo_id>"

        todo_id = parts[3].upper()

        success = warroom_manager.unpark_item(slug, todo_id)
        if success:
            return f"Unparked {todo_id} - item is now active"
        return f"Item {todo_id} not found in parked items."

    # /warroom <slug> questions
    if action == 'questions':
        # Check for today's questions first
        existing = get_todays_questions(slug)
        if existing:
            return existing

        # Generate new questions
        send_message(chat_id, f"Generating hard questions for {warroom.name}...")
        questions = generate_hard_questions(warroom, todo_manager)

        if questions:
            save_questions(slug, questions)
            days = (warroom.target_date - date.today()).days
            return f"Hard Questions - {warroom.name} (T-{days})\n\n{questions}"
        else:
            return "Failed to generate hard questions. Try again later."

    # /warroom <slug> standup
    if action == 'standup':
        return warroom_manager.generate_standup_agenda(slug)

    # /warroom <slug> close
    if action == 'close':
        success = warroom_manager.close(slug)
        if success:
            parked_count = len(warroom.parked)
            return f"Closed War Room: {warroom.name}\n\n{parked_count} parked item(s) flagged for restore."
        return "Failed to close war room."

    # /warroom <slug> decision <text>
    if action == 'decision':
        if len(parts) < 4:
            return "Usage: /warroom <slug> decision <what was decided>"

        decision = ' '.join(parts[3:])
        success = warroom_manager.add_decision(slug, decision)
        if success:
            return f"Recorded decision: {decision}"
        return "Failed to record decision."

    # /warroom <slug> rollback <owner> | <trigger> | <action> | <time>
    if action == 'rollback':
        if len(parts) < 4:
            return "Usage: /warroom <slug> rollback <owner> | <trigger> | <action> | <time estimate>"

        rest = ' '.join(parts[3:])
        parts_rollback = [p.strip() for p in rest.split('|')]

        if len(parts_rollback) != 4:
            return "Usage: /warroom <slug> rollback <owner> | <trigger> | <action> | <time estimate>"

        success = warroom_manager.set_rollback_plan(
            slug,
            owner=parts_rollback[0],
            trigger=parts_rollback[1],
            action=parts_rollback[2],
            time_estimate=parts_rollback[3]
        )
        if success:
            return f"Rollback plan set.\nOwner: {parts_rollback[0]}\nTrigger: {parts_rollback[1]}\nAction: {parts_rollback[2]}\nTime: {parts_rollback[3]}"
        return "Failed to set rollback plan."

    # /warroom <slug> remove <id>
    if action == 'remove':
        if len(parts) < 4:
            return "Usage: /warroom <slug> remove <todo_id>"

        todo_id = parts[3].upper()
        success = warroom_manager.remove_blocker(slug, todo_id)
        if success:
            return f"Removed blocker {todo_id} from war room."
        return f"Blocker {todo_id} not found."

    return f"Unknown warroom command: {action}\n\nAvailable: blocker, owner, confidence, planb, park, unpark, questions, standup, close, decision, rollback, remove"


def handle_send_draft_command(draft_id: str, chat_id: int, user_id: int) -> str:
    """Execute and send a Slack draft."""
    if not DRAFTS_AVAILABLE:
        return "Draft system not available."

    draft = get_draft_by_id(draft_id)
    if not draft:
        return f"Draft {draft_id} not found."

    send_message(chat_id, f"Sending {draft_id} to {draft.get('target_name')}...")

    success, result = execute_draft(draft_id, CLAUDE_PATH)

    if success:
        # Mark referenced TODOs as complete
        todo_ids = draft.get('todo_ids', [])
        completed = []
        for todo_id in todo_ids:
            try:
                if todo_manager:
                    ok, _ = todo_manager.mark_complete(todo_id)
                    if ok:
                        completed.append(todo_id)
            except:
                pass

        response = f"Sent {draft_id}!"
        if completed:
            response += f"\nMarked complete: {', '.join(completed)}"

        # Suggest next action
        pending = get_pending_drafts()
        if pending:
            next_draft = pending[0].get('id')
            response += f"\n\nNext: send {next_draft} | /drafts"

        return response
    else:
        return f"Failed: {result}"


def handle_skip_draft_command(draft_id: str, chat_id: int) -> str:
    """Skip/discard a Slack draft."""
    if not DRAFTS_AVAILABLE:
        return "Draft system not available."

    success, result = skip_draft(draft_id)

    if success:
        response = f"Skipped {draft_id}."
        pending = get_pending_drafts()
        if pending:
            next_draft = pending[0].get('id')
            response += f"\n\nNext: /draft {next_draft} | /drafts"
        return response
    else:
        return f"Failed: {result}"


def handle_command(text: str, user_id: int, chat_id: int) -> Optional[str]:
    """Handle bot commands. Returns response text if command handled, None otherwise"""
    if not text.startswith('/'):
        return None

    command = text.split()[0].lower()

    if command == '/clear':
        session_manager.clear_session(user_id)
        return "✨ Conversation history cleared! Starting fresh."

    elif command == '/ventures':
        if not VENTURES_AVAILABLE or not getattr(config, 'VENTURES_ENABLED', False):
            return "Ventures signal is not enabled."
        return ventures_signal.handle_ventures_command(text, chat_id, user_id)

    elif command == '/help':
        help_text = """**Navi Commands**

/help - This message
/clear - Clear conversation history
/stats - Session statistics

**Smart Views:**
/now - What to work on next
/status - Compact overview with counts
/by [person] - TODOs by person
/proj [name] - TODOs by project
/qw - Quick wins with send/skip
/morning - Morning briefing"""

        if todo_manager:
            help_text += """

**TODO:**
/todo - Show TODO list
/todo slack - Slack TODOs only
/summary - Counts"""

        if job_scheduler:
            help_text += """
/schedule - Scheduled jobs"""

        if DRAFTS_AVAILABLE:
            help_text += """

**Slack Drafts:**
/drafts - Pending drafts
/draft [ID] - View draft
/syncslack - Generate from TODOs"""

        if AGENT_AVAILABLE:
            help_text += """

**Agent:**
/agent [ID] - Plan for a TODO
/approve [ID] - Execute plan
/cancel [ID] - Cancel plan
/plans - List pending
/prework [ID] - Pre-work analysis

**Quick Win Flow (/qw):**
send 1 - Send #1 and mark done
skip 1 - Skip without sending
done all / skip all"""

        if WARROOM_AVAILABLE and warroom_manager:
            help_text += """

**War Room:**
/warroom - List active
/warroom create "Name" --target YYYY-MM-DD
/warroom <slug> - Status
/warroom <slug> questions / standup / close"""

        if gmail_client:
            help_text += """

**Email:**
/email triage [query] - Inbox triage
/email search <query> - Search Gmail
/email send <to> :: <subj> :: <body>
/email draft <to> :: <subj> :: <body>
/email drafts - List drafts
/email fetch [1d|7d|30d] - Fetch to TODOs
/email clean - Run inbox cleaner

**Triage Actions:**
todo 1 / todo 1 2 3 - Create TODOs
archive 1 / archive 1 2 3 - Archive
read 1 - Read full email
nuke - Archive all
undo junk - Restore auto-archived
skip - Dismiss"""

        help_text += """

**Voice Commands:**
Send a voice message — Navi transcribes and acts.

Reliable voice phrases:
• "Show my to-dos" / "What's on my list?"
• "What should I do?" / "What's next?"
• "Add to-do [task]" / "Remind me to [task]"
• "Mark [ID] done" / "Done [ID]"
• "Quick wins"
• "Status"
• "Morning" / "Morning briefing"
• "Email triage"
• "Show drafts" / "Sync Slack"
• Any question — goes to Claude

**Text shortcuts (no slash needed):**
what now / what's next / what should I do
quick wins / qw
status
morning
show drafts / sync slack
agent TXXX / approve TXXX / cancel TXXX"""

        return help_text

    elif command == '/stats':
        stats = session_manager.get_session_stats(user_id)
        if stats['message_count'] > 0:
            return f"""📊 Session Statistics:

Messages: {stats['message_count']}
Session created: {stats['session_created']}
Last activity: {stats['last_activity']}
First message: {stats['first_message']}
Last message: {stats['last_message']}"""
        else:
            return "📊 No conversation history yet. Start chatting!"

    elif command == '/todo' or command.startswith('/todo '):
        if not todo_manager:
            return "❌ TODO manager not available. Make sure ~/TODO.md exists."

        try:
            # Parse filter from command
            source_filter = None
            show_metadata = False

            parts = text.split(maxsplit=1)
            if len(parts) > 1:
                filter_arg = parts[1].lower()
                if filter_arg == 'slack':
                    source_filter = 'slack'
                    show_metadata = True
                elif filter_arg == 'manual':
                    source_filter = 'manual'
                    show_metadata = False
                else:
                    return "❌ Invalid filter. Use: /todo, /todo slack, or /todo manual"

            todos = todo_manager.get_todos(include_completed=False, source_filter=source_filter)
            result = todo_manager.format_todos(todos, numbered=True, show_metadata=show_metadata)

            # Add suggestion footer
            suggestion = get_suggestion_footer(todos, "todo")
            if suggestion:
                result += f"\n\n{suggestion}"

            return result
        except Exception as e:
            logger.error(f"Error getting TODOs: {e}")
            return f"❌ Error reading TODOs: {str(e)}"

    elif command == '/summary':
        if not todo_manager:
            return "❌ TODO manager not available. Make sure ~/TODO.md exists."

        try:
            return todo_manager.get_summary()
        except Exception as e:
            logger.error(f"Error getting TODO summary: {e}")
            return f"❌ Error getting summary: {str(e)}"

    elif command == '/overdue':
        if not todo_manager:
            return "❌ TODO manager not available. Make sure ~/TODO.md exists."

        try:
            overdue = todo_manager.get_overdue_todos()
            if not overdue:
                return "✅ No overdue items! You're on track."
            return "🔴 Overdue Items:\n\n" + todo_manager.format_todos(overdue, numbered=True)
        except Exception as e:
            logger.error(f"Error getting overdue TODOs: {e}")
            return f"❌ Error: {str(e)}"

    elif command == '/duetoday':
        if not todo_manager:
            return "❌ TODO manager not available. Make sure ~/TODO.md exists."

        try:
            due_today = todo_manager.get_due_today_todos()
            if not due_today:
                return "📅 Nothing due today!"
            return "📅 Due Today:\n\n" + todo_manager.format_todos(due_today, numbered=True)
        except Exception as e:
            logger.error(f"Error getting TODOs due today: {e}")
            return f"❌ Error: {str(e)}"

    elif command == '/dueweek':
        if not todo_manager:
            return "❌ TODO manager not available. Make sure ~/TODO.md exists."

        try:
            due_week = todo_manager.get_due_this_week_todos()
            if not due_week:
                return "📅 Nothing due this week!"
            return "📅 Due This Week:\n\n" + todo_manager.format_todos(due_week, numbered=True)
        except Exception as e:
            logger.error(f"Error getting TODOs due this week: {e}")
            return f"❌ Error: {str(e)}"

    elif command == '/priorities':
        if not todo_manager:
            return "❌ TODO manager not available. Make sure ~/TODO.md exists."

        try:
            priorities = todo_manager.get_todos_by_priority(limit=5)
            if not priorities:
                return "📋 No TODO items found!"
            return "🎯 Top 5 Priorities:\n\n" + todo_manager.format_todos(priorities, numbered=True)
        except Exception as e:
            logger.error(f"Error getting priority TODOs: {e}")
            return f"❌ Error: {str(e)}"

    # New smart view commands
    elif command == '/now':
        try:
            return handle_now_command(chat_id, user_id)
        except Exception as e:
            logger.error(f"Error in /now command: {e}")
            return f"❌ Error: {str(e)}"

    elif command == '/status':
        try:
            return handle_status_compact(chat_id, user_id)
        except Exception as e:
            logger.error(f"Error in /status command: {e}")
            return f"❌ Error: {str(e)}"

    elif command == '/by' or command.startswith('/by '):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            return "Usage: /by [person]\n\nExample: /by shyam"

        person = parts[1].strip()
        try:
            return handle_by_person_command(person, chat_id)
        except Exception as e:
            logger.error(f"Error in /by command: {e}")
            return f"❌ Error: {str(e)}"

    elif command == '/proj' or command.startswith('/proj '):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            return "Usage: /proj [project]\n\nExample: /proj project-a"

        project = parts[1].strip()
        try:
            return handle_by_project_command(project, chat_id)
        except Exception as e:
            logger.error(f"Error in /proj command: {e}")
            return f"❌ Error: {str(e)}"

    elif command == '/qw':
        try:
            return handle_qw_command(chat_id, user_id)
        except Exception as e:
            logger.error(f"Error in /qw command: {e}")
            return f"❌ Error: {str(e)}"

    elif command == '/morning':
        try:
            return handle_morning_command(chat_id, user_id)
        except Exception as e:
            logger.error(f"Error in /morning command: {e}")
            return f"❌ Error: {str(e)}"

    elif command == '/schedule' or command.startswith('/schedule '):
        if not job_scheduler:
            return "❌ Scheduler not available."

        parts = text.split(maxsplit=1)

        # Show help if no subcommand
        if len(parts) == 1:
            return """📅 Schedule Commands:

/schedule list - Show all scheduled jobs
/schedule status - Show scheduler status

Scheduled jobs are configured in config.py.
Contact admin to modify job schedules."""

        subcommand = parts[1].lower()

        if subcommand == 'list':
            jobs = job_scheduler.get_jobs()
            return job_scheduler.format_jobs_list(jobs)

        elif subcommand == 'status':
            jobs = job_scheduler.get_jobs()
            job_count = len(jobs)
            return f"""📅 Scheduler Status:

Running: ✅ Yes
Jobs: {job_count}
Timezone: {config.SCHEDULER_TIMEZONE}

Use /schedule list to see all jobs."""

        else:
            return f"❓ Unknown schedule command: {subcommand}\n\nUse /schedule for help."

    elif command == '/drafts':
        if not DRAFTS_AVAILABLE:
            return "❌ Draft system not available."

        try:
            pending = get_pending_drafts()
            if not pending:
                return "📝 No pending drafts.\n\nUse /syncslack to generate drafts from TODOs."

            lines = [f"📝 **{len(pending)} Pending Drafts**\n"]
            for draft in pending:
                draft_id = draft.get('id', '?')
                draft_type = draft.get('type', 'unknown')
                target = draft.get('target_name', 'Unknown')
                todo_ids = ', '.join(draft.get('todo_ids', [])[:3])

                if draft_type == 'dm':
                    lines.append(f"{draft_id}. DM → {target}")
                else:
                    lines.append(f"{draft_id}. {target}")
                lines.append(f"   └ {todo_ids}")

            lines.append("\n\"view [ID]\" or \"send [ID]\"")
            return "\n".join(lines)

        except Exception as e:
            logger.error(f"Error listing drafts: {e}")
            return f"❌ Error: {str(e)}"

    elif command == '/draft' or command.startswith('/draft '):
        if not DRAFTS_AVAILABLE:
            return "❌ Draft system not available."

        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            return "❌ Usage: /draft [ID]\n\nExample: /draft DRF001"

        draft_id = parts[1].upper()
        if not draft_id.startswith('DRF'):
            draft_id = f"DRF{draft_id}"

        try:
            draft = get_draft_by_id(draft_id)
            if not draft:
                return f"❌ Draft {draft_id} not found."

            content = draft.get('content', 'No content')
            target = draft.get('target_name', 'Unknown')
            draft_type = draft.get('type', 'unknown')

            # Extract just the message portion from the file
            lines = content.split('---')
            if len(lines) >= 2:
                message_content = lines[1].strip()
            else:
                message_content = content

            response = f"📤 **Draft {draft_id}** ({draft_type} → {target})\n\n{message_content}\n\n---\n'send {draft_id}' to send | 'skip {draft_id}' to discard"
            return response[:config.MAX_MESSAGE_LENGTH]

        except Exception as e:
            logger.error(f"Error viewing draft: {e}")
            return f"❌ Error: {str(e)}"

    elif command == '/quickwins':
        if not todo_manager:
            return "❌ TODO manager not available."

        if not DRAFTS_AVAILABLE:
            return "❌ Draft system not available."

        try:
            todos = todo_manager.get_todos(include_completed=False)
            quick_wins = identify_quick_wins(todos)

            if not quick_wins:
                return "⚡ No quick wins identified.\n\nQuick wins are items with 'confirm', 'check', 'reply', 'follow up' keywords."

            lines = [f"⚡ **{len(quick_wins)} Quick Wins**\n"]
            for qw in quick_wins[:10]:
                todo_id = qw.get('id', '?')
                text_preview = qw.get('text', '')[:50]
                if len(qw.get('text', '')) > 50:
                    text_preview += '...'
                lines.append(f"{todo_id} - {text_preview}")

            if len(quick_wins) > 10:
                lines.append(f"\n... and {len(quick_wins) - 10} more")

            lines.append("\n\"done [ID]\" to complete")
            return "\n".join(lines)

        except Exception as e:
            logger.error(f"Error getting quick wins: {e}")
            return f"❌ Error: {str(e)}"

    elif command == '/syncslack':
        if not todo_manager:
            return "❌ TODO manager not available."

        if not DRAFTS_AVAILABLE:
            return "❌ Draft system not available."

        try:
            todos = todo_manager.get_todos(include_completed=False)

            if not todos:
                return "📝 No pending TODOs to generate drafts from."

            draft_ids, quick_wins = generate_all_drafts(todos)
            pending = get_pending_drafts()

            lines = ["📝 **Slack Draft Sync Complete**\n"]

            if draft_ids:
                lines.append(f"✅ Generated {len(draft_ids)} new draft(s)")
            else:
                lines.append("ℹ️ No new drafts needed")

            lines.append(f"📋 {len(pending)} total pending drafts")

            if quick_wins:
                lines.append(f"⚡ {len(quick_wins)} quick wins identified")

            lines.append("\nUse /drafts to view all drafts")
            return "\n".join(lines)

        except Exception as e:
            logger.error(f"Error syncing slack: {e}")
            return f"❌ Error: {str(e)}"

    elif command == '/agent' or command.startswith('/agent '):
        if not agent_executor:
            return "❌ Agent system not available."

        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            return "**Agent System**\n\nUsage: /agent [TODO_ID]\n\nExample: /agent TCTC\n\nGenerates a detailed plan for completing the TODO."

        todo_id = parts[1].strip().upper()
        # Remove # prefix if present
        if todo_id.startswith('#'):
            todo_id = todo_id[1:]

        send_message(chat_id, f"Generating agent plan for {todo_id}...")

        success, result = agent_executor.invoke_plan_mode(todo_id)
        if success:
            # Truncate for Telegram if needed
            plan_preview = result[:3000] if len(result) > 3000 else result
            return f"**Plan for {todo_id}**\n\n{plan_preview}\n\n---\n'/approve {todo_id}' to execute | '/cancel {todo_id}' to abort"
        else:
            return f"❌ {result}"

    elif command == '/approve' or command.startswith('/approve '):
        if not agent_executor:
            return "❌ Agent system not available."

        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            return "Usage: /approve [TODO_ID]\n\nApproves and executes a pending plan."

        todo_id = parts[1].strip().upper()
        if todo_id.startswith('#'):
            todo_id = todo_id[1:]

        # Check plan exists and is pending
        plan = agent_executor.get_plan(todo_id)
        if not plan:
            return f"❌ No plan found for {todo_id}. Use '/agent {todo_id}' to generate one."
        if plan.get('status') != 'pending':
            return f"❌ Plan for {todo_id} is not pending (status: {plan.get('status')})"

        send_message(chat_id, f"Executing plan for {todo_id}...")

        success, result = agent_executor.approve_plan(todo_id)
        if success:
            # Truncate result for Telegram
            result_preview = result[:2500] if len(result) > 2500 else result

            # Find next TODO for suggestion
            todos = todo_manager.get_todos(include_completed=False)
            next_todo = None
            for t in todos:
                if t.get('id') != todo_id:
                    next_todo = t
                    break

            suggestion = f"mark {todo_id} done"
            if next_todo:
                next_id = next_todo.get('id', '')
                suggestion += f" | /prework {next_id}"

            return f"**Plan Executed for {todo_id}**\n\n{result_preview}\n\n---\n{suggestion}"
        else:
            return f"❌ Execution failed: {result}"

    elif command == '/cancel' or command.startswith('/cancel '):
        if not agent_executor:
            return "❌ Agent system not available."

        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            return "Usage: /cancel [TODO_ID]\n\nCancels a pending plan."

        todo_id = parts[1].strip().upper()
        if todo_id.startswith('#'):
            todo_id = todo_id[1:]

        success, message = agent_executor.cancel_plan(todo_id)
        if success:
            return f"✅ {message}"
        else:
            return f"❌ {message}"

    elif command == '/plans':
        if not agent_executor:
            return "❌ Agent system not available."

        plans = agent_executor.get_pending_plans()
        if not plans:
            return "📋 No pending plans.\n\nUse '/agent [TODO_ID]' to generate a plan."

        lines = [f"📋 **{len(plans)} Pending Plan(s)**\n"]
        for p in plans:
            todo_id = p.get('todo_id', '?')
            todo_text = p.get('todo_text', 'Unknown')[:50]
            created = p.get('created', '')[:10]  # Just date
            lines.append(f"**{todo_id}** - {todo_text}...")
            lines.append(f"   Created: {created}")

        lines.append("\n---")
        lines.append("'/approve [ID]' to execute | '/cancel [ID]' to abort")
        return "\n".join(lines)

    elif command == '/prework' or command.startswith('/prework '):
        if not prework_engine:
            return "❌ Prework system not available."

        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            return "**Prework System**\n\nUsage: /prework [TODO_ID]\n\nRuns pre-work analysis on a TODO to gather context and suggest quick actions."

        todo_id = parts[1].strip().upper()
        if todo_id.startswith('#'):
            todo_id = todo_id[1:]

        # Find the TODO
        todos = todo_manager.get_todos(include_completed=False)
        todo = next((t for t in todos if t.get('id') == todo_id), None)

        if not todo:
            return f"❌ TODO {todo_id} not found"

        send_message(chat_id, f"Running prework for {todo_id}...")

        result = prework_engine.run_prework(todo)
        formatted = prework_engine.format_prework_result(result)

        # Add contextual suggestion based on result
        if result.is_quick_win and result.suggestion:
            # Already has send/edit/skip in the format
            pass
        else:
            # Suggest agent for complex tasks
            formatted += f"\n\nFor complex tasks: /agent {todo_id}"

        return formatted

    elif command == '/warroom' or command.startswith('/warroom '):
        if not warroom_manager:
            return "War Room system not available."

        try:
            return handle_warroom_command(text, chat_id, user_id)
        except Exception as e:
            logger.error(f"Error in /warroom command: {e}")
            return f"Error: {str(e)}"

    elif command == '/email' or command.startswith('/email '):
        if not gmail_client:
            return "Email system not available. Check Gmail token/OAuth setup."

        try:
            return handle_email_command(text, chat_id, user_id)
        except Exception as e:
            logger.error(f"Error in /email command: {e}")
            return f"Error: {str(e)}"

    else:
        return f"❓ Unknown command: {command}\n\nUse /help to see available commands."

# --- Email classification helpers ---

PROTECTED_SENDERS = set(config.INBOX_PROTECTED_SENDERS)
PROTECTED_PARTIAL = set(config.INBOX_PROTECTED_PARTIAL)

JUNK_SENDERS = {
    # Political
    'democrats.org', 'actblue.com', 'winred.com', 'dscc.org', 'dccc.org',
    'progressiveturnout.org', 'votevets.org', 'turnoutpac.org', 'justicedemocrats.com',
    'leaderswedeserve.com',
    # Newsletter noise
    'theskimm.com', 'gothamist.com', 'metrograph.com', 'neilpatel.com', 'mikenellis',
    # Events & venues
    'boweryballroom.com', 'boweryelectric.com', 'thebowerypresents.com', '930.com',
    'livenation.com', 'ticketmaster.com', 'auctionninja.com', 'hipcomic.com', 'ramsheadgroup.com',
    # Retail & marketing
    'uniqlo', 'humblebundle.com', 'spectrum.com', 'ancestry.com', 'ihg.com',
    'sweetgreen.com', 'ubereats.com', 'catbird.com', '101domain.com', 'phikappapsi', 'blickart.com',
}
JUNK_SUBJECTS = {'chip in', 'rush $', 'donate now', 'unsubscribe'}


def _is_protected_sender(sender: str) -> bool:
    """Check if sender is protected (never archive)."""
    sender_lower = sender.lower()
    if any(p in sender_lower for p in PROTECTED_SENDERS):
        return True
    if any(p in sender_lower for p in PROTECTED_PARTIAL):
        return True
    return False


def _is_junk_email(sender: str, subject: str, snippet: str = "", labels: list = None) -> bool:
    """Check if email looks like junk per inbox-clean rules."""
    sender_lower = sender.lower()
    subject_lower = subject.lower()
    text_lower = f"{subject_lower} {snippet.lower()}"

    # Protected senders are never junk
    if _is_protected_sender(sender_lower):
        return False

    # Gmail categories
    if labels and any(l in labels for l in ['CATEGORY_PROMOTIONS', 'CATEGORY_SOCIAL']):
        return True

    # Known junk senders
    if any(js in sender_lower for js in JUNK_SENDERS):
        return True

    # Junk subject patterns
    if any(js in text_lower for js in JUNK_SUBJECTS):
        return True

    # Substack notifications (not actual newsletters)
    if 'substack.com' in sender_lower and any(w in subject_lower for w in ['posted', 'live video', 'new note']):
        return True

    return False


FINANCE_LABEL_ID = config.INBOX_RECEIPTS_LABEL
FINANCE_KEYWORDS = {'receipt', 'invoice', 'order confirmation', 'payment', 'statement', 'transaction', 'refund', 'charge'}
FINANCE_SENDERS = set(config.INBOX_FINANCE_SENDERS)


def _is_finance_email(subject: str, sender: str, snippet: str = "") -> bool:
    """Check if email is a receipt or financial email."""
    text = f"{subject} {snippet}".lower()
    sender_lower = sender.lower()
    if '$' in text:
        return True
    if any(kw in text for kw in FINANCE_KEYWORDS):
        return True
    if any(fs in sender_lower for fs in FINANCE_SENDERS):
        return True
    return False


def _label_if_finance(message_id: str, subject: str, sender: str, snippet: str = "") -> bool:
    """Apply [Mailbox]/Receipts label if email looks financial. Returns True if labeled."""
    if gmail_client and _is_finance_email(subject, sender, snippet):
        try:
            gmail_client.add_label(message_id, [FINANCE_LABEL_ID])
            return True
        except Exception as e:
            logger.warning(f"Failed to label finance email {message_id}: {e}")
    return False


def _launch_email_background_agent(agent_type: str, period: Optional[str], chat_id: int) -> str:
    """Launch inbox-fetch or inbox-clean as a background Claude process.

    Results are delivered via the agent inbox (polled and sent to Telegram).
    """
    inbox_path = getattr(config, 'AGENT_INBOX_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'inbox'))
    os.makedirs(inbox_path, exist_ok=True)
    timestamp = int(time.time())

    if agent_type == 'fetch':
        period = period or '1d'
        prompt = (
            f"You are running inbox-fetch for {config.USER_NAME}. "
            f"Use the inbox-fetch skill instructions: scan Gmail for actionable emails from the last {period}, "
            f"classify them, label any finance/receipt emails with the Gmail label {config.INBOX_RECEIPTS_LABEL}, "
            f"and create TODOs in ~/TODO.md with proper Navi-compatible format and email metadata. "
            f"Search query: in:inbox is:unread newer_than:{period}. "
            f"Max 25 emails. Skip junk/automated/newsletters. "
            f"When done, write a summary to {inbox_path}/fetch-{timestamp}.md with: "
            f"how many scanned, how many TODOs created (with IDs), how many skipped, how many labeled as Receipts."
        )
        label = f"inbox-fetch {period}"
    elif agent_type == 'clean':
        prompt = (
            f"You are running inbox-clean for {config.USER_NAME}. "
            "Search Gmail for obvious junk emails (promotions, social, political fundraising, "
            "newsletter noise, event listings, retail marketing) using category:promotions, category:social, "
            "and specific sender queries. Archive all matches. "
            "Before archiving, label any emails containing $ or receipt/invoice/payment keywords "
            f"with the Gmail label {config.INBOX_RECEIPTS_LABEL}. "
            f"Protected senders (NEVER archive): {', '.join(config.INBOX_PROTECTED_SENDERS) or 'none configured'}. "
            f"When done, write a summary to {inbox_path}/clean-{timestamp}.md with: "
            f"how many archived by category, how many skipped (protected), how many labeled as Receipts."
        )
        label = "inbox-clean"
    else:
        return f"Unknown agent type: {agent_type}"

    try:
        # Email bodies are untrusted input, so this run gets Gmail tools plus a
        # file write for its summary and nothing else. No shell, no edits.
        subprocess.Popen(
            [CLAUDE_PATH, "-p", "--allowedTools", config.INBOX_ALLOWED_TOOLS, "--model", CLAUDE_MODEL, prompt],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return f"Launched {label} in background. Results will arrive when done."
    except FileNotFoundError:
        return f"Claude CLI not found at {CLAUDE_PATH}"
    except Exception as e:
        logger.error(f"Failed to launch {label}: {e}")
        return f"Error launching {label}: {str(e)}"


def handle_email_command(text: str, chat_id: int, user_id: int) -> str:
    """Handle /email commands."""
    global pending_email_sends

    parts = text.split(maxsplit=2)
    # /email with no subcommand
    if len(parts) < 2:
        return """Email Commands:

/email fetch [1d|7d|30d] - Fetch TODOs from inbox (background)
/email clean - Start inbox cleaner (background)
/email triage [query] - Scan inbox, convert to TODOs + /qw
/email search <query> - Search (Gmail syntax)
/email read <id> - Read full email
/email archive <id> - Archive message
/email send <to> :: <subject> :: <body>
/email draft <to> :: <subject> :: <body>
/email drafts - List Gmail drafts

Triage: converts emails to TODOs with /qw quick-win support

Search examples:
  is:unread
  from:darrell subject:launch
  newer_than:2d has:attachment"""

    subcommand = parts[1].lower()

    # --- /email search <query> ---
    if subcommand == 'search':
        global pending_email_search

        if len(parts) < 3:
            return "Usage: /email search <query>\n\nExample: /email search is:unread"

        query = parts[2]
        results = gmail_client.search(query, max_results=10)
        if not results:
            return f"No results for: {query}"

        pending_email_search[user_id] = {'results': {}, 'state': 'list', 'draft': None, 'reading': None}

        lines = [f"Search: {query} ({len(results)} results)", ""]
        for i, msg in enumerate(results, 1):
            sender = msg['from']
            if '<' in sender:
                sender = sender.split('<')[0].strip().strip('"')
            date_short = msg['date'].split(',')[0] if ',' in msg['date'] else msg['date'][:10]

            pending_email_search[user_id]['results'][i] = {
                'id': msg['id'],
                'thread_id': msg.get('thread_id'),
                'from': msg['from'],
                'from_short': sender,
                'subject': msg.get('subject', '(no subject)'),
                'date': msg.get('date', ''),
            }

            lines.append(f"{i}. {sender}")
            lines.append(f"   {msg['subject']}")
            lines.append(f"   {date_short}")
            lines.append("")

        lines.append('"read N" to view full email')
        lines.append('"reply N" to draft a reply')

        return "\n".join(lines)

    # --- /email read <id> ---
    elif subcommand == 'read':
        if len(parts) < 3:
            return "Usage: /email read <message_id>"

        message_id = parts[2].strip()
        email = gmail_client.read(message_id)
        if not email:
            return f"Could not read message {message_id}"

        body = email['body'] or "(empty body)"
        # Truncate body for Telegram
        if len(body) > 3000:
            body = body[:3000] + "\n\n... (truncated)"

        lines = [
            f"From: {email['from']}",
            f"To: {email['to']}",
        ]
        if email.get('cc'):
            lines.append(f"CC: {email['cc']}")
        lines.extend([
            f"Subject: {email['subject']}",
            f"Date: {email['date']}",
            f"Labels: {', '.join(email.get('labels', []))}",
            "",
            body,
        ])
        return "\n".join(lines)

    # --- /email archive <id> ---
    elif subcommand == 'archive':
        if len(parts) < 3:
            return "Usage: /email archive <message_id>"

        message_id = parts[2].strip()
        gmail_client.archive(message_id)
        return f"Archived message {message_id}"

    # --- /email send <to> :: <subject> :: <body> ---
    elif subcommand == 'send':
        if len(parts) < 3:
            return "Usage: /email send <to> :: <subject> :: <body>"

        raw = parts[2]
        send_parts = [p.strip() for p in raw.split('::')]
        if len(send_parts) < 3:
            return "Format: /email send <to> :: <subject> :: <body>\n\nUse :: to separate fields."

        to_addr, subject, body = send_parts[0], send_parts[1], '::'.join(send_parts[2:])

        # Store pending and ask for confirmation
        pending_email_sends[user_id] = {
            "to": to_addr,
            "subject": subject,
            "body": body,
        }

        preview = f"""Review before sending:

To: {to_addr}
Subject: {subject}

{body[:500]}

Reply "yes" or "send" to confirm, "no" to cancel."""
        return preview

    # --- /email draft <to> :: <subject> :: <body> ---
    elif subcommand == 'draft':
        if len(parts) < 3:
            return "Usage: /email draft <to> :: <subject> :: <body>"

        raw = parts[2]
        draft_parts = [p.strip() for p in raw.split('::')]
        if len(draft_parts) < 3:
            return "Format: /email draft <to> :: <subject> :: <body>\n\nUse :: to separate fields."

        to_addr, subject, body = draft_parts[0], draft_parts[1], '::'.join(draft_parts[2:])
        result = gmail_client.create_draft(to_addr, subject, body)
        return f"Draft created (ID: {result['id']})\nTo: {to_addr}\nSubject: {subject}"

    # --- /email drafts ---
    elif subcommand == 'drafts':
        drafts = gmail_client.list_drafts(max_results=10)
        if not drafts:
            return "No drafts found."

        lines = [f"Gmail Drafts ({len(drafts)})", ""]
        for i, d in enumerate(drafts, 1):
            lines.append(f"{i}. To: {d['to'] or '(no recipient)'}")
            lines.append(f"   {d['subject']}")
            lines.append(f"   ID: {d['id']}")
            lines.append("")

        return "\n".join(lines)

    # --- /email fetch [period] ---
    elif subcommand == 'fetch':
        period = parts[2].strip() if len(parts) > 2 else '1d'
        return _launch_email_background_agent('fetch', period, chat_id)

    # --- /email clean ---
    elif subcommand == 'clean':
        return _launch_email_background_agent('clean', None, chat_id)

    # --- /email triage [query] ---
    elif subcommand == 'triage':
        global pending_email_triage

        query = parts[2].strip() if len(parts) > 2 else getattr(
            config, 'EMAIL_TRIAGE_DEFAULT_QUERY', 'is:inbox is:unread newer_than:3d'
        )
        max_results = getattr(config, 'EMAIL_TRIAGE_MAX_RESULTS', 10)

        results = gmail_client.search(query, max_results=max_results)
        if not results:
            return f"No emails found for: {query}"

        # Separate junk from actionable, auto-archive junk
        pending_email_triage[user_id] = {}
        junk_archived = []
        actionable_idx = 0

        for msg in results:
            sender = msg['from']
            if '<' in sender:
                sender = sender.split('<')[0].strip().strip('"')

            is_junk = _is_junk_email(msg['from'], msg.get('subject', ''), msg.get('snippet', ''), msg.get('labels', []))

            if is_junk:
                # Auto-archive junk immediately
                try:
                    _label_if_finance(msg['id'], msg.get('subject', ''), msg['from'], msg.get('snippet', ''))
                    gmail_client.archive(msg['id'])
                    junk_archived.append({
                        'id': msg['id'],
                        'from_short': sender,
                        'subject': msg.get('subject', '(no subject)'),
                    })
                except Exception as e:
                    logger.warning(f"Failed to auto-archive junk: {e}")
            else:
                actionable_idx += 1
                pending_email_triage[user_id][actionable_idx] = {
                    'id': msg['id'],
                    'thread_id': msg.get('thread_id'),
                    'from': msg['from'],
                    'from_short': sender,
                    'subject': msg.get('subject', '(no subject)'),
                    'snippet': msg.get('snippet', ''),
                    'date': msg.get('date', ''),
                }

        # Store archived junk IDs for undo
        pending_email_triage[user_id]['_junk_archived'] = junk_archived

        # Build output
        lines = [f"Inbox Triage ({len(results)} scanned)", ""]

        if actionable_idx > 0:
            for i in range(1, actionable_idx + 1):
                data = pending_email_triage[user_id][i]
                lines.append(f"{i}. {data['from_short']}")
                lines.append(f"   {data['subject']}")
                lines.append(f'   "{data["snippet"][:80]}"')
                lines.append("")

            lines.append('"todo 1" or "todo 1 2 3" to create TODOs')
            lines.append('"archive 1 2 5" to archive, "nuke" to archive all, "skip" to dismiss')
        else:
            lines.append("No actionable emails.")

        if junk_archived:
            lines.append("")
            lines.append(f"Auto-archived {len(junk_archived)} junk:")
            for j in junk_archived:
                lines.append(f"  - {j['from_short']}: {j['subject'][:50]}")
            lines.append('"undo junk" to move all back to inbox')

        return "\n".join(lines)

    else:
        return f"Unknown email subcommand: {subcommand}\n\nUse /email for help."


def handle_email_send_confirmation(text: str, user_id: int, chat_id: int) -> Optional[str]:
    """Handle yes/no confirmation for pending email sends."""
    global pending_email_sends

    if user_id not in pending_email_sends:
        return None

    text_lower = text.lower().strip()

    if text_lower in ('yes', 'send', 'y', 'confirm'):
        pending = pending_email_sends.pop(user_id)
        result = gmail_client.send(
            to=pending['to'],
            subject=pending['subject'],
            body=pending['body'],
        )
        return f"Email sent to {pending['to']} (ID: {result['id']})"

    elif text_lower in ('no', 'cancel', 'n', 'abort'):
        pending_email_sends.pop(user_id)
        return "Email cancelled."

    return None


def handle_email_triage_action(text: str, user_id: int, chat_id: int) -> Optional[str]:
    """Handle triage responses: 'todo 1', 'todo 1 2 3', 'archive 1', 'skip'."""
    global pending_email_triage

    if user_id not in pending_email_triage or not pending_email_triage[user_id]:
        # Catch known triage keywords so they don't fall through to Claude
        if text.lower().strip() in ('nuke', 'skip', 'undo junk') or re.match(r'(archive|todo|read)\s+[\d\s]+', text.lower().strip()):
            return "No active triage session. Run /email triage first."
        return None

    text_lower = text.lower().strip()

    # "skip" — dismiss triage
    if text_lower == 'skip':
        count = len([k for k in pending_email_triage[user_id] if isinstance(k, int)])
        pending_email_triage.pop(user_id)
        return f"Triage dismissed ({count} emails)."

    # "nuke" — archive everything in triage
    if text_lower == 'nuke':
        items = [(k, v) for k, v in pending_email_triage[user_id].items() if isinstance(k, int)]
        archived = 0
        for num, email_data in items:
            try:
                _label_if_finance(email_data['id'], email_data['subject'], email_data['from'], email_data.get('snippet', ''))
                gmail_client.archive(email_data['id'])
                archived += 1
            except Exception as e:
                logger.warning(f"Nuke failed for #{num}: {e}")
        pending_email_triage.pop(user_id)
        return f"Nuked {archived}/{len(items)} emails. Inbox clear."

    # "archive N" or "archive 1 2 4 5 7" — archive emails
    archive_match = re.match(r'archive\s+([\d\s]+)', text_lower)
    if archive_match:
        nums = [int(n) for n in archive_match.group(1).split()]
        results = []

        for num in nums:
            if num not in pending_email_triage[user_id]:
                results.append(f"#{num}: not found")
                continue

            email_data = pending_email_triage[user_id].pop(num)
            try:
                fin = _label_if_finance(email_data['id'], email_data['subject'], email_data['from'], email_data.get('snippet', ''))
                gmail_client.archive(email_data['id'])
                label_note = " [Receipts]" if fin else ""
                results.append(f"Archived{label_note}: {email_data['from_short']} — {email_data['subject']}")
            except Exception as e:
                results.append(f"#{num}: archive failed — {e}")

        return "\n".join(results)

    # "todo N" or "todo 1 2 3" — convert to TODOs
    todo_match = re.match(r'todo\s+([\d\s]+)', text_lower)
    if todo_match:
        nums = [int(n) for n in todo_match.group(1).split()]
        results = []

        for num in nums:
            if num not in pending_email_triage[user_id]:
                results.append(f"#{num}: not found")
                continue

            email_data = pending_email_triage[user_id].pop(num)

            # Label finance emails + mark as read so it won't reappear in triage
            _label_if_finance(email_data['id'], email_data['subject'], email_data['from'], email_data.get('snippet', ''))
            try:
                gmail_client.mark_read(email_data['id'])
            except Exception as e:
                logger.warning(f"Failed to mark email as read: {e}")

            # Create TODO with email metadata
            todo_text = f"[Email] Reply to {email_data['from_short']}: {email_data['subject']}"
            metadata = {
                'source': 'email',
                'email_id': email_data['id'],
                'email_from': email_data['from'],
                'email_subject': email_data['subject'],
                'email_thread_id': email_data.get('thread_id', ''),
                'created': datetime.now().isoformat() if 'datetime' in dir() else '',
            }

            # Use datetime import
            from datetime import datetime as dt
            metadata['created'] = dt.now().isoformat()

            success, todo_id = todo_manager.add_todo(
                text=todo_text,
                section='TODAY',
                metadata=metadata,
            )

            if success:
                # Run prework to detect quick wins
                qw_note = ""
                if prework_engine:
                    todos = todo_manager.get_todos(include_completed=False)
                    new_todo = next((t for t in todos if t.get('id') == todo_id), None)
                    if new_todo:
                        try:
                            pw_result = run_prework_for_new_todo(
                                todo=new_todo,
                                todo_manager=todo_manager,
                                slack_context=getattr(todo_manager, 'slack_context', None),
                                slack_registry=slack_registry if AGENT_AVAILABLE else None,
                                gmail_client=gmail_client,
                            )
                            if pw_result and pw_result.is_quick_win:
                                qw_note = " (quick win — use /qw)"
                        except Exception as e:
                            logger.warning(f"Prework failed for email TODO: {e}")

                results.append(f"[{todo_id}] {email_data['from_short']}: {email_data['subject']}{qw_note}")
            else:
                results.append(f"#{num}: failed to create TODO")

        return "TODOs created:\n" + "\n".join(results)

    # "undo junk" — unarchive auto-archived junk emails
    if text_lower == 'undo junk':
        junk_list = pending_email_triage[user_id].get('_junk_archived', [])
        if not junk_list:
            return "No junk to undo."

        restored = 0
        for item in junk_list:
            try:
                gmail_client.unarchive(item['id'])
                restored += 1
            except Exception as e:
                logger.warning(f"Failed to unarchive {item['id']}: {e}")

        pending_email_triage[user_id]['_junk_archived'] = []
        return f"Restored {restored}/{len(junk_list)} emails back to inbox."

    # "read N" — read full email from triage
    read_match = re.match(r'read\s+(\d+)', text_lower)
    if read_match:
        num = int(read_match.group(1))
        if num not in pending_email_triage[user_id]:
            return f"#{num} not found in triage."

        email_data = pending_email_triage[user_id][num]
        try:
            full_email = gmail_client.read(email_data['id'])
            if not full_email:
                return f"#{num}: couldn't load email."

            body = full_email.get('body', '').strip()
            if len(body) > 3000:
                body = body[:3000] + "\n\n... (truncated)"

            lines = []
            lines.append(f"From: {full_email.get('from', '')}")
            lines.append(f"To: {full_email.get('to', '')}")
            if full_email.get('cc'):
                lines.append(f"CC: {full_email['cc']}")
            lines.append(f"Subject: {full_email.get('subject', '(no subject)')}")
            lines.append(f"Date: {full_email.get('date', '')}")
            lines.append("")
            lines.append(body)
            lines.append("")
            lines.append(f"— todo {num} | archive {num} | back to triage")

            return "\n".join(lines)
        except Exception as e:
            return f"#{num}: failed to read — {e}"

    return None


def handle_email_search_action(text: str, user_id: int, chat_id: int) -> Optional[str]:
    """Handle search result actions: read N, reply N, draft N [prompt], edit [prompt], send, back."""
    global pending_email_search

    if user_id not in pending_email_search:
        return None

    ctx = pending_email_search[user_id]
    text_lower = text.lower().strip()

    state = ctx.get('state', 'list')

    # --- "back" — return to search results list ---
    if text_lower == 'back':
        if state in ('reading', 'drafting'):
            ctx['state'] = 'list'
            ctx['draft'] = None
            ctx['reading'] = None
            # Re-display results
            lines = ["Back to search results:", ""]
            for i, data in sorted(ctx['results'].items()):
                lines.append(f"{i}. {data['from_short']}")
                lines.append(f"   {data['subject']}")
                lines.append("")
            lines.append('"read N" to view | "reply N" to draft')
            return "\n".join(lines)
        else:
            # Back from list = exit search mode
            pending_email_search.pop(user_id)
            return "Search closed."

    # --- State: list (viewing search results) ---
    if state == 'list':
        # "read N"
        read_match = re.match(r'read\s+(\d+)', text_lower)
        if read_match:
            num = int(read_match.group(1))
            if num not in ctx['results']:
                return f"No search result #{num}."

            email_data = ctx['results'][num]
            email = gmail_client.read(email_data['id'])
            if not email:
                return f"Could not read message."

            body = email.get('body', '(empty)')
            if len(body) > 3000:
                body = body[:3000] + "\n\n... (truncated)"

            ctx['state'] = 'reading'
            ctx['reading'] = num

            lines = [
                f"From: {email['from']}",
                f"To: {email['to']}",
            ]
            if email.get('cc'):
                lines.append(f"CC: {email['cc']}")
            lines.extend([
                f"Subject: {email['subject']}",
                f"Date: {email['date']}",
                "",
                body,
                "",
                "---",
                '"draft" to draft a reply',
                '"draft [instructions]" to draft with specific guidance',
                '"back" to return to results',
            ])
            return "\n".join(lines)

        # "reply N"
        reply_match = re.match(r'reply\s+(\d+)', text_lower)
        if reply_match:
            num = int(reply_match.group(1))
            if num not in ctx['results']:
                return f"No search result #{num}."

            return _generate_reply_draft(user_id, num, ctx)

        # Catch known keywords when no match
        if re.match(r'(read|reply|draft|send|edit)\b', text_lower):
            return "Usage: read N, reply N, or back"

        return None

    # --- State: reading (viewing a full email) ---
    if state == 'reading':
        num = ctx.get('reading')
        if not num or num not in ctx['results']:
            ctx['state'] = 'list'
            return "Lost context. Back to search results — use read N or reply N."

        # "draft" or "draft [instructions]"
        if text_lower == 'draft':
            return _generate_reply_draft(user_id, num, ctx)

        if text_lower.startswith('draft '):
            prompt = text[6:].strip()
            return _generate_reply_draft(user_id, num, ctx, prompt)

        if text_lower == 'back':
            # handled above, but just in case
            ctx['state'] = 'list'
            ctx['reading'] = None
            return "Back to results. Use read N or reply N."

        # Catch other keywords
        if text_lower in ('send', 'edit'):
            return "No draft in progress. Use 'draft' to create one first."

        return None

    # --- State: drafting (reviewing a draft reply) ---
    if state == 'drafting':
        draft = ctx.get('draft')
        if not draft:
            ctx['state'] = 'list'
            return "Lost draft context. Back to results."

        # "send" — send the draft
        if text_lower == 'send':
            try:
                email_data = ctx['results'].get(draft['num'])
                result = gmail_client.send(
                    to=draft['to'],
                    subject=draft['subject'],
                    body=draft['body'],
                    reply_to_message_id=email_data['id'] if email_data else None,
                    thread_id=email_data.get('thread_id') if email_data else None,
                )
                ctx['state'] = 'list'
                ctx['draft'] = None
                return f"Reply sent to {draft['to']} (ID: {result['id']})"
            except Exception as e:
                return f"Send failed: {str(e)}"

        # "edit [instructions]" — regenerate with guidance
        if text_lower.startswith('edit '):
            prompt = text[5:].strip()
            num = draft['num']
            return _generate_reply_draft(user_id, num, ctx, prompt)

        # Any other text while drafting = treat as edit instructions
        if text_lower not in ('back',):
            # Treat freeform text as edit instructions
            num = draft['num']
            return _generate_reply_draft(user_id, num, ctx, text.strip())

        return None

    return None


def _generate_reply_draft(user_id: int, num: int, ctx: dict, instructions: str = None) -> str:
    """Generate a reply draft for search result #num using Claude."""
    email_data = ctx['results'].get(num)
    if not email_data:
        return f"No search result #{num}."

    # Read full email for context
    email = gmail_client.read(email_data['id'])
    if not email:
        return "Could not read email to draft reply."

    body = email.get('body', '')[:2000]
    instruction_line = f"\nSpecific instructions: {instructions}" if instructions else ""

    prompt = (
        f"Draft a brief, ready-to-send email reply.\n\n"
        f"From: {email['from']}\n"
        f"Subject: {email['subject']}\n"
        f"Body:\n{body}\n"
        f"{instruction_line}\n\n"
        f"Requirements:\n"
        f"- Be direct and concise\n"
        f"- Use {config.USER_NAME}'s voice (professional, efficient, friendly)\n"
        f"- Reply to what was asked\n"
        f"- Output ONLY the reply body text, no preamble or subject line"
    )

    draft_body = run_claude(prompt)

    # Determine reply subject
    subj = email['subject']
    if not subj.lower().startswith('re:'):
        subj = f"Re: {subj}"

    # Extract email address from "Name <email>" format
    to_addr = email['from']
    email_match = re.search(r'<([^>]+)>', to_addr)
    if email_match:
        to_addr = email_match.group(1)

    ctx['state'] = 'drafting'
    ctx['draft'] = {
        'num': num,
        'to': to_addr,
        'subject': subj,
        'body': draft_body,
    }

    lines = [
        f"Draft reply to {email_data['from_short']}:",
        f"Subject: {subj}",
        "",
        draft_body,
        "",
        "---",
        '"send" to send',
        '"edit [instructions]" to revise (or just type instructions)',
        '"back" to cancel',
    ]
    return "\n".join(lines)


def run_claude(prompt: str, context: str = "") -> str:
    """Run Claude CLI with error handling and optional conversation context"""
    try:
        # Combine context with current prompt
        full_prompt = f"{context}\n{prompt}" if context else prompt

        result = subprocess.run(
            [CLAUDE_PATH, "-p", "--model", CLAUDE_MODEL, full_prompt],
            capture_output=True,
            text=True,
            timeout=config.CLAUDE_TIMEOUT
        )

        if result.returncode != 0:
            error_msg = result.stderr or "Claude command failed"
            logger.error(f"Claude CLI error: {error_msg}")
            return f"Error running Claude: {error_msg}"

        return result.stdout or result.stderr or "No response from Claude"

    except subprocess.TimeoutExpired:
        logger.error("Claude command timed out")
        return f"Error: Request timed out after {config.CLAUDE_TIMEOUT} seconds"
    except FileNotFoundError:
        logger.error("Claude CLI not found")
        return "Error: Claude CLI is not installed or not in PATH"
    except Exception as e:
        logger.error(f"Unexpected error running Claude: {e}")
        return f"Error: {str(e)}"

def main():
    """Main bot loop with graceful shutdown"""
    global running

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("Bot started. Press Ctrl+C to stop.")

    # Start scheduler and register default jobs
    if job_scheduler and todo_manager:
        try:
            # Register unified morning briefing (work + personal combined)
            hour, minute = config.DEFAULT_TODO_SUMMARY_TIME
            top_n = getattr(config, 'MORNING_TOP_PRIORITIES', 3)
            unified_briefing_job = BuiltInJobs.create_unified_briefing_job(
                send_message,
                todo_manager,
                config.AUTHORIZED_USERS[0],
                scheduler_state,
                top_n,
            )
            job_scheduler.register_job_function('send_todo_summary', unified_briefing_job)

            # Add daily unified briefing job
            job_scheduler.add_daily_job(
                'daily_todo_summary',
                'send_todo_summary',
                hour,
                minute
            )

            # Register evening summary job
            evening_hour, evening_minute = getattr(config, 'DEFAULT_EVENING_SUMMARY_TIME', (17, 0))
            evening_summary_job = BuiltInJobs.create_evening_summary_job(
                send_message,
                todo_manager,
                config.AUTHORIZED_USERS[0],
                scheduler_state
            )
            job_scheduler.register_job_function('send_evening_summary', evening_summary_job)

            # Add daily evening summary job
            job_scheduler.add_daily_job(
                'evening_summary',
                'send_evening_summary',
                evening_hour,
                evening_minute
            )

            # Register ventures dawn read-back push (standup #8 accord)
            if VENTURES_AVAILABLE and getattr(config, 'VENTURES_ENABLED', False):
                v_hour, v_minute = getattr(config, 'VENTURES_MORNING_TIME', (8, 5))

                def send_ventures_morning():
                    try:
                        v_lines = ventures_signal.render_section('morning')
                        if v_lines:
                            send_message(config.AUTHORIZED_USERS[0], "\n".join(v_lines))
                        if scheduler_state:
                            scheduler_state.mark_job_run('ventures_morning')
                    except Exception as e:
                        logger.error(f"ventures morning push failed: {e}")

                job_scheduler.register_job_function('send_ventures_morning', send_ventures_morning)
                job_scheduler.add_daily_job('ventures_morning', 'send_ventures_morning', v_hour, v_minute)

            # Register weekly review job
            weekly_review_job = BuiltInJobs.create_weekly_review_job(
                send_message,
                todo_manager,
                config.AUTHORIZED_USERS[0]
            )
            job_scheduler.register_job_function('send_weekly_review', weekly_review_job)

            # Add weekly review job
            review_hour, review_minute = config.DEFAULT_WEEKLY_REVIEW_TIME
            job_scheduler.add_weekly_job(
                'weekly_review',
                'send_weekly_review',
                config.DEFAULT_WEEKLY_REVIEW_DAY,
                review_hour,
                review_minute
            )

            # Register scheduled Slack TODO sync job (8:15 AM, before digest at 9 AM)
            slack_sync_job = BuiltInJobs.create_slack_sync_job(
                send_message,
                todo_manager,
                config.AUTHORIZED_USERS[0],
                scheduler_state
            )
            job_scheduler.register_job_function('slack_sync', slack_sync_job)
            job_scheduler.add_daily_job('daily_slack_sync', 'slack_sync', 8, 15)
            logger.info("Slack sync job registered at 8:15 AM")

            # Register weekly archive job (Sunday 8 PM)
            archive_job = BuiltInJobs.create_archive_job(
                send_message,
                todo_manager,
                config.AUTHORIZED_USERS[0],
                scheduler_state
            )
            job_scheduler.register_job_function('archive_completed', archive_job)
            job_scheduler.add_weekly_job('weekly_archive', 'archive_completed', 'sun', 20, 0)
            logger.info("Archive job registered for Sunday 8:00 PM")

            # Register slack digest job (if drafts available)
            if DRAFTS_AVAILABLE:
                slack_digest_job = BuiltInJobs.create_slack_digest_job(
                    send_message,
                    todo_manager,
                    config.AUTHORIZED_USERS[0],
                    scheduler_state
                )
                job_scheduler.register_job_function('slack_digest', slack_digest_job)

                # Add morning slack digest job at 9am
                job_scheduler.add_daily_job(
                    'morning_slack_digest',
                    'slack_digest',
                    9,  # 9am
                    0
                )
                logger.info("Slack digest job registered at 9:00 AM")

            # Register war room questions job (if available)
            if WARROOM_AVAILABLE and warroom_manager:
                warroom_questions_job = BuiltInJobs.create_warroom_questions_job(
                    send_message,
                    warroom_manager,
                    todo_manager,
                    config.AUTHORIZED_USERS[0],
                    scheduler_state
                )
                job_scheduler.register_job_function('warroom_questions', warroom_questions_job)

                # Add daily war room questions job
                warroom_hour = getattr(config, 'WARROOM_QUESTIONS_HOUR', 8)
                warroom_minute = getattr(config, 'WARROOM_QUESTIONS_MINUTE', 30)
                job_scheduler.add_daily_job(
                    'daily_warroom_questions',
                    'warroom_questions',
                    warroom_hour,
                    warroom_minute
                )
                logger.info(f"War Room questions job registered at {warroom_hour:02d}:{warroom_minute:02d}")

            # Start scheduler
            job_scheduler.start()
            logger.info(f"Scheduler started with {len(job_scheduler.get_jobs())} jobs")

        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")

    offset = None
    consecutive_errors = 0
    max_consecutive_errors = 10
    last_cleanup = time.time()
    last_inbox_check = time.time()
    last_ventures_alert_check = time.time()

    while running:
        try:
            logger.debug(f"Polling for updates (offset={offset})...")
            updates = get_updates(offset)
            logger.debug(f"Got {len(updates)} updates")

            if updates:
                consecutive_errors = 0

            for update in updates:
                if not running:
                    break

                try:
                    offset = update["update_id"] + 1

                    # Handle inline-keyboard button presses (Claude Code permission gate)
                    callback = update.get("callback_query")
                    if callback:
                        handle_permission_callback(callback)
                        continue

                    msg = update.get("message", {})

                    if not msg:
                        continue

                    text = msg.get("text")
                    voice = msg.get("voice")
                    chat = msg.get("chat", {})
                    chat_id = chat.get("id")
                    user_info = msg.get("from", {})
                    user_id = user_info.get("id")
                    username = user_info.get("username", "unknown")

                    # Handle voice messages
                    is_voice_message = False
                    if voice and not text:
                        if not voice_handler:
                            send_message(chat_id, "Voice not available — handler not initialized")
                            continue

                        file_id = voice.get("file_id")
                        if not file_id:
                            continue

                        send_message(chat_id, "Downloading audio...")
                        audio_path = voice_handler.download_voice_file(file_id)
                        if not audio_path:
                            send_message(chat_id, "Failed to download voice file.")
                            continue

                        send_message(chat_id, "Transcribing...")
                        transcribed_text = voice_handler.transcribe(audio_path)

                        # Clean up temp file
                        try:
                            import os as _os
                            if audio_path and _os.path.exists(audio_path):
                                _os.remove(audio_path)
                        except Exception:
                            pass

                        if not transcribed_text:
                            send_message(chat_id, "Transcription failed.")
                            continue

                        text = transcribed_text
                        is_voice_message = True
                        send_message(chat_id, f"Heard: {text}")
                        logger.info(f"Transcribed voice message from @{username}: {text[:50]}...")

                    if not text or not chat_id or not user_id:
                        continue

                    # Check authorization
                    if not is_authorized(user_id):
                        if config.LOG_UNAUTHORIZED_ATTEMPTS:
                            logger.warning(f"Unauthorized access attempt from @{username} (user_id: {user_id}, chat: {chat_id})")
                        send_message(chat_id, "⛔ Unauthorized. This bot is private.")
                        continue

                    # Handle 'y <req_id>' / 'n <req_id>' permission replies before anything else
                    if handle_permission_text_reply(text, chat_id, user_id):
                        continue

                    # Mobile mode: /mobile /desktop /mode /tabs + reply-to-tab routing
                    if MOBILE_AVAILABLE:
                        try:
                            if mobile_mode.handle_mobile_command(text, chat_id, send_message):
                                continue
                            if mobile_mode.handle_mobile_reply(msg, text, chat_id, send_message):
                                continue
                        except Exception as _me:
                            logger.error(f"mobile_mode error: {_me}")

                    msg_type = "🎤 voice" if is_voice_message else "text"
                    logger.info(f"Received {msg_type} message from @{username} (chat {chat_id}): {text[:50]}...")

                    # Get or create session
                    session_manager.get_or_create_session(user_id, chat_id)

                    # Check for missed daily TODO summary (catch-up on first activity)
                    if scheduler_state and todo_manager and job_scheduler and getattr(config, 'CATCHUP_SUMMARY_ENABLED', True):
                        try:
                            hour, minute = config.DEFAULT_TODO_SUMMARY_TIME
                            if scheduler_state.should_catch_up('daily_todo_summary', hour, minute):
                                # Send the missed summary
                                summary = todo_manager.get_summary()
                                todos = todo_manager.get_todos(include_completed=False)
                                todo_list = todo_manager.format_todos(todos, numbered=True)

                                catch_up_message = f"""☀️ Good morning! (Catch-up summary)

{summary}

{todo_list}"""

                                send_message(chat_id, catch_up_message)
                                scheduler_state.mark_job_run('daily_todo_summary')
                                logger.info(f"Sent catch-up TODO summary to chat {chat_id}")

                        except Exception as e:
                            logger.error(f"Error sending catch-up summary: {e}")

                    # Check if this is a command
                    command_response = handle_command(text, user_id, chat_id)
                    if command_response:
                        send_message(chat_id, command_response)
                        continue

                    # Check for natural language draft commands
                    if DRAFTS_AVAILABLE:
                        text_lower = text.lower()

                        # Draft commands
                        if any(p in text_lower for p in ['show drafts', 'list drafts', 'pending drafts']):
                            response = handle_command('/drafts', user_id, chat_id)
                            if response:
                                send_message(chat_id, response)
                                session_manager.add_message(user_id, 'user', text)
                                session_manager.add_message(user_id, 'assistant', response)
                                continue

                        if any(p in text_lower for p in ['quick wins', 'quickwins', 'low hanging fruit']):
                            response = handle_command('/quickwins', user_id, chat_id)
                            if response:
                                send_message(chat_id, response)
                                session_manager.add_message(user_id, 'user', text)
                                session_manager.add_message(user_id, 'assistant', response)
                                continue

                        if any(p in text_lower for p in ['sync slack', 'generate drafts', 'make drafts']):
                            response = handle_command('/syncslack', user_id, chat_id)
                            if response:
                                send_message(chat_id, response)
                                session_manager.add_message(user_id, 'user', text)
                                session_manager.add_message(user_id, 'assistant', response)
                                continue

                        # View specific draft: "view DRF001" or "show draft DRF001"
                        view_match = re.search(r'(?:view|show)\s+(?:draft\s+)?(?:DRF)?(\d{3})', text, re.IGNORECASE)
                        if view_match:
                            draft_num = view_match.group(1)
                            response = handle_command(f'/draft DRF{draft_num}', user_id, chat_id)
                            if response:
                                send_message(chat_id, response)
                                session_manager.add_message(user_id, 'user', text)
                                session_manager.add_message(user_id, 'assistant', response)
                                continue

                        # Check for "send DRF..." pattern
                        send_draft_match = re.match(r'send\s+(DRF\d{3})', text, re.IGNORECASE)
                        if send_draft_match:
                            draft_id = send_draft_match.group(1).upper()
                            response = handle_send_draft_command(draft_id, chat_id, user_id)
                            send_message(chat_id, response)
                            session_manager.add_message(user_id, 'user', text)
                            session_manager.add_message(user_id, 'assistant', response)
                            continue

                        # Check for "skip DRF..." pattern
                        skip_draft_match = re.match(r'skip\s+(DRF\d{3})', text, re.IGNORECASE)
                        if skip_draft_match:
                            draft_id = skip_draft_match.group(1).upper()
                            response = handle_skip_draft_command(draft_id, chat_id)
                            send_message(chat_id, response)
                            session_manager.add_message(user_id, 'user', text)
                            session_manager.add_message(user_id, 'assistant', response)
                            continue

                    # Check for pending email send confirmation
                    if gmail_client:
                        email_confirm = handle_email_send_confirmation(text, user_id, chat_id)
                        if email_confirm:
                            send_message(chat_id, email_confirm)
                            session_manager.add_message(user_id, 'user', text)
                            session_manager.add_message(user_id, 'assistant', email_confirm)
                            continue

                    # Check for pending email search actions (read N, reply N, send, edit, back)
                    if gmail_client:
                        search_response = handle_email_search_action(text, user_id, chat_id)
                        if search_response:
                            send_message(chat_id, search_response)
                            session_manager.add_message(user_id, 'user', text)
                            session_manager.add_message(user_id, 'assistant', search_response)
                            continue

                    # Check for pending email triage actions (todo N, archive N, skip)
                    if gmail_client:
                        triage_response = handle_email_triage_action(text, user_id, chat_id)
                        if triage_response:
                            send_message(chat_id, triage_response)
                            session_manager.add_message(user_id, 'user', text)
                            session_manager.add_message(user_id, 'assistant', triage_response)
                            continue

                    # Check for quick win actions (send N, skip N, etc.)
                    qw_response = handle_qw_action(text, user_id, chat_id)
                    if qw_response:
                        send_message(chat_id, qw_response)
                        session_manager.add_message(user_id, 'user', text)
                        session_manager.add_message(user_id, 'assistant', qw_response)
                        continue

                    # Check for natural language smart view commands
                    text_lower_check = text.lower().strip()

                    # "what now", "what's next", "what should I do" -> /now
                    if any(p in text_lower_check for p in ['what now', "what's next", 'what next', 'what should i do', 'what do i do']):
                        response = handle_now_command(chat_id, user_id)
                        send_message(chat_id, response)
                        session_manager.add_message(user_id, 'user', text)
                        session_manager.add_message(user_id, 'assistant', response)
                        continue

                    # "quick wins", "qw" -> /qw
                    if text_lower_check in ['quick wins', 'qw', 'quickwins']:
                        response = handle_qw_command(chat_id, user_id)
                        send_message(chat_id, response)
                        session_manager.add_message(user_id, 'user', text)
                        session_manager.add_message(user_id, 'assistant', response)
                        continue

                    # "status" -> /status
                    if text_lower_check == 'status':
                        response = handle_status_compact(chat_id, user_id)
                        send_message(chat_id, response)
                        session_manager.add_message(user_id, 'user', text)
                        session_manager.add_message(user_id, 'assistant', response)
                        continue

                    # "ventures" -> /ventures status; "ack night"/"ack day" -> /ventures ack
                    if VENTURES_AVAILABLE and getattr(config, 'VENTURES_ENABLED', False):
                        if text_lower_check == 'ventures':
                            response = ventures_signal.handle_ventures_command('/ventures', chat_id, user_id)
                            send_message(chat_id, response)
                            session_manager.add_message(user_id, 'user', text)
                            session_manager.add_message(user_id, 'assistant', response)
                            continue
                        ack_match = re.match(r'^ack\s+(night|day)$', text_lower_check)
                        if ack_match:
                            response = ventures_signal.ack(ack_match.group(1))
                            send_message(chat_id, response)
                            session_manager.add_message(user_id, 'user', text)
                            session_manager.add_message(user_id, 'assistant', response)
                            continue

                    # "morning" or "morning briefing" -> /morning
                    if text_lower_check in ['morning', 'morning briefing', 'good morning']:
                        response = handle_morning_command(chat_id, user_id)
                        send_message(chat_id, response)
                        session_manager.add_message(user_id, 'user', text)
                        session_manager.add_message(user_id, 'assistant', response)
                        continue

                    # "todos with [person]", "[person]'s todos" -> /by [person]
                    by_person_match = re.search(r"(?:todos?\s+(?:with|for)\s+|(\w+)'s\s+todos?)(\w+)?", text_lower_check)
                    if by_person_match:
                        person = by_person_match.group(2) or by_person_match.group(1)
                        if person:
                            response = handle_by_person_command(person, chat_id)
                            send_message(chat_id, response)
                            session_manager.add_message(user_id, 'user', text)
                            session_manager.add_message(user_id, 'assistant', response)
                            continue

                    # Check for natural language agent commands
                    if AGENT_AVAILABLE and agent_executor:
                        text_lower = text.lower()

                        # Agent plan: "agent TXXX", "plan TXXX", "generate plan for TXXX"
                        agent_match = re.search(r'(?:agent|plan(?:\s+for)?)\s+#?(T[A-Z0-9]{3})', text, re.IGNORECASE)
                        if agent_match:
                            todo_id = agent_match.group(1).upper()
                            response = handle_command(f'/agent {todo_id}', user_id, chat_id)
                            if response:
                                send_message(chat_id, response)
                                session_manager.add_message(user_id, 'user', text)
                                session_manager.add_message(user_id, 'assistant', response)
                                continue

                        # Approve: "approve TXXX", "execute TXXX", "run plan TXXX"
                        approve_match = re.search(r'(?:approve|execute|run\s+plan(?:\s+for)?)\s+#?(T[A-Z0-9]{3})', text, re.IGNORECASE)
                        if approve_match:
                            todo_id = approve_match.group(1).upper()
                            response = handle_command(f'/approve {todo_id}', user_id, chat_id)
                            if response:
                                send_message(chat_id, response)
                                session_manager.add_message(user_id, 'user', text)
                                session_manager.add_message(user_id, 'assistant', response)
                                continue

                        # Cancel: "cancel TXXX", "abort TXXX"
                        cancel_match = re.search(r'(?:cancel|abort)\s+#?(T[A-Z0-9]{3})', text, re.IGNORECASE)
                        if cancel_match:
                            todo_id = cancel_match.group(1).upper()
                            response = handle_command(f'/cancel {todo_id}', user_id, chat_id)
                            if response:
                                send_message(chat_id, response)
                                session_manager.add_message(user_id, 'user', text)
                                session_manager.add_message(user_id, 'assistant', response)
                                continue

                        # Show plans: "show plans", "pending plans", "list plans"
                        if any(p in text_lower for p in ['show plans', 'pending plans', 'list plans', 'my plans']):
                            response = handle_command('/plans', user_id, chat_id)
                            if response:
                                send_message(chat_id, response)
                                session_manager.add_message(user_id, 'user', text)
                                session_manager.add_message(user_id, 'assistant', response)
                                continue

                    # Check for natural language TODO commands
                    if todo_manager:
                        todo_command = todo_manager.parse_natural_language(text)
                        if todo_command:
                            action = todo_command['action']
                            params = todo_command['params']

                            try:
                                if action == 'add':
                                    due_date = params.get('due_date')
                                    success, todo_id = todo_manager.add_todo(params['text'], due_date=due_date)
                                    if success:
                                        if config.TODO_AUTO_UPDATE_DATE:
                                            todo_manager.update_last_updated_date()
                                        due_msg = f" (due {due_date})" if due_date else ""
                                        response = f"✅ Added to TODO [{todo_id}]: {params['text']}{due_msg}"

                                        # Run prework if available
                                        if prework_engine and AGENT_AVAILABLE:
                                            try:
                                                todos = todo_manager.get_todos(include_completed=False)
                                                new_todo = next((t for t in todos if t.get('id') == todo_id), None)
                                                if new_todo:
                                                    pw_result = prework_engine.run_prework(new_todo)
                                                    if pw_result and pw_result.is_quick_win:
                                                        response += f"\n\n**Quick Win Detected**\nUse '/prework {todo_id}' for suggested action"
                                            except Exception as e:
                                                logger.debug(f"Prework skipped for manual add: {e}")
                                    else:
                                        response = "❌ Failed to add TODO"

                                elif action == 'complete':
                                    success, message = todo_manager.mark_complete(params['identifier'])
                                    if success and config.TODO_AUTO_UPDATE_DATE:
                                        todo_manager.update_last_updated_date()
                                    response = message

                                elif action == 'complete_multiple':
                                    count, messages = todo_manager.mark_multiple_complete(params['identifiers'])
                                    if count > 0 and config.TODO_AUTO_UPDATE_DATE:
                                        todo_manager.update_last_updated_date()
                                    response = f"✅ Marked {count} TODO(s) complete:\n" + "\n".join(messages)

                                elif action == 'show':
                                    todos = todo_manager.get_todos(include_completed=False)
                                    response = todo_manager.format_todos(todos, numbered=True)

                                elif action == 'show_overdue':
                                    overdue = todo_manager.get_overdue_todos()
                                    if not overdue:
                                        response = "✅ No overdue items! You're on track."
                                    else:
                                        response = "🔴 Overdue Items:\n\n" + todo_manager.format_todos(overdue, numbered=True)

                                elif action == 'show_due_today':
                                    due_today = todo_manager.get_due_today_todos()
                                    if not due_today:
                                        response = "📅 Nothing due today!"
                                    else:
                                        response = "📅 Due Today:\n\n" + todo_manager.format_todos(due_today, numbered=True)

                                elif action == 'show_due_week':
                                    due_week = todo_manager.get_due_this_week_todos()
                                    if not due_week:
                                        response = "📅 Nothing due this week!"
                                    else:
                                        response = "📅 Due This Week:\n\n" + todo_manager.format_todos(due_week, numbered=True)

                                elif action == 'show_priorities':
                                    priorities = todo_manager.get_todos_by_priority(limit=5)
                                    if not priorities:
                                        response = "📋 No TODO items found!"
                                    else:
                                        response = "🎯 Top 5 Priorities:\n\n" + todo_manager.format_todos(priorities, numbered=True)

                                else:
                                    response = None

                                if response:
                                    send_message(chat_id, response)
                                    # Save TODO interaction to session
                                    session_manager.add_message(user_id, 'user', text)
                                    session_manager.add_message(user_id, 'assistant', response)
                                    continue

                            except Exception as e:
                                logger.error(f"Error handling TODO command: {e}")
                                send_message(chat_id, f"❌ Error: {str(e)}")
                                continue

                    # Get conversation context
                    context_messages = session_manager.get_context(user_id, config.MAX_CONTEXT_MESSAGES)
                    context = session_manager.format_context_for_claude(context_messages)

                    # Save user message to session
                    session_manager.add_message(user_id, 'user', text)

                    send_message(chat_id, "Processing your request...")

                    # Run Claude with context
                    response = run_claude(text, context)

                    # Save assistant response to session
                    session_manager.add_message(user_id, 'assistant', response)

                    # Use send_long_message to handle responses over 4096 chars
                    if send_long_message(chat_id, response):
                        logger.info(f"Sent response to chat {chat_id} ({len(response)} chars)")
                    else:
                        logger.error(f"Failed to send response to chat {chat_id}")

                except KeyError as e:
                    logger.error(f"Invalid update format: {e}")
                except Exception as e:
                    logger.error(f"Error processing update: {e}")

            # Periodic cleanup of expired sessions
            current_time = time.time()
            if current_time - last_cleanup > config.CLEANUP_INTERVAL_SECONDS:
                deleted = session_manager.cleanup_expired_sessions(config.SESSION_TIMEOUT_MINUTES)
                if deleted > 0:
                    logger.info(f"Cleaned up {deleted} expired session messages")
                last_cleanup = current_time

            # Check agent inbox for background agent completions
            if getattr(config, 'AGENT_INBOX_ENABLED', False) and current_time - last_inbox_check > getattr(config, 'AGENT_INBOX_POLL_SECONDS', 10):
                try:
                    inbox_path = getattr(config, 'AGENT_INBOX_PATH', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'inbox'))
                    if os.path.isdir(inbox_path):
                        for fname in sorted(os.listdir(inbox_path)):
                            fpath = os.path.join(inbox_path, fname)
                            if os.path.isfile(fpath) and fname.endswith('.md'):
                                with open(fpath, 'r') as f:
                                    content = f.read().strip()
                                if content:
                                    # Send to the user via Telegram
                                    header = f"🤖 Agent Complete: {fname.replace('.md', '')}"
                                    # Truncate if too long for Telegram
                                    max_len = config.MAX_MESSAGE_LENGTH - len(header) - 10
                                    if len(content) > max_len:
                                        content = content[:max_len] + "\n..."
                                    send_message(config.AUTHORIZED_USERS[0], f"{header}\n\n{content}")
                                    logger.info(f"Sent agent inbox notification: {fname}")
                                # Remove processed file
                                os.remove(fpath)
                except Exception as e:
                    logger.error(f"Error checking agent inbox: {e}")
                last_inbox_check = current_time

            # Ventures ALERT relay — alerts break cadence, they don't wait for it
            if VENTURES_AVAILABLE and getattr(config, 'VENTURES_ENABLED', False) and \
                    current_time - last_ventures_alert_check > getattr(config, 'VENTURES_ALERT_POLL_SECONDS', 30):
                try:
                    for push in ventures_signal.scan_alerts():
                        send_message(config.AUTHORIZED_USERS[0], push)
                        logger.info("Sent ventures alert relay")
                except Exception as e:
                    logger.error(f"Error in ventures alert relay: {e}")
                last_ventures_alert_check = current_time

            if not updates and running:
                time.sleep(1)

        except Exception as e:
            consecutive_errors += 1
            logger.error(f"Error in main loop: {e} (consecutive errors: {consecutive_errors})")

            if consecutive_errors >= max_consecutive_errors:
                logger.critical(f"Too many consecutive errors ({max_consecutive_errors}), shutting down")
                running = False
            else:
                time.sleep(5)

    logger.info("Bot stopped gracefully")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        sys.exit(1)
