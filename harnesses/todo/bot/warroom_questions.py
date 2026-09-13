"""
War Room Hard Questions Generator - Claude-powered accountability prompts

Generates daily "tough" hard questions that force the PM to confront:
1. Items yellow >3 days - why, and what's Plan B?
2. Missing owners - who owns this?
3. Missing Plan Bs - what if this slips?
4. Scope that should be cut given time remaining
5. Ambiguous status that needs clarification
"""
import os
import subprocess
import logging
from datetime import date, datetime
from typing import Optional

from warroom_manager import WarRoom, WarRoomManager

logger = logging.getLogger(__name__)

# Claude CLI path
CLAUDE_PATH = os.getenv("CLAUDE_PATH", os.path.expanduser("~/.local/bin/claude"))

# Pinned so bot runs never inherit the interactive /model (which may be a
# capped premium tier). Override with CLAUDE_MODEL for a one-off.
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5")


def format_blockers_table(warroom: WarRoom) -> str:
    """Format blockers as a readable table for the prompt."""
    if not warroom.blockers:
        return "No blockers tracked."

    lines = ["Status | ID | Item | Owner | Due | Days in Status | Plan B"]
    lines.append("-" * 70)

    for b in warroom.blockers:
        owner = b.owner or '???'
        due_str = b.due.strftime('%b %d') if b.due else 'none'
        plan_b = b.plan_b[:30] + '...' if b.plan_b and len(b.plan_b) > 30 else (b.plan_b or 'none')

        # Calculate days in status
        days = 0
        if b.status_changed:
            days = (date.today() - b.status_changed).days

        lines.append(f"{b.status.upper()} | {b.id} | {b.item[:40]} | {owner} | {due_str} | {days}d | {plan_b}")

    return "\n".join(lines)


def format_gaps(warroom: WarRoom) -> str:
    """Format gaps as bullet list."""
    if not warroom.gaps:
        return "No gaps detected."

    return "\n".join([f"- {gap}" for gap in warroom.gaps])


def generate_hard_questions(warroom: WarRoom, todo_manager=None) -> Optional[str]:
    """
    Generate tough hard questions for a War Room.

    Uses Claude to analyze the war room state and generate
    pointed questions that force accountability.

    Args:
        warroom: WarRoom instance to analyze
        todo_manager: Optional TodoManager for additional context

    Returns:
        Formatted hard questions string, or None if generation fails
    """
    days_remaining = (warroom.target_date - date.today()).days

    # Count issues
    red_count = len([b for b in warroom.blockers if b.status == 'red'])
    yellow_stale = [b for b in warroom.blockers if b.status == 'yellow'
                    and b.status_changed and (date.today() - b.status_changed).days >= 3]
    no_owner = [b for b in warroom.blockers if not b.owner or b.owner == '???']
    no_planb = [b for b in warroom.blockers if not b.plan_b]

    blockers_table = format_blockers_table(warroom)
    gaps_list = format_gaps(warroom)

    prompt = f"""You are a senior product leader reviewing a War Room for {warroom.name}.

**Context:**
- Target date: {warroom.target_date.strftime('%B %d, %Y')}
- Days remaining: {days_remaining}
- Red blockers: {red_count}
- Yellow items stale >3 days: {len(yellow_stale)}
- Items without owner: {len(no_owner)}
- Items without Plan B: {len(no_planb)}

**Current Blockers:**
{blockers_table}

**Detected Gaps:**
{gaps_list}

**Rollback Plan:** {"Documented" if warroom.rollback_plan else "NOT DOCUMENTED"}

---

Generate 3-5 hard questions that force the PM to confront reality. Focus on:

1. **Red items** - What's blocking resolution? Is the timeline realistic?
2. **Stale yellows (>3 days)** - Why no update? Is this actually blocked?
3. **Missing owners** - Who owns this? No owner = no accountability.
4. **Missing Plan Bs** - What happens if this slips? Have you thought it through?
5. **Scope cuts** - With {days_remaining} days left, what should be cut?
6. **Ambiguity** - What's the actual status? "Yellow" isn't a plan.

**Format each question as:**

### [Number]. [Sharp observation]
**[Hard question in bold]**
→ [Specific action 1] | [Specific action 2]

**Rules:**
- Be direct. No softening language.
- Channel a VP who has seen launches fail.
- Questions should be answerable with specific actions.
- Don't ask rhetorical questions - ask questions that demand answers.
- If there are red blockers, they come first.
- If days remaining < 7, increase urgency.

Generate the questions now:"""

    try:
        result = subprocess.run(
            [CLAUDE_PATH, "-p", "--model", CLAUDE_MODEL, prompt],
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0 and result.stdout:
            return result.stdout.strip()
        else:
            logger.warning(f"Claude returned non-zero: {result.returncode}")
            logger.warning(f"stderr: {result.stderr}")
            return None

    except subprocess.TimeoutExpired:
        logger.error("Hard questions generation timed out")
        return None
    except Exception as e:
        logger.error(f"Failed to generate hard questions: {e}")
        return None


def save_questions(slug: str, questions: str, root_dir: str = None) -> str:
    """
    Save generated questions to the war room's hard-questions directory.

    Args:
        slug: War room slug
        questions: Generated questions content
        root_dir: War rooms root directory

    Returns:
        Path to saved file
    """
    if root_dir is None:
        root_dir = os.path.expanduser("~/work/warrooms")

    questions_dir = os.path.join(root_dir, slug, 'hard-questions')
    os.makedirs(questions_dir, exist_ok=True)

    filename = f"{date.today().isoformat()}.md"
    filepath = os.path.join(questions_dir, filename)

    with open(filepath, 'w') as f:
        f.write(f"# Hard Questions - {date.today().strftime('%B %d, %Y')}\n\n")
        f.write(f"Generated: {datetime.now().strftime('%I:%M %p')}\n\n")
        f.write("---\n\n")
        f.write(questions)

    logger.info(f"Saved hard questions to {filepath}")
    return filepath


def get_todays_questions(slug: str, root_dir: str = None) -> Optional[str]:
    """
    Get today's hard questions if they exist.

    Args:
        slug: War room slug
        root_dir: War rooms root directory

    Returns:
        Questions content or None
    """
    if root_dir is None:
        root_dir = os.path.expanduser("~/work/warrooms")

    filename = f"{date.today().isoformat()}.md"
    filepath = os.path.join(root_dir, slug, 'hard-questions', filename)

    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return f.read()

    return None


def generate_and_save_questions(warroom_manager: WarRoomManager, slug: str) -> Optional[str]:
    """
    Generate hard questions for a war room and save them.

    Args:
        warroom_manager: WarRoomManager instance
        slug: War room slug

    Returns:
        Generated questions or None
    """
    warroom = warroom_manager.get(slug)
    if not warroom:
        return None

    questions = generate_hard_questions(warroom)
    if questions:
        save_questions(slug, questions, warroom_manager.root_dir)

    return questions
