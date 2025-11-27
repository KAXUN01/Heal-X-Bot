#!/bin/bash
# Healing-Bot Self-Managing Startup Script
# This script starts and manages all services with auto-restart, health checks, and monitoring
# Services will automatically restart if they crash or become unhealthy

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
MONITOR_INTERVAL=10  # Check service health every 10 seconds
RESTART_DELAY=5      # Wait 5 seconds before restarting a crashed service
MAX_RESTARTS=5       # Maximum restart attempts per service in 5 minutes
HEALTH_CHECK_TIMEOUT=5  # Timeout for health checks in seconds
STARTUP_WAIT_TIME=15    # Wait time for services to fully start before health check
PID_DIR="$SCRIPT_DIR/.pids"
LOG_DIR="$SCRIPT_DIR/logs"
STATUS_FILE="$SCRIPT_DIR/.service_status.json"

# Ensure directories and files exist with correct permissions
mkdir -p "$PID_DIR" "$LOG_DIR"

# Fix permissions if file exists but is owned by root
if [ -f "$STATUS_FILE" ] && [ ! -w "$STATUS_FILE" ]; then
    log_warn "Status file not writable, removing and recreating..."
    rm -f "$STATUS_FILE" 2>/dev/null || true
fi

# Create status file with proper permissions
touch "$STATUS_FILE" 2>/dev/null || {
    log_error "Cannot create status file: $STATUS_FILE"
    log_error "Please check directory permissions or run: sudo chown -R $USER:$USER $SCRIPT_DIR"
    exit 1
}
chmod 644 "$STATUS_FILE" 2>/dev/null || true

# Service definitions
declare -A SERVICES
SERVICES[model]="DDoS Model API|model|main.py|8080|MODEL_PORT=8080|http://localhost:8080/health"
SERVICES[network-analyzer]="Network Analyzer|monitoring/server|network_analyzer.py|8000|PORT=8000|http://localhost:8000/health"
# Removed dashboard service (port 3001) - using healing-dashboard (port 5001) instead
SERVICES[incident-bot]="Incident Bot|incident-bot|main.py|8001|PORT=8001|http://localhost:8001/health"
SERVICES[monitoring-server]="Monitoring Server|monitoring/server|app.py|5000||http://localhost:5000/health"
SERVICES[healing-dashboard]="Healing Dashboard API|monitoring/server|healing_dashboard_api.py|5001|HEALING_DASHBOARD_PORT=5001|http://localhost:5001/api/health"

# Service status tracking
declare -A SERVICE_PIDS
declare -A SERVICE_RESTART_COUNTS
declare -A SERVICE_LAST_RESTART
declare -A SERVICE_STATUS

# Global flags
MONITORING=false
SHUTDOWN_REQUESTED=false

# ============================================================================
# Utility Functions
# ============================================================================

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1" >&2
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_debug() {
    if [ "${DEBUG:-0}" = "1" ]; then
        echo -e "${CYAN}[DEBUG]${NC} $1" >&2
    fi
}

# Create necessary directories
mkdir -p "$PID_DIR" "$LOG_DIR"

# ============================================================================
# Service Management Functions
# ============================================================================

save_service_status() {
    # Ensure file is writable, recreate if needed
    if [ ! -w "$STATUS_FILE" ] 2>/dev/null; then
        rm -f "$STATUS_FILE" 2>/dev/null || true
        touch "$STATUS_FILE" 2>/dev/null || {
            log_error "Cannot write to status file: $STATUS_FILE"
            return 1
        }
        chmod 644 "$STATUS_FILE" 2>/dev/null || true
    fi
    
    local status_json="{"
    local first=true
    for service in "${!SERVICES[@]}"; do
        if [ "$first" = false ]; then
            status_json+=","
        fi
        first=false
        local pid="${SERVICE_PIDS[$service]:-0}"
        local status="${SERVICE_STATUS[$service]:-unknown}"
        status_json+="\"$service\":{\"pid\":$pid,\"status\":\"$status\"}"
    done
    status_json+="}"
    echo "$status_json" > "$STATUS_FILE"
}

get_service_info() {
    local service=$1
    IFS='|' read -r name path script port env_vars health_url <<< "${SERVICES[$service]}"
    echo "$name|$path|$script|$port|$env_vars|$health_url"
}

check_service_health() {
    local service=$1
    local health_url=$(get_service_info "$service" | cut -d'|' -f6)
    
    if [ -z "$health_url" ] || [ "$health_url" = "null" ]; then
        return 0  # No health check URL, assume healthy if process is running
    fi
    
    # Try to check health endpoint with retries
    local response_code="000"
    local retry=0
    local max_retries=2
    
    while [ $retry -lt $max_retries ]; do
        response_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$HEALTH_CHECK_TIMEOUT" --connect-timeout 2 "$health_url" 2>/dev/null || echo "000")
        
        # If we get 200, service is healthy
        if [ "$response_code" = "200" ]; then
            return 0  # Healthy
        fi
        
        # If connection failed, retry once
        if [ "$response_code" = "000" ] && [ $retry -lt $((max_retries - 1)) ]; then
            sleep 1
            retry=$((retry + 1))
            continue
        fi
        
        break
    done
    
    # Return failure for non-200 or persistent connection failures
    return 1
}

is_service_running() {
    local service=$1
    local pid="${SERVICE_PIDS[$service]:-0}"
    
    if [ "$pid" -eq 0 ]; then
        return 1
    fi
    
    if kill -0 "$pid" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

can_restart_service() {
    local service=$1
    local current_time=$(date +%s)
    local last_restart="${SERVICE_LAST_RESTART[$service]:-0}"
    local restart_count="${SERVICE_RESTART_COUNTS[$service]:-0}"
    
    # Reset restart count if it's been more than 5 minutes since last restart
    if [ $((current_time - last_restart)) -gt 300 ]; then
        SERVICE_RESTART_COUNTS[$service]=0
        restart_count=0
    fi
    
    if [ "$restart_count" -ge "$MAX_RESTARTS" ]; then
        return 1
    fi
    
    return 0
}

start_service() {
    local service=$1
    IFS='|' read -r name path script port env_vars health_url <<< "${SERVICES[$service]}"
    
    local service_log="$LOG_DIR/${name}.log"
    local pid_file="$PID_DIR/${service}.pid"
    
    # Check if service is already running
    if [ -f "$pid_file" ]; then
        local existing_pid=$(cat "$pid_file" 2>/dev/null || echo "0")
        if kill -0 "$existing_pid" 2>/dev/null; then
            log_info "$name is already running (PID: $existing_pid)"
            SERVICE_PIDS[$service]=$existing_pid
            SERVICE_STATUS[$service]="running"
            return 0
        else
            rm -f "$pid_file"
        fi
    fi
    
    # Check if script exists
    if [ ! -f "$path/$script" ]; then
        log_error "Script not found: $path/$script"
        SERVICE_STATUS[$service]="error"
        return 1
    fi
    
    log_info "Starting $name..."
    
    # Prepare environment
    export PYTHONUNBUFFERED=1
    if [ -n "$env_vars" ]; then
        eval "export $env_vars"
    fi
    
    # Start service in background
    cd "$path"
    nohup python3 -u "$script" >> "$service_log" 2>&1 &
    local pid=$!
    cd "$SCRIPT_DIR"
    
    # Save PID
    echo "$pid" > "$pid_file"
    SERVICE_PIDS[$service]=$pid
    SERVICE_STATUS[$service]="starting"
    
    # Wait a bit and check if it's still running
    sleep 2
    if kill -0 "$pid" 2>/dev/null; then
        log_info "$name started successfully (PID: $pid, Port: $port)"
        SERVICE_STATUS[$service]="running"
        save_service_status
        
        # For services with health URLs, wait longer for service to initialize
        if [ -n "$health_url" ] && [ "$health_url" != "null" ]; then
            log_info "Waiting for $name to initialize (this may take up to ${STARTUP_WAIT_TIME}s)..."
            local health_ok=0
            local attempt=0
            local max_attempts=$STARTUP_WAIT_TIME  # Wait up to STARTUP_WAIT_TIME seconds
            
            while [ $attempt -lt $max_attempts ]; do
                sleep 1
                if check_service_health "$service"; then
                    health_ok=1
                    log_info "$name is healthy and ready"
                    break
                fi
                attempt=$((attempt + 1))
                # Show progress every 5 seconds
                if [ $((attempt % 5)) -eq 0 ] && [ $attempt -gt 0 ]; then
                    log_info "  Still waiting for $name... (${attempt}s elapsed)"
                fi
            done
            
            if [ $health_ok -eq 1 ]; then
                log_info "$name is healthy and ready"
            else
                log_warn "$name started but health check not responding after ${STARTUP_WAIT_TIME}s (service may still be initializing)"
                log_warn "   Service will continue running - health check will retry in monitoring loop"
            fi
        fi
        
        return 0
    else
        log_error "$name failed to start - check $service_log"
        SERVICE_STATUS[$service]="failed"
        save_service_status
        return 1
    fi
}

stop_service() {
    local service=$1
    IFS='|' read -r name path script port env_vars health_url <<< "${SERVICES[$service]}"
    local pid="${SERVICE_PIDS[$service]:-0}"
    local pid_file="$PID_DIR/${service}.pid"
    
    if [ "$pid" -eq 0 ] && [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file" 2>/dev/null || echo "0")
    fi
    
    if [ "$pid" -ne 0 ] && kill -0 "$pid" 2>/dev/null; then
        log_info "Stopping $name (PID: $pid)..."
        kill "$pid" 2>/dev/null || true
        sleep 2
        if kill -0 "$pid" 2>/dev/null; then
            log_warn "Force killing $name..."
            kill -9 "$pid" 2>/dev/null || true
        fi
        SERVICE_STATUS[$service]="stopped"
    fi
    
    rm -f "$pid_file"
    SERVICE_PIDS[$service]=0
    save_service_status
}

restart_service() {
    local service=$1
    IFS='|' read -r name path script port env_vars health_url <<< "${SERVICES[$service]}"
    
    local current_time=$(date +%s)
    SERVICE_LAST_RESTART[$service]=$current_time
    SERVICE_RESTART_COUNTS[$service]=$((${SERVICE_RESTART_COUNTS[$service]:-0} + 1))
    
    log_warn "Restarting $name (attempt ${SERVICE_RESTART_COUNTS[$service]}/$MAX_RESTARTS)..."
    stop_service "$service"
    sleep "$RESTART_DELAY"
    start_service "$service"
}

# ============================================================================
# Monitoring Loop
# ============================================================================

monitor_services() {
    log_info "Starting service monitor..."
    MONITORING=true
    
    while [ "$MONITORING" = true ] && [ "$SHUTDOWN_REQUESTED" = false ]; do
        for service in "${!SERVICES[@]}"; do
            IFS='|' read -r name path script port env_vars health_url <<< "${SERVICES[$service]}"
            
            if [ "$SHUTDOWN_REQUESTED" = true ]; then
                break
            fi
            
            # Check if service is running
            if ! is_service_running "$service"; then
                if [ "${SERVICE_STATUS[$service]}" != "stopped" ] && [ "${SERVICE_STATUS[$service]}" != "failed" ]; then
                    log_error "$name crashed or stopped unexpectedly"
                    SERVICE_STATUS[$service]="crashed"
                    
                    if can_restart_service "$service"; then
                        restart_service "$service"
                    else
                        log_error "$name has exceeded maximum restart attempts. Manual intervention required."
                        SERVICE_STATUS[$service]="max_restarts"
                    fi
                    save_service_status
                fi
            else
                # Service is running, check health (but be more lenient during startup)
                local pid="${SERVICE_PIDS[$service]:-0}"
                local should_check_health=true
                
                # Check how long the service has been running
                if [ "$pid" -ne 0 ] && kill -0 "$pid" 2>/dev/null; then
                    local pid_start_time=$(stat -c %Y /proc/$pid 2>/dev/null || echo "0")
                    local current_time=$(date +%s)
                    local uptime=$((current_time - pid_start_time))
                    
                    # Don't restart services that just started (within last 30 seconds)
                    if [ $uptime -lt 30 ]; then
                        should_check_health=false
                        if [ "${SERVICE_STATUS[$service]}" != "starting" ]; then
                            SERVICE_STATUS[$service]="starting"
                        fi
                    fi
                fi
                
                if [ "$should_check_health" = true ]; then
                    if ! check_service_health "$service"; then
                        log_warn "$name health check failed"
                        if [ "${SERVICE_STATUS[$service]}" = "running" ] || [ "${SERVICE_STATUS[$service]}" = "starting" ]; then
                            SERVICE_STATUS[$service]="unhealthy"
                            if can_restart_service "$service"; then
                                log_warn "Restarting $name due to health check failure"
                                restart_service "$service"
                            fi
                        fi
                    else
                        if [ "${SERVICE_STATUS[$service]}" != "running" ]; then
                            SERVICE_STATUS[$service]="running"
                            save_service_status
                        fi
                    fi
                fi
            fi
        done
        
        if [ "$SHUTDOWN_REQUESTED" = false ]; then
            sleep "$MONITOR_INTERVAL"
        fi
    done
    
    log_info "Service monitor stopped"
}

# ============================================================================
# Cleanup Functions
# ============================================================================

cleanup() {
    log_info "Shutting down services..."
    SHUTDOWN_REQUESTED=true
    MONITORING=false
    
    # Stop all services
    for service in "${!SERVICES[@]}"; do
        stop_service "$service"
    done
    
    # Stop Fluent Bit if running
    if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1 2>/dev/null; then
        if docker ps 2>/dev/null | grep -q "fluent-bit"; then
            log_info "Stopping Fluent Bit container..."
            if docker compose version >/dev/null 2>&1 2>/dev/null; then
                docker compose -f config/docker-compose-fluent-bit.yml down 2>/dev/null || true
            elif command -v docker-compose >/dev/null 2>&1; then
                docker-compose -f config/docker-compose-fluent-bit.yml down 2>/dev/null || true
            else
                docker stop fluent-bit 2>/dev/null || true
            fi
        fi
    fi
    
    # Cleanup PID files
    rm -rf "$PID_DIR"
    
    log_info "All services stopped"
    exit 0
}

# Set trap for cleanup
trap cleanup SIGINT SIGTERM EXIT

# ============================================================================
# Initialization
# ============================================================================

print_banner() {
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                    🛡️  HEALING-BOT  🛡️                      ║${NC}"
    echo -e "${BLUE}║                                                              ║${NC}"
    echo -e "${BLUE}║        AI-Powered DDoS Detection & IP Blocking System       ║${NC}"
    echo -e "${BLUE}║                                                              ║${NC}"
    echo -e "${BLUE}║              Self-Managing Service Manager                   ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

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
        log_error "Python 3.8 or higher is required"
        exit 1
    fi
    
    log_info "Python ${PYTHON_VERSION} detected"
}

setup_venv() {
    log_info "Setting up virtual environment..."
    VENV_DIR=".venv"
    
    if [ ! -f "$VENV_DIR/bin/activate" ]; then
        log_info "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
    fi
    
    source "$VENV_DIR/bin/activate"
    log_info "Virtual environment activated"
    
    # Install dependencies
    log_info "Installing dependencies..."
    python3 -m pip install --upgrade pip >/dev/null 2>&1
    
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
    
    # Fix protobuf compatibility
    python3 -m pip install --upgrade "protobuf>=4.25.3,<5" "numpy<2" googleapis-common-protos -q 2>/dev/null || true
    
    log_info "Dependencies installed"
}

check_docker() {
    log_info "Checking Docker for Fluent Bit..."
    DOCKER_OK=1
    
    if ! command -v docker &> /dev/null; then
        log_warn "Docker is not installed"
        DOCKER_OK=0
    elif ! docker info >/dev/null 2>&1; then
        log_warn "Docker daemon is not accessible (may need sudo or user in docker group)"
        DOCKER_OK=0
    fi
    
    if [ "$DOCKER_OK" -eq 1 ]; then
        if docker compose version >/dev/null 2>&1 || command -v docker-compose >/dev/null 2>&1; then
            log_info "Docker and Docker Compose detected"
        else
            log_warn "Docker Compose not found"
            DOCKER_OK=0
        fi
    fi
    
    return $DOCKER_OK
}

start_fluent_bit() {
    if check_docker; then
        log_info "Starting Fluent Bit..."
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
        log_info "Fluent Bit started (if Docker is accessible)"
    else
        log_warn "Skipping Fluent Bit (Docker not available)"
    fi
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    print_banner
    check_python
    setup_venv
    
    # Check for .env file
    if [ ! -f ".env" ] && [ -f "config/env.template" ]; then
        log_warn ".env file not found, creating from template..."
        cp config/env.template .env
        log_info "Created .env file - please configure your API keys"
    fi
    
    # Check project structure
    log_info "Checking project structure..."
    for dir in "monitoring/server" "model" "incident-bot" "config" "monitoring/dashboard"; do
        if [ ! -d "$dir" ]; then
            log_error "Required directory not found: $dir"
            exit 1
        fi
    done
    
    # Start Fluent Bit
    start_fluent_bit
    
    # Start all services
    log_info "Starting all services..."
    for service in "${!SERVICES[@]}"; do
        start_service "$service"
        sleep 1
    done
    
    # Wait a bit for services to initialize
    sleep 5
    
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
    echo -e "${BLUE}║         🛡️  HEALING-BOT IS RUNNING! 🛡️                        ║${NC}"
    echo -e "${BLUE}║                                                              ║${NC}"
    echo -e "${BLUE}║  Services are auto-managed with health checks and restart    ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
    echo ""
    
    # Start monitoring in background
    monitor_services &
    local monitor_pid=$!
    
    # Wait for monitor or user interrupt
    wait $monitor_pid
}

# Run main function
main "$@"

