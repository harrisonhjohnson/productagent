# Voice Message Setup for Navi

## Overview

Navi now supports voice message transcription! Send a voice message via Telegram and it will be automatically transcribed and processed as text.

## Setup Options

You have two options for voice transcription:

### Option 1: OpenAI Whisper API (Recommended)

**Pros:**
- Fast and accurate
- No local installation needed
- Works on any machine

**Cons:**
- Requires OpenAI API key
- Small cost per transcription (a fraction of a cent per minute; see OpenAI pricing)

**Setup:**
1. Get an OpenAI API key from https://platform.openai.com/api-keys
2. Add to your environment:
   ```bash
   export OPENAI_API_KEY="sk-..."
   ```
3. Add to your `~/.zshrc` or `~/.bashrc` for persistence:
   ```bash
   echo 'export OPENAI_API_KEY="sk-..."' >> ~/.zshrc
   source ~/.zshrc
   ```

### Option 2: Local Whisper (Fallback)

**Pros:**
- Free
- No API key needed
- Works offline

**Cons:**
- Requires ~1-5GB model download
- Slower transcription
- Requires powerful CPU/GPU

**Setup:**
1. Install OpenAI Whisper:
   ```bash
   pip install openai-whisper
   ```
2. First transcription will download the model (~1GB for base model)

## How It Works

1. Send a voice message to Navi via Telegram
2. Navi downloads the audio file
3. Transcription happens via:
   - OpenAI API (if `OPENAI_API_KEY` is set)
   - Local Whisper (if installed)
4. Transcribed text is processed like a normal text message:
   - Can be a Claude query
   - Can be a TODO command ("add to my todo...")
   - Can be any natural language input

## Usage Examples

### Voice TODO Addition
🎤 "Add to my TODO list: review Q1 performance metrics"
→ ✅ Added to TODO.md

### Voice Claude Query
🎤 "What's the status of the Canada launch?"
→ Claude processes and responds

### Voice Commands
🎤 "Show my TODO list"
→ Displays TODOs

## Testing

To test if voice is working:
1. Restart the bot: `./manage_bot.sh restart`
2. Send a voice message saying "Hello Navi"
3. You should see:
   - "🎤 Transcribing voice message..."
   - Then Navi's response to "Hello Navi"

## Troubleshooting

**"Transcription failed: no API key or local model available"**
- Neither OpenAI API nor local Whisper is configured
- Set up one of the two options above

**"Voice messages not supported - voice handler not initialized"**
- Voice handler failed to initialize
- Check bot logs: `tail -f ~/tools/navi/bot.error.log`

**Slow transcription**
- Using local Whisper (no API key)
- Consider setting up OpenAI API key for faster transcription

## Cost Estimate (OpenAI API)

- Average voice message: 10-30 seconds
- Cost: a fraction of a cent per message
- 100 voice messages/day: single-digit dollars per month

## Privacy Note

- **OpenAI API**: Audio sent to OpenAI for transcription
- **Local Whisper**: Everything stays on your machine
- Choose based on your privacy preferences!
