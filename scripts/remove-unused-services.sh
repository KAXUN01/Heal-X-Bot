#!/bin/bash
# Remove unused services: nginx, mysql, postgresql, and crazy_hodgkin
# This script removes systemd services and Docker containers

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🗑️  Removing unused services from the system...${NC}"
echo ""

# Function to check if systemd service exists
service_exists() {
    systemctl list-unit-files | grep -q "^${1}\." || \
    systemctl list-units --all | grep -q "${1}"
}

# Function to check if Docker container exists
container_exists() {
    docker ps -a --format '{{.Names}}' | grep -q "^${1}$" 2>/dev/null || \
    docker ps -a --format '{{.Names}}' | grep -q "${1}" 2>/dev/null
}

# Function to check if Docker volume exists
volume_exists() {
    docker volume ls --format '{{.Name}}' | grep -q "^${1}$" 2>/dev/null || \
    docker volume ls --format '{{.Name}}' | grep -q "${1}" 2>/dev/null
}

# 1. Remove systemd services
echo -e "${BLUE}📋 Checking systemd services...${NC}"

SERVICES=("nginx" "mysql" "postgresql")

for service in "${SERVICES[@]}"; do
    echo -n "   Checking ${service}... "
    
    # Try different service name variations
    SERVICE_NAMES=("${service}" "${service}.service" "mariadb" "mariadb.service")
    
    FOUND=false
    for svc_name in "${SERVICE_NAMES[@]}"; do
        if systemctl list-unit-files 2>/dev/null | grep -q "^${svc_name}" || \
           systemctl list-units --all 2>/dev/null | grep -q "${svc_name}"; then
            FOUND=true
            ACTUAL_NAME=$(systemctl list-unit-files 2>/dev/null | grep "^${svc_name}" | head -1 | awk '{print $1}' || \
                          systemctl list-units --all 2>/dev/null | grep "${svc_name}" | head -1 | awk '{print $1}')
            
            if [ -n "$ACTUAL_NAME" ]; then
                echo -e "${YELLOW}found${NC}"
                echo "      Stopping ${ACTUAL_NAME}..."
                sudo systemctl stop "${ACTUAL_NAME}" 2>/dev/null || true
                echo "      Disabling ${ACTUAL_NAME}..."
                sudo systemctl disable "${ACTUAL_NAME}" 2>/dev/null || true
                echo -e "      ${GREEN}✅ ${ACTUAL_NAME} stopped and disabled${NC}"
            fi
            break
        fi
    done
    
    if [ "$FOUND" = false ]; then
        echo -e "${GREEN}not found${NC}"
    fi
done

echo ""

# 2. Remove Docker containers
echo -e "${BLUE}🐳 Checking Docker containers...${NC}"

CONTAINERS=("nginx-container" "mysql-container" "postgresql-container" "crazy_hodgkin")

for container in "${CONTAINERS[@]}"; do
    echo -n "   Checking ${container}... "
    
    # Check for exact match or partial match
    if docker ps -a --format '{{.Names}}' 2>/dev/null | grep -q "^${container}$" || \
       docker ps -a --format '{{.Names}}' 2>/dev/null | grep -q "${container}"; then
        echo -e "${YELLOW}found${NC}"
        
        # Get actual container name
        ACTUAL_NAME=$(docker ps -a --format '{{.Names}}' 2>/dev/null | grep -E "^${container}$|${container}" | head -1)
        
        if [ -n "$ACTUAL_NAME" ]; then
            echo "      Stopping ${ACTUAL_NAME}..."
            docker stop "${ACTUAL_NAME}" 2>/dev/null || true
            echo "      Removing ${ACTUAL_NAME}..."
            docker rm "${ACTUAL_NAME}" 2>/dev/null || true
            echo -e "      ${GREEN}✅ ${ACTUAL_NAME} removed${NC}"
        fi
    else
        echo -e "${GREEN}not found${NC}"
    fi
done

echo ""

# 3. Remove Docker volumes
echo -e "${BLUE}💾 Checking Docker volumes...${NC}"

VOLUMES=("nginx-html" "nginx-data" "mysql-data" "postgresql-data" "postgres-data")

for volume in "${VOLUMES[@]}"; do
    echo -n "   Checking ${volume}... "
    
    if docker volume ls --format '{{.Name}}' 2>/dev/null | grep -q "^${volume}$" || \
       docker volume ls --format '{{.Name}}' 2>/dev/null | grep -q "${volume}"; then
        echo -e "${YELLOW}found${NC}"
        
        # Get actual volume name
        ACTUAL_NAME=$(docker volume ls --format '{{.Name}}' 2>/dev/null | grep -E "^${volume}$|${volume}" | head -1)
        
        if [ -n "$ACTUAL_NAME" ]; then
            echo "      Removing volume ${ACTUAL_NAME}..."
            docker volume rm "${ACTUAL_NAME}" 2>/dev/null || true
            echo -e "      ${GREEN}✅ Volume ${ACTUAL_NAME} removed${NC}"
        fi
    else
        echo -e "${GREEN}not found${NC}"
    fi
done

echo ""
echo -e "${GREEN}✨ Service removal completed!${NC}"
echo ""
echo -e "${YELLOW}📝 Note:${NC}"
echo "   - Systemd services have been stopped and disabled"
echo "   - Docker containers have been removed"
echo "   - Docker volumes have been removed"
echo "   - If services still appear in your management interface, you may need to refresh it"
echo ""

