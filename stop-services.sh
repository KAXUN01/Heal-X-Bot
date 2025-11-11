#!/bin/bash
# Stop all Healing-Bot services gracefully

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PID_DIR="$SCRIPT_DIR/.pids"

declare -A SERVICES
SERVICES[model]="DDoS Model API"
SERVICES[network-analyzer]="Network Analyzer"
SERVICES[dashboard]="ML Dashboard"
SERVICES[incident-bot]="Incident Bot"
SERVICES[monitoring-server]="Monitoring Server"
SERVICES[healing-dashboard]="Healing Dashboard API"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              🛑 STOPPING HEALING-BOT SERVICES  🛑             ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

stop_service() {
    local service=$1
    local name="${SERVICES[$service]}"
    local pid_file="$PID_DIR/${service}.pid"
    
    if [ ! -f "$pid_file" ]; then
        echo -e "${YELLOW}⚠️${NC} $name: Not running"
        return 0
    fi
    
    local pid=$(cat "$pid_file" 2>/dev/null || echo "0")
    
    if [ "$pid" -eq 0 ] || ! kill -0 "$pid" 2>/dev/null; then
        echo -e "${YELLOW}⚠️${NC} $name: Already stopped"
        rm -f "$pid_file"
        return 0
    fi
    
    echo -e "${YELLOW}🛑${NC} Stopping $name (PID: $pid)..."
    kill "$pid" 2>/dev/null || true
    sleep 2
    
    if kill -0 "$pid" 2>/dev/null; then
        echo -e "${RED}⚠️${NC} Force killing $name..."
        kill -9 "$pid" 2>/dev/null || true
    fi
    
    rm -f "$pid_file"
    echo -e "${GREEN}✅${NC} $name: Stopped"
}

# Stop all services
for service in "${!SERVICES[@]}"; do
    stop_service "$service"
done

# Stop Fluent Bit
echo ""
if command -v docker >/dev/null 2>&1; then
    if docker ps 2>/dev/null | grep -q "fluent-bit"; then
        echo -e "${YELLOW}🛑${NC} Stopping Fluent Bit..."
        if docker compose version >/dev/null 2>&1; then
            docker compose -f config/docker-compose-fluent-bit.yml down 2>/dev/null || true
        elif command -v docker-compose >/dev/null 2>&1; then
            docker-compose -f config/docker-compose-fluent-bit.yml down 2>/dev/null || true
        else
            docker stop fluent-bit 2>/dev/null || true
        fi
        echo -e "${GREEN}✅${NC} Fluent Bit: Stopped"
    fi
fi

# Cleanup PID directory
rm -rf "$PID_DIR"

echo ""
echo -e "${GREEN}✅ All services stopped${NC}"
echo ""

