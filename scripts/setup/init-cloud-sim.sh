#!/bin/bash

# Initialize Cloud Simulation Environment
# This script sets up the simulated cloud services for the AI Bot prototype

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CONFIG_DIR="$PROJECT_ROOT/config"

echo "🚀 Initializing Cloud Simulation Environment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Navigate to config directory
cd "$CONFIG_DIR"

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p cloud-sim/web-server
mkdir -p cloud-sim/api-server

# Check if docker-compose-cloud-sim.yml exists
if [ ! -f "docker-compose-cloud-sim.yml" ]; then
    echo "❌ docker-compose-cloud-sim.yml not found!"
    exit 1
fi

# Build and start services
echo "🐳 Building and starting cloud simulation services..."
# Try docker compose (newer syntax) first
if docker compose version &> /dev/null 2>&1; then
    echo "   Using: docker compose"
    docker compose -f docker-compose-cloud-sim.yml up -d --build
elif command -v docker-compose &> /dev/null; then
    echo "   Using: docker-compose"
    docker-compose -f docker-compose-cloud-sim.yml up -d --build
else
    echo "❌ Neither 'docker compose' nor 'docker-compose' is available"
    echo "   Install with: sudo apt install docker-compose"
    exit 1
fi

# Wait for services to be healthy
echo "⏳ Waiting for services to become healthy..."
sleep 10

# Check service health
echo "🔍 Checking service health..."
services=("load-balancer:8080" "web-server:8081" "api-server:8082" "database:5432" "cache:6379")

for service in "${services[@]}"; do
    name=$(echo $service | cut -d: -f1)
    port=$(echo $service | cut -d: -f2)
    
    if curl -f -s "http://localhost:$port/health" > /dev/null 2>&1 || [ "$name" = "database" ] || [ "$name" = "cache" ]; then
        echo "✅ $name is healthy"
    else
        echo "⚠️  $name health check failed (may still be starting)"
    fi
done

echo ""
echo "✅ Cloud Simulation Environment initialized!"
echo ""
echo "📊 Services:"
echo "   - Load Balancer: http://localhost:8080"
echo "   - Web Server: http://localhost:8081"
echo "   - API Server: http://localhost:8082"
echo "   - Database: localhost:5432"
echo "   - Cache: localhost:6379"
echo ""
# Determine which docker compose command to use
if docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker compose"
else
    DOCKER_COMPOSE_CMD="docker-compose"
fi

echo "To stop services: $DOCKER_COMPOSE_CMD -f $CONFIG_DIR/docker-compose-cloud-sim.yml down"
echo "To view logs: $DOCKER_COMPOSE_CMD -f $CONFIG_DIR/docker-compose-cloud-sim.yml logs -f"

