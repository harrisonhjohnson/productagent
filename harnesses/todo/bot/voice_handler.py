"""
Voice Handler for Navi - Voice message transcription and processing
"""
import os
import logging
import requests
import tempfile
from typing import Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class VoiceHandler:
    def __init__(self, telegram_token: str, openai_api_key: str = None):
        """
        Initialize voice handler

        Args:
            telegram_token: Telegram bot token for downloading files
            openai_api_key: OpenAI API key for Whisper transcription (optional, reads from OPENAI_API_KEY env var)
        """
        self.telegram_token = telegram_token
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.telegram_api = f"https://api.telegram.org/bot{telegram_token}"

    def download_voice_file(self, file_id: str) -> Optional[str]:
        """
        Download voice file from Telegram

        Args:
            file_id: Telegram file_id from voice message

        Returns:
            Path to downloaded file or None if failed
        """
        try:
            # Get file path from Telegram
            response = requests.get(f"{self.telegram_api}/getFile", params={"file_id": file_id})
            response.raise_for_status()

            file_path = response.json()["result"]["file_path"]
            file_url = f"https://api.telegram.org/file/bot{self.telegram_token}/{file_path}"

            # Download file to temp directory
            temp_dir = tempfile.gettempdir()
            local_path = os.path.join(temp_dir, f"voice_{file_id}.ogg")

            file_response = requests.get(file_url)
            file_response.raise_for_status()

            with open(local_path, 'wb') as f:
                f.write(file_response.content)

            logger.info(f"Downloaded voice file to {local_path}")
            return local_path

        except Exception as e:
            logger.error(f"Error downloading voice file: {e}")
            return None

    def transcribe_with_openai_whisper(self, audio_file_path: str) -> Optional[str]:
        """
        Transcribe audio using OpenAI Whisper API

        Args:
            audio_file_path: Path to audio file

        Returns:
            Transcribed text or None if failed
        """
        if not self.openai_api_key:
            logger.error("OpenAI API key not configured")
            return None

        try:
            # OpenAI Whisper API endpoint
            url = "https://api.openai.com/v1/audio/transcriptions"

            headers = {
                "Authorization": f"Bearer {self.openai_api_key}"
            }

            with open(audio_file_path, 'rb') as audio_file:
                files = {
                    'file': audio_file,
                    'model': (None, 'whisper-1'),
                }

                response = requests.post(url, headers=headers, files=files)
                response.raise_for_status()

                result = response.json()
                transcribed_text = result.get('text', '')

                logger.info(f"Transcription successful: {transcribed_text[:50]}...")
                return transcribed_text.strip()

        except Exception as e:
            logger.error(f"Error transcribing with OpenAI Whisper: {e}")
            return None

    def transcribe_with_local_whisper(self, audio_file_path: str) -> Optional[str]:
        """
        Transcribe audio using local Whisper model (fallback)
        Requires: pip install openai-whisper

        Args:
            audio_file_path: Path to audio file

        Returns:
            Transcribed text or None if failed
        """
        try:
            import whisper

            # Load base model (good balance of speed and accuracy)
            model = whisper.load_model("base")

            # Transcribe
            result = model.transcribe(audio_file_path)
            transcribed_text = result["text"]

            logger.info(f"Local transcription successful: {transcribed_text[:50]}...")
            return transcribed_text.strip()

        except ImportError:
            logger.warning("Local whisper not installed. Install with: pip install openai-whisper")
            return None
        except Exception as e:
            logger.error(f"Error transcribing with local Whisper: {e}")
            return None

    def transcribe(self, audio_file_path: str, prefer_local: bool = False) -> Optional[str]:
        """
        Transcribe audio file using available method

        Args:
            audio_file_path: Path to audio file
            prefer_local: Try local Whisper first (default: use OpenAI API first)

        Returns:
            Transcribed text or None if all methods failed
        """
        if prefer_local:
            # Try local first, then OpenAI
            text = self.transcribe_with_local_whisper(audio_file_path)
            if text:
                return text
            return self.transcribe_with_openai_whisper(audio_file_path)
        else:
            # Try OpenAI first, then local
            text = self.transcribe_with_openai_whisper(audio_file_path)
            if text:
                return text
            return self.transcribe_with_local_whisper(audio_file_path)

    def process_voice_message(self, file_id: str, prefer_local: bool = False) -> Tuple[Optional[str], Optional[str]]:
        """
        Download and transcribe voice message

        Args:
            file_id: Telegram file_id from voice message
            prefer_local: Prefer local Whisper over OpenAI API

        Returns:
            Tuple of (transcribed_text, error_message)
        """
        # Download voice file
        audio_path = self.download_voice_file(file_id)
        if not audio_path:
            return None, "Failed to download voice file"

        try:
            # Transcribe
            text = self.transcribe(audio_path, prefer_local=prefer_local)

            if not text:
                return None, "Transcription failed - no API key or local model available"

            return text, None

        finally:
            # Clean up temp file
            try:
                if audio_path and os.path.exists(audio_path):
                    os.remove(audio_path)
                    logger.debug(f"Cleaned up temp file: {audio_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp file: {e}")

    @staticmethod
    def format_voice_prompt(transcribed_text: str) -> str:
        """
        Format transcribed text as a prompt for Claude
        Adds context that this was a voice message

        Args:
            transcribed_text: The transcribed voice message

        Returns:
            Formatted prompt for Claude
        """
        return f"[Voice message] {transcribed_text}"
