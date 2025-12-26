#!/bin/bash
# Test script for FreeRouter
# Run all tests with coverage report and timing information

set -e

echo "================================"
echo "Running FreeRouter Test Suite"
echo "================================"
echo ""

# Run pytest with coverage and durations
uv run pytest \
    --cov=freerouter \
    --cov-report=term-missing \
    --durations=0 \
    -v \
    "$@"

echo ""
echo "================================"
echo "Test Summary"
echo "================================"
echo "✓ All tests completed"
echo "See coverage report above"
