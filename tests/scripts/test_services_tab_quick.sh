#!/bin/bash
# Quick test script for services tab feature
# This is a simple bash version for quick verification

BASE_URL="${BASE_URL:-http://localhost:5001}"
API_ENDPOINT="${BASE_URL}/api/services"

echo "=========================================="
echo "  Services Tab Feature - Quick Test"
echo "=========================================="
echo ""
echo "Testing: $API_ENDPOINT"
echo ""

# Test 1: Check if API is accessible
echo "1. Testing API accessibility..."
if curl -s -f "$API_ENDPOINT" > /dev/null 2>&1; then
    echo "   ✅ API is accessible"
else
    echo "   ❌ API is not accessible"
    echo "   Make sure the healing dashboard API is running on port 5001"
    exit 1
fi

# Test 2: Get services and check response
echo ""
echo "2. Fetching services from API..."
RESPONSE=$(curl -s "$API_ENDPOINT")
SERVICE_COUNT=$(echo "$RESPONSE" | jq '.services | length' 2>/dev/null || echo "0")

if [ "$SERVICE_COUNT" = "null" ] || [ -z "$SERVICE_COUNT" ]; then
    echo "   ❌ Invalid response format"
    echo "   Response: $RESPONSE"
    exit 1
fi

echo "   ✅ API returned $SERVICE_COUNT services"

# Test 3: Display services
echo ""
echo "3. Services returned by API:"
if [ "$SERVICE_COUNT" -eq 0 ]; then
    echo "   ✅ No services returned (all services are running)"
else
    echo "$RESPONSE" | jq -r '.services[] | "   🔴 \(.name): \(.status)"'
fi

# Test 4: Check actual service statuses
echo ""
echo "4. Actual service statuses:"
SERVICES=("nginx" "mysql" "ssh" "docker" "postgresql")
for service in "${SERVICES[@]}"; do
    if systemctl is-active --quiet "$service" 2>/dev/null; then
        echo "   🟢 $service: Running"
    else
        echo "   🔴 $service: Stopped"
    fi
done

# Test 5: Verify filtering
echo ""
echo "5. Verifying filtering logic..."
RUNNING_SERVICES=$(for service in "${SERVICES[@]}"; do
    if systemctl is-active --quiet "$service" 2>/dev/null; then
        echo "$service"
    fi
done)

API_SERVICES=$(echo "$RESPONSE" | jq -r '.services[].name' 2>/dev/null)

# Check if any running services are in the API response
VIOLATION=""
while IFS= read -r running_service; do
    if echo "$API_SERVICES" | grep -q "^${running_service}$"; then
        VIOLATION="$VIOLATION $running_service"
    fi
done <<< "$RUNNING_SERVICES"

if [ -n "$VIOLATION" ]; then
    echo "   ❌ ERROR: Running services found in API response:$VIOLATION"
    exit 1
else
    echo "   ✅ All running services correctly filtered out"
fi

echo ""
echo "=========================================="
echo "  ✅ All quick tests passed!"
echo "=========================================="

