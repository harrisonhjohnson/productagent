"""
Tests for claude_permission_hook.py

Covers the pure classification/formatting functions and the main() entry point
via subprocess so we get real stdin/stdout/exit-code behavior without mocking
Claude Code's execution environment.
"""
import json
import os
import subprocess
import sys
from typing import Optional
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import claude_permission_hook as hook

HOOK_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "claude_permission_hook.py")


def run_hook(tool_name: str, tool_input: dict, extra_env: Optional[dict] = None, timeout: int = 5) -> subprocess.CompletedProcess:
    """Run the hook script as a subprocess, with tokens cleared so it can't actually call Telegram."""
    env = {**os.environ, "TELEGRAM_BOT_TOKEN": "", "TELEGRAM_USER_ID": ""}
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, HOOK_PATH],
        input=json.dumps({"tool_name": tool_name, "tool_input": tool_input}).encode(),
        capture_output=True,
        env=env,
        timeout=timeout,
        cwd="/tmp",  # no stray .env nearby
    )


# ---------------------------------------------------------------------------
# is_silent
# ---------------------------------------------------------------------------

class TestIsSilent:
    @pytest.mark.parametrize("tool", sorted(hook.SILENT_TOOLS))
    def test_all_silent_tools_pass_through(self, tool):
        assert hook.is_silent(tool, {})

    def test_bash_git_status(self):
        assert hook.is_silent("Bash", {"command": "git status"})

    def test_bash_ls(self):
        assert hook.is_silent("Bash", {"command": "ls -la"})

    def test_bash_cat_with_space(self):
        # "cat " (with trailing space) prevents "catch" or "cats" from matching
        assert hook.is_silent("Bash", {"command": "cat README.md"})

    def test_bash_rg(self):
        assert hook.is_silent("Bash", {"command": "rg 'def foo' src/"})

    def test_bash_pytest(self):
        assert hook.is_silent("Bash", {"command": "python3 -m pytest tests/"})

    def test_bash_git_push_not_silent(self):
        assert not hook.is_silent("Bash", {"command": "git push origin main"})

    def test_bash_npm_install_not_silent(self):
        assert not hook.is_silent("Bash", {"command": "npm install"})

    def test_bash_rm_not_silent(self):
        assert not hook.is_silent("Bash", {"command": "rm -rf build/"})

    def test_bash_empty_command_not_silent(self):
        assert not hook.is_silent("Bash", {"command": ""})

    def test_bash_missing_command_key_not_silent(self):
        assert not hook.is_silent("Bash", {})

    def test_edit_not_silent(self):
        assert not hook.is_silent("Edit", {"file_path": "/foo.py"})

    def test_write_not_silent(self):
        assert not hook.is_silent("Write", {"file_path": "/foo.py"})

    def test_agent_not_silent(self):
        assert not hook.is_silent("Agent", {"description": "review"})

    def test_unknown_tool_not_silent(self):
        assert not hook.is_silent("UnknownTool", {})


# ---------------------------------------------------------------------------
# is_hard_blocked
# ---------------------------------------------------------------------------

class TestIsHardBlocked:
    def test_rm_rf_root(self):
        assert hook.is_hard_blocked("Bash", {"command": "rm -rf /"})

    def test_rm_rf_home_tilde(self):
        assert hook.is_hard_blocked("Bash", {"command": "rm -rf ~"})

    def test_rm_rf_home_var(self):
        assert hook.is_hard_blocked("Bash", {"command": "rm -rf $HOME"})

    def test_fork_bomb(self):
        assert hook.is_hard_blocked("Bash", {"command": ":(){ :|:& };:"})

    def test_dd_zero(self):
        assert hook.is_hard_blocked("Bash", {"command": "dd if=/dev/zero of=/dev/sda"})

    def test_safe_rm_subdir_not_blocked(self):
        assert not hook.is_hard_blocked("Bash", {"command": "rm -rf ./build"})

    def test_safe_git_push_not_blocked(self):
        assert not hook.is_hard_blocked("Bash", {"command": "git push origin main"})

    def test_non_bash_tool_ignored(self):
        # The dangerous pattern is in the input but tool isn't Bash — should not block
        assert not hook.is_hard_blocked("Edit", {"command": "rm -rf /"})

    def test_empty_command(self):
        assert not hook.is_hard_blocked("Bash", {"command": ""})

    def test_missing_command_key(self):
        assert not hook.is_hard_blocked("Bash", {})


# ---------------------------------------------------------------------------
# format_tool_description
# ---------------------------------------------------------------------------

class TestFormatToolDescription:
    def test_bash_with_description(self):
        out = hook.format_tool_description("Bash", {
            "command": "git push origin main",
            "description": "Push branch to remote",
        })
        assert "git push origin main" in out
        assert "Push branch to remote" in out

    def test_bash_without_description_has_dollar_prefix(self):
        out = hook.format_tool_description("Bash", {"command": "npm install"})
        assert out.startswith("$ ")
        assert "npm install" in out

    def test_bash_truncates_long_command(self):
        out = hook.format_tool_description("Bash", {"command": "x" * 500})
        assert len(out) < 320  # "$ " + 300 chars max

    def test_bash_missing_command(self):
        out = hook.format_tool_description("Bash", {})
        assert out.startswith("$ ")

    def test_edit_shows_path(self):
        out = hook.format_tool_description("Edit", {"file_path": "/home/user/foo.py"})
        assert "Edit" in out
        assert "/home/user/foo.py" in out

    def test_write_shows_path(self):
        out = hook.format_tool_description("Write", {"file_path": "/home/user/bar.js"})
        assert "Write" in out
        assert "/home/user/bar.js" in out

    def test_agent_shows_label_and_prompt(self):
        out = hook.format_tool_description("Agent", {
            "description": "Code review agent",
            "prompt": "Review this PR for bugs",
        })
        assert "Code review agent" in out
        assert "Review this PR for bugs" in out

    def test_agent_truncates_long_prompt(self):
        out = hook.format_tool_description("Agent", {
            "description": "agent",
            "prompt": "p" * 300,
        })
        assert len(out) < 250

    def test_unknown_tool_json_fallback(self):
        out = hook.format_tool_description("UnknownTool", {"foo": "bar"})
        assert "UnknownTool" in out
        assert "bar" in out


# ---------------------------------------------------------------------------
# load_env
# ---------------------------------------------------------------------------

class TestLoadEnv:
    def test_loads_key_value(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("_TEST_NAVI_KEY=hello\n")
        os.environ.pop("_TEST_NAVI_KEY", None)
        with patch.object(hook, "NAVI_ENV", str(env_file)):
            hook.load_env()
        assert os.environ.pop("_TEST_NAVI_KEY") == "hello"

    def test_strips_double_quotes(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text('_TEST_NAVI_Q="quoted"\n')
        os.environ.pop("_TEST_NAVI_Q", None)
        with patch.object(hook, "NAVI_ENV", str(env_file)):
            hook.load_env()
        assert os.environ.pop("_TEST_NAVI_Q") == "quoted"

    def test_strips_single_quotes(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("_TEST_NAVI_SQ='val'\n")
        os.environ.pop("_TEST_NAVI_SQ", None)
        with patch.object(hook, "NAVI_ENV", str(env_file)):
            hook.load_env()
        assert os.environ.pop("_TEST_NAVI_SQ") == "val"

    def test_does_not_overwrite_existing(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("_TEST_NAVI_OW=new\n")
        os.environ["_TEST_NAVI_OW"] = "original"
        with patch.object(hook, "NAVI_ENV", str(env_file)):
            hook.load_env()
        assert os.environ.pop("_TEST_NAVI_OW") == "original"

    def test_ignores_comment_lines(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("# _TEST_NAVI_CM=should_not_load\n")
        with patch.object(hook, "NAVI_ENV", str(env_file)):
            hook.load_env()
        assert "_TEST_NAVI_CM" not in os.environ

    def test_missing_file_is_noop(self, tmp_path):
        with patch.object(hook, "NAVI_ENV", str(tmp_path / "nonexistent.env")):
            hook.load_env()  # must not raise


# ---------------------------------------------------------------------------
# main() — subprocess integration (fast: no real Telegram calls)
# ---------------------------------------------------------------------------

class TestMainIntegration:
    def test_silent_tool_exits_zero_immediately(self):
        result = run_hook("Read", {"file_path": "/some/file"})
        assert result.returncode == 0

    def test_silent_bash_git_status_exits_zero(self):
        result = run_hook("Bash", {"command": "git status"})
        assert result.returncode == 0

    def test_hard_blocked_rm_rf_root_exits_two(self):
        result = run_hook("Bash", {"command": "rm -rf /"})
        assert result.returncode == 2
        assert b"Blocked" in result.stdout

    def test_hard_blocked_fork_bomb_exits_two(self):
        result = run_hook("Bash", {"command": ":(){ :|:& };:"})
        assert result.returncode == 2

    def test_risky_bash_without_token_fails_open(self):
        # No token → can't notify → pass through (fail open)
        result = run_hook("Bash", {"command": "git push origin main"})
        assert result.returncode == 0

    def test_risky_write_without_token_fails_open(self):
        result = run_hook("Write", {"file_path": "/tmp/foo.py"})
        assert result.returncode == 0

    def test_invalid_json_exits_zero(self):
        env = {**os.environ, "TELEGRAM_BOT_TOKEN": "", "TELEGRAM_USER_ID": ""}
        result = subprocess.run(
            [sys.executable, HOOK_PATH],
            input=b"not valid json",
            capture_output=True,
            env=env,
            timeout=5,
            cwd="/tmp",
        )
        assert result.returncode == 0

    def test_empty_stdin_exits_zero(self):
        env = {**os.environ, "TELEGRAM_BOT_TOKEN": "", "TELEGRAM_USER_ID": ""}
        result = subprocess.run(
            [sys.executable, HOOK_PATH],
            input=b"",
            capture_output=True,
            env=env,
            timeout=5,
            cwd="/tmp",
        )
        assert result.returncode == 0
