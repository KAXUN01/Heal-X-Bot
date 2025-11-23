#!/bin/bash
# =============================================================================
# Heal-X-Bot Restore Script
# =============================================================================
# This script restores data from a backup
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
BACKUP_BASE_DIR="${PROJECT_ROOT}/backups"

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
    if [ -d "${BACKUP_BASE_DIR}" ]; then
        local count=1
        for backup in $(ls -1t "${BACKUP_BASE_DIR}" | grep -E "\.tar\.gz$|^[0-9]{8}_[0-9]{6}$"); do
            echo "  ${count}. ${backup}"
            count=$((count + 1))
        done
    else
        log_error "No backups directory found."
        exit 1
    fi
}

select_backup() {
    if [ -z "${1:-}" ]; then
        list_backups
        echo ""
        read -p "Enter backup number or name to restore: " backup_input
        
        if [[ "${backup_input}" =~ ^[0-9]+$ ]]; then
            BACKUP_NAME=$(ls -1t "${BACKUP_BASE_DIR}" | grep -E "\.tar\.gz$|^[0-9]{8}_[0-9]{6}$" | sed -n "${backup_input}p")
        else
            BACKUP_NAME="${backup_input}"
        fi
    else
        BACKUP_NAME="$1"
    fi
    
    if [ -z "${BACKUP_NAME}" ]; then
        log_error "Invalid backup selection."
        exit 1
    fi
    
    # Check if it's a compressed backup
    if [[ "${BACKUP_NAME}" == *.tar.gz ]]; then
        BACKUP_PATH="${BACKUP_BASE_DIR}/${BACKUP_NAME}"
        EXTRACT_DIR="${BACKUP_BASE_DIR}/$(basename "${BACKUP_NAME}" .tar.gz)"
        
        if [ ! -f "${BACKUP_PATH}" ]; then
            log_error "Backup file not found: ${BACKUP_PATH}"
            exit 1
        fi
        
        log_info "Extracting backup..."
        mkdir -p "${EXTRACT_DIR}"
        tar xzf "${BACKUP_PATH}" -C "${BACKUP_BASE_DIR}"
        BACKUP_DIR="${EXTRACT_DIR}"
    else
        BACKUP_DIR="${BACKUP_BASE_DIR}/${BACKUP_NAME}"
    fi
    
    if [ ! -d "${BACKUP_DIR}" ]; then
        log_error "Backup directory not found: ${BACKUP_DIR}"
        exit 1
    fi
    
    log_info "Selected backup: ${BACKUP_NAME}"
    log_info "Backup location: ${BACKUP_DIR}"
}

stop_services() {
    log_warn "Stopping services before restore..."
    read -p "Continue? (y/N): " confirm
    if [ "${confirm}" != "y" ] && [ "${confirm}" != "Y" ]; then
        log_info "Restore cancelled."
        exit 0
    fi
    
    cd "${DOCKER_DIR}"
    # Try docker compose V2 first, then V1
    docker compose -f docker-compose.prod.yml down 2>/dev/null || \
    docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
}

restore_volumes() {
    log_info "Restoring volumes..."
    
    # Restore healing-data
    if [ -f "${BACKUP_DIR}/healing-data.tar.gz" ]; then
        log_info "Restoring healing-data volume..."
        docker volume create heal-x-bot_healing-data 2>/dev/null || true
        docker run --rm \
            -v heal-x-bot_healing-data:/data \
            -v "${BACKUP_DIR}:/backup" \
            alpine sh -c "cd /data && tar xzf /backup/healing-data.tar.gz"
        log_info "healing-data volume restored."
    fi
    
    # Restore Prometheus data
    if [ -f "${BACKUP_DIR}/prometheus-data.tar.gz" ]; then
        log_info "Restoring Prometheus data..."
        docker volume create heal-x-bot_prometheus_data 2>/dev/null || true
        docker run --rm \
            -v heal-x-bot_prometheus_data:/data \
            -v "${BACKUP_DIR}:/backup" \
            alpine sh -c "cd /data && tar xzf /backup/prometheus-data.tar.gz"
        log_info "Prometheus data restored."
    fi
    
    # Restore model cache
    if [ -f "${BACKUP_DIR}/model-cache.tar.gz" ]; then
        log_info "Restoring model cache..."
        docker volume create heal-x-bot_model-cache 2>/dev/null || true
        docker run --rm \
            -v heal-x-bot_model-cache:/data \
            -v "${BACKUP_DIR}:/backup" \
            alpine sh -c "cd /data && tar xzf /backup/model-cache.tar.gz"
        log_info "Model cache restored."
    fi
}

restore_configuration() {
    log_info "Restoring configuration..."
    
    # Restore environment file
    if [ -f "${BACKUP_DIR}/.env.production" ]; then
        cp "${BACKUP_DIR}/.env.production" "${DOCKER_DIR}/.env.production"
        log_info "Environment file restored."
    fi
    
    # Restore model files
    if [ -f "${BACKUP_DIR}/model-files.tar.gz" ]; then
        log_info "Restoring model files..."
        tar xzf "${BACKUP_DIR}/model-files.tar.gz" -C "${PROJECT_ROOT}"
        log_info "Model files restored."
    fi
}

restore_databases() {
    log_info "Restoring databases..."
    
    # Copy database files to volume
    if docker volume ls | grep -q "heal-x-bot_healing-data"; then
        for db_file in "${BACKUP_DIR}"/*.db; do
            if [ -f "${db_file}" ]; then
                log_info "Restoring database: $(basename "${db_file}")"
                docker run --rm \
                    -v heal-x-bot_healing-data:/data \
                    -v "${BACKUP_DIR}:/backup" \
                    alpine cp "/backup/$(basename "${db_file}")" "/data/"
            fi
        done
        log_info "Databases restored."
    fi
}

start_services() {
    log_info "Starting services..."
    cd "${DOCKER_DIR}"
    # Try docker compose V2 first, then V1
    docker compose -f docker-compose.prod.yml up -d 2>/dev/null || \
    docker-compose -f docker-compose.prod.yml up -d
    sleep 5
    log_info "Services started."
}

# Main execution
main() {
    log_info "Starting Heal-X-Bot restore..."
    
    if [ "${1:-}" = "--list" ]; then
        list_backups
        exit 0
    fi
    
    select_backup "${1:-}"
    stop_services
    restore_volumes
    restore_configuration
    restore_databases
    start_services
    
    log_info "Restore completed successfully!"
}

# Run main function
main "$@"

