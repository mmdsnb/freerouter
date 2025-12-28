#!/bin/bash
set -e

# Docker entrypoint for FreeRouter

CONFIG_DIR="/root/.config/freerouter"
PROVIDER_CONFIG="$CONFIG_DIR/providers.yaml"
PID_FILE="$CONFIG_DIR/freerouter.pid"

# Check if providers.yaml exists
if [ ! -f "$PROVIDER_CONFIG" ]; then
    echo "ERROR: $PROVIDER_CONFIG not found!"
    echo "Please mount your config directory with providers.yaml"
    echo "Example: docker run -v ./config:/root/.config/freerouter ..."
    exit 1
fi

# Clean up stale PID file from previous container
if [ -f "$PID_FILE" ]; then
    echo "Cleaning up stale PID file from previous run..."
    rm -f "$PID_FILE"
fi

echo "Starting FreeRouter..."

# Start freerouter in background
freerouter start

# Wait for service to be ready
sleep 3

# Follow logs in foreground (keeps container running)
exec freerouter logs --requests
