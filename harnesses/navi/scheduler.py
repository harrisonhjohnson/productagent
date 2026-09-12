"""
Job Scheduler for Navi - Scheduled tasks and reminders
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
# from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore  # Not using persistent storage
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional
import os

logger = logging.getLogger(__name__)

class JobScheduler:
    def __init__(self, db_path: str = None, timezone: str = 'America/Los_Angeles'):
        """Initialize job scheduler (memory-based, non-persistent)"""
        # Create scheduler without persistent job store
        # Jobs are in-memory and won't persist across restarts
        # This is simpler and avoids serialization issues
        self.scheduler = BackgroundScheduler(timezone=timezone)

        # Track registered job functions
        self.job_functions = {}

        logger.info("Scheduler initialized (memory-based)")

    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")

    def shutdown(self):
        """Shutdown the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler shut down")

    def register_job_function(self, name: str, func: Callable):
        """Register a function that can be used in scheduled jobs"""
        self.job_functions[name] = func
        logger.debug(f"Registered job function: {name}")

    def add_daily_job(
        self,
        job_id: str,
        func_name: str,
        hour: int,
        minute: int = 0,
        **kwargs
    ) -> bool:
        """
        Add a daily job at specific time
        Example: add_daily_job('morning_summary', 'send_todo_summary', 8, 0)
        """
        if func_name not in self.job_functions:
            logger.error(f"Job function '{func_name}' not registered")
            return False

        try:
            trigger = CronTrigger(hour=hour, minute=minute)
            self.scheduler.add_job(
                self.job_functions[func_name],
                trigger=trigger,
                id=job_id,
                kwargs=kwargs,
                replace_existing=True,
                misfire_grace_time=7200  # 2 hour grace period
            )
            logger.info(f"Added daily job '{job_id}' at {hour:02d}:{minute:02d}")
            return True
        except Exception as e:
            logger.error(f"Error adding daily job: {e}")
            return False

    def add_weekly_job(
        self,
        job_id: str,
        func_name: str,
        day_of_week: str,
        hour: int,
        minute: int = 0,
        **kwargs
    ) -> bool:
        """
        Add a weekly job on specific day/time
        day_of_week: 'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'
        Example: add_weekly_job('friday_review', 'send_weekly_summary', 'fri', 17, 0)
        """
        if func_name not in self.job_functions:
            logger.error(f"Job function '{func_name}' not registered")
            return False

        try:
            trigger = CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute)
            self.scheduler.add_job(
                self.job_functions[func_name],
                trigger=trigger,
                id=job_id,
                kwargs=kwargs,
                replace_existing=True,
                misfire_grace_time=7200  # 2 hour grace period
            )
            logger.info(f"Added weekly job '{job_id}' on {day_of_week} at {hour:02d}:{minute:02d}")
            return True
        except Exception as e:
            logger.error(f"Error adding weekly job: {e}")
            return False

    def add_interval_job(
        self,
        job_id: str,
        func_name: str,
        minutes: int = None,
        hours: int = None,
        **kwargs
    ) -> bool:
        """
        Add a job that runs at regular intervals
        Example: add_interval_job('cleanup', 'cleanup_sessions', hours=1)
        """
        if func_name not in self.job_functions:
            logger.error(f"Job function '{func_name}' not registered")
            return False

        try:
            trigger = IntervalTrigger(minutes=minutes, hours=hours)
            self.scheduler.add_job(
                self.job_functions[func_name],
                trigger=trigger,
                id=job_id,
                kwargs=kwargs,
                replace_existing=True
            )
            interval_desc = f"{hours}h" if hours else f"{minutes}m"
            logger.info(f"Added interval job '{job_id}' every {interval_desc}")
            return True
        except Exception as e:
            logger.error(f"Error adding interval job: {e}")
            return False

    def add_onetime_job(
        self,
        job_id: str,
        func_name: str,
        run_date: datetime,
        **kwargs
    ) -> bool:
        """
        Add a one-time job at specific datetime
        Example: add_onetime_job('reminder', 'send_reminder', datetime(2026, 1, 10, 14, 0))
        """
        if func_name not in self.job_functions:
            logger.error(f"Job function '{func_name}' not registered")
            return False

        try:
            trigger = DateTrigger(run_date=run_date)
            self.scheduler.add_job(
                self.job_functions[func_name],
                trigger=trigger,
                id=job_id,
                kwargs=kwargs,
                replace_existing=True
            )
            logger.info(f"Added one-time job '{job_id}' at {run_date}")
            return True
        except Exception as e:
            logger.error(f"Error adding one-time job: {e}")
            return False

    def add_onetime_job_direct(self, job_id: str, func: Callable, run_date: datetime) -> bool:
        """Add a one-time job using a callable directly (no registration required)."""
        try:
            trigger = DateTrigger(run_date=run_date)
            self.scheduler.add_job(
                func,
                trigger=trigger,
                id=job_id,
                replace_existing=True,
            )
            logger.info(f"Added direct one-time job '{job_id}' at {run_date.strftime('%H:%M')}")
            return True
        except Exception as e:
            logger.error(f"Error adding direct one-time job: {e}")
            return False

    def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled job"""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed job '{job_id}'")
            return True
        except Exception as e:
            logger.warning(f"Could not remove job '{job_id}': {e}")
            return False

    def pause_job(self, job_id: str) -> bool:
        """Pause a scheduled job"""
        try:
            self.scheduler.pause_job(job_id)
            logger.info(f"Paused job '{job_id}'")
            return True
        except Exception as e:
            logger.warning(f"Could not pause job '{job_id}': {e}")
            return False

    def resume_job(self, job_id: str) -> bool:
        """Resume a paused job"""
        try:
            self.scheduler.resume_job(job_id)
            logger.info(f"Resumed job '{job_id}'")
            return True
        except Exception as e:
            logger.warning(f"Could not resume job '{job_id}': {e}")
            return False

    def get_jobs(self) -> List[Dict]:
        """Get all scheduled jobs with their details"""
        jobs = []
        for job in self.scheduler.get_jobs():
            # Parse trigger info
            trigger_info = str(job.trigger)
            next_run = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else 'N/A'

            jobs.append({
                'id': job.id,
                'name': job.name,
                'trigger': trigger_info,
                'next_run': next_run,
                'pending': job.pending if hasattr(job, 'pending') else None
            })

        return jobs

    def format_jobs_list(self, jobs: List[Dict]) -> str:
        """Format jobs list for display"""
        if not jobs:
            return "📅 No scheduled jobs"

        output = ["📅 Scheduled Jobs:\n"]

        for job in jobs:
            output.append(f"**{job['id']}**")
            output.append(f"  Trigger: {job['trigger']}")
            output.append(f"  Next run: {job['next_run']}")
            output.append("")

        return "\n".join(output)


class BuiltInJobs:
    """Built-in job functions for common tasks"""

    @staticmethod
    def create_todo_summary_job(send_message_func: Callable, todo_manager, chat_id: int, state_tracker=None, top_n: int = 3):
        """Create function for enhanced daily TODO summary with priorities and due dates"""
        def send_todo_summary():
            try:
                if not todo_manager:
                    logger.warning("TODO manager not available for scheduled summary")
                    return

                message_parts = ["☀️ Good morning! Here's your daily briefing:\n"]

                # Get overdue items
                try:
                    overdue = todo_manager.get_overdue_todos()
                    if overdue:
                        message_parts.append(f"\n🔴 **OVERDUE ({len(overdue)} items):**")
                        for todo in overdue[:5]:  # Show max 5
                            due_str = todo.get('metadata', {}).get('due', 'unknown')
                            id_str = f"[{todo.get('id', '?')}] " if todo.get('id') else ""
                            message_parts.append(f"  • {id_str}{todo['text']} (was due {due_str})")
                        if len(overdue) > 5:
                            message_parts.append(f"  ... and {len(overdue) - 5} more")
                except:
                    pass

                # Get due today
                try:
                    due_today = todo_manager.get_due_today_todos()
                    if due_today:
                        message_parts.append(f"\n📅 **DUE TODAY ({len(due_today)} items):**")
                        for todo in due_today:
                            id_str = f"[{todo.get('id', '?')}] " if todo.get('id') else ""
                            message_parts.append(f"  • {id_str}{todo['text']}")
                    else:
                        message_parts.append("\n📅 Nothing due today!")
                except:
                    message_parts.append("\n📅 Nothing due today!")

                # Get top priorities
                try:
                    priorities = todo_manager.get_todos_by_priority(limit=top_n)
                    if priorities:
                        message_parts.append(f"\n🎯 **TOP {top_n} PRIORITIES:**")
                        for i, todo in enumerate(priorities, 1):
                            due_str = ""
                            if todo.get('metadata', {}).get('due'):
                                due_str = f" (due {todo['metadata']['due']})"
                            id_str = f"[{todo.get('id', '?')}] " if todo.get('id') else ""
                            message_parts.append(f"  {i}. {id_str}{todo['text']}{due_str}")
                except:
                    pass

                # Quick wins from persisted prework results
                try:
                    from prework_engine import load_results
                    prework = load_results()
                    quick_wins = [r for r in prework if r.get('is_quick_win')]
                    if quick_wins:
                        message_parts.append(f"\n⚡ **QUICK WINS ({len(quick_wins)}):**")
                        for qw in quick_wins[:5]:
                            tid = qw.get('todo_id', '?')
                            cls = qw.get('classification', '')
                            message_parts.append(f"  • [{tid}] {cls}")
                        if len(quick_wins) > 5:
                            message_parts.append(f"  ... and {len(quick_wins) - 5} more")
                        message_parts.append("Reply '/qw' for details")
                except Exception:
                    pass

                # Quick summary stats
                try:
                    all_incomplete = todo_manager.get_todos(include_completed=False)
                    message_parts.append(f"\n📊 Total pending: {len(all_incomplete)} items")
                except:
                    pass

                # Update TODAY header date
                try:
                    todo_manager.update_today_header()
                except Exception:
                    pass

                send_message_func(chat_id, "\n".join(message_parts))

                # Mark job as run
                if state_tracker:
                    state_tracker.mark_job_run('daily_todo_summary')

                logger.info(f"Sent enhanced TODO summary to chat {chat_id}")

            except Exception as e:
                logger.error(f"Error sending scheduled TODO summary: {e}")

        return send_todo_summary

    @staticmethod
    def create_evening_summary_job(send_message_func: Callable, todo_manager, chat_id: int, state_tracker=None):
        """Create function for evening summary with completion tracking"""
        def send_evening_summary():
            try:
                if not todo_manager:
                    logger.warning("TODO manager not available for evening summary")
                    return

                message_parts = ["🌙 End of day summary:\n"]

                # Get completed today
                try:
                    completed_today = todo_manager.get_completed_today()
                    if completed_today:
                        message_parts.append(f"✅ **COMPLETED TODAY ({len(completed_today)} items):**")
                        for todo in completed_today:
                            message_parts.append(f"  • {todo['text']}")
                        message_parts.append("")
                    else:
                        message_parts.append("📝 No items completed today.\n")
                except:
                    message_parts.append("📝 No items completed today.\n")

                # Get overdue items
                try:
                    overdue = todo_manager.get_overdue_todos()
                    if overdue:
                        message_parts.append(f"🔴 **OVERDUE ({len(overdue)} items)** - Consider these for tomorrow")
                except:
                    pass

                # Get due tomorrow
                try:
                    from datetime import date, timedelta
                    tomorrow = (date.today() + timedelta(days=1)).isoformat()
                    pending = todo_manager.get_todos(include_completed=False)
                    due_tomorrow = [t for t in pending if t.get('metadata', {}).get('due') == tomorrow]
                    if due_tomorrow:
                        message_parts.append(f"\n📅 **DUE TOMORROW ({len(due_tomorrow)} items):**")
                        for todo in due_tomorrow[:3]:
                            id_str = f"[{todo.get('id', '?')}] " if todo.get('id') else ""
                            message_parts.append(f"  • {id_str}{todo['text']}")
                        if len(due_tomorrow) > 3:
                            message_parts.append(f"  ... and {len(due_tomorrow) - 3} more")
                except:
                    pass

                # Ventures dusk queue check (standup #8 accord)
                try:
                    import config as _cfg
                    if getattr(_cfg, 'VENTURES_ENABLED', False):
                        from ventures_signal import render_section
                        ventures_lines = render_section('evening')
                        if ventures_lines:
                            message_parts.append("")
                            message_parts.extend(ventures_lines)
                except Exception as e:
                    logger.error(f"ventures evening section failed: {e}")

                # Motivational close based on completions
                try:
                    total_completed = len(completed_today) if completed_today else 0
                    if total_completed >= 5:
                        message_parts.append("\n🎉 Great productivity today! Well done!")
                    elif total_completed >= 3:
                        message_parts.append("\n👍 Solid day! Keep the momentum going!")
                    elif total_completed >= 1:
                        message_parts.append("\n💪 Progress is progress. Tomorrow is a new day!")
                    else:
                        message_parts.append("\n🌟 Rest up and tackle it fresh tomorrow!")
                except:
                    message_parts.append("\n🌟 Rest up and tackle it fresh tomorrow!")

                send_message_func(chat_id, "\n".join(message_parts))

                # Mark job as run
                if state_tracker:
                    state_tracker.mark_job_run('evening_summary')

                logger.info(f"Sent evening summary to chat {chat_id}")

            except Exception as e:
                logger.error(f"Error sending evening summary: {e}")

        return send_evening_summary

    @staticmethod
    def create_weekly_review_job(send_message_func: Callable, todo_manager, chat_id: int):
        """Create function for weekly review"""
        def send_weekly_review():
            try:
                if not todo_manager:
                    logger.warning("TODO manager not available for weekly review")
                    return

                summary = todo_manager.get_summary()
                message = f"""🗓️ Weekly Review:

{summary}

What did you ship this week? What's the plan for next week?"""

                send_message_func(chat_id, message)
                logger.info(f"Sent weekly review to chat {chat_id}")

            except Exception as e:
                logger.error(f"Error sending weekly review: {e}")

        return send_weekly_review

    @staticmethod
    def create_reminder_job(send_message_func: Callable, chat_id: int, message: str):
        """Create function for custom reminder"""
        def send_reminder():
            try:
                reminder_msg = f"⏰ Reminder:\n\n{message}"
                send_message_func(chat_id, reminder_msg)
                logger.info(f"Sent reminder to chat {chat_id}")

            except Exception as e:
                logger.error(f"Error sending reminder: {e}")

        return send_reminder

    @staticmethod
    def create_slack_digest_job(
        send_message_func: Callable,
        todo_manager,
        chat_id: int,
        state_tracker=None
    ):
        """
        Create function for Slack draft digest.

        Daily job that:
        1. Groups TODOs by person and project
        2. Generates draft messages
        3. Identifies quick wins (both draft-based and prework-based)
        4. Sends summary to Telegram
        """
        def slack_digest():
            try:
                if not todo_manager:
                    logger.warning("TODO manager not available for slack digest")
                    return

                # Import draft generator
                try:
                    from draft_generator import (
                        generate_all_drafts,
                        identify_quick_wins,
                        format_drafts_summary,
                        get_pending_drafts
                    )
                except ImportError as e:
                    logger.error(f"Could not import draft_generator: {e}")
                    return

                # Try to import prework engine for enhanced analysis
                try:
                    from prework_engine import PreworkEngine
                    import slack_registry
                    prework_available = True
                except ImportError:
                    prework_available = False

                # Get open TODOs
                todos = todo_manager.get_todos(include_completed=False)

                if not todos:
                    send_message_func(chat_id, "No pending TODOs for draft generation.")
                    return

                # Generate drafts
                draft_ids, quick_wins = generate_all_drafts(todos)

                # Get pending drafts for summary
                pending_drafts = get_pending_drafts()

                # Format summary
                summary = format_drafts_summary(pending_drafts, quick_wins)

                # Build message
                message_parts = ["**Slack Draft Digest**\n"]

                if draft_ids:
                    message_parts.append(f"Generated {len(draft_ids)} new draft(s)\n")

                message_parts.append(summary)

                # Run prework on Slack TODOs if available
                if prework_available:
                    try:
                        slack_todos = [t for t in todos if t.get('metadata', {}).get('source') == 'slack']
                        if slack_todos:
                            prework_engine = PreworkEngine(
                                todo_manager=todo_manager,
                                slack_registry=slack_registry
                            )
                            prework_quick_wins = []
                            for todo in slack_todos[:10]:  # Limit to 10 for performance
                                result = prework_engine.run_prework(todo)
                                if result and result.is_quick_win:
                                    prework_quick_wins.append(result)

                            if prework_quick_wins:
                                message_parts.append(f"\n**Agent Quick Wins ({len(prework_quick_wins)})**")
                                for pw in prework_quick_wins[:5]:
                                    message_parts.append(f"  {pw.todo_id}: {pw.classification}")
                                message_parts.append("\nUse '/prework [ID]' for suggested actions")
                    except Exception as e:
                        logger.warning(f"Prework analysis failed in digest: {e}")

                send_message_func(chat_id, "\n".join(message_parts))

                # Mark job as run
                if state_tracker:
                    state_tracker.mark_job_run('slack_digest')

                logger.info(f"Sent slack digest to chat {chat_id}")

            except Exception as e:
                logger.error(f"Error sending slack digest: {e}")
                import traceback
                traceback.print_exc()

        return slack_digest

    @staticmethod
    def create_warroom_questions_job(
        send_message_func: Callable,
        warroom_manager,
        todo_manager,
        chat_id: int,
        state_tracker=None
    ):
        """
        Create function for daily war room hard questions generation.

        Generates Claude-powered accountability questions for all active war rooms.
        """
        def send_warroom_questions():
            try:
                if not warroom_manager:
                    logger.warning("War Room manager not available for scheduled questions")
                    return

                # Import here to avoid circular imports
                from warroom_questions import generate_hard_questions, save_questions

                active_rooms = warroom_manager.get_active()

                if not active_rooms:
                    logger.info("No active war rooms for questions generation")
                    return

                for room in active_rooms:
                    try:
                        days_remaining = (room.target_date - datetime.now().date()).days

                        # Generate questions
                        questions = generate_hard_questions(room, todo_manager)

                        if questions:
                            # Save to file
                            save_questions(room.slug, questions, warroom_manager.root_dir)

                            # Send to Telegram
                            header = f"WAR ROOM: {room.name.upper()} (T-{days_remaining})\n\n"
                            send_message_func(chat_id, header + questions)
                            logger.info(f"Sent hard questions for {room.slug}")
                        else:
                            logger.warning(f"Failed to generate questions for {room.slug}")

                    except Exception as e:
                        logger.error(f"Error generating questions for {room.slug}: {e}")

                # Mark job as run
                if state_tracker:
                    state_tracker.mark_job_run('warroom_questions')

            except Exception as e:
                logger.error(f"Error in warroom questions job: {e}")
                import traceback
                traceback.print_exc()

        return send_warroom_questions

    @staticmethod
    def create_slack_sync_job(
        send_message_func: Callable,
        todo_manager,
        chat_id: int,
        state_tracker=None
    ):
        """
        Create function for scheduled Slack TODO sync.

        Fetches messages from the bot DM channel using Slack API
        and syncs new ones to TODO.md.
        """
        def sync_slack():
            try:
                from integrations.slack_todo_sync import SlackTodoSync
                sync = SlackTodoSync()
                count, ids = sync.fetch_and_sync()
                if count > 0:
                    msg = f"📨 Synced {count} new Slack item(s) to TODO"
                    # Include quick wins if any
                    quick_wins_msg = sync.format_quick_wins_notification()
                    if quick_wins_msg:
                        msg += f"\n\n{quick_wins_msg}"
                    send_message_func(chat_id, msg)
                    logger.info(f"Slack sync: added {count} items")

                    # Persist prework results from sync
                    if sync.last_prework_results:
                        try:
                            from prework_engine import save_results, load_results
                            existing = load_results(max_age_hours=48)
                            # Merge: keep existing, add new
                            existing_ids = {r.get('todo_id') for r in existing}
                            merged = list(existing)
                            for pr in sync.last_prework_results:
                                if pr.todo_id not in existing_ids:
                                    merged.append(pr)
                            save_results(merged)
                        except Exception as e:
                            logger.warning(f"Failed to persist prework results: {e}")
                else:
                    logger.info("Slack sync: no new items")

                if state_tracker:
                    state_tracker.mark_job_run('slack_sync')

            except Exception as e:
                logger.error(f"Error in slack sync job: {e}")
                import traceback
                traceback.print_exc()

        return sync_slack

    @staticmethod
    def create_archive_job(
        send_message_func: Callable,
        todo_manager,
        chat_id: int,
        state_tracker=None
    ):
        """
        Create function for weekly archive of completed TODOs.

        Moves completed items older than 7 days to monthly archive file.
        """
        def archive_completed():
            try:
                if not todo_manager:
                    logger.warning("TODO manager not available for archive job")
                    return

                count = todo_manager.archive_completed(keep_days=7)
                if count > 0:
                    send_message_func(chat_id, f"🗄️ Archived {count} completed item(s) from TODO.md")
                    logger.info(f"Archived {count} completed items")
                else:
                    logger.info("Archive job: nothing to archive")

                if state_tracker:
                    state_tracker.mark_job_run('archive_completed')

            except Exception as e:
                logger.error(f"Error in archive job: {e}")
                import traceback
                traceback.print_exc()

        return archive_completed

    @staticmethod
    def create_unified_briefing_job(
        send_message_func: Callable,
        todo_manager,
        chat_id: int,
        state_tracker=None,
        top_n: int = 3,
        cos_spreadsheet_id: str = None,
    ):
        """
        Create function for unified morning briefing combining work (Navi) and personal (COS).

        Replaces the basic morning summary with a single message covering both domains.
        """
        def unified_briefing():
            try:
                if not todo_manager:
                    logger.warning("TODO manager not available for unified briefing")
                    return

                message_parts = ["☀️ Good morning! Here's your combined briefing:\n"]

                # --- WORK ---
                message_parts.append("**WORK**")

                # Update TODAY header date
                try:
                    todo_manager.update_today_header()
                except Exception:
                    pass

                # Overdue items
                try:
                    overdue = todo_manager.get_overdue_todos()
                    if overdue:
                        message_parts.append(f"\n🔴 **OVERDUE ({len(overdue)} items):**")
                        for todo in overdue[:5]:
                            due_str = todo.get('metadata', {}).get('due', 'unknown')
                            id_str = f"[{todo.get('id', '?')}] " if todo.get('id') else ""
                            message_parts.append(f"  • {id_str}{todo['text']} (was due {due_str})")
                        if len(overdue) > 5:
                            message_parts.append(f"  ... and {len(overdue) - 5} more")
                except Exception:
                    pass

                # Due today
                try:
                    due_today = todo_manager.get_due_today_todos()
                    if due_today:
                        message_parts.append(f"\n📅 **DUE TODAY ({len(due_today)} items):**")
                        for todo in due_today:
                            id_str = f"[{todo.get('id', '?')}] " if todo.get('id') else ""
                            message_parts.append(f"  • {id_str}{todo['text']}")
                    else:
                        message_parts.append("\n📅 Nothing due today!")
                except Exception:
                    message_parts.append("\n📅 Nothing due today!")

                # Top priorities
                try:
                    priorities = todo_manager.get_todos_by_priority(limit=top_n)
                    if priorities:
                        message_parts.append(f"\n🎯 **TOP {top_n} PRIORITIES:**")
                        for i, todo in enumerate(priorities, 1):
                            due_str = ""
                            if todo.get('metadata', {}).get('due'):
                                due_str = f" (due {todo['metadata']['due']})"
                            id_str = f"[{todo.get('id', '?')}] " if todo.get('id') else ""
                            message_parts.append(f"  {i}. {id_str}{todo['text']}{due_str}")
                except Exception:
                    pass

                # Quick wins from persisted prework
                try:
                    from prework_engine import load_results
                    prework = load_results()
                    quick_wins = [r for r in prework if r.get('is_quick_win')]
                    if quick_wins:
                        message_parts.append(f"\n⚡ **QUICK WINS ({len(quick_wins)}):**")
                        for qw in quick_wins[:5]:
                            tid = qw.get('todo_id', '?')
                            cls = qw.get('classification', '')
                            message_parts.append(f"  • [{tid}] {cls}")
                        message_parts.append("Reply '/qw' for details")
                except Exception:
                    pass

                # Total pending
                try:
                    all_incomplete = todo_manager.get_todos(include_completed=False)
                    message_parts.append(f"\n📊 Total pending: {len(all_incomplete)} items")
                except Exception:
                    pass

                # --- PERSONAL (COS Google Sheet) ---
                sheet_id = cos_spreadsheet_id or "1gK7Z9QkpbgTwALGzZYBLYlaSkGprzlT08h4Y2_7lh6U"
                try:
                    import requests as req
                    # Read COS memory for active projects summary
                    cos_memory_path = os.path.expanduser("~/personal/chief-of-staff/MEMORY.md")
                    personal_items = []

                    if os.path.exists(cos_memory_path):
                        with open(cos_memory_path, 'r') as f:
                            memory = f.read()

                        # Extract active projects section
                        import re
                        active_match = re.search(
                            r'(?:Active Projects?|Current Projects?).*?\n((?:[-*].*\n)*)',
                            memory, re.IGNORECASE
                        )
                        if active_match:
                            for line in active_match.group(1).strip().split('\n'):
                                line = line.strip().lstrip('-* ')
                                if line:
                                    personal_items.append(line)

                    if personal_items:
                        message_parts.append("\n\n**PERSONAL**")
                        for item in personal_items[:5]:
                            message_parts.append(f"  • {item}")
                    else:
                        # Fallback: try reading the COS briefing directory
                        briefings_dir = os.path.expanduser("~/personal/chief-of-staff/briefings/")
                        if os.path.isdir(briefings_dir):
                            import glob
                            briefings = sorted(glob.glob(os.path.join(briefings_dir, '*.md')), reverse=True)
                            if briefings:
                                message_parts.append("\n\n**PERSONAL**")
                                message_parts.append(f"  Latest COS briefing: {os.path.basename(briefings[0])}")
                                message_parts.append("  Say 'chief-of-staff' for full personal briefing")

                except Exception as e:
                    logger.warning(f"Could not load personal items: {e}")

                send_message_func(chat_id, "\n".join(message_parts))

                # Mark job as run
                if state_tracker:
                    state_tracker.mark_job_run('daily_todo_summary')

                logger.info(f"Sent unified briefing to chat {chat_id}")

            except Exception as e:
                logger.error(f"Error sending unified briefing: {e}")
                import traceback
                traceback.print_exc()

        return unified_briefing

    @staticmethod
    def state_aware_wrap(
        job_func: Callable,
        scheduler,
        job_id: str,
        max_delay_minutes: int = 60,
        retry_interval_minutes: int = 15,
    ) -> Callable:
        """
        Wrap a scheduled job to defer it when the user isn't interruptible.

        On each trigger: checks behavioral state via behavior_state.py.
        - AVAILABLE or HEADS_DOWN → fires immediately
        - Anything else → schedules a one-time retry in retry_interval_minutes
        - After max_delay_minutes from the first trigger, fires unconditionally
        """
        state = {"first_fire": None}

        def wrapped():
            from behavior_state import is_good_time_to_interrupt
            from datetime import datetime, timedelta

            now = datetime.now()
            if state["first_fire"] is None:
                state["first_fire"] = now

            elapsed_minutes = (now - state["first_fire"]).total_seconds() / 60

            if is_good_time_to_interrupt() or elapsed_minutes >= max_delay_minutes:
                state["first_fire"] = None  # reset for next scheduled occurrence
                job_func()
            else:
                retry_time = now + timedelta(minutes=retry_interval_minutes)
                retry_id = f"{job_id}_retry"
                scheduler.add_onetime_job_direct(retry_id, wrapped, retry_time)
                logger.info(
                    f"State-deferred '{job_id}': not a good time "
                    f"({elapsed_minutes:.0f}/{max_delay_minutes} min elapsed). "
                    f"Retrying at {retry_time.strftime('%H:%M')}"
                )

        wrapped.__name__ = f"{getattr(job_func, '__name__', job_id)}_state_aware"
        return wrapped

    @staticmethod
    def parse_time_string(time_str: str) -> Optional[tuple]:
        """
        Parse natural language time strings
        Returns (hour, minute) or None
        Examples: "8am", "8:30am", "14:00", "2:30pm"
        """
        import re

        time_str = time_str.lower().strip()

        # Match patterns like "8am", "8:30am", "14:00", "2:30pm"
        pattern = r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?'
        match = re.match(pattern, time_str)

        if not match:
            return None

        hour_str, minute_str, meridiem = match.groups()
        hour = int(hour_str)
        minute = int(minute_str) if minute_str else 0

        # Handle AM/PM
        if meridiem:
            if meridiem == 'pm' and hour != 12:
                hour += 12
            elif meridiem == 'am' and hour == 12:
                hour = 0

        # Validate
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return (hour, minute)

        return None
