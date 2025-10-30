#!/bin/bash
# Healing-bot: Simple Unix Launcher
# This script provides an easy way to start the healing-bot system

echo ""
echo "========================================"
echo "   🛡️  HEALING-BOT SYSTEM LAUNCHER  🛡️"
echo "========================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "❌ ERROR: Python is not installed or not in PATH"
        echo "Please install Python 3.8+ and try again"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ ERROR: Python 3.8+ is required, found $PYTHON_VERSION"
    exit 1
fi

# Check if the main script exists
if [ ! -f "run-healing-bot.py" ]; then
    echo "❌ ERROR: run-healing-bot.py not found"
    echo "Please run this script from the healing-bot project directory"
    exit 1
fi

echo "🚀 Starting Healing-bot System..."
echo ""

# Make the script executable
chmod +x run-healing-bot.py

# Run the main launcher script
$PYTHON_CMD run-healing-bot.py "$@"

# If we get here, the script has finished
echo ""
echo "🛑 Healing-bot has stopped"
