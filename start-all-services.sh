#!/bin/bash
# Comprehensive startup script for all Heal-X-Bot services
# This script starts all services with proper error handling and dependency management

set -euo pipefail
IFS=$'\n\t'

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Configuration
LOG_DIR="$SCRIPT_DIR/logs"
PID_DIR="$SCRIPT_DIR/.pids"
VENV_DIR=".venv"
declare -a PIDS=()

# Create necessary directories
mkdir -p "$LOG_DIR" "$PID_DIR"

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Shutting down all services...${NC}"
    
    # Kill all background processes
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${YELLOW}   Stopping process $pid...${NC}"
            kill "$pid" 2>/dev/null || true
        fi
    done
    
    # Kill processes from PID files
    for pid_file in "$PID_DIR"/*.pid; do
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file" 2>/dev/null || echo "0")
            if [ "$pid" -ne 0 ] && kill -0 "$pid" 2>/dev/null; then
                kill "$pid" 2>/dev/null || true
            fi
            rm -f "$pid_file"
        fi
    done
    
    # Stop Fluent Bit if running
    if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
        if docker ps 2>/dev/null | grep -q "fluent-bit"; then
            echo -e "${YELLOW}   Stopping Fluent Bit container...${NC}"
            if docker compose version >/dev/null 2>&1; then
                docker compose -f config/docker-compose-fluent-bit.yml down 2>/dev/null || true
            elif command -v docker-compose >/dev/null 2>&1; then
                docker-compose -f config/docker-compose-fluent-bit.yml down 2>/dev/null || true
            fi
        fi
    fi
    
    sleep 2
    
    # Force kill if still running
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill -9 "$pid" 2>/dev/null || true
        fi
    done
    
    echo -e "${GREEN}✅ All services stopped${NC}"
    exit 0
}

# Set trap for cleanup
trap cleanup SIGINT SIGTERM EXIT

# Print banner
print_banner() {
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                    🛡️  HEAL-X-BOT  🛡️                        ║${NC}"
    echo -e "${BLUE}║                                                              ║${NC}"
    echo -e "${BLUE}║        AI-Powered DDoS Detection & IP Blocking System       ║${NC}"
    echo -e "${BLUE}║                                                              ║${NC}"
    echo -e "${BLUE}║              Complete Service Startup Script                 ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Check Python
check_python() {
    echo -e "${YELLOW}🔍 Checking Python version...${NC}"
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ ERROR: Python 3 is not installed${NC}"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
        echo -e "${RED}❌ ERROR: Python 3.8 or higher is required${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Python ${PYTHON_VERSION} detected${NC}"
}

# Setup virtual environment
setup_venv() {
    echo -e "${YELLOW}📦 Setting up virtual environment...${NC}"
    
    if [ ! -f "$VENV_DIR/bin/activate" ]; then
        echo -e "${YELLOW}   Creating virtual environment...${NC}"
        python3 -m venv "$VENV_DIR"
    fi
    
    source "$VENV_DIR/bin/activate"
    echo -e "${GREEN}✅ Virtual environment activated${NC}"
    
    # Install/upgrade pip
    echo -e "${YELLOW}   Upgrading pip...${NC}"
    python3 -m pip install --upgrade pip >/dev/null 2>&1
    
    # Install dependencies
    echo -e "${YELLOW}   Installing dependencies...${NC}"
    if [ -f "requirements.txt" ]; then
        python3 -m pip install -r requirements.txt -q
    fi
    
    # Install per-service requirements
    for req_file in "model/requirements.txt" "monitoring/server/requirements.txt" \
                    "monitoring/dashboard/requirements.txt" "incident-bot/requirements.txt"; do
        if [ -f "$req_file" ]; then
            python3 -m pip install -r "$req_file" -q
        fi
    done
    
    # Fix protobuf compatibility (critical for TensorFlow)
    echo -e "${YELLOW}   Fixing protobuf compatibility...${NC}"
    # Ensure protobuf is compatible with TensorFlow 2.20.0
    python3 -m pip install --force-reinstall "protobuf>=5.28.0,<6.0.0" --no-cache-dir -q 2>/dev/null || true
    python3 -m pip install --upgrade "numpy<2" googleapis-common-protos -q 2>/dev/null || true
    # Verify protobuf version
    PROTOBUF_VERSION=$(python3 -m pip show protobuf 2>/dev/null | grep Version | awk '{print $2}' || echo "unknown")
    echo -e "${CYAN}   Protobuf version: $PROTOBUF_VERSION${NC}"
    
    echo -e "${GREEN}✅ Dependencies installed${NC}"
}

# Check Docker
check_docker() {
    echo -e "${YELLOW}🔍 Checking Docker for Fluent Bit...${NC}"
    DOCKER_OK=1
    
    if ! command -v docker &> /dev/null; then
        echo -e "${YELLOW}⚠️  Docker is not installed (Fluent Bit will be skipped)${NC}"
        DOCKER_OK=0
    elif ! docker info >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Docker daemon is not accessible (Fluent Bit will be skipped)${NC}"
        DOCKER_OK=0
    fi
    
    if [ "$DOCKER_OK" -eq 1 ]; then
        if docker compose version >/dev/null 2>&1 || command -v docker-compose >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Docker and Docker Compose detected${NC}"
        else
            echo -e "${YELLOW}⚠️  Docker Compose not found (Fluent Bit will be skipped)${NC}"
            DOCKER_OK=0
        fi
    fi
    
    return $DOCKER_OK
}

# Start Fluent Bit
start_fluent_bit() {
    if check_docker; then
        echo -e "${YELLOW}🐳 Starting Fluent Bit...${NC}"
        cd config
        
        # Create network if it doesn't exist
        docker network create healing-network 2>/dev/null || true
        
        # Start Fluent Bit
        if docker compose version >/dev/null 2>&1; then
            docker compose -f docker-compose-fluent-bit.yml up -d 2>/dev/null || true
        elif command -v docker-compose >/dev/null 2>&1; then
            docker-compose -f docker-compose-fluent-bit.yml up -d 2>/dev/null || true
        fi
        
        cd "$SCRIPT_DIR"
        echo -e "${GREEN}✅ Fluent Bit started${NC}"
    else
        echo -e "${YELLOW}⏭️  Skipping Fluent Bit (Docker not available)${NC}"
    fi
}

# Start a service
start_service() {
    local service_name=$1
    local service_path=$2
    local script_name=$3
    local port=$4
    local env_vars="${5:-}"
    local pid_file="$PID_DIR/${service_name// /_}.pid"
    
    echo -e "${YELLOW}🚀 Starting $service_name...${NC}"
    
    # Check if already running
    if [ -f "$pid_file" ]; then
        local existing_pid=$(cat "$pid_file" 2>/dev/null || echo "0")
        if kill -0 "$existing_pid" 2>/dev/null; then
            echo -e "${GREEN}✅ $service_name is already running (PID: $existing_pid)${NC}"
            PIDS+=($existing_pid)
            return 0
        else
            rm -f "$pid_file"
        fi
    fi
    
    # Check if script exists
    if [ ! -f "$service_path/$script_name" ]; then
        echo -e "${RED}❌ ERROR: Script not found: $service_path/$script_name${NC}"
        return 1
    fi
    
    # Prepare environment
    export PYTHONUNBUFFERED=1
    if [ -n "$env_vars" ]; then
        eval "export $env_vars"
    fi
    
    # Start service in background
    cd "$service_path"
    nohup python3 -u "$script_name" >> "$LOG_DIR/${service_name}.log" 2>&1 &
    local pid=$!
    cd "$SCRIPT_DIR"
    
    # Save PID
    echo "$pid" > "$pid_file"
    PIDS+=($pid)
    
    # Wait and check if it started successfully
    sleep 3
    if kill -0 "$pid" 2>/dev/null; then
        echo -e "${GREEN}✅ $service_name started (PID: $pid, Port: $port)${NC}"
        return 0
    else
        echo -e "${RED}❌ $service_name failed to start - check $LOG_DIR/${service_name}.log${NC}"
        return 1
    fi
}

# Wait for service to be healthy
wait_for_service() {
    local service_name=$1
    local health_url=$2
    local max_attempts=30
    local attempt=0
    
    if [ -z "$health_url" ] || [ "$health_url" = "null" ]; then
        return 0
    fi
    
    echo -e "${CYAN}   Waiting for $service_name to be healthy...${NC}"
    while [ $attempt -lt $max_attempts ]; do
        if curl -s --max-time 2 "$health_url" >/dev/null 2>&1; then
            echo -e "${GREEN}   ✅ $service_name is healthy${NC}"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    
    echo -e "${YELLOW}   ⚠️  $service_name health check timeout (may still be starting)${NC}"
    return 1
}

# Main execution
main() {
    print_banner
    check_python
    setup_venv
    
    # Check for .env file
    if [ ! -f ".env" ] && [ -f "config/env.template" ]; then
        echo -e "${YELLOW}⚠️  .env file not found, creating from template...${NC}"
        cp config/env.template .env
        echo -e "${GREEN}✅ Created .env file - please configure your API keys${NC}"
    fi
    
    # Check project structure
    echo -e "${YELLOW}🔍 Checking project structure...${NC}"
    for dir in "monitoring/server" "model" "incident-bot" "config" "monitoring/dashboard"; do
        if [ ! -d "$dir" ]; then
            echo -e "${RED}❌ ERROR: Required directory not found: $dir${NC}"
            exit 1
        fi
    done
    echo -e "${GREEN}✅ Project structure verified${NC}"
    
    # Start Fluent Bit
    start_fluent_bit
    
    # Start all services
    echo ""
    echo -e "${GREEN}🚀 Starting all services...${NC}"
    echo ""
    
    # Start services
    start_service "DDoS Model API" "model" "main.py" "8080" "MODEL_PORT=8080"
    wait_for_service "DDoS Model API" "http://localhost:8080/health"
    
    start_service "Network Analyzer" "monitoring/server" "network_analyzer.py" "8000" "PORT=8000"
    wait_for_service "Network Analyzer" "http://localhost:8000/health"
    
    start_service "Incident Bot" "incident-bot" "main.py" "8001" "PORT=8001"
    wait_for_service "Incident Bot" "http://localhost:8001/health"
    
    start_service "Monitoring Server" "monitoring/server" "app.py" "5000"
    wait_for_service "Monitoring Server" "http://localhost:5000/health"
    
    # Start Healing Dashboard API with uvicorn
    echo -e "${YELLOW}🚀 Starting Healing Dashboard API...${NC}"
    export PYTHONUNBUFFERED=1
    export HEALING_DASHBOARD_PORT=5001
    cd monitoring/server
    nohup python3 -m uvicorn healing_dashboard_api:app --host 0.0.0.0 --port 5001 >> "$LOG_DIR/Healing Dashboard API.log" 2>&1 &
    healing_pid=$!
    cd "$SCRIPT_DIR"
    echo "$healing_pid" > "$PID_DIR/Healing_Dashboard_API.pid"
    PIDS+=($healing_pid)
    sleep 3
    if kill -0 "$healing_pid" 2>/dev/null; then
        echo -e "${GREEN}✅ Healing Dashboard API started (PID: $healing_pid, Port: 5001)${NC}"
    else
        echo -e "${RED}❌ Healing Dashboard API failed to start${NC}"
    fi
    wait_for_service "Healing Dashboard API" "http://localhost:5001/"
    
    # Print access information
    echo ""
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                    🌐 ACCESS POINTS                          ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}🛡️  Healing Dashboard:${NC}      http://localhost:5001"
    echo -e "${GREEN}🤖 DDoS Model API:${NC}               http://localhost:8080"
    echo -e "${GREEN}🔍 Network Analyzer:${NC}        http://localhost:8000"
    echo -e "${GREEN}🚨 Incident Bot:${NC}            http://localhost:8001"
    echo -e "${GREEN}📈 Monitoring Server:${NC}       http://localhost:5000"
    echo -e "${GREEN}📊 Fluent Bit:${NC}               http://localhost:8888"
    echo ""
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║         🛡️  ALL SERVICES ARE RUNNING! 🛡️                    ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
    echo ""
    
    # Keep script running and wait for all background processes
    wait
}

# Run main function
main "$@"

