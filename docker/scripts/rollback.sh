#!/bin/bash
# =============================================================================
# Heal-X-Bot Rollback Script
# =============================================================================
# This script rolls back to a previous deployment version
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
BACKUP_DIR="${PROJECT_ROOT}/backups"

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

list_backups() {
    log_info "Available backups:"
    if [ -d "${BACKUP_DIR}" ]; then
        ls -1t "${BACKUP_DIR}" | nl
    else
        log_error "No backups directory found."
        exit 1
    fi
}

select_backup() {
    if [ -z "${1:-}" ]; then
        list_backups
        echo ""
        read -p "Enter backup number to restore: " backup_num
        BACKUP_NAME=$(ls -1t "${BACKUP_DIR}" | sed -n "${backup_num}p")
    else
        BACKUP_NAME="$1"
    fi
    
    if [ -z "${BACKUP_NAME}" ] || [ ! -d "${BACKUP_DIR}/${BACKUP_NAME}" ]; then
        log_error "Invalid backup selection."
        exit 1
    fi
    
    log_info "Selected backup: ${BACKUP_NAME}"
}

stop_services() {
    log_info "Stopping current services..."
    cd "${DOCKER_DIR}"
    detect_docker_compose
    ${DOCKER_COMPOSE_CMD} -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" down
}

restore_backup() {
    log_info "Restoring from backup..."
    
    BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"
    
    # Restore environment file
    if [ -f "${BACKUP_PATH}/.env.production" ]; then
        cp "${BACKUP_PATH}/.env.production" "${ENV_FILE}"
        log_info "Environment file restored."
    fi
    
    # Restore volumes
    if [ -f "${BACKUP_PATH}/healing-data.tar.gz" ]; then
        log_info "Restoring volumes..."
        docker volume create heal-x-bot_healing-data 2>/dev/null || true
        docker run --rm \
            -v heal-x-bot_healing-data:/data \
            -v "${BACKUP_PATH}:/backup" \
            alpine sh -c "cd /data && tar xzf /backup/healing-data.tar.gz"
        log_info "Volumes restored."
    fi
}

restore_images() {
    log_info "Restoring previous images..."
    
    # If using image tags, restore previous version
    # For now, rebuild from current code
    cd "${DOCKER_DIR}"
    detect_docker_compose
    
    export BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
    export VCS_REF=$(git -C "${PROJECT_ROOT}" rev-parse --short HEAD 2>/dev/null || echo "unknown")
    export VERSION=rollback
    
    ${DOCKER_COMPOSE_CMD} -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" build
}

start_services() {
    log_info "Starting services..."
    cd "${DOCKER_DIR}"
    detect_docker_compose
    ${DOCKER_COMPOSE_CMD} -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" up -d
}

verify_rollback() {
    log_info "Verifying rollback..."
    sleep 10
    
    cd "${DOCKER_DIR}"
    detect_docker_compose
    if ${DOCKER_COMPOSE_CMD} -f "${COMPOSE_FILE}" ps | grep -q "Up"; then
        log_info "Rollback successful!"
        return 0
    else
        log_error "Rollback may have failed. Check logs."
        return 1
    fi
}

# Main execution
main() {
    log_info "Starting Heal-X-Bot rollback..."
    
    if [ "${1:-}" = "--list" ]; then
        list_backups
        exit 0
    fi
    
    select_backup "${1:-}"
    stop_services
    restore_backup
    restore_images
    start_services
    verify_rollback
    
    log_info "Rollback completed!"
}

# Run main function
main "$@"

