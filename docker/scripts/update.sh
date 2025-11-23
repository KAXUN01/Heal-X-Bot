#!/bin/bash
# =============================================================================
# Heal-X-Bot Update Script
# =============================================================================
# This script updates the Heal-X-Bot deployment with zero downtime
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
        log_error "Docker Compose is not installed."
        exit 1
    fi
}

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

pull_latest() {
    log_info "Pulling latest code..."
    cd "${PROJECT_ROOT}"
    git pull || log_warn "Git pull failed. Continuing with local code..."
}

backup_before_update() {
    log_info "Creating backup before update..."
    "${SCRIPT_DIR}/backup.sh" || log_warn "Backup failed. Continuing anyway..."
}

update_images() {
    log_info "Updating Docker images..."
    
    cd "${DOCKER_DIR}"
    detect_docker_compose
    
    # Set build arguments
    export BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
    export VCS_REF=$(git -C "${PROJECT_ROOT}" rev-parse --short HEAD 2>/dev/null || echo "unknown")
    export VERSION=${VERSION:-latest}
    
    # Build new images with build args
    ${DOCKER_COMPOSE_CMD} -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" build \
        --build-arg BUILD_DATE="${BUILD_DATE}" \
        --build-arg VCS_REF="${VCS_REF}" \
        --build-arg VERSION="${VERSION}"
    
    log_info "Images updated."
}

rolling_update() {
    log_info "Performing rolling update..."
    
    cd "${DOCKER_DIR}"
    detect_docker_compose
    
    # Update services one by one to minimize downtime
    services=("model" "server" "healing-dashboard" "incident-bot")
    
    for service in "${services[@]}"; do
        log_info "Updating ${service}..."
        ${DOCKER_COMPOSE_CMD} -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" up -d --no-deps "${service}"
        
        # Wait for service to be healthy
        sleep 5
        if ${DOCKER_COMPOSE_CMD} -f "${COMPOSE_FILE}" ps "${service}" | grep -q "healthy"; then
            log_info "${service} updated successfully."
        else
            log_warn "${service} may not be healthy. Check logs."
        fi
    done
}

verify_deployment() {
    log_info "Verifying deployment..."
    
    cd "${DOCKER_DIR}"
    detect_docker_compose
    
    # Check all services are running
    if ${DOCKER_COMPOSE_CMD} -f "${COMPOSE_FILE}" ps | grep -q "Up"; then
        log_info "All services are running."
        return 0
    else
        log_error "Some services are not running."
        return 1
    fi
}

# Main execution
main() {
    log_info "Starting Heal-X-Bot update..."
    
    pull_latest
    backup_before_update
    update_images
    rolling_update
    verify_deployment
    
    log_info "Update completed successfully!"
}

# Run main function
main "$@"

