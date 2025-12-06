#!/bin/bash
# Pull and create Docker containers for nginx, mysql, and postgresql

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🐳 Pulling and creating Docker containers for nginx, mysql, and postgresql...${NC}"
echo ""

# Function to check if container exists
container_exists() {
    docker ps -a --format '{{.Names}}' | grep -q "^${1}$"
}

# Function to check if container is running
container_running() {
    docker ps --format '{{.Names}}' | grep -q "^${1}$"
}

# Function to stop and remove container
cleanup_container() {
    if container_exists "$1"; then
        echo -e "${YELLOW}⚠️  Container '$1' already exists. Removing it...${NC}"
        if container_running "$1"; then
            docker stop "$1" > /dev/null 2>&1
        fi
        docker rm "$1" > /dev/null 2>&1
    fi
}

# 1. Pull images
echo -e "${BLUE}📥 Pulling Docker images...${NC}"
echo ""

echo "📥 Pulling nginx image..."
docker pull nginx:latest

echo "📥 Pulling mysql image..."
docker pull mysql:latest

echo "📥 Pulling postgresql image..."
docker pull postgres:latest

echo ""
echo -e "${GREEN}✅ All images pulled successfully!${NC}"
echo ""

# 2. Cleanup existing containers (optional)
echo -e "${BLUE}🧹 Cleaning up existing containers (if any)...${NC}"
cleanup_container "nginx-container"
cleanup_container "mysql-container"
cleanup_container "postgresql-container"
echo ""

# 3. Create and start containers
echo -e "${BLUE}🚀 Creating and starting containers...${NC}"
echo ""

# Create PostgreSQL container
echo "🐘 Creating PostgreSQL container..."
docker run -d \
    --name postgresql-container \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_PASSWORD=postgres \
    -e POSTGRES_DB=healxdb \
    -p 5432:5432 \
    -v postgresql-data:/var/lib/postgresql/data \
    postgres:latest

echo -e "${GREEN}✅ PostgreSQL container created and started!${NC}"
echo "   - Port: 5432"
echo "   - User: postgres"
echo "   - Password: postgres"
echo "   - Database: healxdb"
echo ""

# Create MySQL container
echo "🐬 Creating MySQL container..."
docker run -d \
    --name mysql-container \
    -e MYSQL_ROOT_PASSWORD=rootpassword \
    -e MYSQL_DATABASE=healxdb \
    -e MYSQL_USER=healxuser \
    -e MYSQL_PASSWORD=healxpass \
    -p 3306:3306 \
    -v mysql-data:/var/lib/mysql \
    mysql:latest

echo -e "${GREEN}✅ MySQL container created and started!${NC}"
echo "   - Port: 3306"
echo "   - Root Password: rootpassword"
echo "   - Database: healxdb"
echo "   - User: healxuser"
echo "   - Password: healxpass"
echo ""

# Create Nginx container
echo "🌐 Creating Nginx container..."
docker run -d \
    --name nginx-container \
    -p 8080:80 \
    -v nginx-html:/usr/share/nginx/html \
    nginx:latest

echo -e "${GREEN}✅ Nginx container created and started!${NC}"
echo "   - Port: 8080 (mapped to container port 80)"
echo "   - Access: http://localhost:8080"
echo ""

# 4. Display status
echo -e "${BLUE}📊 Container Status:${NC}"
docker ps --filter "name=nginx-container" --filter "name=mysql-container" --filter "name=postgresql-container" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo -e "${GREEN}✨ All containers are up and running!${NC}"
echo ""
echo -e "${YELLOW}📝 Quick Commands:${NC}"
echo "   - View logs: docker logs <container-name>"
echo "   - Stop containers: docker stop nginx-container mysql-container postgresql-container"
echo "   - Start containers: docker start nginx-container mysql-container postgresql-container"
echo "   - Remove containers: docker rm -f nginx-container mysql-container postgresql-container"
echo ""
echo -e "${YELLOW}💡 Note:${NC}"
echo "   - PostgreSQL data is persisted in volume: postgresql-data"
echo "   - MySQL data is persisted in volume: mysql-data"
echo "   - Nginx HTML files are in volume: nginx-html"
echo ""

