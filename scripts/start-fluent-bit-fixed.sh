#!/bin/bash
# Start Fluent Bit with fixed configuration

set -e

cd "$(dirname "$0")/.."
PROJECT_ROOT="$(pwd)"
CONFIG_DIR="$PROJECT_ROOT/config"
OUTPUT_DIR="$PROJECT_ROOT/logs/fluent-bit"

echo "🚀 Starting Fluent Bit with fixed configuration..."

# Stop existing container
docker stop fluent-bit 2>/dev/null || true
docker rm fluent-bit 2>/dev/null || true

# Create network
docker network create healing-network 2>/dev/null || true

# Create output directory
mkdir -p "$OUTPUT_DIR"
chmod 755 "$OUTPUT_DIR"

# Start Fluent Bit
echo "📦 Starting container..."
docker run -d \
    --name fluent-bit \
    --restart unless-stopped \
    --network healing-network \
    -v "$CONFIG_DIR/fluent-bit/fluent-bit.conf:/fluent-bit/etc/fluent-bit.conf:ro" \
    -v /var/log:/var/log:ro \
    -v "$OUTPUT_DIR:/fluent-bit-output" \
    fluent/fluent-bit:latest \
    /fluent-bit/bin/fluent-bit -c /fluent-bit/etc/fluent-bit.conf

# Wait a moment
sleep 3

# Check status
if docker ps | grep -q fluent-bit; then
    echo "✅ Fluent Bit started successfully!"
    echo ""
    echo "📊 Container Status:"
    docker ps | grep fluent-bit
    echo ""
    echo "📝 Recent Logs:"
    docker logs fluent-bit --tail 10
    echo ""
    echo "📁 Log file: $OUTPUT_DIR/fluent-bit-output.jsonl"
else
    echo "❌ Container failed to start"
    echo "📋 Error Logs:"
    docker logs fluent-bit 2>&1 | tail -20
    exit 1
fi

