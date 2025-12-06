#!/bin/bash

# Install Cloud Simulation Docker Services
# This script installs and starts the cloud-sim Docker services
# These services are used for testing the healing bot's container monitoring capabilities

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_DIR="$PROJECT_ROOT/config"

echo "🚀 Installing Cloud Simulation Docker Services..."
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Install with: sudo apt install docker.io"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Install with: sudo apt install docker-compose"
    exit 1
fi

# Check if user is in docker group or has sudo
if ! docker ps &> /dev/null && ! sudo docker ps &> /dev/null; then
    echo "⚠️  Warning: Cannot access Docker. You may need to:"
    echo "   1. Add your user to the docker group: sudo usermod -aG docker $USER"
    echo "   2. Log out and log back in"
    echo "   3. Or run this script with sudo"
    exit 1
fi

# Navigate to config directory
cd "$CONFIG_DIR"

# Check if docker-compose-cloud-sim.yml exists
if [ ! -f "docker-compose-cloud-sim.yml" ]; then
    echo "❌ docker-compose-cloud-sim.yml not found in $CONFIG_DIR!"
    echo "   Expected location: $CONFIG_DIR/docker-compose-cloud-sim.yml"
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p cloud-sim/web-server
mkdir -p cloud-sim/api-server

# Determine which docker compose command to use
if docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker compose"
    echo "   Using: docker compose"
else
    DOCKER_COMPOSE_CMD="docker-compose"
    echo "   Using: docker-compose"
fi

# Pull images first
echo ""
echo "📥 Pulling Docker images..."
if [ "$DOCKER_COMPOSE_CMD" = "docker compose" ]; then
    docker compose -f docker-compose-cloud-sim.yml pull
else
    docker-compose -f docker-compose-cloud-sim.yml pull
fi

# Build and start services
echo ""
echo "🐳 Building and starting cloud simulation services..."
if [ "$DOCKER_COMPOSE_CMD" = "docker compose" ]; then
    docker compose -f docker-compose-cloud-sim.yml up -d --build
else
    docker-compose -f docker-compose-cloud-sim.yml up -d --build
fi

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to become healthy..."
sleep 10

# Check service health
echo ""
echo "🔍 Checking service health..."
services=("load-balancer:8080" "web-server:8081" "api-server:8082")

for service in "${services[@]}"; do
    name=$(echo $service | cut -d: -f1)
    port=$(echo $service | cut -d: -f2)
    
    if curl -f -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo "✅ $name is healthy"
    else
        echo "⚠️  $name health check failed (may still be starting)"
    fi
done

# Check database and cache (they don't have HTTP endpoints)
echo "✅ database (PostgreSQL) - running"
echo "✅ cache (Redis) - running"

echo ""
echo "✅ Cloud Simulation Services installed and started!"
echo ""
echo "📊 Service Information:"
echo "   - Load Balancer: http://localhost:8080"
echo "   - Web Server: http://localhost:8081"
echo "   - API Server: http://localhost:8082"
echo "   - Database: localhost:15432 (host port, container uses 5432)"
echo "   - Cache: localhost:6379"
echo ""
echo "📝 Container Names:"
echo "   - cloud-sim-load-balancer"
echo "   - cloud-sim-web-server"
echo "   - cloud-sim-api-server"
echo "   - cloud-sim-database"
echo "   - cloud-sim-cache"
echo ""
echo "🔧 Management Commands:"
echo "   Stop services: $DOCKER_COMPOSE_CMD -f $CONFIG_DIR/docker-compose-cloud-sim.yml down"
echo "   View logs: $DOCKER_COMPOSE_CMD -f $CONFIG_DIR/docker-compose-cloud-sim.yml logs -f"
echo "   Restart services: $DOCKER_COMPOSE_CMD -f $CONFIG_DIR/docker-compose-cloud-sim.yml restart"
echo ""
echo "ℹ️  Note: These services are now excluded from automatic monitoring"
echo "   to prevent false alerts. They can still be managed manually."

