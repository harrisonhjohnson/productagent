"""
Git sync for TODO.md changes.
Wraps TodoManager._write_file to auto-commit and push after writes.
"""
import subprocess
import logging
import os
import threading
import time

logger = logging.getLogger(__name__)

REPO_DIR = os.path.expanduser("~/navi-mobile")
TODO_PATH = os.path.join(REPO_DIR, "TODO.md")

# Debounce: batch rapid writes into a single commit
_pending_push = False
_push_lock = threading.Lock()
_DEBOUNCE_SECONDS = 5


def _git_push():
    """Commit and push TODO.md changes."""
    global _pending_push
    time.sleep(_DEBOUNCE_SECONDS)

    with _push_lock:
        if not _pending_push:
            return
        _pending_push = False

    try:
        # Stage, commit, push
        subprocess.run(
            ["git", "add", "TODO.md"],
            cwd=REPO_DIR, capture_output=True, timeout=10
        )

        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=REPO_DIR, capture_output=True, timeout=10
        )

        if result.returncode != 0:  # There are staged changes
            subprocess.run(
                ["git", "commit", "-m", "todo update"],
                cwd=REPO_DIR, capture_output=True, timeout=10
            )
            subprocess.run(
                ["git", "push"],
                cwd=REPO_DIR, capture_output=True, timeout=30
            )
            logger.info("Git: TODO.md pushed to GitHub")
        else:
            logger.debug("Git: no changes to push")

    except subprocess.TimeoutExpired:
        logger.warning("Git push timed out")
    except Exception as e:
        logger.error(f"Git push failed: {e}")


def trigger_sync():
    """Trigger a debounced git push."""
    global _pending_push
    with _push_lock:
        was_pending = _pending_push
        _pending_push = True

    if not was_pending:
        thread = threading.Thread(target=_git_push, daemon=True)
        thread.start()


def patch_todo_manager(todo_manager):
    """
    Monkey-patch a TodoManager instance to auto-push after writes.
    Call this once at startup.
    """
    original_write = todo_manager._write_file

    def _write_and_sync(content):
        original_write(content)
        trigger_sync()

    todo_manager._write_file = _write_and_sync
    logger.info("Git sync: patched TodoManager._write_file")
