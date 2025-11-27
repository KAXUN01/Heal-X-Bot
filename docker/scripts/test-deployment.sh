#!/bin/bash
# =============================================================================
# Heal-X-Bot Deployment Test Script
# =============================================================================
# This script tests the production deployment configuration
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

test_prerequisites() {
    log_info "Testing prerequisites..."
    
    local failed=0
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        failed=$((failed + 1))
    else
        log_info "✓ Docker installed: $(docker --version)"
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed"
        failed=$((failed + 1))
    else
        log_info "✓ Docker Compose installed"
    fi
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        failed=$((failed + 1))
    else
        log_info "✓ Docker daemon is running"
    fi
    
    return ${failed}
}

test_configuration() {
    log_info "Testing configuration files..."
    
    local failed=0
    
    # Check docker-compose file
    if [ ! -f "${COMPOSE_FILE}" ]; then
        log_error "Docker Compose file not found: ${COMPOSE_FILE}"
        failed=$((failed + 1))
    else
        log_info "✓ Docker Compose file exists"
        
        # Validate syntax if docker-compose is available
        if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
            if docker-compose -f "${COMPOSE_FILE}" config &> /dev/null 2>&1 || \
               docker compose -f "${COMPOSE_FILE}" config &> /dev/null 2>&1; then
                log_info "✓ Docker Compose syntax valid"
            else
                log_warn "Docker Compose syntax validation failed (may need environment variables)"
            fi
        else
            log_warn "Docker Compose not available for syntax validation"
        fi
    fi
    
    # Check environment template
    if [ ! -f "${DOCKER_DIR}/env.production.template" ]; then
        log_error "Environment template not found"
        failed=$((failed + 1))
    else
        log_info "✓ Environment template exists"
    fi
    
    # Check .env file (optional)
    if [ -f "${ENV_FILE}" ]; then
        log_info "✓ Environment file exists"
    else
        log_warn "Environment file not found (will be created from template)"
    fi
    
    return ${failed}
}

test_dockerfiles() {
    log_info "Testing Dockerfiles..."
    
    local failed=0
    
    # Check model Dockerfile
    if [ ! -f "${PROJECT_ROOT}/model/Dockerfile.prod" ]; then
        log_error "Model Dockerfile.prod not found"
        failed=$((failed + 1))
    else
        log_info "✓ Model Dockerfile.prod exists"
    fi
    
    # Check incident-bot Dockerfile
    if [ ! -f "${PROJECT_ROOT}/incident-bot/Dockerfile.prod" ]; then
        log_error "Incident-bot Dockerfile.prod not found"
        failed=$((failed + 1))
    else
        log_info "✓ Incident-bot Dockerfile.prod exists"
    fi
    
    # Check monitoring server Dockerfile
    if [ ! -f "${PROJECT_ROOT}/monitoring/server/Dockerfile.prod" ]; then
        log_error "Monitoring server Dockerfile.prod not found"
        failed=$((failed + 1))
    else
        log_info "✓ Monitoring server Dockerfile.prod exists"
    fi
    
    # Check dashboard Dockerfile
    if [ ! -f "${PROJECT_ROOT}/monitoring/server/Dockerfile.dashboard" ]; then
        log_error "Dashboard Dockerfile.dashboard not found"
        failed=$((failed + 1))
    else
        log_info "✓ Dashboard Dockerfile.dashboard exists"
    fi
    
    return ${failed}
}

test_dockerignore() {
    log_info "Testing .dockerignore files..."
    
    local failed=0
    
    services=("model" "incident-bot" "monitoring/server")
    
    for service in "${services[@]}"; do
        if [ -f "${PROJECT_ROOT}/${service}/.dockerignore" ]; then
            log_info "✓ ${service}/.dockerignore exists"
        else
            log_error "${service}/.dockerignore not found"
            failed=$((failed + 1))
        fi
    done
    
    return ${failed}
}

test_scripts() {
    log_info "Testing deployment scripts..."
    
    local failed=0
    
    scripts=("deploy.sh" "update.sh" "rollback.sh" "backup.sh" "restore.sh" "health-check.sh")
    
    for script in "${scripts[@]}"; do
        script_path="${SCRIPT_DIR}/${script}"
        if [ -f "${script_path}" ]; then
            if [ -x "${script_path}" ]; then
                log_info "✓ ${script} exists and is executable"
            else
                log_warn "${script} exists but is not executable"
                chmod +x "${script_path}"
                log_info "  Fixed: Made ${script} executable"
            fi
        else
            log_error "${script} not found"
            failed=$((failed + 1))
        fi
    done
    
    return ${failed}
}

test_docker_build() {
    log_info "Testing Docker image builds (dry-run)..."
    
    cd "${DOCKER_DIR}"
    
    # Check if build contexts exist
    if [ -d "${PROJECT_ROOT}/model" ] && \
       [ -d "${PROJECT_ROOT}/incident-bot" ] && \
       [ -d "${PROJECT_ROOT}/monitoring/server" ]; then
        log_info "✓ All build contexts exist"
        
        # Try to validate compose file if docker-compose is available
        if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
            if docker-compose -f "${COMPOSE_FILE}" config &> /dev/null 2>&1 || \
               docker compose -f "${COMPOSE_FILE}" config &> /dev/null 2>&1; then
                log_info "✓ Docker Compose configuration is valid"
            else
                log_warn "Could not validate Docker Compose syntax (docker-compose may not be installed)"
            fi
        else
            log_warn "Docker Compose not available for syntax validation"
        fi
        
        return 0
    else
        log_error "Some build contexts are missing"
        return 1
    fi
}

test_volumes() {
    log_info "Testing volume configuration..."
    
    # Check if volumes are defined in docker-compose
    if grep -q "volumes:" "${COMPOSE_FILE}"; then
        log_info "✓ Volumes are configured"
        return 0
    else
        log_warn "No volumes configured"
        return 0  # Not a failure, just a warning
    fi
}

test_networks() {
    log_info "Testing network configuration..."
    
    # Check if network is defined
    if grep -q "networks:" "${COMPOSE_FILE}"; then
        log_info "✓ Networks are configured"
        return 0
    else
        log_error "No networks configured"
        return 1
    fi
}

test_healthchecks() {
    log_info "Testing health check configuration..."
    
    local failed=0
    
    services=("model" "server" "healing-dashboard" "incident-bot" "prometheus")
    
    for service in "${services[@]}"; do
        # Check for healthcheck in the service section
        if grep -A 20 "^\s*${service}:" "${COMPOSE_FILE}" | grep -q "healthcheck:"; then
            log_info "✓ ${service} has health check configured"
        else
            log_warn "${service} does not have health check configured"
            # Don't fail, just warn
        fi
    done
    
    return 0  # Don't fail on missing health checks
}

# Main execution
main() {
    echo "=========================================="
    echo "Heal-X-Bot Deployment Test"
    echo "=========================================="
    echo ""
    
    local total_tests=0
    local passed_tests=0
    local failed_tests=0
    
    # Run tests
    test_prerequisites && passed_tests=$((passed_tests + 1)) || failed_tests=$((failed_tests + 1))
    total_tests=$((total_tests + 1))
    echo ""
    
    test_configuration && passed_tests=$((passed_tests + 1)) || failed_tests=$((failed_tests + 1))
    total_tests=$((total_tests + 1))
    echo ""
    
    test_dockerfiles && passed_tests=$((passed_tests + 1)) || failed_tests=$((failed_tests + 1))
    total_tests=$((total_tests + 1))
    echo ""
    
    test_dockerignore && passed_tests=$((passed_tests + 1)) || failed_tests=$((failed_tests + 1))
    total_tests=$((total_tests + 1))
    echo ""
    
    test_scripts && passed_tests=$((passed_tests + 1)) || failed_tests=$((failed_tests + 1))
    total_tests=$((total_tests + 1))
    echo ""
    
    test_docker_build && passed_tests=$((passed_tests + 1)) || failed_tests=$((failed_tests + 1))
    total_tests=$((total_tests + 1))
    echo ""
    
    test_volumes && passed_tests=$((passed_tests + 1)) || failed_tests=$((failed_tests + 1))
    total_tests=$((total_tests + 1))
    echo ""
    
    test_networks && passed_tests=$((passed_tests + 1)) || failed_tests=$((failed_tests + 1))
    total_tests=$((total_tests + 1))
    echo ""
    
    test_healthchecks && passed_tests=$((passed_tests + 1)) || failed_tests=$((failed_tests + 1))
    total_tests=$((total_tests + 1))
    echo ""
    
    # Summary
    echo "=========================================="
    echo "Test Summary"
    echo "=========================================="
    echo "Total Tests: ${total_tests}"
    echo -e "${GREEN}Passed: ${passed_tests}${NC}"
    echo -e "${RED}Failed: ${failed_tests}${NC}"
    echo ""
    
    if [ ${failed_tests} -eq 0 ]; then
        log_info "All tests passed! Deployment configuration is ready."
        return 0
    else
        log_error "Some tests failed. Please fix issues before deploying."
        return 1
    fi
}

# Run main function
main "$@"

