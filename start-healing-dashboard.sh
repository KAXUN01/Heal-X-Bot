#!/bin/bash
#
# Healing Bot Dashboard Launcher
# Launch the comprehensive web-based monitoring dashboard
#

echo "🛡️  Starting Healing Bot Dashboard..."
echo "======================================"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Python 3 found"

# Check/Install dependencies
echo ""
echo "📦 Checking dependencies..."

if [ ! -f "monitoring/server/healing_requirements.txt" ]; then
    echo -e "${RED}❌ Requirements file not found${NC}"
    exit 1
fi

# Install dependencies
pip3 install -q -r monitoring/server/healing_requirements.txt

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Dependencies installed"
else
    echo -e "${YELLOW}⚠${NC}  Some dependencies may need manual installation"
fi

# Check sudo access
echo ""
echo "🔐 Checking permissions..."

if sudo -n true 2>/dev/null; then 
    echo -e "${GREEN}✓${NC} Sudo access available"
else
    echo -e "${YELLOW}⚠${NC}  Some features require sudo access"
    echo "   Configure sudoers for full functionality"
fi

# Check .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠${NC}  No .env file found"
    if [ -f "config/env.template" ]; then
        echo "   Creating .env from template..."
        cp config/env.template .env
        echo -e "${GREEN}✓${NC} Created .env file - please configure Discord webhook"
    fi
fi

# Set default port
PORT=${HEALING_DASHBOARD_PORT:-5001}

echo ""
echo "🚀 Launching dashboard..."
echo "======================================"
echo -e "   URL: ${BLUE}http://localhost:$PORT${NC}"
echo "   Logs: monitoring/server/healing_dashboard.log"
echo ""
echo "Press Ctrl+C to stop"
echo "======================================"
echo ""

# Start the dashboard
python3 monitoring/server/healing_dashboard_api.py 2>&1 | tee monitoring/server/healing_dashboard.log

# Cleanup on exit
trap 'echo -e "\n${YELLOW}Shutting down dashboard...${NC}"; exit 0' SIGINT SIGTERM

echo -e "${GREEN}✓${NC} Dashboard stopped"

