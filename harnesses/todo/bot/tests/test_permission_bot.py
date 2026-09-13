"""
Tests for the Claude Code permission gate functions in telegram_bot.py.

We import only the three pure-ish functions (resolve_permission,
handle_permission_text_reply, handle_permission_callback) by patching the
heavy module-level side-effects before the import lands.
"""
import os
import sys
import types
from unittest.mock import MagicMock, patch, call
import pytest

# ---------------------------------------------------------------------------
# Stub out the module-level side-effects so we can import telegram_bot
# without a running Telegram connection, scheduler, DB, etc.
# ---------------------------------------------------------------------------

def _make_stub(name):
    m = types.ModuleType(name)
    m.__spec__ = None
    return m


for mod in ("config", "session", "todo_manager", "scheduler", "scheduler_state",
            "voice_handler", "integrations", "integrations.email_client",
            "agent_executor", "prework_engine", "slack_registry",
            "warroom_manager", "warroom_questions", "draft_generator"):
    sys.modules.setdefault(mod, _make_stub(mod))

# Config values the bot reads at import time
config_stub = sys.modules["config"]
config_stub.MAX_MESSAGE_LENGTH = 4096
config_stub.CLAUDE_TIMEOUT = 120
config_stub.MAX_RETRIES = 3
config_stub.INITIAL_RETRY_DELAY = 2
config_stub.MAX_RETRY_DELAY = 30
config_stub.RETRY_BACKOFF_MULTIPLIER = 2
config_stub.CONFLICT_WAIT_TIME = 35
config_stub.LOG_UNAUTHORIZED_ATTEMPTS = True
config_stub.LOG_FILE_MAX_BYTES = 10 * 1024 * 1024
config_stub.LOG_FILE_BACKUP_COUNT = 5
config_stub.SESSION_TIMEOUT_MINUTES = 30
config_stub.MAX_CONTEXT_MESSAGES = 10
config_stub.CLEANUP_INTERVAL_SECONDS = 300
config_stub.TODO_PATH = None
config_stub.TODO_AUTO_UPDATE_DATE = True
config_stub.SCHEDULER_TIMEZONE = "America/Los_Angeles"
config_stub.SCHEDULER_ENABLED = False
config_stub.DEFAULT_TODO_SUMMARY_TIME = (8, 0)
config_stub.DEFAULT_EVENING_SUMMARY_TIME = (17, 0)
config_stub.DEFAULT_WEEKLY_REVIEW_DAY = "fri"
config_stub.DEFAULT_WEEKLY_REVIEW_TIME = (17, 0)
config_stub.MORNING_TOP_PRIORITIES = 3
config_stub.CATCHUP_SUMMARY_ENABLED = False
config_stub.SLACK_NOTIFICATIONS_ENABLED = False
config_stub.SLACK_USER_NAME = "Test"
config_stub.WARROOM_ENABLED = False
config_stub.WARROOM_QUESTIONS_HOUR = 8
config_stub.WARROOM_QUESTIONS_MINUTE = 30
config_stub.WARROOM_ROOT = None
config_stub.EMAIL_ENABLED = False
config_stub.GMAIL_TOKEN_PATH = "/tmp/fake"
config_stub.GMAIL_OAUTH_CLIENT_PATH = "/tmp/fake"
config_stub.EMAIL_TRIAGE_DEFAULT_QUERY = ""
config_stub.EMAIL_TRIAGE_MAX_RESULTS = 10
config_stub.AGENT_INBOX_ENABLED = False
config_stub.AGENT_INBOX_PATH = "/tmp/fake_inbox"
config_stub.AGENT_INBOX_POLL_SECONDS = 10
config_stub.AUTHORIZED_USERS = [12345]

session_stub = sys.modules["session"]
session_stub.SessionManager = MagicMock

todo_stub = sys.modules["todo_manager"]
todo_stub.TodoManager = MagicMock

scheduler_stub = sys.modules["scheduler"]
scheduler_stub.JobScheduler = MagicMock
scheduler_stub.BuiltInJobs = MagicMock

ss_stub = sys.modules["scheduler_state"]
ss_stub.SchedulerState = MagicMock

voice_stub = sys.modules["voice_handler"]
voice_stub.VoiceHandler = MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "fake_token", "TELEGRAM_USER_ID": "12345"}):
    import telegram_bot as bot


# ---------------------------------------------------------------------------
# resolve_permission
# ---------------------------------------------------------------------------

class TestResolvePermission:
    def test_returns_true_and_writes_decision_when_pending_exists(self, tmp_path):
        req_id = "abcd1234"
        (tmp_path / f"{req_id}.pending").write_text("{}")

        with patch.object(bot, "PERM_DIR", str(tmp_path)):
            result = bot.resolve_permission(req_id, "y")

        assert result is True
        assert (tmp_path / f"{req_id}.decision").read_text() == "y"
        assert not (tmp_path / f"{req_id}.pending").exists()

    def test_returns_false_when_no_pending_file(self, tmp_path):
        with patch.object(bot, "PERM_DIR", str(tmp_path)):
            result = bot.resolve_permission("nosuchid", "y")

        assert result is False
        assert not (tmp_path / "nosuchid.decision").exists()

    def test_writes_deny_decision(self, tmp_path):
        req_id = "deadbeef"
        (tmp_path / f"{req_id}.pending").write_text("{}")

        with patch.object(bot, "PERM_DIR", str(tmp_path)):
            bot.resolve_permission(req_id, "n")

        assert (tmp_path / f"{req_id}.decision").read_text() == "n"

    def test_removes_pending_file_on_resolution(self, tmp_path):
        req_id = "cafebabe"
        pending = tmp_path / f"{req_id}.pending"
        pending.write_text("{}")

        with patch.object(bot, "PERM_DIR", str(tmp_path)):
            bot.resolve_permission(req_id, "y")

        assert not pending.exists()


# ---------------------------------------------------------------------------
# handle_permission_text_reply
# ---------------------------------------------------------------------------

class TestHandlePermissionTextReply:
    def test_allow_reply_resolves_and_returns_true(self, tmp_path):
        req_id = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6"
        (tmp_path / f"{req_id}.pending").write_text("{}")

        with patch.object(bot, "PERM_DIR", str(tmp_path)), \
             patch.object(bot, "send_message") as mock_send:
            result = bot.handle_permission_text_reply(f"y {req_id}", 99, 12345)

        assert result is True
        assert (tmp_path / f"{req_id}.decision").read_text() == "y"
        mock_send.assert_called_once()
        assert "Allowed" in mock_send.call_args[0][1]

    def test_deny_reply_resolves_and_returns_true(self, tmp_path):
        req_id = "e5f6a7b8c9d0e1f2a3b4c5d6a1b2c3d4"
        (tmp_path / f"{req_id}.pending").write_text("{}")

        with patch.object(bot, "PERM_DIR", str(tmp_path)), \
             patch.object(bot, "send_message") as mock_send:
            result = bot.handle_permission_text_reply(f"n {req_id}", 99, 12345)

        assert result is True
        assert (tmp_path / f"{req_id}.decision").read_text() == "n"
        assert "Denied" in mock_send.call_args[0][1]

    def test_expired_request_returns_true_but_sends_not_found(self, tmp_path):
        # Pattern matches but no pending file → expired
        with patch.object(bot, "PERM_DIR", str(tmp_path)), \
             patch.object(bot, "send_message") as mock_send:
            result = bot.handle_permission_text_reply("y " + "0" * 32, 99, 12345)

        assert result is True
        assert "not found" in mock_send.call_args[0][1]

    def test_non_matching_text_returns_false(self, tmp_path):
        with patch.object(bot, "PERM_DIR", str(tmp_path)):
            assert not bot.handle_permission_text_reply("hello world", 99, 12345)
            assert not bot.handle_permission_text_reply("y tooshort", 99, 12345)
            assert not bot.handle_permission_text_reply("y " + "a" * 33, 99, 12345)
            assert not bot.handle_permission_text_reply("maybe a1b2c3d4", 99, 12345)

    def test_uppercase_y_works(self, tmp_path):
        req_id = "f1e2d3c4a5b6c7d8e9f0a1b2c3d4e5f6"
        (tmp_path / f"{req_id}.pending").write_text("{}")

        with patch.object(bot, "PERM_DIR", str(tmp_path)), \
             patch.object(bot, "send_message"):
            result = bot.handle_permission_text_reply(f"Y {req_id}", 99, 12345)

        assert result is True
        assert (tmp_path / f"{req_id}.decision").read_text() == "y"


# ---------------------------------------------------------------------------
# handle_permission_callback
# ---------------------------------------------------------------------------

class TestHandlePermissionCallback:
    def _make_callback(self, data: str, user_id: int = 12345, message_id: int = 1, text: str = "original msg\n\nAllow? Tap below"):
        return {
            "id": "cb_001",
            "data": data,
            "from": {"id": user_id},
            "message": {
                "message_id": message_id,
                "chat": {"id": 99},
                "text": text,
            },
        }

    def test_allow_callback_resolves_and_acknowledges(self, tmp_path):
        req_id = "12345678901234567890123456789012"
        (tmp_path / f"{req_id}.pending").write_text("{}")

        with patch.object(bot, "PERM_DIR", str(tmp_path)), \
             patch.object(bot, "answer_callback_query") as mock_answer, \
             patch.object(bot, "edit_message_reply_markup"):
            bot.handle_permission_callback(self._make_callback(f"allow_{req_id}"))

        assert (tmp_path / f"{req_id}.decision").read_text() == "y"
        mock_answer.assert_called_once_with("cb_001", text="✅ Allowed")

    def test_deny_callback_resolves_and_acknowledges(self, tmp_path):
        req_id = "87654321098765432109876543210987"
        (tmp_path / f"{req_id}.pending").write_text("{}")

        with patch.object(bot, "PERM_DIR", str(tmp_path)), \
             patch.object(bot, "answer_callback_query") as mock_answer, \
             patch.object(bot, "edit_message_reply_markup"):
            bot.handle_permission_callback(self._make_callback(f"deny_{req_id}"))

        assert (tmp_path / f"{req_id}.decision").read_text() == "n"
        mock_answer.assert_called_once_with("cb_001", text="❌ Denied")

    def test_unauthorized_user_is_rejected(self, tmp_path):
        with patch.object(bot, "PERM_DIR", str(tmp_path)), \
             patch.object(bot, "answer_callback_query") as mock_answer:
            bot.handle_permission_callback(self._make_callback("allow_" + "a" * 32, user_id=99999))

        mock_answer.assert_called_once_with("cb_001", text="Unauthorized")

    def test_expired_request_answers_with_not_found(self, tmp_path):
        # No pending file
        with patch.object(bot, "PERM_DIR", str(tmp_path)), \
             patch.object(bot, "answer_callback_query") as mock_answer, \
             patch.object(bot, "edit_message_reply_markup"):
            bot.handle_permission_callback(self._make_callback("allow_" + "0" * 32))

        mock_answer.assert_called_once_with("cb_001", text="Request expired or not found")

    def test_unrelated_callback_data_is_ignored(self, tmp_path):
        with patch.object(bot, "PERM_DIR", str(tmp_path)), \
             patch.object(bot, "answer_callback_query") as mock_answer:
            bot.handle_permission_callback(self._make_callback("some_other_button"))

        mock_answer.assert_not_called()

    def test_message_is_edited_after_allow(self, tmp_path):
        req_id = "aabbccdd" * 4
        (tmp_path / f"{req_id}.pending").write_text("{}")

        with patch.object(bot, "PERM_DIR", str(tmp_path)), \
             patch.object(bot, "answer_callback_query"), \
             patch.object(bot, "edit_message_reply_markup") as mock_edit:
            bot.handle_permission_callback(self._make_callback(f"allow_{req_id}"))

        mock_edit.assert_called_once()
        edited_text = mock_edit.call_args[0][2]
        assert "✅ Allowed" in edited_text
