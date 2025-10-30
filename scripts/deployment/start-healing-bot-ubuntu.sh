
#!/bin/bash

################################################################################
# AUTOMATIC SELF-HEALING BOT - Ubuntu Startup Script
################################################################################
# This script sets up and runs the entire Healing-bot system on Ubuntu
#
# Features:
# - Checks system requirements
# - Installs dependencies
# - Verifies environment configuration
# - Starts all services
# - Provides health monitoring
# - Graceful shutdown handling
#
# Usage:
#   ./start-healing-bot-ubuntu.sh [options]
#
# Options:
#   --install-deps    Install system dependencies
#   --setup-env       Run environment setup wizard
#   --dev             Run in development mode (separate terminals)
#   --stop            Stop all running services
#   --status          Check status of all services
#   --logs            Show logs from all services
#   --help            Show this help message
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
PID_DIR="$PROJECT_ROOT/.pids"

# Service Configuration
declare -A SERVICES=(
    ["model"]="model/main.py:8080"
    ["network-analyzer"]="monitoring/server/network_analyzer.py:8000"
    ["monitoring-server"]="monitoring/server/app.py:5000"
    ["dashboard"]="monitoring/dashboard/app.py:3001"
    ["incident-bot"]="incident-bot/main.py:8001"
)

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "${CYAN}"
    echo "╔════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                    ║"
    echo "║          🤖 AUTOMATIC SELF-HEALING BOT - Ubuntu Launcher          ║"
    echo "║                                                                    ║"
    echo "║              AI-Powered DDoS Detection & Auto-Healing              ║"
    echo "║                                                                    ║"
    echo "╚════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_step() {
    echo -e "${PURPLE}▶ $1${NC}"
}

################################################################################
# System Requirements Check
################################################################################

check_system_requirements() {
    log_step "Checking system requirements..."
    
    local missing_deps=()
    
    # Check Python 3
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    else
        local python_version=$(python3 --version | awk '{print $2}')
        log_success "Python 3 found: $python_version"
    fi
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        missing_deps+=("python3-pip")
    else
        log_success "pip3 found"
    fi
    
    # Check git
    if ! command -v git &> /dev/null; then
        log_warning "git not found (optional)"
    else
        log_success "git found"
    fi
    
    # Check curl
    if ! command -v curl &> /dev/null; then
        missing_deps+=("curl")
    else
        log_success "curl found"
    fi
    
    # Check if any dependencies are missing
    if [ ${#missing_deps[@]} -gt 0 ]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        log_info "Install with: sudo apt update && sudo apt install -y ${missing_deps[*]}"
        log_info "Or run: $0 --install-deps"
        exit 1
    fi
    
    log_success "All system requirements met!"
}

################################################################################
# Install Dependencies
################################################################################

install_system_dependencies() {
    log_step "Installing system dependencies..."
    
    if [ "$EUID" -ne 0 ]; then
        log_error "This option requires sudo privileges"
        log_info "Run: sudo $0 --install-deps"
        exit 1
    fi
    
    log_info "Updating package lists..."
    apt update
    
    log_info "Installing required packages..."
    apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        build-essential \
        curl \
        git \
        net-tools \
        lsof
    
    log_success "System dependencies installed!"
}

install_python_dependencies() {
    log_step "Installing Python dependencies..."
    
    cd "$PROJECT_ROOT"
    
    # Upgrade pip
    log_info "Upgrading pip..."
    python3 -m pip install --upgrade pip
    
    # Install main requirements
    if [ -f "requirements.txt" ]; then
        log_info "Installing main requirements..."
        pip3 install -r requirements.txt
    fi
    
    # Install monitoring server requirements
    if [ -f "monitoring/server/requirements.txt" ]; then
        log_info "Installing monitoring server requirements..."
        pip3 install -r monitoring/server/requirements.txt
    fi
    
    # Install dashboard requirements
    if [ -f "monitoring/dashboard/requirements.txt" ]; then
        log_info "Installing dashboard requirements..."
        pip3 install -r monitoring/dashboard/requirements.txt
    fi
    
    # Install incident bot requirements
    if [ -f "incident-bot/requirements.txt" ]; then
        log_info "Installing incident bot requirements..."
        pip3 install -r incident-bot/requirements.txt
    fi
    
    # Install model requirements
    if [ -f "model/requirements.txt" ]; then
        log_info "Installing model requirements..."
        pip3 install -r model/requirements.txt
    fi
    
    log_success "Python dependencies installed!"
}

################################################################################
# Environment Setup
################################################################################

check_environment() {
    log_step "Checking environment configuration..."
    
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        log_warning ".env file not found"
        log_info "Creating .env from template..."
        
        if [ -f "$PROJECT_ROOT/config/env.template" ]; then
            cp "$PROJECT_ROOT/config/env.template" "$PROJECT_ROOT/.env"
            log_success "Created .env file from template"
            log_warning "Please edit .env and add your GEMINI_API_KEY"
            log_info "Get your free API key: https://aistudio.google.com/app/apikey"
            log_info "Or run: python3 scripts/setup/setup_env.py"
            return 1
        else
            log_error "config/env.template not found"
            return 1
        fi
    fi
    
    # Check for GEMINI_API_KEY
    if grep -q "GEMINI_API_KEY=your_gemini_api_key_here" "$PROJECT_ROOT/.env" 2>/dev/null || \
       grep -q "GEMINI_API_KEY=$" "$PROJECT_ROOT/.env" 2>/dev/null; then
        log_warning "GEMINI_API_KEY not configured in .env"
        log_info "AI log analysis will not work without this key"
        log_info "Get your free API key: https://aistudio.google.com/app/apikey"
        log_info "Or run: python3 scripts/setup/setup_env.py"
        # Don't return error - system can run without AI features
    fi
    
    # Load .env file
    if [ -f "$PROJECT_ROOT/.env" ]; then
        set -a
        source "$PROJECT_ROOT/.env"
        set +a
        log_success "Environment variables loaded from .env"
    fi
    
    log_success "Environment configuration OK"
    return 0
}

run_env_setup() {
    log_step "Running environment setup wizard..."
    cd "$PROJECT_ROOT"
    if [ -f "scripts/setup/setup_env.py" ]; then
        python3 scripts/setup/setup_env.py
    else
        log_error "setup_env.py not found at scripts/setup/setup_env.py"
        log_info "Please manually edit .env file"
        return 1
    fi
}

################################################################################
# Service Management
################################################################################

create_directories() {
    log_step "Creating necessary directories..."
    mkdir -p "$LOG_DIR"
    mkdir -p "$PID_DIR"
    mkdir -p "$PROJECT_ROOT/monitoring/server/data"
    log_success "Directories created"
}

check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

start_service() {
    local name=$1
    local script=$2
    local port=$3
    
    log_step "Starting $name..."
    
    # Check if port is already in use
    if check_port $port; then
        log_warning "$name already running on port $port"
        return 0
    fi
    
    # Get directory and script name
    local service_dir=$(dirname "$script")
    local script_name=$(basename "$script")
    
    # Start service in background
    cd "$PROJECT_ROOT/$service_dir"
    
    nohup python3 "$script_name" \
        > "$LOG_DIR/${name}.log" 2>&1 &
    
    local pid=$!
    echo $pid > "$PID_DIR/${name}.pid"
    
    # Wait a bit and check if process is running
    sleep 2
    
    if kill -0 $pid 2>/dev/null; then
        log_success "$name started (PID: $pid, Port: $port)"
        return 0
    else
        log_error "$name failed to start"
        log_info "Check logs: tail -f $LOG_DIR/${name}.log"
        return 1
    fi
}

start_all_services() {
    log_step "Starting all Healing-bot services..."
    
    local failed=0
    
    # Start services in order
    for service_name in model network-analyzer monitoring-server dashboard incident-bot; do
        local service_info="${SERVICES[$service_name]}"
        local script="${service_info%:*}"
        local port="${service_info#*:}"
        
        if ! start_service "$service_name" "$script" "$port"; then
            ((failed++))
        fi
        
        # Small delay between services
        sleep 1
    done
    
    echo ""
    if [ $failed -eq 0 ]; then
        log_success "All services started successfully!"
        show_access_points
    else
        log_error "$failed service(s) failed to start"
        log_info "Check logs in: $LOG_DIR/"
        return 1
    fi
}

stop_service() {
    local name=$1
    local pid_file="$PID_DIR/${name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 $pid 2>/dev/null; then
            log_info "Stopping $name (PID: $pid)..."
            kill $pid
            sleep 1
            
            # Force kill if still running
            if kill -0 $pid 2>/dev/null; then
                log_warning "Force stopping $name..."
                kill -9 $pid
            fi
            
            rm "$pid_file"
            log_success "$name stopped"
        else
            log_info "$name not running"
            rm "$pid_file"
        fi
    else
        log_info "$name not running (no PID file)"
    fi
}

stop_all_services() {
    log_step "Stopping all Healing-bot services..."
    
    for service_name in incident-bot dashboard monitoring-server network-analyzer model; do
        stop_service "$service_name"
    done
    
    # Cleanup any remaining processes
    pkill -f "model/main.py" 2>/dev/null || true
    pkill -f "network_analyzer.py" 2>/dev/null || true
    pkill -f "monitoring/server/app.py" 2>/dev/null || true
    pkill -f "monitoring/dashboard/app.py" 2>/dev/null || true
    pkill -f "incident-bot/main.py" 2>/dev/null || true
    
    log_success "All services stopped"
}

################################################################################
# Status & Monitoring
################################################################################

check_service_status() {
    local name=$1
    local port=$2
    local pid_file="$PID_DIR/${name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 $pid 2>/dev/null; then
            if check_port $port; then
                echo -e "${GREEN}✅ Running${NC} (PID: $pid, Port: $port)"
            else
                echo -e "${YELLOW}⚠️  Running but port $port not listening${NC}"
            fi
        else
            echo -e "${RED}❌ Dead${NC} (PID file exists but process not found)"
        fi
    else
        if check_port $port; then
            echo -e "${YELLOW}⚠️  Running${NC} (Port $port in use, but no PID file)"
        else
            echo -e "${RED}❌ Stopped${NC}"
        fi
    fi
}

show_status() {
    log_step "Healing-bot System Status"
    echo ""
    
    printf "%-25s %-50s\n" "Service" "Status"
    printf "%-25s %-50s\n" "-------" "------"
    
    for service_name in model network-analyzer monitoring-server dashboard incident-bot; do
        local service_info="${SERVICES[$service_name]}"
        local port="${service_info#*:}"
        
        printf "%-25s " "$service_name"
        check_service_status "$service_name" "$port"
    done
    
    echo ""
}

show_access_points() {
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
    echo -e "${YELLOW}💡 Tip: Use '$0 --status' to check service status${NC}"
    echo -e "${YELLOW}💡 Tip: Use '$0 --logs' to view logs${NC}"
    echo -e "${YELLOW}💡 Tip: Use '$0 --stop' to stop all services${NC}"
    echo ""
}

show_logs() {
    log_step "Viewing logs from all services..."
    echo ""
    
    if [ ! -d "$LOG_DIR" ]; then
        log_error "Log directory not found: $LOG_DIR"
        return 1
    fi
    
    # Show last 50 lines from each log
    for log_file in "$LOG_DIR"/*.log; do
        if [ -f "$log_file" ]; then
            local service_name=$(basename "$log_file" .log)
            echo -e "${CYAN}═══ $service_name ═══${NC}"
            tail -n 20 "$log_file"
            echo ""
        fi
    done
    
    log_info "To follow logs in real-time:"
    echo "  tail -f $LOG_DIR/*.log"
}

################################################################################
# Development Mode
################################################################################

start_dev_mode() {
    log_step "Starting Healing-bot in development mode..."
    log_info "Each service will open in a new terminal window"
    
    # Check if gnome-terminal or xterm is available
    local terminal=""
    if command -v gnome-terminal &> /dev/null; then
        terminal="gnome-terminal"
    elif command -v xterm &> /dev/null; then
        terminal="xterm"
    elif command -v konsole &> /dev/null; then
        terminal="konsole"
    else
        log_error "No supported terminal found (gnome-terminal, xterm, or konsole)"
        log_info "Starting in background mode instead..."
        start_all_services
        return
    fi
    
    log_success "Using $terminal"
    
    # Start each service in its own terminal
    for service_name in model network-analyzer monitoring-server dashboard incident-bot; do
        local service_info="${SERVICES[$service_name]}"
        local script="${service_info%:*}"
        local service_dir=$(dirname "$script")
        local script_name=$(basename "$script")
        
        log_info "Starting $service_name in new terminal..."
        
        if [ "$terminal" = "gnome-terminal" ]; then
            gnome-terminal --tab --title="$service_name" -- bash -c "cd '$PROJECT_ROOT/$service_dir' && python3 '$script_name'; exec bash"
        elif [ "$terminal" = "xterm" ]; then
            xterm -T "$service_name" -e "cd '$PROJECT_ROOT/$service_dir' && python3 '$script_name'; bash" &
        elif [ "$terminal" = "konsole" ]; then
            konsole --new-tab -e bash -c "cd '$PROJECT_ROOT/$service_dir' && python3 '$script_name'; exec bash" &
        fi
        
        sleep 1
    done
    
    log_success "All services started in development mode"
    show_access_points
}

################################################################################
# Main Menu
################################################################################

show_help() {
    print_header
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --install-deps    Install system dependencies (requires sudo)"
    echo "  --setup-env       Run environment setup wizard"
    echo "  --dev             Run in development mode (separate terminals)"
    echo "  --stop            Stop all running services"
    echo "  --status          Check status of all services"
    echo "  --logs            Show logs from all services"
    echo "  --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                        # Start all services"
    echo "  $0 --dev                  # Start in development mode"
    echo "  $0 --status               # Check service status"
    echo "  $0 --stop                 # Stop all services"
    echo "  sudo $0 --install-deps    # Install system dependencies"
    echo ""
}

################################################################################
# Cleanup Handler
################################################################################

cleanup() {
    echo ""
    log_warning "Received interrupt signal"
    stop_all_services
    exit 0
}

trap cleanup SIGINT SIGTERM

################################################################################
# Main Function
################################################################################

main() {
    # Parse arguments
    case "${1:-}" in
        --help|-h)
            show_help
            exit 0
            ;;
        --install-deps)
            print_header
            install_system_dependencies
            install_python_dependencies
            exit 0
            ;;
        --setup-env)
            print_header
            run_env_setup
            exit 0
            ;;
        --stop)
            print_header
            stop_all_services
            exit 0
            ;;
        --status)
            print_header
            show_status
            exit 0
            ;;
        --logs)
            print_header
            show_logs
            exit 0
            ;;
        --dev)
            print_header
            check_system_requirements
            if ! check_environment; then
                log_error "Environment not properly configured"
                log_info "Run: $0 --setup-env"
                exit 1
            fi
            install_python_dependencies
            create_directories
            start_dev_mode
            exit 0
            ;;
        "")
            # Default: Start all services
            print_header
            check_system_requirements
            if ! check_environment; then
                log_error "Environment not properly configured"
                log_info "Run: $0 --setup-env"
                exit 1
            fi
            install_python_dependencies
            create_directories
            start_all_services
            
            # Keep script running
            log_info "Press Ctrl+C to stop all services"
            while true; do
                sleep 10
            done
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
}

################################################################################
# Run Main
################################################################################

main "$@"

