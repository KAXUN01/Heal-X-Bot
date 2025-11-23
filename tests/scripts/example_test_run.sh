#!/bin/bash
# Example test run script
# This demonstrates how to test the services tab feature

echo "=========================================="
echo "  Services Tab Feature - Example Test"
echo "=========================================="
echo ""

# Check if API is running
echo "Step 1: Checking if API is running..."
if curl -s http://localhost:5001/api/health > /dev/null 2>&1; then
    echo "✅ API is running"
else
    echo "❌ API is not running. Please start it first:"
    echo "   python monitoring/server/healing_dashboard_api.py"
    exit 1
fi

echo ""
echo "Step 2: Current service statuses..."
echo "-----------------------------------"
SERVICES=("nginx" "mysql" "ssh" "docker" "postgresql")
for service in "${SERVICES[@]}"; do
    if systemctl is-active --quiet "$service" 2>/dev/null; then
        echo "🟢 $service: Running"
    else
        echo "🔴 $service: Stopped"
    fi
done

echo ""
echo "Step 3: Testing API endpoint..."
echo "-----------------------------------"
echo "API Response:"
curl -s http://localhost:5001/api/services | jq '.'

echo ""
echo "Step 4: Verifying filtering..."
echo "-----------------------------------"
API_SERVICES=$(curl -s http://localhost:5001/api/services | jq -r '.services[].name' 2>/dev/null)
echo "Services returned by API:"
if [ -z "$API_SERVICES" ]; then
    echo "  (none - all services are running)"
else
    echo "$API_SERVICES" | while read -r service; do
        echo "  🔴 $service"
    done
fi

echo ""
echo "Step 5: Manual test - Stop a service"
echo "-----------------------------------"
echo "To test the feature manually:"
echo "  1. Stop a service: sudo systemctl stop nginx"
echo "  2. Check API: curl http://localhost:5001/api/services | jq ."
echo "  3. Verify nginx appears in the response"
echo "  4. Start it again: sudo systemctl start nginx"
echo "  5. Verify nginx is removed from the response"

echo ""
echo "=========================================="
echo "  Test Complete"
echo "=========================================="

