#!/bin/bash
# =============================================================================
# Heal-X-Bot Health Check Script
# =============================================================================
# This script checks the health of all Heal-X-Bot services
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
DOCKER_DIR="${PROJECT_ROOT}/docker/production"
COMPOSE_FILE="${DOCKER_DIR}/docker-compose.prod.yml"
ENV_FILE="${DOCKER_DIR}/.env.production"

# Detect Docker Compose command
detect_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null 2>&1; then
        DOCKER_COMPOSE_CMD="docker compose"
    else
        DOCKER_COMPOSE_CMD="docker compose"  # Default to V2
    fi
}

# Load environment variables
if [ -f "${ENV_FILE}" ]; then
    source "${ENV_FILE}"
fi

# Default ports
MODEL_PORT=${MODEL_PORT:-8080}
MONITORING_SERVER_PORT=${MONITORING_SERVER_PORT:-5000}
HEALING_DASHBOARD_PORT=${HEALING_DASHBOARD_PORT:-5001}
INCIDENT_BOT_PORT=${INCIDENT_BOT_PORT:-8001}
PROMETHEUS_PORT=${PROMETHEUS_PORT:-9090}

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_service() {
    local service_name=$1
    local port=$2
    local endpoint=${3:-/health}
    
    if curl -f -s "http://localhost:${port}${endpoint}" > /dev/null 2>&1; then
        log_info "${service_name}: ✓ Healthy (port ${port})"
        return 0
    else
        log_error "${service_name}: ✗ Unhealthy (port ${port})"
        return 1
    fi
}

check_container() {
    local container_name=$1
    
    if docker ps --format '{{.Names}}' | grep -q "^${container_name}$"; then
        local status=$(docker inspect --format='{{.State.Status}}' "${container_name}")
        local health=$(docker inspect --format='{{.State.Health.Status}}' "${container_name}" 2>/dev/null || echo "no-healthcheck")
        
        if [ "${status}" = "running" ]; then
            if [ "${health}" = "healthy" ] || [ "${health}" = "no-healthcheck" ]; then
                log_info "Container ${container_name}: ✓ Running (${health})"
                return 0
            else
                log_warn "Container ${container_name}: ⚠ Running but ${health}"
                return 1
            fi
        else
            log_error "Container ${container_name}: ✗ ${status}"
            return 1
        fi
    else
        log_error "Container ${container_name}: ✗ Not found"
        return 1
    fi
}

check_docker_compose() {
    log_info "Checking Docker Compose services..."
    cd "${DOCKER_DIR}"
    detect_docker_compose
    
    if [ ! -f "${COMPOSE_FILE}" ]; then
        log_error "Docker Compose file not found: ${COMPOSE_FILE}"
        return 1
    fi
    
    ${DOCKER_COMPOSE_CMD} -f "${COMPOSE_FILE}" ps
}

check_all_services() {
    log_info "Checking all service endpoints..."
    
    local failed=0
    
    check_service "Model API" "${MODEL_PORT}" "/health" || failed=$((failed + 1))
    check_service "Monitoring Server" "${MONITORING_SERVER_PORT}" "/health" || failed=$((failed + 1))
    check_service "Healing Dashboard" "${HEALING_DASHBOARD_PORT}" "/api/health" || failed=$((failed + 1))
    check_service "Incident Bot" "${INCIDENT_BOT_PORT}" "/health" || failed=$((failed + 1))
    check_service "Prometheus" "${PROMETHEUS_PORT}" "/-/healthy" || failed=$((failed + 1))
    
    return ${failed}
}

check_all_containers() {
    log_info "Checking all containers..."
    
    local failed=0
    
    check_container "heal-x-bot-model" || failed=$((failed + 1))
    check_container "heal-x-bot-monitoring" || failed=$((failed + 1))
    check_container "heal-x-bot-dashboard" || failed=$((failed + 1))
    check_container "heal-x-bot-incident-bot" || failed=$((failed + 1))
    check_container "heal-x-bot-prometheus" || failed=$((failed + 1))
    
    return ${failed}
}

check_resources() {
    log_info "Checking resource usage..."
    
    cd "${DOCKER_DIR}"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
}

# Main execution
main() {
    local exit_code=0
    
    echo "=========================================="
    echo "Heal-X-Bot Health Check"
    echo "=========================================="
    echo ""
    
    check_docker_compose
    echo ""
    
    check_all_containers
    echo ""
    
    check_all_services
    echo ""
    
    check_resources
    echo ""
    
    if [ ${exit_code} -eq 0 ]; then
        log_info "All health checks passed!"
    else
        log_error "Some health checks failed!"
        exit 1
    fi
}

# Run main function
main "$@"

