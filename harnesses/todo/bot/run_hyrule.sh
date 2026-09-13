#!/bin/bash
#
# HYRULE Server Startup Script
# Launches the FastAPI server and opens HYRULE in the browser
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "  HYRULE Server"
echo "========================================"
echo ""

# Check if uvicorn is available
if ! python3 -c "import uvicorn" 2>/dev/null; then
    echo "Installing required packages..."
    pip3 install fastapi uvicorn
fi

# Check if server is already running
if curl -s http://localhost:8765/api/health > /dev/null 2>&1; then
    echo "Server already running at http://localhost:8765"
    echo "Opening HYRULE in browser..."
    open "http://localhost:8765"
    exit 0
fi

echo "Starting HYRULE server on port 8765..."
echo ""

# Open browser after a short delay (in background)
(sleep 2 && open "http://localhost:8765") &

# Start the server
python3 hyrule_server.py
