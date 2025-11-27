#!/bin/bash
# =============================================================================
# Heal-X-Bot Backup Script
# =============================================================================
# This script creates backups of data, volumes, and configuration
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
BACKUP_DIR="${BACKUP_BASE_DIR}/$(date +%Y%m%d_%H%M%S)"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

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

create_backup_dir() {
    mkdir -p "${BACKUP_DIR}"
    log_info "Backup directory created: ${BACKUP_DIR}"
}

backup_volumes() {
    log_info "Backing up Docker volumes..."
    
    # Backup healing-data volume
    if docker volume ls | grep -q "heal-x-bot_healing-data"; then
        log_info "Backing up healing-data volume..."
        docker run --rm \
            -v heal-x-bot_healing-data:/data:ro \
            -v "${BACKUP_DIR}:/backup" \
            alpine tar czf /backup/healing-data.tar.gz -C /data . 2>/dev/null || log_warn "Failed to backup healing-data volume"
    fi
    
    # Backup prometheus data
    if docker volume ls | grep -q "heal-x-bot_prometheus_data"; then
        log_info "Backing up Prometheus data..."
        docker run --rm \
            -v heal-x-bot_prometheus_data:/data:ro \
            -v "${BACKUP_DIR}:/backup" \
            alpine tar czf /backup/prometheus-data.tar.gz -C /data . 2>/dev/null || log_warn "Failed to backup Prometheus data"
    fi
    
    # Backup model cache
    if docker volume ls | grep -q "heal-x-bot_model-cache"; then
        log_info "Backing up model cache..."
        docker run --rm \
            -v heal-x-bot_model-cache:/data:ro \
            -v "${BACKUP_DIR}:/backup" \
            alpine tar czf /backup/model-cache.tar.gz -C /data . 2>/dev/null || log_warn "Failed to backup model cache"
    fi
}

backup_configuration() {
    log_info "Backing up configuration files..."
    
    # Backup environment file
    if [ -f "${DOCKER_DIR}/.env.production" ]; then
        cp "${DOCKER_DIR}/.env.production" "${BACKUP_DIR}/.env.production"
        log_info "Environment file backed up."
    fi
    
    # Backup docker-compose file
    if [ -f "${DOCKER_DIR}/docker-compose.prod.yml" ]; then
        cp "${DOCKER_DIR}/docker-compose.prod.yml" "${BACKUP_DIR}/docker-compose.prod.yml"
        log_info "Docker Compose file backed up."
    fi
    
    # Backup model files
    if [ -d "${PROJECT_ROOT}/model" ]; then
        tar czf "${BACKUP_DIR}/model-files.tar.gz" -C "${PROJECT_ROOT}" model/ddos_model.keras model/ddos_model model/artifacts 2>/dev/null || log_warn "Failed to backup model files"
        log_info "Model files backed up."
    fi
}

backup_database() {
    log_info "Backing up databases..."
    
    # Backup SQLite databases from volumes
    if docker volume ls | grep -q "heal-x-bot_healing-data"; then
        docker run --rm \
            -v heal-x-bot_healing-data:/data:ro \
            -v "${BACKUP_DIR}:/backup" \
            alpine sh -c "find /data -name '*.db' -exec cp {} /backup/ \;" 2>/dev/null || log_warn "Failed to backup databases"
        log_info "Databases backed up."
    fi
}

create_backup_manifest() {
    log_info "Creating backup manifest..."
    
    cat > "${BACKUP_DIR}/MANIFEST.txt" << EOF
Heal-X-Bot Backup Manifest
==========================
Backup Date: $(date -u +'%Y-%m-%d %H:%M:%S UTC')
Backup Location: ${BACKUP_DIR}
System: $(uname -a)
Docker Version: $(docker --version)
Docker Compose Version: $(docker compose version 2>/dev/null || docker-compose --version 2>/dev/null || echo "not installed")

Contents:
$(ls -lh "${BACKUP_DIR}")

Volumes Backed Up:
$(docker volume ls | grep "heal-x-bot" || echo "No volumes found")

Services Status:
$(cd "${DOCKER_DIR}" && (docker compose -f docker-compose.prod.yml ps 2>/dev/null || docker-compose -f docker-compose.prod.yml ps 2>/dev/null || echo "Services not running"))
EOF

    log_info "Manifest created."
}

compress_backup() {
    log_info "Compressing backup..."
    
    cd "${BACKUP_BASE_DIR}"
    tar czf "$(basename "${BACKUP_DIR}").tar.gz" "$(basename "${BACKUP_DIR}")"
    rm -rf "${BACKUP_DIR}"
    
    BACKUP_FILE="${BACKUP_BASE_DIR}/$(basename "${BACKUP_DIR}").tar.gz"
    log_info "Backup compressed: ${BACKUP_FILE}"
    echo "Backup size: $(du -h "${BACKUP_FILE}" | cut -f1)"
}

cleanup_old_backups() {
    log_info "Cleaning up old backups (older than ${RETENTION_DAYS} days)..."
    
    find "${BACKUP_BASE_DIR}" -name "*.tar.gz" -type f -mtime +${RETENTION_DAYS} -delete 2>/dev/null || true
    find "${BACKUP_BASE_DIR}" -type d -mtime +${RETENTION_DAYS} -exec rm -rf {} + 2>/dev/null || true
    
    log_info "Old backups cleaned up."
}

# Main execution
main() {
    log_info "Starting Heal-X-Bot backup..."
    
    create_backup_dir
    backup_volumes
    backup_configuration
    backup_database
    create_backup_manifest
    
    if [ "${COMPRESS:-true}" = "true" ]; then
        compress_backup
    fi
    
    cleanup_old_backups
    
    log_info "Backup completed successfully!"
    log_info "Backup location: ${BACKUP_FILE:-${BACKUP_DIR}}"
}

# Run main function
main "$@"

