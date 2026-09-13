"""
TODO Manager for Navi - Natural language TODO.md management
"""
import os
import re
import random
import string
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date, timedelta
import logging

# Try to import dateutil for natural language date parsing
try:
    from dateutil import parser as dateutil_parser
    DATEUTIL_AVAILABLE = True
except ImportError:
    DATEUTIL_AVAILABLE = False
import html.parser

logger = logging.getLogger(__name__)


def generate_todo_id() -> str:
    """
    Generate a unique 4-character alphanumeric TODO ID.
    Format: T + 3 random chars (e.g., T7X2, TA9K)
    """
    chars = string.ascii_uppercase + string.digits
    return 'T' + ''.join(random.choices(chars, k=3))

# Import config for Slack notification settings
try:
    import config
except ImportError:
    config = None
    logger.warning("Config module not available")

# Try to import Slack integration (optional)
try:
    from integrations.slack_context import SlackContext
    from integrations.slack_notifier import SlackNotificationManager
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False
    logger.info("Slack integration not available")

class TodoManager:
    def __init__(self, todo_path: str = None, slack_context: 'SlackContext' = None):
        """
        Initialize TODO manager with path to TODO.md

        Args:
            todo_path: Path to TODO.md file
            slack_context: Optional SlackContext instance for fetching thread info
        """
        if todo_path is None:
            todo_path = os.path.expanduser("~/TODO.md")

        self.todo_path = todo_path

        if not os.path.exists(self.todo_path):
            raise FileNotFoundError(f"TODO.md not found at {self.todo_path}")

        # Initialize Slack context if available
        if slack_context:
            self.slack_context = slack_context
        elif SLACK_AVAILABLE:
            try:
                self.slack_context = SlackContext()
                if self.slack_context.is_configured():
                    logger.info("Slack context integration enabled")
                else:
                    self.slack_context = None
                    logger.info("Slack context not configured (missing credentials)")
            except Exception as e:
                logger.warning(f"Failed to initialize Slack context: {e}")
                self.slack_context = None
        else:
            self.slack_context = None

        # Initialize Slack notifier if available
        if SLACK_AVAILABLE:
            try:
                self.slack_notifier = SlackNotificationManager()
                if self.slack_notifier.is_enabled():
                    logger.info("Slack notifications enabled")
                else:
                    self.slack_notifier = None
                    logger.info("Slack notifications not configured")
            except Exception as e:
                logger.warning(f"Failed to initialize Slack notifier: {e}")
                self.slack_notifier = None
        else:
            self.slack_notifier = None

    def _read_file(self) -> str:
        """Read TODO.md file"""
        with open(self.todo_path, 'r') as f:
            return f.read()

    def _write_file(self, content: str):
        """Write content to TODO.md"""
        with open(self.todo_path, 'w') as f:
            f.write(content)
        logger.info(f"Updated TODO.md at {self.todo_path}")

    def _parse_metadata(self, comment_line: str) -> Dict:
        """
        Parse metadata from HTML comment line
        Format: <!-- source:slack thread:1234567890.123456 channel:C12345 created:2026-01-05T10:30:00Z -->
        Returns dict with metadata fields or empty dict if no metadata
        """
        metadata = {}

        # Match HTML comment
        comment_match = re.match(r'^\s*<!--\s*(.+?)\s*-->\s*$', comment_line)
        if not comment_match:
            return metadata

        content = comment_match.group(1)

        # Parse key:value pairs
        # Handle special case of thread timestamp which contains colon
        parts = content.split()
        for part in parts:
            if ':' in part:
                key, value = part.split(':', 1)
                metadata[key] = value

        return metadata

    def _get_existing_ids(self) -> set:
        """Get all existing TODO IDs from the file to avoid duplicates"""
        content = self._read_file()
        ids = set()
        # Find all id:XXXX patterns in metadata comments
        for match in re.finditer(r'<!--[^>]*\bid:(\w+)[^>]*-->', content):
            ids.add(match.group(1))
        return ids

    def _generate_unique_id(self) -> str:
        """Generate a unique ID that doesn't exist in the file"""
        existing = self._get_existing_ids()
        for _ in range(100):  # Try up to 100 times
            new_id = generate_todo_id()
            if new_id not in existing:
                return new_id
        # Fallback: use timestamp-based ID
        return f"T{int(datetime.now().timestamp()) % 100000}"

    def _parse_due_date(self, text: str) -> Optional[date]:
        """
        Parse natural language due date from text.
        Supports: "tomorrow", "Friday", "Jan 15", "next week", "in 3 days"
        Returns date object or None.
        """
        if not text:
            return None

        text_lower = text.lower().strip()
        today = date.today()

        # Relative dates
        if text_lower in ('today', 'tod'):
            return today
        if text_lower in ('tomorrow', 'tmrw', 'tom'):
            return today + timedelta(days=1)
        if text_lower in ('yesterday'):
            return today - timedelta(days=1)

        # "next week"
        if text_lower == 'next week':
            return today + timedelta(weeks=1)

        # "in X days"
        in_days_match = re.match(r'in\s+(\d+)\s+days?', text_lower)
        if in_days_match:
            return today + timedelta(days=int(in_days_match.group(1)))

        # Day of week (this week or next occurrence)
        days = {
            'monday': 0, 'mon': 0,
            'tuesday': 1, 'tue': 1, 'tues': 1,
            'wednesday': 2, 'wed': 2,
            'thursday': 3, 'thu': 3, 'thurs': 3,
            'friday': 4, 'fri': 4,
            'saturday': 5, 'sat': 5,
            'sunday': 6, 'sun': 6
        }
        for day_name, day_num in days.items():
            if text_lower == day_name:
                days_ahead = day_num - today.weekday()
                if days_ahead <= 0:  # Target day already passed this week
                    days_ahead += 7
                return today + timedelta(days=days_ahead)

        # Try dateutil for everything else (e.g., "Jan 15", "January 15, 2026")
        if DATEUTIL_AVAILABLE:
            try:
                parsed = dateutil_parser.parse(text, fuzzy=True, default=datetime(today.year, 1, 1))
                parsed_date = parsed.date()
                # If parsed date is in past, assume next year
                if parsed_date < today:
                    parsed_date = parsed_date.replace(year=parsed_date.year + 1)
                return parsed_date
            except:
                pass

        return None

    def get_todos(self, include_completed: bool = False, source_filter: str = None) -> List[Dict]:
        """
        Extract all TODO items from TODO.md
        Returns list of dicts with: text, completed, line_number, section, metadata, id

        Args:
            include_completed: Include completed TODOs
            source_filter: Filter by source ('slack', 'manual', or None for all)
        """
        content = self._read_file()
        lines = content.split('\n')

        todos = []
        current_section = "General"
        current_subsection = None

        for i, line in enumerate(lines, 1):
            # Track sections
            if line.startswith('## '):
                current_section = line[3:].strip()
                current_subsection = None
                continue
            elif line.startswith('### '):
                current_subsection = line[4:].strip()
                continue

            # Match TODO items: - [ ] or - [x]
            todo_match = re.match(r'^(\s*)- \[([ x])\] (.+)$', line)
            if todo_match:
                indent, status, text = todo_match.groups()
                is_completed = (status.lower() == 'x')

                if not include_completed and is_completed:
                    continue

                section_name = current_section
                if current_subsection:
                    section_name = f"{current_section} > {current_subsection}"

                # Check for metadata on next line
                metadata = {}
                if i < len(lines):  # Not last line
                    next_line = lines[i]  # i is 1-indexed, lines is 0-indexed
                    metadata = self._parse_metadata(next_line)

                # Apply source filter if specified
                if source_filter:
                    todo_source = metadata.get('source', 'manual')
                    if source_filter != todo_source:
                        continue

                # Extract ID from metadata or text
                todo_id = metadata.get('id')

                todos.append({
                    'id': todo_id,
                    'text': text.strip(),
                    'completed': is_completed,
                    'line_number': i,
                    'section': section_name,
                    'indent': len(indent),
                    'metadata': metadata
                })

        return todos

    def format_todos(self, todos: List[Dict], numbered: bool = True, show_metadata: bool = False, show_ids: bool = True) -> str:
        """
        Format todos for display

        Args:
            todos: List of TODO items
            numbered: Show numbers for each item
            show_metadata: Show source and timestamp metadata
            show_ids: Show TODO IDs for easy reference (default True)
        """
        if not todos:
            return "📋 No TODO items found!"

        output = ["📋 Your TODOs:\n"]
        if show_ids:
            output.append("💡 Use ID (e.g., 'mark T7X2 done') to complete items\n")
        current_section = None

        for idx, todo in enumerate(todos, 1):
            # Add section header if changed
            if todo['section'] != current_section:
                current_section = todo['section']
                output.append(f"\n**{current_section}**")

            # Format item
            status = "✅" if todo['completed'] else "⬜️"
            prefix = f"{idx}. " if numbered else ""
            indent = "  " * (todo['indent'] // 2)  # Preserve indentation

            # Include ID if available
            id_str = f"[{todo['id']}] " if show_ids and todo.get('id') else ""

            # Include due date if available
            due_str = ""
            if todo.get('metadata', {}).get('due'):
                due_date_str = todo['metadata']['due']
                try:
                    due_date = date.fromisoformat(due_date_str)
                    today = date.today()
                    if due_date < today:
                        days_overdue = (today - due_date).days
                        due_str = f" 🔴 OVERDUE ({due_date.strftime('%b %d')}, {days_overdue}d ago)"
                    elif due_date == today:
                        due_str = " 📅 Due Today"
                    elif due_date == today + timedelta(days=1):
                        due_str = " 📅 Due Tomorrow"
                    else:
                        due_str = f" 📅 Due {due_date.strftime('%b %d')}"
                except:
                    pass

            output.append(f"{indent}{prefix}{status} {id_str}{todo['text']}{due_str}")

            # Add metadata if requested and available
            if show_metadata and todo.get('metadata'):
                metadata = todo['metadata']
                source = metadata.get('source', 'manual')

                if source == 'slack':
                    indent_prefix = "  " * ((todo['indent'] // 2) + 1) + "  "

                    # Fetch Slack thread context if available
                    thread_context = None
                    if self.slack_context and metadata.get('channel') and metadata.get('thread'):
                        try:
                            thread_context = self.slack_context.get_thread_context(
                                metadata['channel'],
                                metadata['thread']
                            )
                        except Exception as e:
                            logger.warning(f"Failed to fetch Slack context: {e}")

                    if thread_context:
                        # Rich context with thread preview
                        output.append(f"{indent_prefix}📱 From Slack #{thread_context['channel_name']} ({thread_context['time_ago']})")
                        output.append(f"{indent_prefix}💬 {thread_context['preview']}")
                        output.append(f"{indent_prefix}🔗 {thread_context['link']}")
                    else:
                        # Fallback to basic metadata display
                        meta_parts = ["📱 From Slack"]

                        # Show channel if available
                        if metadata.get('channel'):
                            meta_parts.append(f"in #{metadata['channel']}")

                        # Show timestamp if available
                        if metadata.get('created'):
                            try:
                                created_dt = datetime.fromisoformat(metadata['created'].replace('Z', '+00:00'))
                                time_str = created_dt.strftime('%b %d, %I:%M %p')
                                meta_parts.append(f"at {time_str}")
                            except:
                                pass

                        meta_line = indent_prefix + " ".join(meta_parts)
                        output.append(meta_line)

        return "\n".join(output)

    def add_todo(self, text: str, section: str = None, metadata: Dict = None, due_date: str = None) -> Tuple[bool, Optional[str]]:
        """
        Add a new TODO item to TODO.md with optional metadata and due date

        Args:
            text: TODO item text
            section: Section to add to (default: Work section)
            metadata: Optional dict with keys: source, thread, channel, created
            due_date: Optional due date string (natural language supported)

        Returns:
            Tuple of (success: bool, todo_id: str or None)
        """
        content = self._read_file()
        lines = content.split('\n')

        # Generate unique ID for this TODO
        todo_id = self._generate_unique_id()

        # Parse due date from text if not explicitly provided
        # Pattern: "due Friday", "due Jan 15", "(Due: Jan 15)"
        if not due_date:
            due_match = re.search(r'\(?\s*due[:\s]+([^)]+)\)?', text, re.IGNORECASE)
            if due_match:
                due_date = due_match.group(1).strip()
                # Remove due date from text for cleaner display
                text = re.sub(r'\s*\(?\s*due[:\s]+[^)]+\)?\s*', ' ', text, flags=re.IGNORECASE).strip()

        # Parse the due date to ISO format
        due_iso = None
        if due_date:
            parsed_due = self._parse_due_date(due_date)
            if parsed_due:
                due_iso = parsed_due.isoformat()

        # Create new todo line
        new_todo = f"- [ ] {text}"

        # Create metadata comment - always include ID
        if metadata is None:
            metadata = {}

        parts = [f"id:{todo_id}"]
        if due_iso:
            parts.append(f"due:{due_iso}")
        if metadata.get('source'):
            parts.append(f"source:{metadata['source']}")
        if metadata.get('thread'):
            parts.append(f"thread:{metadata['thread']}")
        if metadata.get('channel'):
            parts.append(f"channel:{metadata['channel']}")
        if metadata.get('created'):
            parts.append(f"created:{metadata['created']}")

        metadata_comment = f"<!-- {' '.join(parts)} -->"

        # Find insertion point
        if section:
            # Try to find the specified section
            for i, line in enumerate(lines):
                if line.startswith('## ') and section.lower() in line.lower():
                    # Found section, insert after section header
                    # Skip any blank lines or subsection headers
                    insert_pos = i + 1
                    while insert_pos < len(lines) and (
                        not lines[insert_pos].strip() or
                        lines[insert_pos].startswith('###') or
                        lines[insert_pos].startswith('**')
                    ):
                        insert_pos += 1

                    lines.insert(insert_pos, new_todo)
                    lines.insert(insert_pos + 1, metadata_comment)
                    self._write_file('\n'.join(lines))
                    logger.info(f"Added TODO [{todo_id}] to {section}: {text}")
                    return True, todo_id

        # Default: Add to Work section
        for i, line in enumerate(lines):
            if line.startswith('## Work'):
                # Skip to after "Active Projects:" or first subsection
                insert_pos = i + 1
                while insert_pos < len(lines) and (
                    not lines[insert_pos].strip() or
                    lines[insert_pos].startswith('###') or
                    lines[insert_pos].startswith('**') or
                    'Active Projects' in lines[insert_pos]
                ):
                    insert_pos += 1
                    # If we hit a subsection header, add after it
                    if insert_pos < len(lines) and lines[insert_pos].startswith('###'):
                        insert_pos += 1
                        break

                lines.insert(insert_pos, new_todo)
                lines.insert(insert_pos + 1, metadata_comment)
                self._write_file('\n'.join(lines))
                logger.info(f"Added TODO [{todo_id}] to Work section: {text}")
                return True, todo_id

        # Fallback: Add at the end
        lines.append(new_todo)
        lines.append(metadata_comment)
        self._write_file('\n'.join(lines))
        logger.info(f"Added TODO [{todo_id}] at end: {text}")
        return True, todo_id

    def mark_complete(self, identifier: str) -> Tuple[bool, str]:
        """
        Mark TODO as complete by ID, number, or text match.
        identifier can be: "T7X2" (ID), "1", "first", "2nd", or partial text match
        Returns (success, message)
        """
        todos = self.get_todos(include_completed=False)

        if not todos:
            return False, "No incomplete TODOs found!"

        # Parse identifier
        todo_to_complete = None

        # Clean up identifier (remove # prefix if present, e.g., "#T7X2" -> "T7X2")
        identifier_clean = identifier.strip().lstrip('#')

        # PRIORITY 1: Check if it's a TODO ID (format: T + 3 alphanumeric chars)
        if re.match(r'^T[A-Z0-9]{3}$', identifier_clean.upper()):
            identifier_upper = identifier_clean.upper()
            for todo in todos:
                if todo.get('id') and todo['id'].upper() == identifier_upper:
                    todo_to_complete = todo
                    break

        # PRIORITY 2: Check if it's a number
        if not todo_to_complete:
            try:
                num = int(identifier_clean)
                if 1 <= num <= len(todos):
                    todo_to_complete = todos[num - 1]
            except ValueError:
                pass

        # PRIORITY 3: Check for ordinal words (first, second, third, etc.)
        if not todo_to_complete:
            ordinals = {
                'first': 1, '1st': 1,
                'second': 2, '2nd': 2,
                'third': 3, '3rd': 3,
                'fourth': 4, '4th': 4,
                'fifth': 5, '5th': 5,
                'last': len(todos)
            }

            identifier_lower = identifier_clean.lower()
            for word, num in ordinals.items():
                if word in identifier_lower:
                    if 1 <= num <= len(todos):
                        todo_to_complete = todos[num - 1]
                    break

        # PRIORITY 4: Check for text match
        if not todo_to_complete:
            identifier_lower = identifier_clean.lower()
            for todo in todos:
                if identifier_lower in todo['text'].lower():
                    todo_to_complete = todo
                    break

        if not todo_to_complete:
            # Provide helpful error message with available IDs
            available_ids = [t.get('id') for t in todos[:5] if t.get('id')]
            id_hint = f" Available IDs: {', '.join(available_ids)}" if available_ids else ""
            return False, f"Could not find TODO matching: {identifier}.{id_hint}"

        # Mark as complete
        content = self._read_file()
        lines = content.split('\n')

        line_idx = todo_to_complete['line_number'] - 1
        if line_idx < len(lines):
            # Replace [ ] with [x]
            lines[line_idx] = lines[line_idx].replace('- [ ]', '- [x]', 1)

            # Add completion timestamp to metadata on the next line
            if line_idx + 1 < len(lines):
                meta_line = lines[line_idx + 1]
                if meta_line.strip().startswith('<!--') and 'id:' in meta_line:
                    # Add completed timestamp before closing -->
                    completed_ts = datetime.now().isoformat()
                    meta_line = meta_line.replace(' -->', f' completed:{completed_ts} -->')
                    lines[line_idx + 1] = meta_line

            self._write_file('\n'.join(lines))

            todo_id = todo_to_complete.get('id', 'no-id')
            logger.info(f"Marked TODO [{todo_id}] complete: {todo_to_complete['text']}")

            # Send Slack notification if TODO has Slack metadata and notifications enabled
            if self.slack_notifier and todo_to_complete.get('metadata'):
                try:
                    user_name = config.SLACK_USER_NAME if config else "User"
                    success = self.slack_notifier.notify_completion(
                        metadata=todo_to_complete['metadata'],
                        todo_text=todo_to_complete['text'],
                        user_name=user_name
                    )
                    if success:
                        logger.info(f"Slack notification sent for completed TODO")
                except Exception as e:
                    logger.error(f"Failed to send Slack notification: {e}")

            # Include ID in success message if available
            id_str = f" [{todo_id}]" if todo_to_complete.get('id') else ""
            return True, f"✅ Marked complete{id_str}: {todo_to_complete['text']}"

        return False, "Failed to update TODO file"

    def mark_multiple_complete(self, identifiers: List[str]) -> Tuple[int, List[str]]:
        """
        Mark multiple TODOs as complete
        Returns (count_completed, list_of_messages)
        """
        messages = []
        count = 0

        for identifier in identifiers:
            success, message = self.mark_complete(identifier)
            if success:
                count += 1
            messages.append(message)

        return count, messages

    def parse_natural_language(self, text: str) -> Optional[Dict]:
        """
        Parse natural language commands about TODOs
        Returns dict with 'action', 'params' or None if not a TODO command
        """
        text_lower = text.lower()

        # Add TODO with due date patterns (check first)
        add_due_patterns = [
            r'add (?:to )?(?:my )?todo[s]?:?\s*(.+?)\s+due\s+(.+)',
            r'remind me to\s+(.+?)\s+(?:by|due|on)\s+(.+)',
        ]

        for pattern in add_due_patterns:
            match = re.search(pattern, text_lower)
            if match:
                task = text[match.start(1):match.end(1)].strip()
                due_text = match.group(2).strip()
                return {
                    'action': 'add',
                    'params': {'text': task, 'due_date': due_text}
                }

        # Add TODO patterns (without due date)
        add_patterns = [
            r'add (?:to )?(?:my )?todo[s]?:?\s*(.+)',
            r'add (?:to )?(?:my )?(?:todo )?list:?\s*(.+)',
            r'remind me to\s+(.+)',
            r'todo:?\s*(.+)',
        ]

        for pattern in add_patterns:
            match = re.search(pattern, text_lower)
            if match:
                task = text[match.start(1):match.end(1)].strip()
                # Clean up common artifacts
                task = re.sub(r'^["\']|["\']$', '', task)  # Remove quotes
                return {
                    'action': 'add',
                    'params': {'text': task}
                }

        # Mark complete patterns
        complete_patterns = [
            # Direct ID patterns (e.g., "T7X2 done", "#T7X2 complete", "done T7X2")
            r'#?(t[a-z0-9]{3})\s+(?:is\s+)?(?:done|complete|finished)',
            r'(?:done|complete|finished)\s+#?(t[a-z0-9]{3})',
            # Standard patterns
            r'mark\s+(?:the\s+)?(.+?)\s+(?:as\s+)?(?:complete|done)',
            r'complete\s+(?:the\s+)?(.+)',
            r'(?:i\s+)?(?:finished|completed|done)\s+(?:the\s+)?(.+)',
            r'check off\s+(?:the\s+)?(.+)',
        ]

        for pattern in complete_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                identifier = match.group(1).strip()
                # Handle "first three" or "first 3" patterns
                multi_match = re.match(r'(?:first|last)\s+(\d+|three|four|five)', identifier)
                if multi_match:
                    count_str = multi_match.group(1)
                    count_map = {'three': 3, 'four': 4, 'five': 5}
                    count = int(count_str) if count_str.isdigit() else count_map.get(count_str, 1)

                    return {
                        'action': 'complete_multiple',
                        'params': {'identifiers': [str(i) for i in range(1, count + 1)]}
                    }

                return {
                    'action': 'complete',
                    'params': {'identifier': identifier}
                }

        # Show TODOs patterns
        show_patterns = [
            r'(?:show|list|what are|what\'s)\s+(?:my\s+)?todos?',
            r'(?:show|display)\s+(?:my\s+)?(?:todo\s+)?list',
            r'what do i need to do',
            r'what\'s on my (?:todo\s+)?list',
        ]

        for pattern in show_patterns:
            if re.search(pattern, text_lower):
                return {
                    'action': 'show',
                    'params': {}
                }

        # Show filtered TODOs patterns (due date filtering)
        show_filter_patterns = [
            (r'(?:show|what\'?s|list)\s+(?:is\s+)?overdue', 'show_overdue'),
            (r'(?:show|what\'?s|list)\s+due\s+today', 'show_due_today'),
            (r'(?:show|what\'?s|list)\s+due\s+this\s+week', 'show_due_week'),
            (r'(?:show|what are|list)\s+(?:my\s+)?priorities?', 'show_priorities'),
            (r'(?:show|what\'?s|list)\s+(?:my\s+)?top\s+\d+', 'show_priorities'),
        ]

        for pattern, action in show_filter_patterns:
            if re.search(pattern, text_lower):
                return {
                    'action': action,
                    'params': {}
                }

        return None

    def update_last_updated_date(self):
        """Update the 'Last Updated' date in TODO.md"""
        content = self._read_file()
        lines = content.split('\n')

        today = datetime.now().strftime("%B %d, %Y")
        today = today.replace(' 0', ' ')  # Remove leading zero from day

        for i, line in enumerate(lines):
            if line.startswith('**Last Updated:**'):
                lines[i] = f'**Last Updated:** {today}'
                self._write_file('\n'.join(lines))
                logger.info(f"Updated last updated date to {today}")
                return

    def get_summary(self, source_filter: str = None) -> str:
        """
        Get a summary of TODO status

        Args:
            source_filter: Filter by source ('slack', 'manual', or None for all)
        """
        all_todos = self.get_todos(include_completed=True, source_filter=source_filter)
        incomplete_todos = self.get_todos(include_completed=False, source_filter=source_filter)

        total = len(all_todos)
        incomplete = len(incomplete_todos)
        complete = total - incomplete

        if total == 0:
            filter_text = f" ({source_filter})" if source_filter else ""
            return f"📋 No TODOs{filter_text} in your list!"

        percentage = int((complete / total) * 100) if total > 0 else 0

        source_text = f" ({source_filter.title()})" if source_filter else ""
        return f"""📊 TODO Summary{source_text}:

Total: {total} tasks
✅ Complete: {complete}
⬜️ Incomplete: {incomplete}
Progress: {percentage}%"""

    def get_slack_todos(self, include_completed: bool = False) -> List[Dict]:
        """Get only TODOs from Slack"""
        return self.get_todos(include_completed=include_completed, source_filter='slack')

    def get_manual_todos(self, include_completed: bool = False) -> List[Dict]:
        """Get only manually added TODOs (non-Slack)"""
        return self.get_todos(include_completed=include_completed, source_filter='manual')

    # Due date filtering methods

    def get_due_today_todos(self, include_completed: bool = False) -> List[Dict]:
        """Get TODOs due today"""
        today = date.today().isoformat()
        todos = self.get_todos(include_completed=include_completed)
        return [t for t in todos if t.get('metadata', {}).get('due') == today]

    def get_overdue_todos(self) -> List[Dict]:
        """Get overdue TODOs (past due date, not completed)"""
        today = date.today()
        todos = self.get_todos(include_completed=False)
        overdue = []
        for todo in todos:
            due_str = todo.get('metadata', {}).get('due')
            if due_str:
                try:
                    due_date = date.fromisoformat(due_str)
                    if due_date < today:
                        overdue.append(todo)
                except:
                    pass
        # Sort by due date (oldest first)
        overdue.sort(key=lambda t: t.get('metadata', {}).get('due', '9999-99-99'))
        return overdue

    def get_due_this_week_todos(self, include_completed: bool = False) -> List[Dict]:
        """Get TODOs due this week (today through Sunday)"""
        today = date.today()
        # Find end of week (Sunday)
        days_until_sunday = 6 - today.weekday()
        if days_until_sunday < 0:
            days_until_sunday = 0
        end_of_week = today + timedelta(days=days_until_sunday)

        todos = self.get_todos(include_completed=include_completed)
        due_this_week = []
        for todo in todos:
            due_str = todo.get('metadata', {}).get('due')
            if due_str:
                try:
                    due_date = date.fromisoformat(due_str)
                    if today <= due_date <= end_of_week:
                        due_this_week.append(todo)
                except:
                    pass
        # Sort by due date
        due_this_week.sort(key=lambda t: t.get('metadata', {}).get('due', '9999-99-99'))
        return due_this_week

    def get_todos_by_priority(self, limit: int = 3) -> List[Dict]:
        """Get top priority TODOs sorted by due date (soonest first)"""
        todos = self.get_todos(include_completed=False)

        # Separate todos with and without due dates
        with_due = []
        without_due = []

        for todo in todos:
            due_str = todo.get('metadata', {}).get('due')
            if due_str:
                try:
                    todo['_due_date'] = date.fromisoformat(due_str)
                    with_due.append(todo)
                except:
                    without_due.append(todo)
            else:
                without_due.append(todo)

        # Sort by due date
        with_due.sort(key=lambda t: t['_due_date'])

        # Return due items first, then others
        result = with_due[:limit]
        if len(result) < limit:
            result.extend(without_due[:limit - len(result)])

        # Clean up temporary key
        for todo in result:
            todo.pop('_due_date', None)

        return result

    def get_completed_today(self) -> List[Dict]:
        """Get TODOs completed today"""
        today = date.today().isoformat()
        todos = self.get_todos(include_completed=True)
        completed_today = []

        for todo in todos:
            if not todo['completed']:
                continue
            completed_ts = todo.get('metadata', {}).get('completed', '')
            if completed_ts.startswith(today):
                completed_today.append(todo)

        return completed_today

    def get_urgency_score(self, todo: dict) -> int:
        """
        Calculate urgency score for a TODO.

        Scoring:
        - Overdue: +100
        - Due today: +50
        - Due this week: +20
        - Has person (actionable): +10
        - Quick win keywords: +5
        """
        score = 0
        today = date.today()
        metadata = todo.get('metadata', {})
        text = todo.get('text', '').lower()

        # Due date scoring
        due_str = metadata.get('due')
        if due_str:
            try:
                due_date = date.fromisoformat(due_str)
                if due_date < today:
                    score += 100  # Overdue
                elif due_date == today:
                    score += 50  # Due today
                elif due_date <= today + timedelta(days=7):
                    score += 20  # Due this week
            except:
                pass

        # Has person (more actionable)
        if metadata.get('person'):
            score += 10

        # Quick win keywords
        quick_keywords = ['reply', 'confirm', 'check', 'follow up', 'ping']
        if any(kw in text for kw in quick_keywords):
            score += 5

        return score

    def get_todos_sorted_by_urgency(self, limit: int = 10) -> List[Dict]:
        """
        Get TODOs sorted by urgency score (highest first).

        Args:
            limit: Maximum number of TODOs to return

        Returns:
            List of TODOs sorted by urgency
        """
        todos = self.get_todos(include_completed=False)

        # Calculate urgency scores
        for todo in todos:
            todo['_urgency_score'] = self.get_urgency_score(todo)

        # Sort by urgency (descending)
        todos.sort(key=lambda t: t['_urgency_score'], reverse=True)

        # Clean up temporary key and limit
        result = todos[:limit]
        for todo in result:
            todo.pop('_urgency_score', None)

        return result

    def get_grouping_summary(self) -> dict:
        """
        Get summary of TODOs grouped by person and project.

        Returns:
            Dict with:
            - total: Total open TODOs
            - overdue_count: Number overdue
            - due_today_count: Number due today
            - by_person: {name: count}
            - by_project: {name: count}
            - quick_win_count: Number of quick wins
        """
        todos = self.get_todos(include_completed=False)
        today = date.today()

        summary = {
            'total': len(todos),
            'overdue_count': 0,
            'due_today_count': 0,
            'by_person': {},
            'by_project': {},
            'quick_win_count': 0
        }

        quick_keywords = ['reply', 'confirm', 'check', 'follow up', 'ping']

        for todo in todos:
            metadata = todo.get('metadata', {})
            text = todo.get('text', '').lower()

            # Due date counts
            due_str = metadata.get('due')
            if due_str:
                try:
                    due_date = date.fromisoformat(due_str)
                    if due_date < today:
                        summary['overdue_count'] += 1
                    elif due_date == today:
                        summary['due_today_count'] += 1
                except:
                    pass

            # Person grouping
            person = metadata.get('person')
            if person:
                summary['by_person'][person] = summary['by_person'].get(person, 0) + 1

            # Project grouping
            project = metadata.get('project')
            if project:
                summary['by_project'][project] = summary['by_project'].get(project, 0) + 1

            # Quick win detection
            if any(kw in text for kw in quick_keywords):
                summary['quick_win_count'] += 1

        return summary

    def get_quick_win_todos(self) -> List[Dict]:
        """
        Get TODOs that are quick wins (reply, confirm, follow-up).

        Returns:
            List of quick win TODOs
        """
        todos = self.get_todos(include_completed=False)
        quick_keywords = ['reply', 'confirm', 'check', 'follow up', 'follow-up', 'ping', 'nudge']

        quick_wins = []
        for todo in todos:
            text = todo.get('text', '').lower()
            if any(kw in text for kw in quick_keywords):
                quick_wins.append(todo)

        return quick_wins

    def update_today_header(self):
        """Update the TODAY section header to reflect today's date.
        Matches pattern: ## ... TODAY - <date> ...
        Preserves any parenthetical suffix like (Focus: ...)
        """
        content = self._read_file()
        lines = content.split('\n')

        today_str = datetime.now().strftime("%B %-d")

        for i, line in enumerate(lines):
            # Match TODAY header with date
            match = re.match(r'^(## .* TODAY - )([^(]+?)(\s*\(.*\))?\s*$', line)
            if match:
                prefix = match.group(1)
                suffix = match.group(3) or ''
                new_line = f"{prefix}{today_str}{suffix}"
                if lines[i] != new_line:
                    lines[i] = new_line
                    self._write_file('\n'.join(lines))
                    logger.info(f"Updated TODAY header date to {today_str}")
                return

    def archive_completed(self, keep_days: int = 7) -> int:
        """
        Archive completed TODOs older than keep_days to a monthly archive file.

        Args:
            keep_days: Number of days to keep completed items (default 7)

        Returns:
            Number of items archived
        """
        content = self._read_file()
        lines = content.split('\n')
        today = date.today()
        cutoff = today - timedelta(days=keep_days)

        # Collect lines to archive (todo line + metadata line)
        archive_items = []  # List of (section, todo_line, meta_line)
        lines_to_remove = set()  # Line indices to remove (0-indexed)
        current_section = "General"

        for i, line in enumerate(lines):
            # Track sections
            if line.startswith('## '):
                current_section = line.strip()
                continue

            # Match completed TODOs
            todo_match = re.match(r'^\s*- \[x\] (.+)$', line)
            if todo_match:
                # Check metadata on next line for completion date
                meta_line = ""
                completed_date = None
                if i + 1 < len(lines):
                    meta_line = lines[i + 1]
                    # Extract completed timestamp
                    completed_match = re.search(r'completed:(\S+)', meta_line)
                    if completed_match:
                        try:
                            completed_dt = datetime.fromisoformat(completed_match.group(1))
                            completed_date = completed_dt.date()
                        except (ValueError, TypeError):
                            pass

                # Only archive if completed before cutoff
                if completed_date and completed_date < cutoff:
                    archive_items.append((current_section, line, meta_line))
                    lines_to_remove.add(i)
                    # Also remove metadata line if it's a comment
                    if meta_line.strip().startswith('<!--'):
                        lines_to_remove.add(i + 1)

        if not archive_items:
            return 0

        # Build archive content
        archive_month = today.strftime("%b-%Y")
        archive_path = os.path.expanduser(f"~/TODO-archive-{archive_month}.md")

        # Read existing archive or create new
        archive_content = ""
        if os.path.exists(archive_path):
            with open(archive_path, 'r') as f:
                archive_content = f.read()
        else:
            archive_content = f"# TODO Archive - {today.strftime('%B %Y')}\n\n"

        # Group by section and append
        current_sec = None
        archive_lines = []
        for section, todo_line, meta_line in archive_items:
            if section != current_sec:
                current_sec = section
                archive_lines.append(f"\n{section}")
            archive_lines.append(todo_line)
            if meta_line.strip().startswith('<!--'):
                archive_lines.append(meta_line)

        archive_content += f"\n## Archived {today.strftime('%Y-%m-%d')}\n"
        archive_content += '\n'.join(archive_lines) + '\n'

        with open(archive_path, 'w') as f:
            f.write(archive_content)

        # Remove archived lines from TODO.md (reverse order to preserve indices)
        new_lines = [line for i, line in enumerate(lines) if i not in lines_to_remove]

        # Clean up double blank lines left by removal
        cleaned = []
        prev_blank = False
        for line in new_lines:
            is_blank = not line.strip()
            if is_blank and prev_blank:
                continue
            cleaned.append(line)
            prev_blank = is_blank

        self._write_file('\n'.join(cleaned))
        logger.info(f"Archived {len(archive_items)} completed items to {archive_path}")
        return len(archive_items)
