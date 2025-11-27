#!/bin/bash
# Stop all Heal-X-Bot services

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/../.." && pwd )"
cd "$PROJECT_ROOT"

PID_DIR="$PROJECT_ROOT/.pids"

echo "Stopping all services..."

for pid_file in "$PID_DIR"/*.pid; do
    if [ -f "$pid_file" ]; then
        service=$(basename "$pid_file" .pid)
        pid=$(cat "$pid_file" 2>/dev/null || echo "0")
        if [ "$pid" -ne 0 ] && kill -0 "$pid" 2>/dev/null; then
            echo "Stopping $service (PID: $pid)..."
            kill "$pid" 2>/dev/null || true
        fi
        rm -f "$pid_file"
    fi
done

# Force kill any remaining processes
pkill -f "python3.*main.py" 2>/dev/null || true
pkill -f "python3.*app.py" 2>/dev/null || true
pkill -f "python3.*network_analyzer.py" 2>/dev/null || true
pkill -f "python3.*healing_dashboard_api.py" 2>/dev/null || true

sleep 2
echo "✅ All services stopped"
