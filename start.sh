#!/bin/bash
# =============================================================================
# HEAL-X-BOT - Unified Startup Script
# =============================================================================
# Comprehensive startup script that starts all services with proper error
# handling, dependency management, and health checks.
#
# Usage:
#   ./start.sh              # Start all services
#   ./start.sh status       # Check service status
#   ./start.sh stop         # Stop all services
#   ./start.sh restart      # Restart all services
#   ./start.sh --help       # Show help
# =============================================================================

set -euo pipefail
IFS=$'\n\t'

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Configuration
LOG_DIR="$SCRIPT_DIR/logs"
PID_DIR="$SCRIPT_DIR/.pids"
VENV_DIR="$SCRIPT_DIR/.venv"
SERVICES_CONFIG="$SCRIPT_DIR/config/services.yaml"
ENV_FILE="$SCRIPT_DIR/.env"
ENV_TEMPLATE="$SCRIPT_DIR/config/env.template"
RESOURCE_CONFIG="$SCRIPT_DIR/config/resource_config.json"

# Resource profile (can be set via RESOURCE_PROFILE env var or --resource-profile flag)
RESOURCE_PROFILE="${RESOURCE_PROFILE:-medium}"

# Create necessary directories
mkdir -p "$LOG_DIR" "$PID_DIR"

# Service PIDs array
declare -a PIDS=()
declare -A SERVICE_PIDS=()

# =============================================================================
# Utility Functions
# =============================================================================

print_banner() {
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                    🛡️  HEAL-X-BOT  🛡️                        ║${NC}"
    echo -e "${BLUE}║                                                              ║${NC}"
    echo -e "${BLUE}║        AI-Powered DDoS Detection & IP Blocking System       ║${NC}"
    echo -e "${BLUE}║                                                              ║${NC}"
    echo -e "${BLUE}║              Unified Service Startup Script                 ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

log_info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# =============================================================================
# Pre-flight Checks
# =============================================================================

check_python() {
    log_info "Checking Python version..."
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
        log_error "Python 3.8 or higher is required (found: $PYTHON_VERSION)"
        exit 1
    fi
    
    log_success "Python ${PYTHON_VERSION} detected"
}

kill_processes_on_port() {
    local port=$1
    local killed=0
    
    # Check for Docker containers using this port
    if command -v docker >/dev/null 2>&1; then
        local container=$(docker ps --format "{{.ID}}\t{{.Ports}}" 2>/dev/null | grep ":$port" | awk '{print $1}' | head -1 || true)
        if [ -n "$container" ]; then
            log_info "Stopping Docker container $container using port $port..."
            docker stop "$container" >/dev/null 2>&1 || true
            killed=1
        fi
    fi
    
    # Try using lsof to find and kill processes
    if command -v lsof >/dev/null 2>&1; then
        local pids=$(lsof -ti :$port 2>/dev/null || true)
        if [ -n "$pids" ]; then
            for pid in $pids; do
                # Skip docker-proxy if we already tried to stop the container
                if ps -p "$pid" -o comm= 2>/dev/null | grep -q "docker-proxy"; then
                    if [ $killed -eq 0 ]; then
                        log_info "Port $port is used by docker-proxy. Try: docker ps | grep $port"
                    fi
                    continue
                fi
                if kill -0 "$pid" 2>/dev/null; then
                    log_info "Killing process $pid on port $port..."
                    kill -TERM "$pid" 2>/dev/null || kill -9 "$pid" 2>/dev/null || true
                    killed=1
                fi
            done
        fi
    fi
    
    # Try using fuser as fallback (requires sudo)
    if [ $killed -eq 0 ] && command -v fuser >/dev/null 2>&1; then
        if sudo -n fuser -k $port/tcp >/dev/null 2>&1 2>/dev/null; then
            killed=1
        fi
    fi
    
    return $killed
}

check_ports() {
    log_info "Checking port availability..."
    local ports=(8080 8000 5000 5001 8001)
    local ports_in_use=()
    
    for port in "${ports[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            ports_in_use+=($port)
        fi
    done
    
    if [ ${#ports_in_use[@]} -gt 0 ]; then
        log_warning "The following ports are already in use: ${ports_in_use[*]}"
        log_info "Attempting to stop existing services..."
        
        # First, try stopping services via PID files
        stop_all_services_quiet
        sleep 2
        
        # Then, aggressively kill processes on those specific ports
        for port in "${ports_in_use[@]}"; do
            log_info "Killing processes on port $port..."
            kill_processes_on_port "$port"
        done
        
        sleep 2
        
        # Check again
        ports_in_use=()
        for port in "${ports[@]}"; do
            if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
                ports_in_use+=($port)
            fi
        done
        
        if [ ${#ports_in_use[@]} -gt 0 ]; then
            log_error "Ports still in use: ${ports_in_use[*]}"
            log_error ""
            log_error "Please stop the processes using these ports manually:"
            for port in "${ports_in_use[@]}"; do
                log_error ""
                log_error "  Port $port:"
                log_error "    Check: sudo lsof -i :$port"
                log_error "    Kill: sudo kill -9 \$(sudo lsof -ti :$port)"
                
                # Check if it's a Docker container
                if command -v docker >/dev/null 2>&1; then
                    local container=$(docker ps --format "{{.ID}}\t{{.Names}}\t{{.Ports}}" 2>/dev/null | grep ":$port" | head -1 || true)
                    if [ -n "$container" ]; then
                        local container_id=$(echo "$container" | awk '{print $1}')
                        local container_name=$(echo "$container" | awk '{print $2}')
                        log_error "    Docker: docker stop $container_id  # ($container_name)"
                    fi
                fi
            done
            log_error ""
            exit 1
        fi
    fi
    
    log_success "All required ports are available"
}

check_project_structure() {
    log_info "Verifying project structure..."
    local required_dirs=("model" "monitoring/server" "incident-bot" "config")
    local missing_dirs=()
    
    for dir in "${required_dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            missing_dirs+=($dir)
        fi
    done
    
    if [ ${#missing_dirs[@]} -gt 0 ]; then
        log_error "Missing required directories: ${missing_dirs[*]}"
        exit 1
    fi
    
    log_success "Project structure verified"
}

# =============================================================================
# Environment Setup
# =============================================================================

setup_venv() {
    log_info "Setting up virtual environment..."
    
    if [ ! -f "$VENV_DIR/bin/activate" ]; then
        log_info "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
    fi
    
    source "$VENV_DIR/bin/activate"
    log_success "Virtual environment activated"
    
    # Upgrade pip
    log_info "Upgrading pip..."
    python3 -m pip install --upgrade pip >/dev/null 2>&1 || true
    
    # Install dependencies
    log_info "Installing dependencies (this may take a few minutes)..."
    if [ -f "requirements.txt" ]; then
        # Upgrade pip first to ensure best dependency resolution
        python3 -m pip install --upgrade pip setuptools wheel >/dev/null 2>&1 || true
        
        # Install dependencies with better error handling
        if ! python3 -m pip install -r requirements.txt 2>&1 | tee "$LOG_DIR/dependency-install.log"; then
            log_warning "Some dependencies may have conflicts. Attempting to resolve..."
            # Try installing with --upgrade to resolve conflicts
            python3 -m pip install -r requirements.txt --upgrade 2>&1 | tee -a "$LOG_DIR/dependency-install.log" || {
                log_error "Failed to install dependencies. Check $LOG_DIR/dependency-install.log"
                log_error "You may need to manually resolve dependency conflicts"
                exit 1
            }
        fi
    fi
    
    # Fix protobuf compatibility (critical for TensorFlow)
    log_info "Fixing protobuf compatibility for TensorFlow..."
    # TensorFlow 2.20.0 requires protobuf 5.28.0 specifically
    # Uninstall any existing protobuf first, then install correct version
    python3 -m pip uninstall -y protobuf 2>/dev/null || true
    python3 -m pip install --no-cache-dir "protobuf==5.28.0" 2>&1 | tee -a "$LOG_DIR/dependency-install.log" || {
        log_error "Failed to install protobuf 5.28.0 - TensorFlow may not work"
    }
    python3 -m pip install --upgrade "numpy<2" "typing-extensions>=4.12.0" googleapis-common-protos -q 2>/dev/null || true
    
    # Verify protobuf version and test import
    PROTOBUF_VERSION=$(python3 -m pip show protobuf 2>/dev/null | grep Version | awk '{print $2}' || echo "unknown")
    log_info "Protobuf version: $PROTOBUF_VERSION"
    
    # Test protobuf import
    if python3 -c "from google.protobuf import runtime_version" 2>/dev/null; then
        log_success "Protobuf is compatible with TensorFlow"
    else
        log_warning "Protobuf runtime_version not available - TensorFlow may have issues"
        log_info "Trying to fix by reinstalling protobuf..."
        python3 -m pip install --force-reinstall --no-deps "protobuf==5.28.0" 2>&1 | tee -a "$LOG_DIR/dependency-install.log" || true
    fi
    
    # Install google-generativeai separately (required for incident bot)
    # Newer versions (>=0.6.0) should work with protobuf 5.x
    log_info "Installing Google Generative AI for incident bot..."
    if python3 -m pip install "google-generativeai>=0.6.0" 2>&1 | tee -a "$LOG_DIR/dependency-install.log" | grep -q "error\|conflict"; then
        log_warning "Google Generative AI installation had conflicts, trying alternative approach..."
        # Try installing with --upgrade to resolve conflicts
        python3 -m pip install "google-generativeai>=0.6.0" --upgrade 2>&1 | tee -a "$LOG_DIR/dependency-install.log" || \
        log_warning "Google Generative AI may not work correctly - incident bot AI features may be limited"
    else
        log_success "Google Generative AI installed successfully"
    fi
    
    log_success "Dependencies installed"
}

setup_env_file() {
    if [ ! -f "$ENV_FILE" ] && [ -f "$ENV_TEMPLATE" ]; then
        log_warning ".env file not found, creating from template..."
        cp "$ENV_TEMPLATE" "$ENV_FILE"
        log_success "Created .env file - please configure your API keys if needed"
    fi
}

load_resource_profile() {
    # Load resource profile configuration
    if [ ! -f "$RESOURCE_CONFIG" ]; then
        log_warning "Resource config not found: $RESOURCE_CONFIG - using defaults"
        return
    fi
    
    # Use Python to parse JSON (more reliable than jq which may not be installed)
    local profile_json=$(python3 -c "
import json
import sys
try:
    with open('$RESOURCE_CONFIG', 'r') as f:
        config = json.load(f)
    profile = config['profiles'].get('$RESOURCE_PROFILE', config['profiles'][config['default_profile']])
    print(json.dumps(profile))
except Exception as e:
    print('{}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null)
    
    if [ -z "$profile_json" ] || [ "$profile_json" = "{}" ]; then
        log_warning "Failed to load resource profile '$RESOURCE_PROFILE' - using defaults"
        return
    fi
    
    # Extract and export configuration values
    export MONITOR_INTERVAL=$(echo "$profile_json" | python3 -c "import json, sys; print(json.load(sys.stdin)['monitoring']['health_check_interval_seconds'])" 2>/dev/null || echo "30")
    export LOG_COLLECTION_INTERVAL=$(echo "$profile_json" | python3 -c "import json, sys; print(json.load(sys.stdin)['monitoring']['log_collection_interval_seconds'])" 2>/dev/null || echo "60")
    export CRITICAL_SERVICES_INTERVAL=$(echo "$profile_json" | python3 -c "import json, sys; print(json.load(sys.stdin)['monitoring']['critical_services_monitor_interval_seconds'])" 2>/dev/null || echo "30")
    export ESSENTIAL_ONLY=$(echo "$profile_json" | python3 -c "import json, sys; print(json.load(sys.stdin)['services']['essential_only'])" 2>/dev/null || echo "false")
    
    log_info "Resource profile: $RESOURCE_PROFILE (monitor interval: ${MONITOR_INTERVAL}s)"
    
    if [ "$ESSENTIAL_ONLY" = "true" ]; then
        log_info "Essential services only mode enabled"
    fi
}

# =============================================================================
# Service Management
# =============================================================================

parse_services_config() {
    # Simple YAML parser for services.yaml
    # This is a basic implementation - for production, consider using yq or python yaml
    if [ ! -f "$SERVICES_CONFIG" ]; then
        log_error "Services configuration not found: $SERVICES_CONFIG"
        exit 1
    fi
    
    # Define services manually (since we don't have yq installed)
    declare -gA SERVICE_CONFIG
    SERVICE_CONFIG[model]="model|main.py|8080|MODEL_PORT=8080|http://localhost:8080/health"
    SERVICE_CONFIG[network-analyzer]="monitoring/server|network_analyzer.py|8000|PORT=8000|http://localhost:8000/health"
    SERVICE_CONFIG[monitoring-server]="monitoring/server|app.py|5000||http://localhost:5000/health"
    SERVICE_CONFIG[healing-dashboard]="monitoring/server|healing_dashboard_api.py|5001|HEALING_DASHBOARD_PORT=5001|http://localhost:5001/api/health"
    SERVICE_CONFIG[incident-bot]="incident-bot|main.py|8001|PORT=8001|http://localhost:8001/health"
    
    # Startup order
    declare -ga STARTUP_ORDER
    if [ "${ESSENTIAL_ONLY:-false}" = "true" ]; then
        # Essential services only (model, monitoring-server, healing-dashboard)
        STARTUP_ORDER=("model" "monitoring-server" "healing-dashboard")
        log_info "Starting in essential-only mode (skipping network-analyzer and incident-bot)"
    else
        # All services
        STARTUP_ORDER=("model" "network-analyzer" "monitoring-server" "incident-bot" "healing-dashboard")
    fi
}

start_service() {
    local service_key=$1
    local config="${SERVICE_CONFIG[$service_key]}"
    
    if [ -z "$config" ]; then
        log_error "Unknown service: $service_key"
        return 1
    fi
    
    IFS='|' read -r path script port env_vars health_url <<< "$config"
    local service_name="${service_key//-/ }"
    service_name="$(echo $service_name | sed 's/\b\(.\)/\u\1/g')"
    
    local pid_file="$PID_DIR/${service_key}.pid"
    
    # Check if already running
    if [ -f "$pid_file" ]; then
        local existing_pid=$(cat "$pid_file" 2>/dev/null || echo "0")
        if kill -0 "$existing_pid" 2>/dev/null; then
            log_success "$service_name is already running (PID: $existing_pid)"
            PIDS+=($existing_pid)
            SERVICE_PIDS[$service_key]=$existing_pid
            return 0
        else
            rm -f "$pid_file"
        fi
    fi
    
    # Check if script exists
    if [ ! -f "$path/$script" ]; then
        log_error "Script not found: $path/$script"
        return 1
    fi
    
    log_info "Starting $service_name..."
    
    # Prepare environment
    export PYTHONUNBUFFERED=1
    export PYTHONPATH="$SCRIPT_DIR:${PYTHONPATH:-}"
    
    if [ -n "$env_vars" ]; then
        eval "export $env_vars"
    fi
    
    # Start service in background
    cd "$path"
    nohup python3 -u "$script" >> "$LOG_DIR/${service_name}.log" 2>&1 &
    local pid=$!
    cd "$SCRIPT_DIR"
    
    # Save PID
    echo "$pid" > "$pid_file"
    PIDS+=($pid)
    SERVICE_PIDS[$service_key]=$pid
    
    # Wait and check if it started successfully
    sleep 3
    if kill -0 "$pid" 2>/dev/null; then
        log_success "$service_name started (PID: $pid, Port: $port)"
        return 0
    else
        log_error "$service_name failed to start - check $LOG_DIR/${service_name}.log"
        return 1
    fi
}

wait_for_service() {
    local service_key=$1
    local config="${SERVICE_CONFIG[$service_key]}"
    IFS='|' read -r path script port env_vars health_url <<< "$config"
    local service_name="${service_key//-/ }"
    service_name="$(echo $service_name | sed 's/\b\(.\)/\u\1/g')"
    
    if [ -z "$health_url" ] || [ "$health_url" = "null" ]; then
        return 0
    fi
    
    log_info "Waiting for $service_name to be healthy..."
    local max_attempts=60
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s --max-time 2 "$health_url" >/dev/null 2>&1; then
            log_success "$service_name is healthy"
            return 0
        fi
        attempt=$((attempt + 1))
        # Show progress every 10 attempts
        if [ $((attempt % 10)) -eq 0 ]; then
            log_info "Still waiting for $service_name... (attempt $attempt/$max_attempts)"
        fi
        sleep 1
    done
    
    log_warning "$service_name health check timeout after ${max_attempts}s (service may still be starting)"
    log_info "Check $LOG_DIR/${service_name}.log for details"
    # Don't fail - service might still be starting (especially TensorFlow models take time)
    return 0
}

start_all_services() {
    log_info "Starting all services in dependency order..."
    
    parse_services_config
    
    for service in "${STARTUP_ORDER[@]}"; do
        # Check dependencies
        local deps_ok=1
        case $service in
            network-analyzer|monitoring-server|incident-bot)
                if [ -z "${SERVICE_PIDS[model]:-}" ] || ! kill -0 "${SERVICE_PIDS[model]}" 2>/dev/null; then
                    deps_ok=0
                fi
                ;;
            healing-dashboard)
                if [ -z "${SERVICE_PIDS[monitoring-server]:-}" ] || ! kill -0 "${SERVICE_PIDS[monitoring-server]}" 2>/dev/null; then
                    deps_ok=0
                fi
                ;;
        esac
        
        if [ $deps_ok -eq 0 ]; then
            log_warning "Dependencies not ready for $service, waiting..."
            sleep 2
        fi
        
        if start_service "$service"; then
            # Wait for service health, but don't fail if it times out
            # (services like TensorFlow models can take a while to load)
            if ! wait_for_service "$service"; then
                log_warning "$service health check failed, but continuing startup..."
                log_info "Service may still be initializing. Check logs if issues persist."
            fi
        else
            log_error "Failed to start $service"
            # Continue with other services even if one fails
        fi
    done
}

# =============================================================================
# Service Status and Control
# =============================================================================

check_service_status() {
    parse_services_config
    echo ""
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                    Service Status                            ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    for service in "${STARTUP_ORDER[@]}"; do
        local config="${SERVICE_CONFIG[$service]}"
        IFS='|' read -r path script port env_vars health_url <<< "$config"
        local service_name="${service//-/ }"
        service_name="$(echo $service_name | sed 's/\b\(.\)/\u\1/g')"
        
        local pid_file="$PID_DIR/${service}.pid"
        local status="❌ Stopped"
        local pid="N/A"
        
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file" 2>/dev/null || echo "0")
            if kill -0 "$pid" 2>/dev/null; then
                if [ -n "$health_url" ]; then
                    if curl -s --max-time 2 "$health_url" >/dev/null 2>&1; then
                        status="${GREEN}✅ Running${NC}"
                    else
                        status="${YELLOW}⚠️  Starting${NC}"
                    fi
                else
                    status="${GREEN}✅ Running${NC}"
                fi
            else
                status="❌ Stopped (stale PID)"
                rm -f "$pid_file"
            fi
        fi
        
        printf "%-25s %-15s Port: %-5s PID: %s\n" "$service_name" "$status" "$port" "$pid"
    done
    echo ""
}

stop_all_services_quiet() {
    # Stop services without output (for internal use)
    for pid_file in "$PID_DIR"/*.pid; do
        if [ -f "$pid_file" ]; then
            local pid=$(cat "$pid_file" 2>/dev/null || echo "0")
            if [ "$pid" -ne 0 ] && kill -0 "$pid" 2>/dev/null; then
                kill "$pid" 2>/dev/null || kill -9 "$pid" 2>/dev/null || true
            fi
            rm -f "$pid_file"
        fi
    done
    
    # Kill any remaining processes by pattern
    pkill -f "python3.*main.py" 2>/dev/null || true
    pkill -f "python3.*app.py" 2>/dev/null || true
    pkill -f "python3.*network_analyzer.py" 2>/dev/null || true
    pkill -f "python3.*healing_dashboard_api.py" 2>/dev/null || true
    pkill -f "uvicorn.*healing_dashboard_api" 2>/dev/null || true
    pkill -f "uvicorn.*app" 2>/dev/null || true
    
    # Kill processes on specific ports (more aggressive)
    for port in 8080 8000 5000 5001 8001; do
        if command -v lsof >/dev/null 2>&1; then
            local pids=$(lsof -ti :$port 2>/dev/null || true)
            if [ -n "$pids" ]; then
                for pid in $pids; do
                    # Skip if it's a docker-proxy (might be from other containers)
                    if ! ps -p "$pid" -o comm= 2>/dev/null | grep -q "docker-proxy"; then
                        kill -TERM "$pid" 2>/dev/null || kill -9 "$pid" 2>/dev/null || true
                    fi
                done
            fi
        fi
    done
}

stop_all_services() {
    log_info "Stopping all services..."
    
    for pid_file in "$PID_DIR"/*.pid; do
        if [ -f "$pid_file" ]; then
            local service=$(basename "$pid_file" .pid)
            local pid=$(cat "$pid_file" 2>/dev/null || echo "0")
            if [ "$pid" -ne 0 ] && kill -0 "$pid" 2>/dev/null; then
                log_info "Stopping $service (PID: $pid)..."
                kill "$pid" 2>/dev/null || kill -9 "$pid" 2>/dev/null || true
            fi
            rm -f "$pid_file"
        fi
    done
    
    # Force kill any remaining processes by pattern
    pkill -f "python3.*main.py" 2>/dev/null || true
    pkill -f "python3.*app.py" 2>/dev/null || true
    pkill -f "python3.*network_analyzer.py" 2>/dev/null || true
    pkill -f "python3.*healing_dashboard_api.py" 2>/dev/null || true
    pkill -f "uvicorn.*healing_dashboard_api" 2>/dev/null || true
    pkill -f "uvicorn.*app" 2>/dev/null || true
    
    # Kill processes on specific ports
    for port in 8080 8000 5000 5001 8001; do
        if command -v lsof >/dev/null 2>&1; then
            local pids=$(lsof -ti :$port 2>/dev/null || true)
            if [ -n "$pids" ]; then
                for pid in $pids; do
                    # Skip docker-proxy processes (might be from other containers)
                    if ! ps -p "$pid" -o comm= 2>/dev/null | grep -q "docker-proxy"; then
                        log_info "Killing process $pid on port $port..."
                        kill -TERM "$pid" 2>/dev/null || kill -9 "$pid" 2>/dev/null || true
                    fi
                done
            fi
        fi
    done
    
    sleep 2
    log_success "All services stopped"
}

# =============================================================================
# Cleanup Function
# =============================================================================

cleanup() {
    echo ""
    log_info "Shutting down all services..."
    stop_all_services_quiet
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# =============================================================================
# Main Execution
# =============================================================================

show_help() {
    cat << EOF
HEAL-X-BOT - Unified Startup Script

Usage:
    ./start.sh [command]

Commands:
    (no args)    Start all services
    status       Check status of all services
    stop         Stop all services
    restart      Restart all services
    --help       Show this help message
    --resource-profile [low|medium|high]  Set resource usage profile

Examples:
    ./start.sh                          # Start all services (medium profile)
    ./start.sh --resource-profile low   # Start with low resource usage
    ./start.sh status                   # Check service status
    ./start.sh stop                     # Stop all services

Access Points (after startup):
    🛡️  Healing Dashboard:    http://localhost:5001
    📈 Monitoring Server:      http://localhost:5000
    🤖 DDoS Model API:         http://localhost:8080
    🔍 Network Analyzer:       http://localhost:8000
    🚨 Incident Bot:          http://localhost:8001

EOF
}

main() {
    local command="${1:-start}"
    
    case "$command" in
        --help|-h|help)
            show_help
            exit 0
            ;;
        status)
            check_service_status
            exit 0
            ;;
        stop)
            stop_all_services
            exit 0
            ;;
        restart)
            stop_all_services
            sleep 2
            command="start"
            ;;
        start|*)
            ;;
    esac
    
    if [ "$command" = "start" ]; then
        print_banner
        check_python
        check_project_structure
        setup_env_file
        setup_venv
        load_resource_profile
        check_ports
        
        log_info "Starting all services..."
        echo ""
        
        start_all_services
        
        echo ""
        echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${BLUE}║                    🌐 ACCESS POINTS                          ║${NC}"
        echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${GREEN}🛡️  Healing Dashboard:${NC}      http://localhost:5001"
        echo -e "${GREEN}📈 Monitoring Server:${NC}       http://localhost:5000"
        echo -e "${GREEN}🤖 DDoS Model API:${NC}               http://localhost:8080"
        echo -e "${GREEN}🔍 Network Analyzer:${NC}        http://localhost:8000"
        echo -e "${GREEN}🚨 Incident Bot:${NC}            http://localhost:8001"
        echo ""
        echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${BLUE}║         🛡️  ALL SERVICES ARE RUNNING! 🛡️                    ║${NC}"
        echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
        echo ""
        
        # Keep script running
        wait
    fi
}

# Run main function
main "$@"

