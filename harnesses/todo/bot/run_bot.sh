#!/bin/bash

# Determine script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load environment variables from .env file
if [ -f "$SCRIPT_DIR/.env" ]; then
    export $(grep -v '^\s*#' "$SCRIPT_DIR/.env" | grep -v '^\s*$' | xargs)
fi

# Set PATH - include common locations for claude CLI
export PATH="$HOME/.local/bin:$HOME/.npm-global/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

# Change to home directory so Claude CLI has full access
cd "$HOME"

# Run the bot from navi directory
/usr/bin/python3 -u "$SCRIPT_DIR/telegram_bot.py"
