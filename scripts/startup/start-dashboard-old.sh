#!/bin/bash
# Simple script to start the Healing Dashboard and essential services

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         🛡️  Starting Healing Dashboard 🛡️                   ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if services are already running
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Start Monitoring Server (required for dashboard)
if check_port 5000; then
    echo -e "${GREEN}✅ Monitoring Server already running on port 5000${NC}"
else
    echo -e "${YELLOW}📈 Starting Monitoring Server...${NC}"
    cd monitoring/server
    nohup python3 -u app.py > ../../logs/Monitoring\ Server.log 2>&1 &
    MONITORING_PID=$!
    cd "$SCRIPT_DIR"
    echo $MONITORING_PID > .pids/monitoring-server.pid
    echo -e "${GREEN}✅ Monitoring Server started (PID: $MONITORING_PID)${NC}"
    sleep 3
fi

# Start Healing Dashboard API
if check_port 5001; then
    echo -e "${GREEN}✅ Healing Dashboard API already running on port 5001${NC}"
else
    echo -e "${YELLOW}🛡️  Starting Healing Dashboard API...${NC}"
    cd monitoring/server
    nohup python3 -u healing_dashboard_api.py > ../../logs/Healing\ Dashboard\ API.log 2>&1 &
    DASHBOARD_PID=$!
    cd "$SCRIPT_DIR"
    echo $DASHBOARD_PID > .pids/healing-dashboard.pid
    echo -e "${GREEN}✅ Healing Dashboard API started (PID: $DASHBOARD_PID)${NC}"
    
    # Wait for dashboard to be ready
    echo -e "${YELLOW}⏳ Waiting for dashboard to initialize...${NC}"
    for i in {1..20}; do
        sleep 1
        if curl -s http://localhost:5001/api/health >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Dashboard is ready!${NC}"
            break
        fi
        if [ $i -eq 20 ]; then
            echo -e "${YELLOW}⚠️  Dashboard may still be initializing...${NC}"
        fi
    done
fi

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    🌐 ACCESS POINTS                          ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}🛡️  Healing Dashboard:${NC}      http://localhost:5001"
echo -e "${GREEN}📈 Monitoring Server:${NC}       http://localhost:5000"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop services${NC}"
echo ""

# Keep script running
trap "echo ''; echo -e '${YELLOW}Stopping services...${NC}'; pkill -P $$ 2>/dev/null || true; exit" INT TERM

# Wait for interrupt
while true; do
    sleep 1
done

