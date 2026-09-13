"""
Navi MCP Server - Exposes TODO tools via MCP protocol.

Runs as a standalone SSE server accessible via Cloudflare Tunnel.
Wraps existing TodoManager for all TODO operations.
"""
import os
import sys
import logging
from datetime import date, timedelta
from typing import Optional

# Add navi directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP
import config

# Apply Pi config if available
try:
    import config_pi
    for attr in dir(config_pi):
        if attr.isupper():
            setattr(config, attr, getattr(config_pi, attr))
except ImportError:
    pass

from todo_manager import TodoManager

# Try to patch with git sync
try:
    import git_sync
    _original_init = TodoManager.__init__
    def _patched_init(self, *args, **kwargs):
        _original_init(self, *args, **kwargs)
        git_sync.patch_todo_manager(self)
    TodoManager.__init__ = _patched_init
except ImportError:
    pass

logger = logging.getLogger(__name__)

# Initialize TodoManager
todo_path = getattr(config, 'TODO_PATH', None)
if todo_path:
    todo_manager = TodoManager(todo_path)
else:
    todo_manager = TodoManager()

# Disable Slack features (not available on Pi)
todo_manager.slack_notifier = None
todo_manager.slack_context = None

# Create MCP server
mcp = FastMCP(
    "Navi TODO",
    instructions=f"""Navi is {config.USER_NAME}'s personal TODO manager.
    Use these tools to view, add, and manage TODOs.
    TODOs follow a specific format with IDs (e.g., T7X2) and metadata.
    Always use IDs when referring to specific TODOs."""
)


@mcp.tool()
def get_todos(
    section: Optional[str] = None,
    include_completed: bool = False
) -> str:
    """
    Get all TODO items from the user's TODO list.

    Args:
        section: Filter by section name (e.g., "Work", "Today"). None for all.
        include_completed: Include completed TODOs (default: False).

    Returns:
        Formatted list of TODOs with IDs, text, section, and due dates.
    """
    todos = todo_manager.get_todos(include_completed=include_completed)

    if section:
        section_lower = section.lower()
        todos = [t for t in todos if section_lower in t['section'].lower()]

    if not todos:
        return "No TODOs found" + (f" in section '{section}'" if section else "") + "."

    # Format as structured text
    lines = []
    current_section = None
    for todo in todos:
        if todo['section'] != current_section:
            current_section = todo['section']
            lines.append(f"\n## {current_section}")

        status = "[x]" if todo['completed'] else "[ ]"
        id_str = f"[{todo['id']}]" if todo.get('id') else ""
        due_str = ""
        metadata = todo.get('metadata', {})
        if metadata.get('due'):
            try:
                due_date = date.fromisoformat(metadata['due'])
                today = date.today()
                if due_date < today:
                    days = (today - due_date).days
                    due_str = f" (OVERDUE {days}d)"
                elif due_date == today:
                    due_str = " (due today)"
                elif due_date == today + timedelta(days=1):
                    due_str = " (due tomorrow)"
                else:
                    due_str = f" (due {due_date.strftime('%b %d')})"
            except ValueError:
                pass

        lines.append(f"- {status} {id_str} {todo['text']}{due_str}")

    return "\n".join(lines)


@mcp.tool()
def get_todo_detail(todo_id: str) -> str:
    """
    Get full details for a specific TODO by its ID.

    Args:
        todo_id: The TODO ID (e.g., "T7X2", "TA9K").

    Returns:
        Full TODO details including metadata, due date, section, and status.
    """
    todos = todo_manager.get_todos(include_completed=True)
    todo_id_upper = todo_id.upper()

    for todo in todos:
        if todo.get('id', '').upper() == todo_id_upper:
            lines = [
                f"**{todo['text']}**",
                f"ID: {todo.get('id', 'none')}",
                f"Status: {'Completed' if todo['completed'] else 'Open'}",
                f"Section: {todo['section']}",
            ]
            metadata = todo.get('metadata', {})
            if metadata.get('due'):
                lines.append(f"Due: {metadata['due']}")
            if metadata.get('source'):
                lines.append(f"Source: {metadata['source']}")
            if metadata.get('channel'):
                lines.append(f"Slack channel: {metadata['channel']}")
            if metadata.get('thread'):
                lines.append(f"Thread: {metadata['thread']}")
            if metadata.get('completed'):
                lines.append(f"Completed at: {metadata['completed']}")
            return "\n".join(lines)

    return f"No TODO found with ID '{todo_id}'."


@mcp.tool()
def mark_complete(todo_id: str) -> str:
    """
    Mark a TODO as complete by its ID.

    Args:
        todo_id: The TODO ID to mark complete (e.g., "T7X2").

    Returns:
        Confirmation message with the completed TODO text.
    """
    success, message = todo_manager.mark_complete(todo_id)
    return message


@mcp.tool()
def mark_incomplete(todo_id: str) -> str:
    """
    Mark a completed TODO as incomplete (reopen it) by its ID.

    Args:
        todo_id: The TODO ID to reopen (e.g., "T7X2").

    Returns:
        Confirmation message.
    """
    import re

    todos = todo_manager.get_todos(include_completed=True)
    todo_id_upper = todo_id.upper()

    for todo in todos:
        if todo.get('id', '').upper() == todo_id_upper:
            if not todo['completed']:
                return f"TODO [{todo_id}] is already open."

            content = todo_manager._read_file()
            lines = content.split('\n')
            line_idx = todo['line_number'] - 1

            if line_idx < len(lines):
                lines[line_idx] = lines[line_idx].replace('- [x]', '- [ ]', 1)
                # Remove completed timestamp from metadata
                if line_idx + 1 < len(lines):
                    meta_line = lines[line_idx + 1]
                    if 'completed:' in meta_line:
                        meta_line = re.sub(r'\s*completed:\S+', '', meta_line)
                        lines[line_idx + 1] = meta_line

                todo_manager._write_file('\n'.join(lines))
                return f"Reopened [{todo_id}]: {todo['text']}"

    return f"No TODO found with ID '{todo_id}'."


@mcp.tool()
def add_todo(
    text: str,
    section: Optional[str] = None,
    due_date: Optional[str] = None
) -> str:
    """
    Add a new TODO item.

    Args:
        text: The TODO text (what needs to be done).
        section: Section to add to (e.g., "Work", "Today"). Default: Work section.
        due_date: Optional due date (supports natural language: "tomorrow", "Friday", "Jan 15").

    Returns:
        Confirmation with the new TODO ID.
    """
    success, todo_id = todo_manager.add_todo(
        text=text,
        section=section,
        due_date=due_date
    )

    if success:
        due_str = f" (due: {due_date})" if due_date else ""
        section_str = f" in {section}" if section else ""
        return f"Added [{todo_id}]{section_str}: {text}{due_str}"
    else:
        return "Failed to add TODO."


@mcp.tool()
def search_todos(query: str) -> str:
    """
    Search TODOs by keyword.

    Args:
        query: Search text to match against TODO content.

    Returns:
        Matching TODOs with IDs and sections.
    """
    query_lower = query.lower()
    todos = todo_manager.get_todos(include_completed=False)
    matches = [t for t in todos if query_lower in t['text'].lower()]

    if not matches:
        return f"No TODOs matching '{query}'."

    lines = [f"Found {len(matches)} matching TODOs:"]
    for todo in matches:
        id_str = f"[{todo['id']}]" if todo.get('id') else ""
        lines.append(f"- {id_str} {todo['text']} ({todo['section']})")

    return "\n".join(lines)


@mcp.tool()
def morning_brief() -> str:
    """
    Get a morning briefing: overdue items, due today, and quick wins.
    Use this when the user asks for a summary or "what should I focus on today".

    Returns:
        Structured morning brief with priorities.
    """
    overdue = todo_manager.get_overdue_todos()
    due_today = todo_manager.get_due_today_todos()
    quick_wins = todo_manager.get_quick_win_todos()
    summary = todo_manager.get_grouping_summary()

    lines = ["# Morning Brief", ""]

    # Overdue
    if overdue:
        lines.append(f"## OVERDUE ({len(overdue)} items)")
        for t in overdue:
            due = t.get('metadata', {}).get('due', '?')
            lines.append(f"- [{t.get('id', '?')}] {t['text']} (due {due})")
        lines.append("")

    # Due today
    if due_today:
        lines.append(f"## Due Today ({len(due_today)} items)")
        for t in due_today:
            lines.append(f"- [{t.get('id', '?')}] {t['text']}")
        lines.append("")

    # Quick wins
    if quick_wins:
        lines.append(f"## Quick Wins ({len(quick_wins)} items)")
        for t in quick_wins[:5]:
            lines.append(f"- [{t.get('id', '?')}] {t['text']}")
        lines.append("")

    # Stats
    lines.append(f"## Stats")
    lines.append(f"- Total open: {summary['total']}")
    lines.append(f"- Overdue: {summary['overdue_count']}")
    lines.append(f"- Due today: {summary['due_today_count']}")
    lines.append(f"- Quick wins: {summary['quick_win_count']}")

    if not overdue and not due_today:
        lines.insert(2, "Nothing overdue or due today. Check your full TODO list for what to tackle.")

    return "\n".join(lines)


if __name__ == "__main__":
    # stdio is the safe default: only the local Claude Code process can reach it.
    # SSE exposes the list over HTTP, so it is opt-in and must sit behind something
    # that authenticates (a tunnel with access control), never on a bare URL.
    if os.environ.get("NAVI_MCP_TRANSPORT", "stdio") == "sse":
        mcp.run(transport="sse")
    else:
        mcp.run()
