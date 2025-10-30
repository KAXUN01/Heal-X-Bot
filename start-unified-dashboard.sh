#!/bin/bash
#
# Unified Healing Bot Dashboard Launcher
# Launches the combined ML Monitoring + System Healing Dashboard
#

echo "🛡️  Starting Unified Healing Bot Dashboard..."
echo "=========================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Python 3 found"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."

pip3 install -q -r monitoring/dashboard/requirements.txt
pip3 install -q -r monitoring/server/healing_requirements.txt 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Dependencies installed"
else
    echo -e "${YELLOW}⚠${NC}  Some dependencies may need manual installation"
fi

# Check permissions
echo ""
echo "🔐 Checking permissions..."

if sudo -n true 2>/dev/null; then 
    echo -e "${GREEN}✓${NC} Sudo access available"
else
    echo -e "${YELLOW}⚠${NC}  Some features require sudo access"
fi

# Set port
PORT=${DASHBOARD_PORT:-3001}

echo ""
echo "🚀 Launching unified dashboard..."
echo "=========================================="
echo -e "   ML Monitoring: ${BLUE}http://localhost:$PORT${NC}"
echo -e "   Healing Dashboard: ${BLUE}http://localhost:$PORT/static/healing-dashboard.html${NC}"
echo ""
echo "   Features:"
echo "   • 📊 ML Model Performance Metrics"
echo "   • 🎯 DDoS Attack Detection"
echo "   • 🚫 IP Blocking Management"  
echo "   • ⚙️  Service Auto-Restart"
echo "   • 🔍 Resource Hog Detection"
echo "   • 🔐 SSH Intrusion Detection"
echo "   • 🧹 Automated Disk Cleanup"
echo "   • 🔔 Discord Alerts"
echo "   • 🤖 AI Log Analysis"
echo "   • ⚡ CLI Terminal"
echo ""
echo "Press Ctrl+C to stop"
echo "=========================================="
echo ""

# Start the dashboard
cd monitoring/dashboard
python3 -m uvicorn unified_app:app --host 0.0.0.0 --port $PORT --reload 2>&1 | tee ../logs/unified_dashboard.log

trap 'echo -e "\n${YELLOW}Shutting down...${NC}"; exit 0' SIGINT SIGTERM

echo -e "${GREEN}✓${NC} Dashboard stopped"

