#!/bin/bash
# Start Healing-bot services using virtual environment

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
PID_DIR="$PROJECT_ROOT/.pids"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║                    🛡️  HEALING-BOT LAUNCHER  🛡️                   ║"
echo "║              AI-Powered DDoS Detection & Auto-Healing              ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Create directories
mkdir -p "$LOG_DIR"
mkdir -p "$PID_DIR"

# Activate virtual environment
echo -e "${BLUE}🔧 Activating virtual environment...${NC}"
source "$PROJECT_ROOT/venv/bin/activate"

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
    echo -e "${GREEN}✅ Environment variables loaded${NC}"
fi

# Start services
echo -e "${BLUE}🚀 Starting services...${NC}"
echo ""

# Model Service
echo -e "${BLUE}▶ Starting DDoS Model API...${NC}"
cd "$PROJECT_ROOT/model"
nohup python main.py > "$LOG_DIR/model.log" 2>&1 &
echo $! > "$PID_DIR/model.pid"
echo -e "${GREEN}✅ Model started (Port 8080)${NC}"
sleep 2

# Network Analyzer
echo -e "${BLUE}▶ Starting Network Analyzer...${NC}"
cd "$PROJECT_ROOT/monitoring/server"
nohup python network_analyzer.py > "$LOG_DIR/network-analyzer.log" 2>&1 &
echo $! > "$PID_DIR/network-analyzer.pid"
echo -e "${GREEN}✅ Network Analyzer started (Port 8000)${NC}"
sleep 2

# Monitoring Server
echo -e "${BLUE}▶ Starting Monitoring Server...${NC}"
cd "$PROJECT_ROOT/monitoring/server"
nohup python app.py > "$LOG_DIR/monitoring-server.log" 2>&1 &
echo $! > "$PID_DIR/monitoring-server.pid"
echo -e "${GREEN}✅ Monitoring Server started (Port 5000)${NC}"
sleep 2

# Dashboard
echo -e "${BLUE}▶ Starting ML Dashboard...${NC}"
cd "$PROJECT_ROOT/monitoring/dashboard"
nohup python app.py > "$LOG_DIR/dashboard.log" 2>&1 &
echo $! > "$PID_DIR/dashboard.pid"
echo -e "${GREEN}✅ Dashboard started (Port 3001)${NC}"
sleep 2

# Incident Bot
echo -e "${BLUE}▶ Starting Incident Bot...${NC}"
cd "$PROJECT_ROOT/incident-bot"
nohup python main.py > "$LOG_DIR/incident-bot.log" 2>&1 &
echo $! > "$PID_DIR/incident-bot.pid"
echo -e "${GREEN}✅ Incident Bot started (Port 8001)${NC}"
sleep 2

echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                       🌐 Access Points                              ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${GREEN}📊 Dashboard:${NC}          http://localhost:3001"
echo -e "  ${GREEN}🤖 Model API:${NC}          http://localhost:8080"
echo -e "  ${GREEN}🔍 Network Analyzer:${NC}   http://localhost:8000"
echo -e "  ${GREEN}📈 Monitoring Server:${NC}  http://localhost:5000"
echo -e "  ${GREEN}🚨 Incident Bot:${NC}       http://localhost:8001"
echo ""
echo -e "  ${BLUE}📝 Logs:${NC}               $LOG_DIR/"
echo -e "  ${BLUE}🔧 PIDs:${NC}               $PID_DIR/"
echo ""
echo -e "${GREEN}✅ All services started successfully!${NC}"
echo -e "${BLUE}💡 Check status with: $0 --status${NC}"
echo -e "${BLUE}💡 Stop services with: $0 --stop${NC}"
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo -e "${BLUE}🛑 Stopping all services...${NC}"
    
    for pid_file in "$PID_DIR"/*.pid; do
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file")
            if kill -0 $pid 2>/dev/null; then
                kill $pid
            fi
            rm "$pid_file"
        fi
    done
    
    echo -e "${GREEN}✅ All services stopped${NC}"
    exit 0
}

# Check status
if [ "$1" == "--status" ]; then
    echo -e "${BLUE}📊 Service Status:${NC}"
    echo ""
    for pid_file in "$PID_DIR"/*.pid; do
        if [ -f "$pid_file" ]; then
            service_name=$(basename "$pid_file" .pid)
            pid=$(cat "$pid_file")
            if kill -0 $pid 2>/dev/null; then
                echo -e "  ${GREEN}✅ $service_name (PID: $pid)${NC}"
            else
                echo -e "  ${RED}❌ $service_name (dead)${NC}"
            fi
        fi
    done
    echo ""
    exit 0
fi

# Stop services
if [ "$1" == "--stop" ]; then
    cleanup
fi

# Keep running
trap cleanup SIGINT SIGTERM
echo -e "${BLUE}Press Ctrl+C to stop all services${NC}"
while true; do
    sleep 10
done

