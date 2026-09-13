"""
State tracking for scheduled jobs - tracks when jobs last ran
"""
import json
import os
from datetime import datetime, date
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class SchedulerState:
    def __init__(self, state_file: str = None):
        """Initialize scheduler state tracker"""
        if state_file is None:
            state_file = os.path.join(os.path.dirname(__file__), 'scheduler_state.json')

        self.state_file = state_file
        self.state = self._load_state()

    def _load_state(self) -> dict:
        """Load state from file"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading scheduler state: {e}")
                return {}
        return {}

    def _save_state(self):
        """Save state to file"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving scheduler state: {e}")

    def mark_job_run(self, job_name: str, run_date: date = None):
        """Mark that a job has run on a specific date"""
        if run_date is None:
            run_date = date.today()

        date_str = run_date.isoformat()
        self.state[job_name] = date_str
        self._save_state()
        logger.debug(f"Marked job '{job_name}' as run on {date_str}")

    def get_last_run_date(self, job_name: str) -> Optional[date]:
        """Get the last date a job was run"""
        date_str = self.state.get(job_name)
        if date_str:
            try:
                return date.fromisoformat(date_str)
            except Exception as e:
                logger.error(f"Error parsing date for job '{job_name}': {e}")
                return None
        return None

    def was_run_today(self, job_name: str) -> bool:
        """Check if a job was run today"""
        last_run = self.get_last_run_date(job_name)
        if last_run is None:
            return False
        return last_run == date.today()

    def should_catch_up(self, job_name: str, scheduled_hour: int, scheduled_minute: int) -> bool:
        """
        Check if we should catch up and run a missed job
        Returns True if:
        - Job hasn't run today
        - Current time is past the scheduled time
        - Current time is within grace period (handled by caller)
        """
        if self.was_run_today(job_name):
            return False

        now = datetime.now()
        today_scheduled = datetime(
            now.year, now.month, now.day,
            scheduled_hour, scheduled_minute
        )

        # If current time is past the scheduled time, we should catch up
        return now > today_scheduled
