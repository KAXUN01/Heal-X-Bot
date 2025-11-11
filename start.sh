#!/bin/bash
# Healing-Bot Startup Script
# This script starts the entire healing-bot application
# Uses native Python for services, Docker only for Fluent Bit

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Array to store background process PIDs
declare -a PIDS=()

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Shutting down services...${NC}"
    
    # Kill all background Python processes
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${YELLOW}   Stopping process $pid...${NC}"
            kill "$pid" 2>/dev/null || true
        fi
    done
    
    # Stop Fluent Bit Docker container
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
    
    # Wait a bit for processes to terminate
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

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM EXIT

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    🛡️  HEALING-BOT  🛡️                      ║${NC}"
echo -e "${BLUE}║                                                              ║${NC}"
echo -e "${BLUE}║        AI-Powered DDoS Detection & IP Blocking System       ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check Python version
echo -e "${YELLOW}🔍 Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ ERROR: Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✅ Python ${PYTHON_VERSION} detected${NC}"

# Check if Python version is 3.8 or higher
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo -e "${RED}❌ ERROR: Python 3.8 or higher is required${NC}"
    exit 1
fi

# Check Docker for Fluent Bit
echo -e "${YELLOW}🔍 Checking Docker for Fluent Bit...${NC}"
DOCKER_OK=1
COMPOSE_CMD=""
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ ERROR: Docker is not installed (required for Fluent Bit)${NC}"
    DOCKER_OK=0
else
    # Verify Docker daemon access/permissions
    if ! docker info >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  WARNING: Docker is installed but not accessible by this user or daemon isn't running${NC}"
        echo -e "${YELLOW}   Try:${NC}"
        echo -e "${YELLOW}   - Start daemon: sudo systemctl start docker${NC}"
        echo -e "${YELLOW}   - Add your user: sudo usermod -aG docker $USER && newgrp docker${NC}"
        DOCKER_OK=0
    fi
fi

if [ "$DOCKER_OK" -eq 1 ]; then
    if docker compose version >/dev/null 2>&1; then
        COMPOSE_CMD="docker compose"
    elif command -v docker-compose >/dev/null 2>&1; then
        COMPOSE_CMD="docker-compose"
    else
        echo -e "${YELLOW}⚠️  WARNING: Docker Compose not found (v2 or legacy). Fluent Bit will be skipped.${NC}"
        DOCKER_OK=0
    fi
fi

if [ "$DOCKER_OK" -eq 1 ]; then
    echo -e "${GREEN}✅ Docker and Docker Compose detected${NC}"
else
    echo -e "${YELLOW}⚠️  Proceeding without Fluent Bit due to Docker/Compose issue${NC}"
fi

# Ensure and activate virtual environment, then install Python deps
VENV_DIR=""
if [ -d ".venv" ]; then
    VENV_DIR=".venv"
elif [ -d "venv" ]; then
    VENV_DIR="venv"
else
    VENV_DIR=".venv"
fi

if [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment (${VENV_DIR})...${NC}"
    python3 -m venv "$VENV_DIR"
fi

if [ -f "$VENV_DIR/bin/activate" ]; then
    # shellcheck disable=SC1090
    source "$VENV_DIR/bin/activate"
    echo -e "${GREEN}✅ Virtual environment activated (${VENV_DIR})${NC}"
else
    echo -e "${RED}❌ ERROR: Failed to prepare virtual environment at ${VENV_DIR}${NC}"
    exit 1
fi

echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
python3 -m pip install --upgrade pip >/dev/null
if [ -f "requirements.txt" ]; then
    python3 -m pip install -r requirements.txt
fi
# Install per-service requirements if present
if [ -f "model/requirements.txt" ]; then
    python3 -m pip install -r model/requirements.txt
fi
if [ -f "monitoring/server/requirements.txt" ]; then
    python3 -m pip install -r monitoring/server/requirements.txt
fi
if [ -f "monitoring/dashboard/requirements.txt" ]; then
    python3 -m pip install -r monitoring/dashboard/requirements.txt
fi
if [ -f "incident-bot/requirements.txt" ]; then
    python3 -m pip install -r incident-bot/requirements.txt
fi
# Ensure protobuf is compatible with TensorFlow
python3 -m pip install --upgrade "protobuf>=4.25.3,<5" googleapis-common-protos >/dev/null || true
echo -e "${GREEN}✅ Virtual environment ready${NC}"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  WARNING: .env file not found${NC}"
    if [ -f "config/env.template" ]; then
        echo -e "${YELLOW}📝 Creating .env file from template...${NC}"
        cp config/env.template .env
        echo -e "${GREEN}✅ Created .env file - please configure your API keys${NC}"
    else
        echo -e "${YELLOW}⚠️  No env.template found - continuing without .env${NC}"
    fi
fi

# Check for required directories
echo -e "${YELLOW}🔍 Checking project structure...${NC}"
REQUIRED_DIRS=("monitoring/server" "model" "incident-bot" "config" "monitoring/dashboard")
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        echo -e "${RED}❌ ERROR: Required directory not found: $dir${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✅ Project structure verified${NC}"

# Check if ports are available
echo -e "${YELLOW}🔍 Checking port availability...${NC}"
PORTS=(8080 8000 8001 3001 5000 5001 8888)
OCCUPIED_PORTS=()

for port in "${PORTS[@]}"; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 || netstat -an 2>/dev/null | grep -q ":$port.*LISTEN"; then
        OCCUPIED_PORTS+=($port)
    fi
done

if [ ${#OCCUPIED_PORTS[@]} -gt 0 ]; then
    echo -e "${YELLOW}⚠️  WARNING: Ports ${OCCUPIED_PORTS[@]} are already in use${NC}"
    echo -e "${YELLOW}   The application may not start properly if these ports are needed${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}❌ Startup cancelled${NC}"
        exit 1
    fi
fi

# Create Docker network for Fluent Bit if it doesn't exist
if [ "$DOCKER_OK" -eq 1 ]; then
    echo -e "${YELLOW}🔍 Setting up Docker network for Fluent Bit...${NC}"
    if ! docker network ls | grep -q "healing-network"; then
        echo -e "${YELLOW}   Creating healing-network...${NC}"
        docker network create healing-network 2>/dev/null || true
        echo -e "${GREEN}✅ Docker network created${NC}"
    else
        echo -e "${GREEN}✅ Docker network already exists${NC}"
    fi
fi

# Start Fluent Bit with Docker (only if Docker/Compose available)
if [ "$DOCKER_OK" -eq 1 ]; then
    echo -e "${YELLOW}🐳 Starting Fluent Bit with Docker...${NC}"
    cd config
    if $COMPOSE_CMD -f docker-compose-fluent-bit.yml up -d; then
        echo -e "${GREEN}✅ Fluent Bit started${NC}"
    else
        echo -e "${RED}❌ ERROR: Failed to start Fluent Bit${NC}"
        exit 1
    fi
    cd "$SCRIPT_DIR"
else
    echo -e "${YELLOW}⏭️  Skipping Fluent Bit startup (Docker/Compose unavailable)${NC}"
fi

# Start Python services natively
echo ""
echo -e "${GREEN}🚀 Starting Python services...${NC}"
echo ""

# Function to start a service
start_service() {
    local service_name=$1
    local service_path=$2
    local script_name=$3
    local port=$4
    local env_vars="${5:-}"  # Optional environment variables
    
    if [ ! -f "$service_path/$script_name" ]; then
        echo -e "${RED}❌ ERROR: Script not found: $service_path/$script_name${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}🚀 Starting $service_name...${NC}"
    
    # Start the service in background with environment variables
    # Set PYTHONUNBUFFERED and any service-specific env vars
    local pid
    
    if [ -n "$env_vars" ]; then
        # Export variables for this service (will be used by the python process)
        eval "export PYTHONUNBUFFERED=1; export $env_vars"
        cd "$service_path"
        python3 -u "$script_name" > "$SCRIPT_DIR/logs/${service_name}.log" 2>&1 &
        pid=$!
        cd "$SCRIPT_DIR"
    else
        export PYTHONUNBUFFERED=1
        cd "$service_path"
        python3 -u "$script_name" > "$SCRIPT_DIR/logs/${service_name}.log" 2>&1 &
        pid=$!
        cd "$SCRIPT_DIR"
    fi
    
    PIDS+=($pid)
    
    # Wait a moment to check if it started successfully
    sleep 2
    if kill -0 "$pid" 2>/dev/null; then
        echo -e "${GREEN}✅ $service_name started (PID: $pid, Port: $port)${NC}"
        return 0
    else
        echo -e "${RED}❌ $service_name failed to start - check logs/${service_name}.log${NC}"
        return 1
    fi
}

# Create logs directory if it doesn't exist
mkdir -p logs

# Start all services
# Note: Using different ports to avoid conflicts
start_service "DDoS Model API" "model" "main.py" "8080" "MODEL_PORT=8080"
start_service "Network Analyzer" "monitoring/server" "network_analyzer.py" "8000" "PORT=8000"
start_service "ML Dashboard" "monitoring/dashboard" "app.py" "3001" "DASHBOARD_PORT=3001"
start_service "Incident Bot" "incident-bot" "main.py" "8001" "PORT=8001"
start_service "Monitoring Server" "monitoring/server" "app.py" "5000"
start_service "Healing Dashboard API" "monitoring/server" "healing_dashboard_api.py" "5001" "HEALING_DASHBOARD_PORT=5001"

# Wait a bit for services to initialize
echo ""
echo -e "${YELLOW}⏳ Waiting for services to initialize...${NC}"
sleep 5

# Print access information
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    🌐 ACCESS POINTS                          ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}📊 Dashboard:${NC}              http://localhost:3001"
echo -e "${GREEN}🛡️  Healing Dashboard:${NC}      http://localhost:5001"
echo -e "${GREEN}🤖 Model API:${NC}               http://localhost:8080"
echo -e "${GREEN}🔍 Network Analyzer:${NC}        http://localhost:8000"
echo -e "${GREEN}🚨 Incident Bot:${NC}            http://localhost:8001"
echo -e "${GREEN}📈 Monitoring Server:${NC}       http://localhost:5000"
echo -e "${GREEN}📊 Fluent Bit:${NC}               http://localhost:8888"
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         🛡️  HEALING-BOT IS RUNNING! 🛡️                        ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
echo ""

# Keep script running and wait for all background processes
wait
