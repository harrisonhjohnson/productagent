"""
War Room Manager for Navi - Focused launch tracking with accountability

War Rooms provide:
1. Focused blocker tracking for launches
2. Status dashboards (red/yellow/green)
3. Gap detection (missing owners, Plan Bs, etc.)
4. Daily hard questions via Claude
5. Parking lot for non-critical items
"""
import os
import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class Blocker:
    """A blocker item in a War Room."""
    id: str                             # From TODO.md (e.g., TBLC)
    item: str                           # Task text
    owner: Optional[str] = None         # Person responsible
    due: Optional[date] = None          # Due date
    status: str = 'yellow'              # red | yellow | green
    confidence: Optional[str] = None    # high | medium | low
    days_in_status: int = 0             # Auto-calculated
    plan_b: Optional[str] = None        # Fallback plan
    note: Optional[str] = None          # Latest status note
    status_changed: Optional[date] = None  # When status last changed


@dataclass
class ParkedItem:
    """An item parked (deferred) during a War Room."""
    id: str
    item: str
    original_due: Optional[date] = None
    reason: str = ""


@dataclass
class WarRoom:
    """A War Room for tracking a launch or critical milestone."""
    name: str                           # e.g., "Project A"
    slug: str                           # e.g., "project-a"
    target_date: date
    created: date
    status: str = 'active'              # active | closed
    tags: List[str] = field(default_factory=list)
    blockers: List[Blocker] = field(default_factory=list)
    parked: List[ParkedItem] = field(default_factory=list)
    gaps: List[str] = field(default_factory=list)
    rollback_plan: Optional[Dict] = None
    decisions: List[Dict] = field(default_factory=list)
    slack_channel: Optional[str] = None
    standup_time: Optional[str] = None


def slugify(name: str) -> str:
    """Convert name to slug format."""
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


class WarRoomManager:
    """
    Manages War Room files and operations.

    War Rooms are stored as markdown files in ~/work/warrooms/<slug>/WAR_ROOM.md
    """

    def __init__(self, root_dir: str = None):
        """
        Initialize War Room manager.

        Args:
            root_dir: Root directory for war room files (default: ~/work/warrooms)
        """
        if root_dir is None:
            root_dir = os.path.expanduser("~/work/warrooms")

        self.root_dir = root_dir

        # Create root directory if it doesn't exist
        if not os.path.exists(self.root_dir):
            os.makedirs(self.root_dir)
            logger.info(f"Created warrooms directory: {self.root_dir}")

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    def create(self, name: str, target_date: date, tags: List[str] = None) -> WarRoom:
        """
        Create a new War Room.

        Args:
            name: Display name (e.g., "Project A")
            target_date: Target launch/milestone date
            tags: Tags for filtering TODOs

        Returns:
            Created WarRoom instance
        """
        slug = slugify(name)

        # Check if already exists
        if self.get(slug):
            raise ValueError(f"War Room '{slug}' already exists")

        # Create war room directory
        warroom_dir = os.path.join(self.root_dir, slug)
        os.makedirs(warroom_dir, exist_ok=True)

        # Create hard-questions subdirectory
        os.makedirs(os.path.join(warroom_dir, 'hard-questions'), exist_ok=True)

        # Create war room
        warroom = WarRoom(
            name=name,
            slug=slug,
            target_date=target_date,
            created=date.today(),
            tags=tags or []
        )

        # Detect initial gaps
        warroom.gaps = self.detect_gaps(warroom)

        # Write to file
        self._write_warroom(warroom)

        logger.info(f"Created War Room: {name} (target: {target_date})")
        return warroom

    def get(self, slug: str) -> Optional[WarRoom]:
        """
        Get a War Room by slug.

        Args:
            slug: War room slug (e.g., "project-a")

        Returns:
            WarRoom or None if not found
        """
        warroom_path = os.path.join(self.root_dir, slug, 'WAR_ROOM.md')

        if not os.path.exists(warroom_path):
            return None

        return self._read_warroom(slug)

    def get_active(self) -> List[WarRoom]:
        """Get all active War Rooms."""
        active = []

        if not os.path.exists(self.root_dir):
            return active

        for item in os.listdir(self.root_dir):
            if os.path.isdir(os.path.join(self.root_dir, item)):
                warroom = self.get(item)
                if warroom and warroom.status == 'active':
                    active.append(warroom)

        # Sort by target date (soonest first)
        active.sort(key=lambda w: w.target_date)
        return active

    def close(self, slug: str) -> bool:
        """
        Close a War Room.

        Marks status as closed and flags parked items for restore.

        Args:
            slug: War room slug

        Returns:
            True if closed successfully
        """
        warroom = self.get(slug)
        if not warroom:
            return False

        warroom.status = 'closed'

        # Add decision about closing
        warroom.decisions.append({
            'date': date.today().isoformat(),
            'decision': 'War room closed',
            'context': f'{len(warroom.parked)} parked items to restore'
        })

        self._write_warroom(warroom)
        logger.info(f"Closed War Room: {slug}")
        return True

    # =========================================================================
    # Blocker Management
    # =========================================================================

    def add_blocker(
        self,
        slug: str,
        todo_id: str,
        item_text: str = None,
        status: str = 'yellow',
        owner: str = None,
        due: date = None,
        note: str = None
    ) -> bool:
        """
        Add a blocker to a War Room.

        Args:
            slug: War room slug
            todo_id: TODO ID from TODO.md
            item_text: Task text (optional, can be pulled from TODO)
            status: Initial status (red/yellow/green)
            owner: Person responsible
            due: Due date
            note: Status note

        Returns:
            True if added successfully
        """
        warroom = self.get(slug)
        if not warroom:
            return False

        # Check if already exists
        for b in warroom.blockers:
            if b.id == todo_id:
                return False  # Already exists

        blocker = Blocker(
            id=todo_id,
            item=item_text or f"TODO {todo_id}",
            owner=owner,
            due=due,
            status=status,
            note=note,
            status_changed=date.today()
        )

        warroom.blockers.append(blocker)

        # Re-detect gaps
        warroom.gaps = self.detect_gaps(warroom)

        self._write_warroom(warroom)
        logger.info(f"Added blocker {todo_id} to {slug}")
        return True

    def update_blocker(
        self,
        slug: str,
        todo_id: str,
        status: str = None,
        owner: str = None,
        due: date = None,
        confidence: str = None,
        note: str = None
    ) -> bool:
        """
        Update a blocker's status or metadata.

        Args:
            slug: War room slug
            todo_id: Blocker TODO ID
            status: New status (red/yellow/green)
            owner: New owner
            due: New due date
            confidence: New confidence level (high/medium/low)
            note: New status note

        Returns:
            True if updated successfully
        """
        warroom = self.get(slug)
        if not warroom:
            return False

        for blocker in warroom.blockers:
            if blocker.id == todo_id:
                if status and status != blocker.status:
                    blocker.status = status
                    blocker.status_changed = date.today()
                    blocker.days_in_status = 0

                if owner is not None:
                    blocker.owner = owner if owner else None

                if due is not None:
                    blocker.due = due

                if confidence is not None:
                    blocker.confidence = confidence if confidence else None

                if note is not None:
                    blocker.note = note if note else None

                # Re-detect gaps
                warroom.gaps = self.detect_gaps(warroom)

                self._write_warroom(warroom)
                logger.info(f"Updated blocker {todo_id} in {slug}")
                return True

        return False  # Blocker not found

    def set_plan_b(self, slug: str, todo_id: str, plan_b: str) -> bool:
        """
        Set Plan B for a blocker.

        Args:
            slug: War room slug
            todo_id: Blocker TODO ID
            plan_b: Fallback plan description

        Returns:
            True if set successfully
        """
        warroom = self.get(slug)
        if not warroom:
            return False

        for blocker in warroom.blockers:
            if blocker.id == todo_id:
                blocker.plan_b = plan_b

                # Re-detect gaps
                warroom.gaps = self.detect_gaps(warroom)

                self._write_warroom(warroom)
                logger.info(f"Set Plan B for {todo_id} in {slug}")
                return True

        return False

    def remove_blocker(self, slug: str, todo_id: str) -> bool:
        """
        Remove a blocker from a War Room.

        Args:
            slug: War room slug
            todo_id: Blocker TODO ID

        Returns:
            True if removed successfully
        """
        warroom = self.get(slug)
        if not warroom:
            return False

        for i, blocker in enumerate(warroom.blockers):
            if blocker.id == todo_id:
                warroom.blockers.pop(i)
                warroom.gaps = self.detect_gaps(warroom)
                self._write_warroom(warroom)
                logger.info(f"Removed blocker {todo_id} from {slug}")
                return True

        return False

    # =========================================================================
    # Parking
    # =========================================================================

    def park_item(self, slug: str, todo_id: str, item_text: str, reason: str, original_due: date = None) -> bool:
        """
        Park an item (defer until after launch).

        Args:
            slug: War room slug
            todo_id: TODO ID
            item_text: Task text
            reason: Why it's being parked
            original_due: Original due date to restore

        Returns:
            True if parked successfully
        """
        warroom = self.get(slug)
        if not warroom:
            return False

        # Check if already parked
        for p in warroom.parked:
            if p.id == todo_id:
                return False

        parked = ParkedItem(
            id=todo_id,
            item=item_text,
            original_due=original_due,
            reason=reason
        )

        warroom.parked.append(parked)
        self._write_warroom(warroom)
        logger.info(f"Parked {todo_id} in {slug}: {reason}")
        return True

    def unpark_item(self, slug: str, todo_id: str) -> bool:
        """
        Unpark an item (restore to active).

        Args:
            slug: War room slug
            todo_id: TODO ID

        Returns:
            True if unparked successfully
        """
        warroom = self.get(slug)
        if not warroom:
            return False

        for i, parked in enumerate(warroom.parked):
            if parked.id == todo_id:
                warroom.parked.pop(i)
                self._write_warroom(warroom)
                logger.info(f"Unparked {todo_id} from {slug}")
                return True

        return False

    # =========================================================================
    # Queries
    # =========================================================================

    def get_days_remaining(self, warroom: WarRoom) -> int:
        """Calculate days remaining until target date."""
        return (warroom.target_date - date.today()).days

    def get_blockers_by_status(self, slug: str, status: str) -> List[Blocker]:
        """Get blockers filtered by status."""
        warroom = self.get(slug)
        if not warroom:
            return []

        return [b for b in warroom.blockers if b.status == status]

    def detect_gaps(self, warroom: WarRoom) -> List[str]:
        """
        Auto-detect gaps in a War Room.

        Checks for:
        - No rollback plan
        - Blockers without owners
        - Blockers without Plan B
        - No go/no-go meeting scheduled
        """
        gaps = []

        # No rollback plan
        if not warroom.rollback_plan:
            gaps.append("No rollback plan documented")

        # Blockers without owners
        unowned = [b for b in warroom.blockers if not b.owner or b.owner == '???']
        if unowned:
            gaps.append(f"{len(unowned)} blocker(s) have no owner")

        # Blockers without Plan B
        no_planb = [b for b in warroom.blockers if not b.plan_b]
        if no_planb:
            gaps.append(f"{len(no_planb)} blocker(s) have no Plan B")

        # No go/no-go meeting (check decisions)
        days_remaining = self.get_days_remaining(warroom)
        has_gonogo = any('go/no-go' in d.get('decision', '').lower()
                        for d in warroom.decisions)
        if not has_gonogo and days_remaining <= 14:
            gaps.append("No go/no-go meeting scheduled")

        return gaps

    def get_status_summary(self, slug: str) -> str:
        """
        Generate status summary for a War Room.

        Returns formatted string for Telegram display.
        """
        warroom = self.get(slug)
        if not warroom:
            return f"War room '{slug}' not found."

        days_remaining = self.get_days_remaining(warroom)

        # Count blockers by status
        red_count = len([b for b in warroom.blockers if b.status == 'red'])
        yellow_count = len([b for b in warroom.blockers if b.status == 'yellow'])
        green_count = len([b for b in warroom.blockers if b.status == 'green'])

        # Status emoji
        if warroom.status == 'closed':
            status_icon = "CLOSED"
        elif red_count > 0:
            status_icon = "WAR ROOM"
        else:
            status_icon = "WAR ROOM"

        lines = [
            f"{status_icon}: {warroom.name.upper()}",
            f"   T-{days_remaining} | {warroom.target_date.strftime('%b %d, %Y')}",
            "",
            f"   Blockers: {red_count} red | {yellow_count} yellow | {green_count} green",
        ]

        # Gaps
        if warroom.gaps:
            lines.append(f"   Gaps: {len(warroom.gaps)} open")

        # Rollback status
        if warroom.rollback_plan:
            lines.append(f"   Rollback: Documented")
        else:
            lines.append(f"   Rollback: Not documented")

        lines.append("")

        # Red blockers first
        for blocker in warroom.blockers:
            if blocker.status == 'red':
                owner_str = blocker.owner or 'no owner'
                due_str = f"due {blocker.due.strftime('%b %d')}" if blocker.due else 'no due date'
                lines.append(f"   RED {blocker.id} - {blocker.item[:40]} ({owner_str}, {due_str})")

        # Yellow blockers
        for blocker in warroom.blockers:
            if blocker.status == 'yellow':
                owner_str = blocker.owner or 'no owner'
                due_str = f"due {blocker.due.strftime('%b %d')}" if blocker.due else 'no due date'
                lines.append(f"   YLW {blocker.id} - {blocker.item[:40]} ({owner_str}, {due_str})")

        # Commands hint
        lines.extend([
            "",
            f"/warroom {slug} questions | /warroom {slug} standup"
        ])

        return "\n".join(lines)

    def list_active_summary(self) -> str:
        """Generate summary of all active War Rooms."""
        active = self.get_active()

        if not active:
            return "No active War Rooms.\n\nCreate one: /warroom create \"Name\" --target YYYY-MM-DD"

        lines = [f"Active War Rooms ({len(active)})", ""]

        for warroom in active:
            days = self.get_days_remaining(warroom)
            red_count = len([b for b in warroom.blockers if b.status == 'red'])
            yellow_count = len([b for b in warroom.blockers if b.status == 'yellow'])

            status_emoji = "RED" if red_count > 0 else ("YLW" if yellow_count > 0 else "GRN")
            lines.append(f"{status_emoji} {warroom.name} (T-{days})")
            lines.append(f"    /warroom {warroom.slug}")

        return "\n".join(lines)

    def generate_standup_agenda(self, slug: str) -> str:
        """
        Generate standup agenda for a War Room.

        Shows:
        - Days remaining
        - Red blockers (must discuss)
        - Yellow blockers > 3 days (need update)
        - Gaps to address
        """
        warroom = self.get(slug)
        if not warroom:
            return f"War room '{slug}' not found."

        days_remaining = self.get_days_remaining(warroom)

        lines = [
            f"STANDUP: {warroom.name}",
            f"T-{days_remaining} days",
            "",
            "MUST DISCUSS:"
        ]

        # Red blockers
        reds = [b for b in warroom.blockers if b.status == 'red']
        if reds:
            for b in reds:
                lines.append(f"  [RED] {b.id}: {b.item[:50]}")
                if b.note:
                    lines.append(f"        Latest: {b.note}")
        else:
            lines.append("  (no red blockers)")

        lines.append("")
        lines.append("NEED UPDATE (yellow > 3 days):")

        # Yellow blockers stale for > 3 days
        for b in warroom.blockers:
            if b.status == 'yellow':
                days_stale = (date.today() - b.status_changed).days if b.status_changed else 0
                if days_stale >= 3:
                    lines.append(f"  [YLW] {b.id}: {b.item[:50]} ({days_stale}d)")

        lines.append("")
        lines.append("GAPS:")
        if warroom.gaps:
            for gap in warroom.gaps:
                lines.append(f"  - {gap}")
        else:
            lines.append("  (none)")

        return "\n".join(lines)

    # =========================================================================
    # Rollback Plan
    # =========================================================================

    def set_rollback_plan(
        self,
        slug: str,
        owner: str,
        trigger: str,
        action: str,
        time_estimate: str
    ) -> bool:
        """
        Set rollback plan for a War Room.

        Args:
            slug: War room slug
            owner: Person responsible for executing rollback
            trigger: Condition that triggers rollback
            action: What to do if triggered
            time_estimate: How long rollback takes

        Returns:
            True if set successfully
        """
        warroom = self.get(slug)
        if not warroom:
            return False

        warroom.rollback_plan = {
            'owner': owner,
            'trigger': trigger,
            'action': action,
            'time': time_estimate
        }

        # Re-detect gaps (should remove "No rollback plan" gap)
        warroom.gaps = self.detect_gaps(warroom)

        self._write_warroom(warroom)
        logger.info(f"Set rollback plan for {slug}")
        return True

    # =========================================================================
    # Decisions
    # =========================================================================

    def add_decision(self, slug: str, decision: str, context: str = None) -> bool:
        """
        Record a decision in the War Room.

        Args:
            slug: War room slug
            decision: What was decided
            context: Why/background

        Returns:
            True if added successfully
        """
        warroom = self.get(slug)
        if not warroom:
            return False

        warroom.decisions.append({
            'date': date.today().isoformat(),
            'decision': decision,
            'context': context or ''
        })

        self._write_warroom(warroom)
        logger.info(f"Added decision to {slug}: {decision}")
        return True

    # =========================================================================
    # File I/O
    # =========================================================================

    def _read_warroom(self, slug: str) -> Optional[WarRoom]:
        """Read and parse a War Room from file."""
        warroom_path = os.path.join(self.root_dir, slug, 'WAR_ROOM.md')

        if not os.path.exists(warroom_path):
            return None

        with open(warroom_path, 'r') as f:
            content = f.read()

        return self._parse_warroom_md(content, slug)

    def _write_warroom(self, warroom: WarRoom) -> None:
        """Write War Room to file."""
        warroom_dir = os.path.join(self.root_dir, warroom.slug)
        os.makedirs(warroom_dir, exist_ok=True)

        warroom_path = os.path.join(warroom_dir, 'WAR_ROOM.md')

        content = self._render_warroom_md(warroom)

        with open(warroom_path, 'w') as f:
            f.write(content)

    def _parse_warroom_md(self, content: str, slug: str) -> WarRoom:
        """Parse War Room markdown content."""
        lines = content.split('\n')

        # Extract header info
        name = slug
        target_date = date.today() + timedelta(days=30)
        created = date.today()
        status = 'active'
        tags = []
        slack_channel = None
        standup_time = None

        # Parse header
        for line in lines:
            if line.startswith('# War Room:'):
                name = line.replace('# War Room:', '').strip()
            elif line.startswith('**Target:**'):
                try:
                    target_str = line.replace('**Target:**', '').strip()
                    target_date = date.fromisoformat(target_str)
                except:
                    pass
            elif line.startswith('**Created:**'):
                try:
                    created_str = line.replace('**Created:**', '').strip()
                    created = date.fromisoformat(created_str)
                except:
                    pass
            elif line.startswith('**Status:**'):
                status = line.replace('**Status:**', '').strip()
            elif line.startswith('tags:'):
                tags_str = line.replace('tags:', '').strip()
                tags = [t.strip() for t in tags_str.split(',') if t.strip()]
            elif line.startswith('slack_channel:'):
                slack_channel = line.replace('slack_channel:', '').strip()
            elif line.startswith('standup_time:'):
                standup_time = line.replace('standup_time:', '').strip()

        # Parse blockers
        blockers = []
        in_blockers_section = False

        for line in lines:
            if line.startswith('## Blockers'):
                in_blockers_section = True
                continue
            elif line.startswith('## ') and in_blockers_section:
                in_blockers_section = False

            if in_blockers_section and line.startswith('| ') and not line.startswith('| ID') and not line.startswith('|--'):
                parts = [p.strip() for p in line.split('|')[1:-1]]
                if len(parts) >= 8:
                    try:
                        due_date = None
                        if parts[3] and parts[3] not in ['-', '']:
                            try:
                                due_date = datetime.strptime(parts[3], '%b %d').replace(year=date.today().year).date()
                                if due_date < date.today() - timedelta(days=180):
                                    due_date = due_date.replace(year=due_date.year + 1)
                            except:
                                pass

                        blocker = Blocker(
                            id=parts[0],
                            item=parts[1],
                            owner=parts[2] if parts[2] and parts[2] != '???' else None,
                            due=due_date,
                            status=parts[4] if parts[4] else 'yellow',
                            confidence=parts[5] if parts[5] and parts[5] != '-' else None,
                            days_in_status=int(parts[6]) if parts[6].isdigit() else 0,
                            plan_b=parts[7] if parts[7] and parts[7] != '-' else None
                        )
                        blockers.append(blocker)
                    except Exception as e:
                        logger.warning(f"Failed to parse blocker line: {line} - {e}")

        # Parse gaps
        gaps = []
        in_gaps_section = False

        for line in lines:
            if line.startswith('## Gaps'):
                in_gaps_section = True
                continue
            elif line.startswith('## ') and in_gaps_section:
                in_gaps_section = False

            if in_gaps_section:
                if line.startswith('- [ ]'):
                    gaps.append(line[6:].strip())

        # Parse rollback plan
        rollback_plan = None
        in_rollback_section = False
        rollback_data = {}

        for line in lines:
            if line.startswith('## Rollback Plan'):
                in_rollback_section = True
                continue
            elif line.startswith('## ') and in_rollback_section:
                in_rollback_section = False

            if in_rollback_section:
                if line.startswith('**Owner:**'):
                    rollback_data['owner'] = line.replace('**Owner:**', '').strip()
                elif line.startswith('**Trigger:**'):
                    rollback_data['trigger'] = line.replace('**Trigger:**', '').strip()
                elif line.startswith('**Action:**'):
                    rollback_data['action'] = line.replace('**Action:**', '').strip()
                elif line.startswith('**Time:**'):
                    rollback_data['time'] = line.replace('**Time:**', '').strip()

        if rollback_data:
            rollback_plan = rollback_data

        # Parse parked items
        parked = []
        in_parked_section = False

        for line in lines:
            if line.startswith('## Parked'):
                in_parked_section = True
                continue
            elif line.startswith('## ') and in_parked_section:
                in_parked_section = False

            if in_parked_section and line.startswith('| ') and not line.startswith('| ID') and not line.startswith('|--'):
                parts = [p.strip() for p in line.split('|')[1:-1]]
                if len(parts) >= 3:
                    parked.append(ParkedItem(
                        id=parts[0],
                        item=parts[1],
                        reason=parts[2] if len(parts) > 2 else ''
                    ))

        # Parse decisions
        decisions = []
        in_decisions_section = False

        for line in lines:
            if line.startswith('## Decisions'):
                in_decisions_section = True
                continue
            elif line.startswith('## ') and in_decisions_section:
                in_decisions_section = False

            if in_decisions_section and line.startswith('| ') and not line.startswith('| Date') and not line.startswith('|--'):
                parts = [p.strip() for p in line.split('|')[1:-1]]
                if len(parts) >= 2:
                    decisions.append({
                        'date': parts[0],
                        'decision': parts[1],
                        'context': parts[2] if len(parts) > 2 else ''
                    })

        return WarRoom(
            name=name,
            slug=slug,
            target_date=target_date,
            created=created,
            status=status,
            tags=tags,
            blockers=blockers,
            parked=parked,
            gaps=gaps,
            rollback_plan=rollback_plan,
            decisions=decisions,
            slack_channel=slack_channel,
            standup_time=standup_time
        )

    def _render_warroom_md(self, warroom: WarRoom) -> str:
        """Render War Room to markdown."""
        days_remaining = self.get_days_remaining(warroom)

        lines = [
            f"# War Room: {warroom.name}",
            "",
            f"**Target:** {warroom.target_date.isoformat()}",
            f"**Created:** {warroom.created.isoformat()}",
            f"**Status:** {warroom.status}",
            f"**Days Remaining:** {days_remaining}",
            "",
            "---",
            "",
            "## Config",
            "",
            f"tags: {', '.join(warroom.tags)}" if warroom.tags else "tags:",
            f"slack_channel: {warroom.slack_channel or ''}",
            f"standup_time: {warroom.standup_time or ''}",
            "",
            "---",
            "",
            "## Blockers",
            "",
            "| ID | Item | Owner | Due | Status | Confidence | Days | Plan B |",
            "|----|------|-------|-----|--------|------------|------|--------|",
        ]

        for b in warroom.blockers:
            owner = b.owner or '???'
            due_str = b.due.strftime('%b %d') if b.due else '-'
            conf = b.confidence or '-'
            plan_b = b.plan_b or '-'
            days = b.days_in_status

            lines.append(f"| {b.id} | {b.item} | {owner} | {due_str} | {b.status} | {conf} | {days} | {plan_b} |")

        lines.extend([
            "",
            "---",
            "",
            "## Gaps",
            "",
        ])

        for gap in warroom.gaps:
            lines.append(f"- [ ] {gap}")

        if not warroom.gaps:
            lines.append("- [x] All gaps addressed")

        lines.extend([
            "",
            "---",
            "",
            "## Rollback Plan",
            "",
        ])

        if warroom.rollback_plan:
            lines.extend([
                f"**Owner:** {warroom.rollback_plan.get('owner', 'TBD')}",
                f"**Trigger:** {warroom.rollback_plan.get('trigger', 'TBD')}",
                f"**Action:** {warroom.rollback_plan.get('action', 'TBD')}",
                f"**Time:** {warroom.rollback_plan.get('time', 'TBD')}",
            ])
        else:
            lines.append("*No rollback plan documented*")

        lines.extend([
            "",
            "---",
            "",
            f"## Parked (restore after {warroom.target_date.strftime('%b %d')})",
            "",
            "| ID | Item | Reason |",
            "|----|------|--------|",
        ])

        for p in warroom.parked:
            lines.append(f"| {p.id} | {p.item} | {p.reason} |")

        lines.extend([
            "",
            "---",
            "",
            "## Decisions",
            "",
            "| Date | Decision | Context |",
            "|------|----------|---------|",
        ])

        for d in warroom.decisions:
            lines.append(f"| {d.get('date', '')} | {d.get('decision', '')} | {d.get('context', '')} |")

        lines.extend([
            "",
            "---",
            "",
            "## Changelog",
            "",
            "| Date | Change |",
            "|------|--------|",
            f"| {date.today().isoformat()} | Updated war room |",
            f"| {warroom.created.isoformat()} | Created war room |",
        ])

        return "\n".join(lines)
