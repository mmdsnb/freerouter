#!/bin/bash
# FreeLLM - Update and Restart Script
# This script fetches new free LLM services and restarts the litellm service

set -e

echo "======================================================================"
echo "FreeLLM Update & Restart"
echo "======================================================================"

# Change to project root
cd "$(dirname "$0")/.."

# Fetch new services and generate config
echo "→ Fetching free LLM services..."
python scripts/fetch.py

if [ $? -ne 0 ]; then
    echo "✗ Failed to fetch services!"
    exit 1
fi

echo "✓ Config updated successfully!"

# Check if running in Docker
if [ -f /.dockerenv ]; then
    echo "→ Running in Docker, restarting service..."
    # In Docker, just restart the Python process
    pkill -f "litellm" || true
    sleep 2
    python scripts/start.py &
else
    # Check if using docker-compose
    if command -v docker-compose &> /dev/null && [ -f docker-compose.yml ]; then
        echo "→ Restarting Docker Compose service..."
        docker-compose restart
    else
        echo "→ Restarting local service..."
        # Kill existing litellm process
        pkill -f "litellm" || true
        sleep 2
        # Start new service in background
        python scripts/start.py &
        echo "✓ Service restarted (PID: $!)"
    fi
fi

echo "======================================================================"
echo "✓ FreeLLM service updated and restarted!"
echo "======================================================================"
