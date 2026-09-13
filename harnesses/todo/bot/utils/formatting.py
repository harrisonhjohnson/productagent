"""
Formatting Utilities for Navi - Convert between Slack mrkdwn and Telegram markdown
"""
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class MessageFormatter:
    """
    Convert between Slack mrkdwn and Telegram markdown formats

    Slack mrkdwn reference: https://api.slack.com/reference/surfaces/formatting
    Telegram markdown reference: https://core.telegram.org/bots/api#markdown-style
    """

    @staticmethod
    def slack_to_telegram(text: str) -> str:
        """
        Convert Slack mrkdwn formatting to Telegram markdown

        Conversions:
        - *bold* → **bold**
        - _italic_ → _italic_ (same)
        - ~strike~ → ~strike~ (same)
        - `code` → `code` (same)
        - ```code block``` → ```code block``` (same)
        - <url|text> → [text](url)
        - <url> → url
        - <@U123> → @user
        - <#C123|channel> → #channel
        - > quote → (remove, not supported well in Telegram)

        Args:
            text: Slack-formatted text

        Returns:
            Telegram-formatted text
        """
        if not text:
            return text

        # Store code blocks temporarily to avoid processing them
        code_blocks = []
        def store_code_block(match):
            code_blocks.append(match.group(0))
            return f"__CODE_BLOCK_{len(code_blocks)-1}__"

        # Extract code blocks (triple backticks)
        text = re.sub(r'```[\s\S]*?```', store_code_block, text)

        # Store inline code temporarily
        inline_codes = []
        def store_inline_code(match):
            inline_codes.append(match.group(0))
            return f"__INLINE_CODE_{len(inline_codes)-1}__"

        text = re.sub(r'`[^`]+`', store_inline_code, text)

        # Convert Slack bold (*text*) to Telegram bold (**text**)
        # Need to be careful not to match emphasis or bullet points
        text = re.sub(r'(?<!\*)\*(?!\*)([^\*\n]+?)(?<!\*)\*(?!\*)', r'**\1**', text)

        # Italic stays the same: _text_
        # Strike stays the same: ~text~

        # Convert user mentions: <@U123> → @user (do this BEFORE general link conversion)
        text = re.sub(r'<@[A-Z0-9]+>', '@user', text)

        # Convert channel mentions: <#C123|channel-name> → #channel-name (do this BEFORE general link conversion)
        text = re.sub(r'<#[A-Z0-9]+\|([^>]+)>', r'#\1', text)

        # Convert Slack links: <url|text> → [text](url)
        text = re.sub(r'<([^|>]+)\|([^>]+)>', r'[\2](\1)', text)

        # Convert bare URLs: <url> → url
        text = re.sub(r'<(https?://[^>]+)>', r'\1', text)

        # Convert special mentions
        text = text.replace('<!channel>', '@channel')
        text = text.replace('<!here>', '@here')
        text = text.replace('<!everyone>', '@everyone')

        # Remove quote markers (>) as Telegram doesn't support them well
        # Just remove the leading > and space
        text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)

        # Restore inline code
        for i, code in enumerate(inline_codes):
            text = text.replace(f"__INLINE_CODE_{i}__", code)

        # Restore code blocks
        for i, block in enumerate(code_blocks):
            text = text.replace(f"__CODE_BLOCK_{i}__", block)

        return text

    @staticmethod
    def telegram_to_slack(text: str) -> str:
        """
        Convert Telegram markdown formatting to Slack mrkdwn

        Conversions:
        - **bold** → *bold*
        - _italic_ → _italic_ (same)
        - ~strike~ → ~strike~ (same)
        - `code` → `code` (same)
        - ```code block``` → ```code block``` (same)
        - [text](url) → <url|text>

        Args:
            text: Telegram-formatted text

        Returns:
            Slack-formatted text
        """
        if not text:
            return text

        # Store code blocks temporarily
        code_blocks = []
        def store_code_block(match):
            code_blocks.append(match.group(0))
            return f"__CODE_BLOCK_{len(code_blocks)-1}__"

        text = re.sub(r'```[\s\S]*?```', store_code_block, text)

        # Store inline code
        inline_codes = []
        def store_inline_code(match):
            inline_codes.append(match.group(0))
            return f"__INLINE_CODE_{len(inline_codes)-1}__"

        text = re.sub(r'`[^`]+`', store_inline_code, text)

        # Convert Telegram bold (**text**) to Slack bold (*text*)
        text = re.sub(r'\*\*([^\*]+?)\*\*', r'*\1*', text)

        # Italic stays the same: _text_
        # Strike stays the same: ~text~

        # Convert Telegram links: [text](url) → <url|text>
        text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<\2|\1>', text)

        # Restore inline code
        for i, code in enumerate(inline_codes):
            text = text.replace(f"__INLINE_CODE_{i}__", code)

        # Restore code blocks
        for i, block in enumerate(code_blocks):
            text = text.replace(f"__CODE_BLOCK_{i}__", block)

        return text

    @staticmethod
    def clean_for_telegram(text: str, preserve_formatting: bool = True) -> str:
        """
        Clean text for Telegram display

        Args:
            text: Raw text
            preserve_formatting: Keep markdown formatting (default True)

        Returns:
            Cleaned text safe for Telegram
        """
        if not text:
            return text

        # If not preserving formatting, escape special characters
        if not preserve_formatting:
            # Escape Telegram markdown special characters
            special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
            for char in special_chars:
                text = text.replace(char, f'\\{char}')

        # Remove excessive newlines (more than 2)
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Trim whitespace
        text = text.strip()

        return text

    @staticmethod
    def format_code_block(code: str, language: str = None) -> str:
        """
        Format code block for Telegram

        Args:
            code: Code content
            language: Programming language (optional)

        Returns:
            Formatted code block
        """
        if language:
            return f"```{language}\n{code}\n```"
        else:
            return f"```\n{code}\n```"

    @staticmethod
    def escape_markdown(text: str) -> str:
        """
        Escape markdown special characters for literal display

        Args:
            text: Text to escape

        Returns:
            Escaped text
        """
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, f'\\{char}')
        return text

    @staticmethod
    def format_list(items: list, ordered: bool = False) -> str:
        """
        Format a list for display

        Args:
            items: List items
            ordered: Use numbers (True) or bullets (False)

        Returns:
            Formatted list
        """
        if not items:
            return ""

        lines = []
        for i, item in enumerate(items, 1):
            if ordered:
                lines.append(f"{i}. {item}")
            else:
                lines.append(f"• {item}")

        return "\n".join(lines)

    @staticmethod
    def truncate_with_ellipsis(text: str, max_length: int = 4096) -> str:
        """
        Truncate text to fit Telegram's message limit

        Args:
            text: Text to truncate
            max_length: Maximum length (default 4096 for Telegram)

        Returns:
            Truncated text with ellipsis if needed
        """
        if len(text) <= max_length:
            return text

        # Try to truncate at a word boundary
        truncated = text[:max_length-3]
        last_space = truncated.rfind(' ')

        if last_space > max_length * 0.8:  # Only use word boundary if it's reasonably close
            truncated = truncated[:last_space]

        return truncated + "..."


def format_slack_message_for_telegram(slack_text: str) -> str:
    """
    Convenience function to format Slack message for Telegram

    Args:
        slack_text: Slack-formatted text

    Returns:
        Telegram-formatted text
    """
    formatter = MessageFormatter()
    return formatter.slack_to_telegram(slack_text)


def format_telegram_message_for_slack(telegram_text: str) -> str:
    """
    Convenience function to format Telegram message for Slack

    Args:
        telegram_text: Telegram-formatted text

    Returns:
        Slack-formatted text
    """
    formatter = MessageFormatter()
    return formatter.telegram_to_slack(telegram_text)
