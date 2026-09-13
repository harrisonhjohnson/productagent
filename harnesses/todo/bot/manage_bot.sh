#!/bin/bash

PLIST="$HOME/Library/LaunchAgents/com.navi.telegrambot.plist"
LOG="$HOME/tools/navi/bot.log"
ERROR_LOG="$HOME/tools/navi/bot.error.log"

case "$1" in
    start)
        echo "Starting Navi bot..."
        launchctl load "$PLIST"
        sleep 2
        launchctl list | grep navi
        ;;
    stop)
        echo "Stopping Navi bot..."
        launchctl unload "$PLIST"
        ;;
    restart)
        echo "Restarting Navi bot..."
        launchctl unload "$PLIST" 2>/dev/null
        launchctl load "$PLIST"
        sleep 2
        launchctl list | grep navi
        ;;
    status)
        echo "Checking Navi bot status..."
        launchctl list | grep navi
        echo ""
        ps aux | grep telegram_bot.py | grep -v grep
        ;;
    logs)
        echo "=== Bot Logs (last 50 lines) ==="
        tail -50 "$LOG"
        ;;
    errors)
        echo "=== Error Logs (last 50 lines) ==="
        tail -50 "$ERROR_LOG"
        ;;
    follow)
        echo "Following logs (Ctrl+C to stop)..."
        tail -f "$LOG"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|errors|follow}"
        exit 1
        ;;
esac
