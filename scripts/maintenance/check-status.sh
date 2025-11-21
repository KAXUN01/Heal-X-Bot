#!/bin/bash
# Service Status Checker for Healing-Bot
# Quickly check the status of all services

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PID_DIR="$SCRIPT_DIR/.pids"
STATUS_FILE="$SCRIPT_DIR/.service_status.json"

# Service definitions
declare -A SERVICES
SERVICES[model]="DDoS Model API|8080|http://localhost:8080/health"
SERVICES[network-analyzer]="Network Analyzer|8000|http://localhost:8000/health"
SERVICES[dashboard]="ML Dashboard|3001|http://localhost:3001/"
SERVICES[incident-bot]="Incident Bot|8001|http://localhost:8001/health"
SERVICES[monitoring-server]="Monitoring Server|5000|http://localhost:5000/health"
SERVICES[healing-dashboard]="Healing Dashboard API|5001|http://localhost:5001/api/health"

check_service() {
    local service=$1
    IFS='|' read -r name port health_url <<< "${SERVICES[$service]}"
    local pid_file="$PID_DIR/${service}.pid"
    
    if [ ! -f "$pid_file" ]; then
        echo -e "${RED}❌${NC} $name: ${RED}Not running${NC}"
        return 1
    fi
    
    local pid=$(cat "$pid_file" 2>/dev/null || echo "0")
    
    if [ "$pid" -eq 0 ] || ! kill -0 "$pid" 2>/dev/null; then
        echo -e "${RED}❌${NC} $name: ${RED}Crashed (PID: $pid)${NC}"
        return 1
    fi
    
    # Check health
    local response_code
    response_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 2 "$health_url" 2>/dev/null || echo "000")
    
    if [ "$response_code" = "200" ]; then
        echo -e "${GREEN}✅${NC} $name: ${GREEN}Running${NC} (PID: $pid, Port: $port)"
        return 0
    elif [ "$response_code" = "000" ]; then
        echo -e "${YELLOW}⚠️${NC} $name: ${YELLOW}Running but health check failed${NC} (PID: $pid, Port: $port)"
        return 0
    else
        echo -e "${YELLOW}⚠️${NC} $name: ${YELLOW}Running but unhealthy${NC} (PID: $pid, Port: $port, HTTP: $response_code)"
        return 0
    fi
}

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              🛡️  HEALING-BOT SERVICE STATUS  🛡️              ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

for service in "${!SERVICES[@]}"; do
    check_service "$service"
done

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    📊 ADDITIONAL INFO                         ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check Fluent Bit
if command -v docker >/dev/null 2>&1 && docker ps 2>/dev/null | grep -q "fluent-bit"; then
    echo -e "${GREEN}✅${NC} Fluent Bit: ${GREEN}Running in Docker${NC}"
else
    echo -e "${YELLOW}⚠️${NC} Fluent Bit: ${YELLOW}Not running${NC}"
fi

# Show status file if exists
if [ -f "$STATUS_FILE" ]; then
    echo ""
    echo -e "${CYAN}Status file:${NC} $STATUS_FILE"
    cat "$STATUS_FILE" | python3 -m json.tool 2>/dev/null || cat "$STATUS_FILE"
fi

echo ""

