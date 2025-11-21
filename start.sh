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
        stop_all_services_quiet
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
            log_error "Please stop the processes using these ports or modify the configuration"
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
    log_info "Fixing protobuf compatibility..."
    python3 -m pip install --force-reinstall "protobuf>=5.28.0,<6.0.0" --no-cache-dir -q 2>/dev/null || true
    python3 -m pip install --upgrade "numpy<2" "typing-extensions>=4.12.0" googleapis-common-protos -q 2>/dev/null || true
    
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
    STARTUP_ORDER=("model" "network-analyzer" "monitoring-server" "incident-bot" "healing-dashboard")
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
    export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
    
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
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s --max-time 2 "$health_url" >/dev/null 2>&1; then
            log_success "$service_name is healthy"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    
    log_warning "$service_name health check timeout (may still be starting)"
    return 1
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
            wait_for_service "$service"
        else
            log_error "Failed to start $service"
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
                kill "$pid" 2>/dev/null || true
            fi
            rm -f "$pid_file"
        fi
    done
    
    # Kill any remaining processes
    pkill -f "python3.*main.py" 2>/dev/null || true
    pkill -f "python3.*app.py" 2>/dev/null || true
    pkill -f "python3.*network_analyzer.py" 2>/dev/null || true
    pkill -f "python3.*healing_dashboard_api.py" 2>/dev/null || true
}

stop_all_services() {
    log_info "Stopping all services..."
    
    for pid_file in "$PID_DIR"/*.pid; do
        if [ -f "$pid_file" ]; then
            local service=$(basename "$pid_file" .pid)
            local pid=$(cat "$pid_file" 2>/dev/null || echo "0")
            if [ "$pid" -ne 0 ] && kill -0 "$pid" 2>/dev/null; then
                log_info "Stopping $service (PID: $pid)..."
                kill "$pid" 2>/dev/null || true
            fi
            rm -f "$pid_file"
        fi
    done
    
    # Force kill any remaining processes
    pkill -f "python3.*main.py" 2>/dev/null || true
    pkill -f "python3.*app.py" 2>/dev/null || true
    pkill -f "python3.*network_analyzer.py" 2>/dev/null || true
    pkill -f "python3.*healing_dashboard_api.py" 2>/dev/null || true
    
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

Examples:
    ./start.sh              # Start all services
    ./start.sh status       # Check service status
    ./start.sh stop         # Stop all services

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

