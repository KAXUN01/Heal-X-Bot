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
    
    # Pull Fluent Bit image first if not present
    echo "📥 Checking for Fluent Bit image..."
    if ! docker images | grep -q "fluent/fluent-bit"; then
        echo "📥 Pulling Fluent Bit image (this may take a minute)..."
        docker pull fluent/fluent-bit:latest
    else
        echo "✅ Fluent Bit image already exists"
    fi
    
    cd "$CONFIG_DIR"
    
    # Use docker-compose if available, otherwise try docker compose
    if command -v docker-compose &> /dev/null; then
        echo "🔧 Using docker-compose..."
        docker-compose -f docker-compose-fluent-bit.yml up -d
    elif docker compose version &> /dev/null; then
        echo "🔧 Using docker compose..."
        docker compose -f docker-compose-fluent-bit.yml up -d
    else
        echo "❌ Error: Neither docker-compose nor 'docker compose' is available"
        echo "💡 Installing docker-compose..."
        echo "   Option 1: Install docker-compose: sudo apt install docker-compose"
        echo "   Option 2: Upgrade Docker to a version that supports 'docker compose'"
        echo ""
        echo "🔄 Trying to start container manually with docker run..."
        
        # Try to start manually with docker run
        OUTPUT_DIR="$PROJECT_ROOT/logs/fluent-bit"
        mkdir -p "$OUTPUT_DIR"
        
        docker run -d \
            --name fluent-bit \
            --restart unless-stopped \
            --network healing-network \
            -v "$CONFIG_DIR/fluent-bit/fluent-bit.conf:/fluent-bit/etc/fluent-bit.conf:ro" \
            -v "$CONFIG_DIR/fluent-bit/parsers.conf:/fluent-bit/etc/parsers.conf:ro" \
            -v /var/log:/var/log:ro \
            -v /var/lib/docker/containers:/var/lib/docker/containers:ro \
            -v "$OUTPUT_DIR:/fluent-bit-output" \
            -v /run/journal:/run/journal:ro \
            -v /var/run/docker.sock:/var/run/docker.sock:ro \
            -p 8888:8888 \
            fluent/fluent-bit:latest \
            /fluent-bit/bin/fluent-bit -c /fluent-bit/etc/fluent-bit.conf
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

