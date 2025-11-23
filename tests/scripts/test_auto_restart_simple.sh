#!/bin/bash
# Simple test script for auto-restart feature
# Stops a service and checks if it gets automatically restarted

SERVICE="${1:-nginx}"  # Default to nginx if not specified
WAIT_TIME="${2:-30}"    # Default wait time 30 seconds
CHECK_INTERVAL=2

echo "=========================================="
echo "  Auto-Restart Feature Test"
echo "=========================================="
echo ""
echo "Service to test: $SERVICE"
echo "Wait time: ${WAIT_TIME}s"
echo ""

# Check if service exists
if ! systemctl list-unit-files | grep -q "^${SERVICE}.service"; then
    echo "❌ Service $SERVICE not found"
    exit 1
fi

# Check initial status
echo "Step 1: Checking initial status..."
if systemctl is-active --quiet "$SERVICE"; then
    echo "✅ Service $SERVICE is running"
else
    echo "⚠️  Service $SERVICE is not running. Starting it..."
    sudo systemctl start "$SERVICE"
    sleep 2
    if systemctl is-active --quiet "$SERVICE"; then
        echo "✅ Service $SERVICE started"
    else
        echo "❌ Failed to start $SERVICE"
        exit 1
    fi
fi

# Stop the service
echo ""
echo "Step 2: Stopping service $SERVICE..."
sudo systemctl stop "$SERVICE"
sleep 1

if systemctl is-active --quiet "$SERVICE"; then
    echo "❌ Service $SERVICE is still running after stop command"
    exit 1
fi
echo "✅ Service $SERVICE stopped successfully"

# Wait and check for auto-restart
echo ""
echo "Step 3: Waiting for automatic restart (checking every ${CHECK_INTERVAL}s)..."
echo "-----------------------------------"

START_TIME=$(date +%s)
ELAPSED=0
RESTARTED=false

while [ $ELAPSED -lt $WAIT_TIME ]; do
    if systemctl is-active --quiet "$SERVICE"; then
        RESTARTED=true
        break
    fi
    
    sleep $CHECK_INTERVAL
    ELAPSED=$(($(date +%s) - START_TIME))
    
    # Show progress every 5 seconds
    if [ $((ELAPSED % 5)) -eq 0 ] && [ $ELAPSED -gt 0 ]; then
        echo "  Still waiting... (${ELAPSED}s elapsed)"
    fi
done

# Results
echo ""
echo "=========================================="
if [ "$RESTARTED" = true ]; then
    echo "✅ SUCCESS: Service $SERVICE was automatically restarted!"
    echo "   Restart time: ${ELAPSED} seconds"
    echo "=========================================="
    exit 0
else
    echo "❌ FAILED: Service $SERVICE was NOT automatically restarted"
    echo "   Waited: ${ELAPSED} seconds"
    echo ""
    echo "Possible reasons:"
    echo "  - Auto-restart is disabled in configuration"
    echo "  - Monitoring loop is not running"
    echo "  - Service is not in the monitored services list"
    echo "=========================================="
    exit 1
fi

