#!/bin/bash
# Quick test script to verify dashboard visualization

echo "=========================================="
echo "Dashboard Visualization Test"
echo "=========================================="
echo ""
echo "Step 1: Checking dashboard..."
curl -s http://localhost:5001/api/health > /dev/null && echo "✅ Dashboard is running" || echo "❌ Dashboard not running"
echo ""
echo "Step 2: Testing API endpoints..."
echo "  Risk Score:"
curl -s http://localhost:5001/api/predict-failure-risk | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"    Risk: {d.get('risk_score', 0)*100:.2f}%\" if 'error' not in d else f\"    Error: {d.get('error')}\")" 2>/dev/null
echo ""
echo "Step 3: Ready to demo!"
echo ""
echo "📋 Instructions:"
echo "  1. Open: http://localhost:5001"
echo "  2. Click: Predictive Maintenance tab"
echo "  3. Run: python3 continuous_demo.py"
echo "  4. Watch the dashboard update!"
echo ""
