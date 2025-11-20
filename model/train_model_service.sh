#!/bin/bash
"""
Systemd Service Script for Automated Model Training

This script can be used as a systemd service to periodically retrain the model.
"""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment if it exists
if [ -d "../venv" ]; then
    source ../venv/bin/activate
fi

# Run automated retraining
python3 automated_retraining.py "$@"

exit_code=$?

# Deactivate virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi

exit $exit_code

