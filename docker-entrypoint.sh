#!/bin/bash
set -e

# Docker entrypoint for FreeRouter
# Runs litellm in foreground mode

CONFIG_DIR="/root/.config/freerouter"
CONFIG_FILE="$CONFIG_DIR/config.yaml"

# Check if config exists, if not generate it
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Config not found, generating..."

    # Check if providers.yaml exists
    PROVIDER_CONFIG="$CONFIG_DIR/providers.yaml"
    if [ ! -f "$PROVIDER_CONFIG" ]; then
        echo "ERROR: $PROVIDER_CONFIG not found!"
        echo "Please mount your config directory with providers.yaml"
        echo "Example: docker run -v ./config:/root/.config/freerouter ..."
        exit 1
    fi

    # Generate config using freerouter fetch
    freerouter fetch
fi

# Get port and host from environment
LITELLM_PORT=${LITELLM_PORT:-4000}
LITELLM_HOST=${LITELLM_HOST:-0.0.0.0}

echo "=========================================="
echo "Starting FreeRouter (Docker Mode)"
echo "=========================================="
echo "Host: $LITELLM_HOST"
echo "Port: $LITELLM_PORT"
echo "Config: $CONFIG_FILE"
echo "=========================================="

# Run litellm in foreground (exec replaces shell process)
exec litellm \
    --config "$CONFIG_FILE" \
    --port "$LITELLM_PORT" \
    --host "$LITELLM_HOST"
