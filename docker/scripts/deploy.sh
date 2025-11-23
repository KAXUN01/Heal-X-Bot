#!/bin/bash
# =============================================================================
# Heal-X-Bot Production Deployment Script
# =============================================================================
# This script handles the complete deployment of Heal-X-Bot in production
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

# Detect Docker Compose command
detect_docker_compose() {
    if command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null 2>&1; then
        DOCKER_COMPOSE_CMD="docker compose"
    else
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    log_info "Using Docker Compose: ${DOCKER_COMPOSE_CMD}"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Detect Docker Compose command
    detect_docker_compose
    
    # Verify Docker Compose works
    if ! ${DOCKER_COMPOSE_CMD} version &> /dev/null; then
        log_error "Docker Compose is not working. Please check installation."
        exit 1
    fi
    
    # Check if .env file exists
    if [ ! -f "${ENV_FILE}" ]; then
        log_warn ".env.production file not found. Creating from template..."
        if [ -f "${DOCKER_DIR}/env.production.template" ]; then
            cp "${DOCKER_DIR}/env.production.template" "${ENV_FILE}"
            log_warn "Please edit ${ENV_FILE} and fill in your configuration before continuing."
            exit 1
        else
            log_error "Template file not found. Please create ${ENV_FILE} manually."
            exit 1
        fi
    fi
    
    log_info "Prerequisites check passed."
}

backup_existing() {
    log_info "Creating backup of existing deployment..."
    
    BACKUP_DIR="${PROJECT_ROOT}/backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "${BACKUP_DIR}"
    
    # Backup volumes
    if docker volume ls | grep -q "heal-x-bot"; then
        log_info "Backing up Docker volumes..."
        docker run --rm \
            -v heal-x-bot_healing-data:/data:ro \
            -v "${BACKUP_DIR}:/backup" \
            alpine tar czf /backup/healing-data.tar.gz -C /data .
    fi
    
    # Backup configuration
    if [ -f "${ENV_FILE}" ]; then
        cp "${ENV_FILE}" "${BACKUP_DIR}/.env.production"
    fi
    
    log_info "Backup created at ${BACKUP_DIR}"
}

build_images() {
    log_info "Building Docker images..."
    
    cd "${DOCKER_DIR}"
    
    # Set build arguments
    export BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
    export VCS_REF=$(git -C "${PROJECT_ROOT}" rev-parse --short HEAD 2>/dev/null || echo "unknown")
    export VERSION=${VERSION:-latest}
    
    # Build images with build args
    ${DOCKER_COMPOSE_CMD} -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" build \
        --build-arg BUILD_DATE="${BUILD_DATE}" \
        --build-arg VCS_REF="${VCS_REF}" \
        --build-arg VERSION="${VERSION}" \
        --no-cache
    
    log_info "Images built successfully."
}

deploy_services() {
    log_info "Deploying services..."
    
    cd "${DOCKER_DIR}"
    
    # Pull latest images (if using registry)
    # docker-compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" pull
    
    # Start services
    ${DOCKER_COMPOSE_CMD} -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" up -d
    
    log_info "Services deployed."
}

wait_for_health() {
    log_info "Waiting for services to become healthy..."
    
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if ${DOCKER_COMPOSE_CMD} -f "${COMPOSE_FILE}" ps | grep -q "healthy"; then
            log_info "Services are healthy."
            return 0
        fi
        
        attempt=$((attempt + 1))
        sleep 2
    done
    
    log_warn "Some services may not be healthy. Check logs with: ${DOCKER_COMPOSE_CMD} -f ${COMPOSE_FILE} logs"
}

show_status() {
    log_info "Deployment status:"
    cd "${DOCKER_DIR}"
    ${DOCKER_COMPOSE_CMD} -f "${COMPOSE_FILE}" ps
    
    log_info "Service URLs:"
    echo "  - Healing Dashboard: http://localhost:${HEALING_DASHBOARD_PORT:-5001}"
    echo "  - Monitoring Server: http://localhost:${MONITORING_SERVER_PORT:-5000}"
    echo "  - Model API: http://localhost:${MODEL_PORT:-8080}"
    echo "  - Incident Bot: http://localhost:${INCIDENT_BOT_PORT:-8001}"
    echo "  - Prometheus: http://localhost:${PROMETHEUS_PORT:-9090}"
}

# Main execution
main() {
    log_info "Starting Heal-X-Bot production deployment..."
    
    check_prerequisites
    backup_existing
    build_images
    deploy_services
    wait_for_health
    show_status
    
    log_info "Deployment completed successfully!"
}

# Run main function
main "$@"

