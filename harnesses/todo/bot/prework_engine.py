"""
Pre-work Engine for NAVI - Automatic context gathering and one-shot suggestions

This module provides:
1. TODO classification (reply, confirm, research, action, blocker)
2. Context gathering from related TODOs
3. Quick-win detection and message suggestion generation
"""
import os
import json
import subprocess
import logging
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
try:
    from config import USER_NAME
except ImportError:  # pragma: no cover
    USER_NAME = "you"

logger = logging.getLogger(__name__)

# Claude CLI path
CLAUDE_PATH = os.getenv("CLAUDE_PATH", os.path.expanduser("~/.local/bin/claude"))

# Pinned so bot runs never inherit the interactive /model (which may be a
# capped premium tier). Override with CLAUDE_MODEL for a one-off.
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5")


@dataclass
class OneShotSuggestion:
    """A suggested quick action for a TODO."""
    action_type: str  # 'message', 'file_edit', 'bash', 'search'
    description: str  # Human-readable description
    command: str  # The actual content/command to execute
    confidence: str  # 'high', 'medium', 'low'
    target: str = ""  # Target person/file


@dataclass
class PreworkResult:
    """Result of pre-work analysis for a TODO."""
    todo_id: str
    classification: str  # 'reply', 'confirm', 'follow_up', 'research', 'action', 'blocker'
    context: Dict = field(default_factory=dict)
    is_quick_win: bool = False
    suggestion: Optional[OneShotSuggestion] = None
    prework_time: str = ""


class PreworkEngine:
    """
    Pre-work pipeline for TODOs.

    Automatically runs when:
    1. New TODO arrives via Slack sync
    2. New TODO added via Telegram
    3. During morning briefing
    """

    def __init__(self, todo_manager):
        """
        Initialize pre-work engine.

        Args:
            todo_manager: TodoManager instance
        """
        self.todo_manager = todo_manager

        logger.info("PreworkEngine initialized")

    def run_prework(self, todo: dict) -> PreworkResult:
        """
        Full pre-work pipeline for a TODO.

        1. Classify TODO type
        2. Gather relevant context
        3. Check quick-win potential
        4. Generate one-shot suggestion if applicable

        Args:
            todo: TODO dict from TodoManager

        Returns:
            PreworkResult with classification, context, and optional suggestion
        """
        todo_id = todo.get('id', 'UNKNOWN')
        logger.info(f"Running prework for TODO {todo_id}")

        # 1. Classify TODO
        classification = self.classify_todo(todo)

        # 2. Gather context
        context = self.gather_context(todo)

        # 3. Check quick-win potential
        is_quick_win = self._is_quick_win(todo, classification, context)

        # 4. Generate one-shot if applicable
        suggestion = None
        if is_quick_win:
            suggestion = self.suggest_one_shot(todo, context, classification)

        result = PreworkResult(
            todo_id=todo_id,
            classification=classification,
            context=context,
            is_quick_win=is_quick_win,
            suggestion=suggestion,
            prework_time=datetime.now().isoformat()
        )

        logger.info(f"Prework complete for {todo_id}: {classification}, quick_win={is_quick_win}")
        return result

    def classify_todo(self, todo: dict) -> str:
        """
        Classify TODO type based on text patterns.

        Categories:
        - reply: Respond to someone
        - confirm: Check/verify something
        - follow_up: Nudge/ping someone
        - research: Investigate/find information
        - blocker: Waiting on something
        - action: General action item
        """
        text = todo.get('text', '').lower()

        # Reply patterns
        if any(kw in text for kw in ['reply to', 'respond to', 'answer', 'get back to']):
            return 'reply'

        # Confirm/check patterns
        if any(kw in text for kw in ['confirm', 'check', 'verify', 'status', 'ensure']):
            return 'confirm'

        # Follow-up patterns
        if any(kw in text for kw in ['follow up', 'follow-up', 'ping', 'nudge', 'remind']):
            return 'follow_up'

        # Research patterns
        if any(kw in text for kw in ['research', 'investigate', 'look into', 'find out', 'explore']):
            return 'research'

        # Blocker patterns
        if any(kw in text for kw in ['blocked', 'blocker', 'waiting on', 'depends on', 'need from']):
            return 'blocker'

        # Default to general action
        return 'action'

    def gather_context(self, todo: dict) -> dict:
        """
        Gather relevant context from related TODOs.
        """
        context = {}
        metadata = todo.get('metadata', {})
        person = metadata.get('person')
        project = metadata.get('project')

        # Related TODOs (same person or project)
        try:
            all_todos = self.todo_manager.get_todos(include_completed=False)
            related = []

            for t in all_todos:
                if t.get('id') == todo.get('id'):
                    continue

                t_meta = t.get('metadata', {})
                if (person and t_meta.get('person') == person) or \
                   (project and t_meta.get('project') == project):
                    related.append({
                        'id': t.get('id'),
                        'text': t.get('text', '')[:80]
                    })

            context['related_todos'] = related[:5]  # Limit to 5
        except Exception as e:
            logger.warning(f"Failed to get related TODOs: {e}")

        return context

    def _is_quick_win(self, todo: dict, classification: str, context: dict) -> bool:
        """
        Determine if TODO is a quick win.

        Quick wins are:
        - Explicit quick_win:true in metadata
        - Classification: reply, confirm, follow_up
        """
        metadata = todo.get('metadata', {})

        # Explicit flag
        if metadata.get('quick_win') == 'true':
            return True

        # Classification-based
        if classification in ['reply', 'confirm', 'follow_up']:
            return True

        return False

    def suggest_one_shot(
        self,
        todo: dict,
        context: dict,
        classification: str
    ) -> Optional[OneShotSuggestion]:
        """
        Generate one-shot message suggestion using Claude.

        For quick wins, generates a ready-to-copy message.
        """
        metadata = todo.get('metadata', {})
        text = todo.get('text', '')
        person_key = metadata.get('person', '')

        # Build prompt for Claude to generate suggestion
        prompt = f"""Generate a brief, ready-to-send message for this TODO.

TODO: {text}
Type: {classification}

Requirements:
- Be direct and concise (2-3 sentences max)
- Use {USER_NAME}'s voice (casual, efficient, friendly)
- If it's a follow-up, politely check status
- If it's a confirmation request, ask the specific question
- If it's a reply, answer what was asked based on context

Output ONLY the message text, no preamble or explanation."""

        try:
            result = subprocess.run(
                [CLAUDE_PATH, "-p", "--model", CLAUDE_MODEL, prompt],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0 and result.stdout:
                suggested_text = result.stdout.strip()
                confidence = 'high' if classification in ['reply', 'confirm'] else 'medium'

                return OneShotSuggestion(
                    action_type='message',
                    description=f"Message for {person_key or 'recipient'}",
                    command=suggested_text,
                    confidence=confidence,
                    target=person_key or ''
                )

        except subprocess.TimeoutExpired:
            logger.warning("One-shot suggestion timed out")
        except Exception as e:
            logger.warning(f"Failed to generate one-shot suggestion: {e}")

        return None

    def format_prework_result(self, result: PreworkResult, compact: bool = False) -> str:
        """
        Format prework result for Telegram display.

        Args:
            result: PreworkResult to format
            compact: If True, use compact inline format for /qw

        Returns:
            Formatted string for Telegram
        """
        if compact and result.is_quick_win and result.suggestion:
            # Compact format for /qw command
            return f'-> "{result.suggestion.command[:100]}{"..." if len(result.suggestion.command) > 100 else ""}"'

        lines = [
            f"**Prework for {result.todo_id}**",
            f"Type: {result.classification}",
        ]

        if result.is_quick_win and result.suggestion:
            lines.extend([
                "",
                "**Quick Win Detected**",
                f"Action: {result.suggestion.description}",
                f"Confidence: {result.suggestion.confidence}",
                "",
                "**Suggested Message:**",
                f'"{result.suggestion.command}"',
                "",
                "---",
                "copy | skip"
            ])
        else:
            lines.extend([
                "",
                "No quick-win action suggested.",
                f"Use '/agent {result.todo_id}' for a detailed plan."
            ])

        return "\n".join(lines)

    def run_batch_prework(self, todos: List[dict], limit: int = 5) -> List[PreworkResult]:
        """
        Run prework on multiple TODOs efficiently.

        Used by /qw command to prepare quick win suggestions.

        Args:
            todos: List of TODO dicts
            limit: Maximum number to process

        Returns:
            List of PreworkResults (only quick wins)
        """
        results = []

        for todo in todos[:limit]:
            try:
                result = self.run_prework(todo)
                if result.is_quick_win and result.suggestion:
                    results.append(result)
            except Exception as e:
                logger.warning(f"Batch prework failed for {todo.get('id', '?')}: {e}")

        return results


def run_prework_for_new_todo(
    todo: dict,
    todo_manager
) -> Optional[PreworkResult]:
    """
    Convenience function to run prework for a newly added TODO.

    Args:
        todo: The new TODO dict
        todo_manager: TodoManager instance

    Returns:
        PreworkResult or None if prework fails
    """
    try:
        engine = PreworkEngine(todo_manager=todo_manager)
        return engine.run_prework(todo)
    except Exception as e:
        logger.error(f"Prework failed for TODO {todo.get('id', '?')}: {e}")
        return None


# --- Persistence ---

PREWORK_RESULTS_PATH = os.path.expanduser("~/tools/navi/prework_results.json")


def save_results(results: List[PreworkResult], path: str = None):
    """
    Save prework results to JSON file for persistence across restarts.

    Args:
        results: List of PreworkResult objects
        path: File path (default: ~/tools/navi/prework_results.json)
    """
    path = path or PREWORK_RESULTS_PATH
    try:
        serializable = []
        for r in results:
            d = {
                'todo_id': r.todo_id,
                'classification': r.classification,
                'context': r.context,
                'is_quick_win': r.is_quick_win,
                'prework_time': r.prework_time,
            }
            if r.suggestion:
                d['suggestion'] = asdict(r.suggestion)
            else:
                d['suggestion'] = None
            serializable.append(d)

        data = {
            'timestamp': datetime.now().isoformat(),
            'count': len(serializable),
            'results': serializable,
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        logger.info(f"Saved {len(results)} prework results to {path}")
    except Exception as e:
        logger.error(f"Failed to save prework results: {e}")


def load_results(path: str = None, max_age_hours: int = 24) -> List[Dict]:
    """
    Load prework results from JSON file.

    Args:
        path: File path (default: ~/tools/navi/prework_results.json)
        max_age_hours: Ignore results older than this many hours

    Returns:
        List of result dicts (not full PreworkResult objects)
    """
    path = path or PREWORK_RESULTS_PATH
    try:
        if not os.path.exists(path):
            return []

        with open(path, 'r') as f:
            data = json.load(f)

        # Check staleness
        ts = data.get('timestamp', '')
        if ts:
            saved_time = datetime.fromisoformat(ts)
            age_hours = (datetime.now() - saved_time).total_seconds() / 3600
            if age_hours > max_age_hours:
                logger.info(f"Prework results are {age_hours:.1f}h old, ignoring")
                return []

        return data.get('results', [])
    except Exception as e:
        logger.error(f"Failed to load prework results: {e}")
        return []
