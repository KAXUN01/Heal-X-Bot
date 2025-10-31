#!/bin/bash
# Start Fluent Bit Docker container in background

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_DIR="$PROJECT_ROOT/config"

echo "🚀 Starting Fluent Bit for log management..."

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed or not in PATH"
    exit 1
fi

# Check if Docker daemon is running
if ! docker ps &> /dev/null; then
    echo "❌ Error: Docker daemon is not running"
    echo ""
    echo "Please start Docker first:"
    echo "  - On Linux with systemd: sudo systemctl start docker"
    echo "  - On Linux with Docker Desktop: Check if Docker Desktop is running"
    echo "  - On macOS/Windows: Start Docker Desktop application"
    exit 1
fi

# Check if fluent-bit config exists
if [ ! -f "$CONFIG_DIR/fluent-bit/fluent-bit.conf" ]; then
    echo "❌ Error: Fluent Bit configuration not found at $CONFIG_DIR/fluent-bit/fluent-bit.conf"
    exit 1
fi

# Create output directory if it doesn't exist (in project logs directory)
OUTPUT_DIR="$PROJECT_ROOT/logs/fluent-bit"
mkdir -p "$OUTPUT_DIR"
chmod 755 "$OUTPUT_DIR" 2>/dev/null || true

# Check if network exists, create if not
if ! docker network ls | grep -q healing-network; then
    echo "📡 Creating healing-network..."
    docker network create healing-network 2>/dev/null || true
fi

# Check if container is already running
if docker ps -a --format '{{.Names}}' | grep -q "^fluent-bit$"; then
    if docker ps --format '{{.Names}}' | grep -q "^fluent-bit$"; then
        echo "✅ Fluent Bit is already running"
        docker ps --filter "name=fluent-bit" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        exit 0
    else
        echo "🔄 Starting existing Fluent Bit container..."
        docker start fluent-bit
    fi
else
    echo "🐳 Starting Fluent Bit container..."
    cd "$CONFIG_DIR"
    
    # Use docker-compose if available, otherwise docker compose
    if command -v docker-compose &> /dev/null; then
        docker-compose -f docker-compose-fluent-bit.yml up -d
    else
        docker compose -f docker-compose-fluent-bit.yml up -d
    fi
fi

# Wait a moment for container to start
sleep 2

# Check if container is running
if docker ps --format '{{.Names}}' | grep -q "^fluent-bit$"; then
    echo "✅ Fluent Bit started successfully!"
    echo ""
    echo "📊 Container Status:"
    docker ps --filter "name=fluent-bit" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
    echo "📝 To view logs:"
    echo "   docker logs -f fluent-bit"
    echo ""
    echo "🛑 To stop:"
    echo "   docker stop fluent-bit"
    echo ""
    echo "🔍 Fluent Bit logs output:"
    echo "   $OUTPUT_DIR/fluent-bit-output.jsonl"
else
    echo "❌ Failed to start Fluent Bit"
    echo "📋 Container logs:"
    docker logs fluent-bit 2>&1 | tail -20
    exit 1
fi

