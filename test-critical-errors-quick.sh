#!/bin/bash
#
# Quick Critical Errors Test Script
# Faster version that generates errors and checks immediately
#

set -e

echo "============================================================"
echo "🔴 QUICK CRITICAL ERRORS TEST"
echo "============================================================"
echo ""

API_URL="http://localhost:5001/api/critical-services/issues"
TIMESTAMP=$(date -Is)

# Check API
if ! curl -s "$API_URL" > /dev/null 2>&1; then
    echo "❌ Error: Cannot connect to API at $API_URL"
    echo "   Make sure the dashboard server is running on port 5001"
    exit 1
fi

echo "✅ API is accessible"
echo ""

# Get baseline
echo "📊 Baseline issues:"
baseline=$(curl -s "$API_URL" | grep -o '"count":[0-9]*' | grep -o '[0-9]*' | head -1 || echo "0")
echo "   Count: $baseline"
echo ""

# Generate CRITICAL errors
echo "📝 Generating CRITICAL errors..."
echo ""

for i in {1..5}; do
    logger -p 2 -t "nginx" "CRITICAL: Quick test error #$i at $TIMESTAMP - Nginx service failure test"
    logger -p 2 -t "docker" "CRITICAL: Quick test error #$i at $TIMESTAMP - Docker daemon failure test"
    logger -p 2 -t "test-service" "CRITICAL: Quick test error #$i at $TIMESTAMP - Generic service failure"
done

if command -v systemd-cat &> /dev/null; then
    echo "CRITICAL: System-wide quick test error" | systemd-cat -t "test-system" -p "crit"
fi

echo "✅ Generated 15+ CRITICAL logs"
echo ""

# Wait for collection
echo "⏳ Waiting 15 seconds for monitor to collect..."
sleep 15

# Check results
echo ""
echo "📊 Results:"
final=$(curl -s "$API_URL" | grep -o '"count":[0-9]*' | grep -o '[0-9]*' | head -1 || echo "0")
critical=$(curl -s "$API_URL" | grep -o '"severity":"CRITICAL"' | wc -l || echo "0")

echo "   Baseline: $baseline"
echo "   Final: $final"
echo "   CRITICAL: $critical"
echo ""

if [ "$final" -gt "$baseline" ]; then
    echo "✅ SUCCESS: New errors detected!"
    echo ""
    echo "Check dashboard: http://localhost:5001"
    echo "Scroll to 'Critical Errors Only' section"
else
    echo "⚠️  No new errors detected (may need more time)"
    echo "   Check dashboard manually"
fi

echo ""

