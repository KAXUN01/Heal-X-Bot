#!/bin/bash
# Simple script to start the Healing Dashboard

cd "$(dirname "$0")/monitoring/server"

echo "Starting Healing Dashboard on port 5001..."
echo "Press Ctrl+C to stop"

python3 -m uvicorn healing_dashboard_api:app --host 0.0.0.0 --port 5001

