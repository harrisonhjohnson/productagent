# Rich Text Formatting Guide for Navi

## Overview

Navi now automatically converts between Slack mrkdwn and Telegram markdown formats, ensuring professional communication parity across platforms.

## Formatting Conversions

### Slack → Telegram

When displaying Slack messages in Navi (e.g., thread previews), formatting is automatically converted:

| Slack mrkdwn | Telegram Markdown | Description |
|--------------|-------------------|-------------|
| `*bold*` | `**bold**` | Bold text |
| `_italic_` | `_italic_` | Italic text (same) |
| `~strike~` | `~strike~` | Strike-through (same) |
| `` `code` `` | `` `code` `` | Inline code (same) |
| ` ```code``` ` | ` ```code``` ` | Code block (same) |
| `<url\|text>` | `[text](url)` | Link with label |
| `<url>` | `url` | Bare URL |
| `<@U123>` | `@user` | User mention |
| `<#C123\|channel>` | `#channel` | Channel mention |
| `<!channel>` | `@channel` | Special mention |

### Telegram → Slack

For bidirectional updates (Batch 5), Navi will convert Telegram formatting back to Slack:

| Telegram Markdown | Slack mrkdwn | Description |
|-------------------|--------------|-------------|
| `**bold**` | `*bold*` | Bold text |
| `_italic_` | `_italic_` | Italic text (same) |
| `[text](url)` | `<url\|text>` | Link with label |

## Examples

### Example 1: Thread Preview with Formatting

**Original Slack message:**
```
*Important:* Check out <https://docs.example.com|the docs> for details about `api.call()`
```

**Displayed in Navi:**
```
**Important:** Check out [the docs](https://docs.example.com) for details about `api.call()`
```

### Example 2: Code Block

**Original Slack message:**
```
Here's the fix:
```python
def calculate_total(items):
    return sum(item.price for item in items)
```
```

**Displayed in Navi:**
```
Here's the fix:
```python
def calculate_total(items):
    return sum(item.price for item in items)
```
```

### Example 3: Mixed Formatting

**Original Slack message:**
```
Hey <@U123>! Can you review the PR in <#C456|engineering>?

Status: ~blocked~ → *in progress*

Details: <https://github.com/org/repo/pull/42|PR #42>
```

**Displayed in Navi:**
```
Hey @user! Can you review the PR in #engineering?

Status: ~blocked~ → **in progress**

Details: [PR #42](https://github.com/org/repo/pull/42)
```

## Where Formatting is Applied

### 1. Slack Thread Previews

When you run `/todo slack`, thread previews automatically show converted formatting:

```
📋 Your TODOs:

**Work > Active Projects**
1. ⬜️ Connect Canada ad data to dashboard
    📱 From Slack #marketing (3 hours ago)
    💬 **Urgent:** Can you pull the numbers? See [dashboard](https://tableau.com/view) (2 replies)
    🔗 https://app.slack.com/client/...
```

### 2. Future: Claude Responses (Optional)

In future updates, Claude's responses could also apply formatting for better readability.

### 3. Future: Bidirectional Updates (Batch 5)

When Navi posts completion updates back to Slack, formatting will be converted automatically.

## Code Examples

### Using the Formatter Directly

```python
from utils.formatting import MessageFormatter

formatter = MessageFormatter()

# Convert Slack to Telegram
slack_text = "*Bold* and <https://example.com|link>"
telegram_text = formatter.slack_to_telegram(slack_text)
# Result: "**Bold** and [link](https://example.com)"

# Convert Telegram to Slack
telegram_text = "**Bold** and [link](https://example.com)"
slack_text = formatter.telegram_to_slack(telegram_text)
# Result: "*Bold* and <https://example.com|link>"
```

### Convenience Functions

```python
from utils.formatting import format_slack_message_for_telegram

slack_message = "Check <#C123|general> for updates"
telegram_message = format_slack_message_for_telegram(slack_message)
# Result: "Check #general for updates"
```

## Special Cases

### Code Blocks are Protected

Code blocks are temporarily extracted before formatting conversions to prevent mangling code:

```python
# Slack message with code
"""
Here's the fix:
```
const x = *5*;  // asterisks preserved in code
```
"""

# Telegram output preserves code exactly:
"""
Here's the fix:
```
const x = *5*;  // asterisks preserved in code
```
"""
```

### Inline Code is Protected

Inline code segments are also protected:

```
Use the `api.call(*args)` method
# Asterisks in code preserved as-is
```

### Quote Blocks

Slack quote blocks (lines starting with `>`) are simplified for Telegram since Telegram doesn't support quote blocks natively:

**Slack:**
```
> This is a quote
> Multi-line quote
```

**Telegram:**
```
This is a quote
Multi-line quote
```

## Limitations

### Not Converted

Some Slack features don't have Telegram equivalents:

- **Attachments**: Not converted (displayed as separate messages if needed)
- **Reactions**: Not displayed in thread previews
- **Threads structure**: Flattened to preview + reply count
- **Mentions with names**: Simplified to `@user` (no name lookup)

### Telegram Limitations

Telegram markdown has some limitations:

- No nested formatting (can't have bold italic together)
- Limited code block language highlighting
- No quote blocks
- No spoiler tags (in standard markdown)

## Troubleshooting

### Formatting Not Applied

**Symptom:** Slack messages show with raw formatting like `*bold*` instead of `**bold**`

**Cause:** MessageFormatter not available

**Solution:** Check import in slack_context.py:
```bash
cd ~/tools/navi
python3 -c "from utils.formatting import MessageFormatter; print('✅ Formatter available')"
```

### Links Not Clickable

**Symptom:** Links show as `[text](url)` but aren't clickable in Telegram

**Cause:** Telegram needs HTML mode or proper markdown mode enabled

**Solution:** Ensure Telegram messages are sent with `parse_mode='Markdown'` parameter

### Code Blocks Not Formatted

**Symptom:** Code blocks show without syntax highlighting

**Cause:** Telegram's markdown doesn't support all language identifiers

**Solution:** This is a Telegram limitation. Code blocks will still be monospaced but may not have syntax colors.

## Future Enhancements

### Planned for Batch 5 (Bidirectional Updates)

When Navi posts to Slack:
- Convert Telegram formatting to Slack mrkdwn
- Handle emoji conversion
- Format completion messages professionally

### Potential Future Features

- Preserve user mention names (requires Slack API user lookup)
- Convert reactions to emoji text
- Better quote block handling
- Slack attachment preview extraction

## Technical Details

### Implementation

The formatting module (`utils/formatting.py`) uses regex-based conversion with:
- **Code protection**: Extract and restore code blocks/inline code
- **Order of operations**: Process mentions before links to avoid conflicts
- **Safe defaults**: Graceful degradation if conversions fail

### Performance

- **Fast**: Regex-based conversions are nearly instant
- **Memory efficient**: Processes text in-place
- **No API calls**: Pure text transformation

### Testing

Run formatting tests:
```bash
cd ~/tools/navi
python3 -c "
from utils.formatting import MessageFormatter
formatter = MessageFormatter()

# Test conversion
result = formatter.slack_to_telegram('*Bold* and <https://example.com|link>')
print(f'Result: {result}')
# Expected: **Bold** and [link](https://example.com)
"
```

## Best Practices

### When Creating Slack Messages

For best Navi display:
- Use standard Slack mrkdwn syntax
- Keep thread previews concise (first message is what's shown)
- Use meaningful link labels: `<url|description>` not `<url|link>`
- Avoid excessive formatting in critical information

### When Using Navi

- Formatting is automatic - no special commands needed
- `/todo slack` shows formatted previews
- Click deep links to see full thread with all formatting in Slack

## Summary

Rich text formatting ensures that whether you're viewing TODOs from Slack in Telegram or (in the future) posting updates from Telegram to Slack, the formatting always looks professional and readable. The conversion is automatic, fast, and handles all common formatting patterns used in professional communication.
