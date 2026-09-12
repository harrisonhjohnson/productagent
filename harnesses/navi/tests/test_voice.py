"""
Tests for voice transcription pipeline.

Validates: VoiceHandler init, Whisper API connectivity, transcription,
and that transcribed text flows through the full dispatch pipeline
without import errors or crashes.
"""
import os
import sys
import struct
import tempfile
import pytest

# Add parent dir to path so we can import navi modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _load_env():
    """Load .env from project root."""
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k, v)


_load_env()


@pytest.fixture
def voice_handler():
    from voice_handler import VoiceHandler
    return VoiceHandler(telegram_token=os.environ.get('TELEGRAM_BOT_TOKEN', 'test'))


@pytest.fixture
def silent_wav():
    """Create a minimal valid WAV file (1s silence)."""
    sample_rate = 8000
    num_samples = sample_rate
    data_size = num_samples * 2

    path = os.path.join(tempfile.gettempdir(), 'navi_test_voice.wav')
    with open(path, 'wb') as f:
        f.write(b'RIFF')
        f.write(struct.pack('<I', 36 + data_size))
        f.write(b'WAVE')
        f.write(b'fmt ')
        f.write(struct.pack('<I', 16))
        f.write(struct.pack('<H', 1))           # PCM
        f.write(struct.pack('<H', 1))           # mono
        f.write(struct.pack('<I', sample_rate))
        f.write(struct.pack('<I', sample_rate * 2))
        f.write(struct.pack('<H', 2))
        f.write(struct.pack('<H', 16))
        f.write(b'data')
        f.write(struct.pack('<I', data_size))
        f.write(b'\x00' * data_size)

    yield path
    if os.path.exists(path):
        os.remove(path)


# --- Unit tests (no network) ---

class TestVoiceHandlerInit:
    def test_loads_api_key_from_env(self, voice_handler):
        assert voice_handler.openai_api_key is not None, "OPENAI_API_KEY not loaded from .env"

    def test_key_looks_valid(self, voice_handler):
        assert voice_handler.openai_api_key.startswith('sk-'), f"Key doesn't start with sk-: {voice_handler.openai_api_key[:8]}"

    def test_telegram_api_url(self, voice_handler):
        assert 'api.telegram.org/bot' in voice_handler.telegram_api


class TestVoiceHandlerNoKey:
    def test_transcribe_returns_none_without_key(self, silent_wav):
        from voice_handler import VoiceHandler
        vh = VoiceHandler(telegram_token='test')
        vh.openai_api_key = None
        assert vh.transcribe(silent_wav) is None

    def test_process_returns_error_without_key(self):
        from voice_handler import VoiceHandler
        vh = VoiceHandler(telegram_token='test')
        vh.openai_api_key = None
        text, error = vh.process_voice_message('fake_file_id')
        assert text is None
        assert error is not None


# --- Integration tests (hit real APIs) ---

@pytest.mark.integration
class TestWhisperAPI:
    def test_whisper_transcribes_silence(self, voice_handler, silent_wav):
        """Whisper should return something (even empty-ish) for valid audio."""
        result = voice_handler.transcribe(silent_wav)
        assert result is not None, "Whisper returned None — check API key and billing"

    def test_telegram_bot_api_reachable(self, voice_handler):
        import requests
        r = requests.get(f"{voice_handler.telegram_api}/getMe", timeout=5)
        assert r.status_code == 200
        assert r.json().get('ok') is True


# --- Dispatch pipeline tests (the re import bug) ---

class TestDispatchPipeline:
    """Verify that transcribed text can flow through the bot's dispatch
    pipeline without crashing. This catches missing imports like `re`."""

    def test_top_level_imports(self):
        """telegram_bot.py must import re at top level."""
        import telegram_bot
        assert hasattr(telegram_bot, 're'), "telegram_bot.py missing top-level 'import re'"

    def test_handle_command_with_voice_text(self):
        """Simulated voice commands shouldn't crash."""
        import telegram_bot
        # These are typical voice transcriptions — they should either
        # match a command or return None (fall through to Claude).
        # They must NOT raise an exception.
        test_phrases = [
            "show my todos",
            "summarize my to do",
            "add todo call the dentist",
            "what should I do next",
            "mark T123 complete",
            "email triage",
            "quick wins",
            "status",
            "archive 1 2 3",
            "nuke",
            "skip",
            "undo junk",
            "read 1",
        ]
        for phrase in test_phrases:
            try:
                # handle_command returns a string or None — either is fine
                telegram_bot.handle_command(phrase, 12345, 12345)
            except Exception as e:
                pytest.fail(f"handle_command crashed on '{phrase}': {e}")

    def test_triage_handler_with_voice_text(self):
        """Triage actions shouldn't crash when no session active."""
        import telegram_bot
        test_phrases = ["todo 1", "archive 1 2", "nuke", "skip", "undo junk", "read 3"]
        for phrase in test_phrases:
            try:
                result = telegram_bot.handle_email_triage_action(phrase, 99999, 99999)
                # Should return a string (no active session msg) or None
                assert result is None or isinstance(result, str), f"Unexpected return for '{phrase}': {result}"
            except Exception as e:
                pytest.fail(f"handle_email_triage_action crashed on '{phrase}': {e}")

    def test_search_handler_with_voice_text(self):
        """Search actions shouldn't crash when no session active."""
        import telegram_bot
        test_phrases = ["read 1", "reply 2", "send", "back"]
        for phrase in test_phrases:
            try:
                result = telegram_bot.handle_email_search_action(phrase, 99999, 99999)
                assert result is None or isinstance(result, str)
            except Exception as e:
                pytest.fail(f"handle_email_search_action crashed on '{phrase}': {e}")

    def test_regex_patterns_dont_crash(self):
        """All regex patterns used in dispatch should compile and match without errors."""
        import re
        patterns = [
            (r'(archive|todo|read)\s+[\d\s]+', "archive 1 2 3"),
            (r'archive\s+([\d\s]+)', "archive 1 2"),
            (r'todo\s+([\d\s]+)', "todo 1"),
            (r'read\s+(\d+)', "read 3"),
            (r'(?:agent|plan(?:\s+for)?)\s+#?(T[A-Z0-9]{3})', "agent T123"),
            (r'(?:approve|execute|run\s+plan(?:\s+for)?)\s+#?(T[A-Z0-9]{3})', "approve T123"),
            (r'(?:cancel|abort)\s+#?(T[A-Z0-9]{3})', "cancel T123"),
            (r'send\s+(DRF\d{3})', "send DRF001"),
            (r'skip\s+(DRF\d{3})', "skip DRF001"),
        ]
        for pattern, test_str in patterns:
            try:
                re.match(pattern, test_str)
            except re.error as e:
                pytest.fail(f"Regex pattern failed to compile: {pattern} — {e}")
