#!/bin/bash
# Check status of all Heal-X-Bot services

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"
cd "$PROJECT_ROOT"

# Use the main start.sh script's status command
"$PROJECT_ROOT/start.sh" status

