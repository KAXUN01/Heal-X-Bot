#!/bin/bash
# Fix Fluent Bit container restarting issues

set -e

echo "🔧 Fixing Fluent Bit container issues..."

# Stop and remove the failing container
echo "🛑 Stopping and removing existing container..."
docker stop fluent-bit 2>/dev/null || true
docker rm fluent-bit 2>/dev/null || true

# Check if network exists, create if not
echo "📡 Checking Docker network..."
if ! docker network ls | grep -q healing-network; then
    echo "📡 Creating healing-network..."
    docker network create healing-network
else
    echo "✅ Network exists"
fi

# Create output directory with proper permissions
echo "📁 Creating output directory..."
mkdir -p logs/fluent-bit
chmod 755 logs/fluent-bit

# Check configuration files
echo "📋 Checking configuration files..."
if [ ! -f config/fluent-bit/fluent-bit.conf ]; then
    echo "❌ Error: fluent-bit.conf not found!"
    exit 1
fi

if [ ! -f config/fluent-bit/parsers.conf ]; then
    echo "⚠️  Warning: parsers.conf not found, creating minimal one..."
    cat > config/fluent-bit/parsers.conf << 'EOF'
[PARSER]
    Name        syslog-rfc5424
    Format      regex
    Regex       ^\<(?<pri>[0-9]+)\>(?<time>[^ ]* {1,2}[^ ]* [^ ]*) (?<host>[^ ]*) (?<ident>[a-zA-Z0-9_\/\.\-]*)(?:\[(?<pid>[0-9]+)\])?(?:[^\:]*\:)? *(?<message>.*)$
    Time_Key    time
    Time_Format %Y-%m-%dT%H:%M:%S.%L
    Time_Keep   On
EOF
fi

# Test Fluent Bit configuration
echo "🧪 Testing Fluent Bit configuration..."
if docker run --rm -v "$(pwd)/config/fluent-bit:/fluent-bit/etc:ro" fluent/fluent-bit:latest /fluent-bit/bin/fluent-bit -c /fluent-bit/etc/fluent-bit.conf --dry-run 2>&1 | grep -q "error\|Error\|ERROR"; then
    echo "❌ Configuration has errors! Check the output above."
    docker run --rm -v "$(pwd)/config/fluent-bit:/fluent-bit/etc:ro" fluent/fluent-bit:latest /fluent-bit/bin/fluent-bit -c /fluent-bit/etc/fluent-bit.conf --dry-run
    exit 1
else
    echo "✅ Configuration is valid"
fi

# Start Fluent Bit with proper error handling
echo "🚀 Starting Fluent Bit container..."
cd config

# Use absolute paths for volumes
PROJECT_ROOT="$(cd .. && pwd)"
CONFIG_DIR="$PROJECT_ROOT/config"
OUTPUT_DIR="$PROJECT_ROOT/logs/fluent-bit"

docker run -d \
    --name fluent-bit \
    --restart unless-stopped \
    --network healing-network \
    -v "$CONFIG_DIR/fluent-bit/fluent-bit.conf:/fluent-bit/etc/fluent-bit.conf:ro" \
    -v "$CONFIG_DIR/fluent-bit/parsers.conf:/fluent-bit/etc/parsers.conf:ro" \
    -v /var/log:/var/log:ro \
    -v "$OUTPUT_DIR:/fluent-bit-output" \
    -v /run/journal:/run/journal:ro \
    fluent/fluent-bit:latest \
    /fluent-bit/bin/fluent-bit -c /fluent-bit/etc/fluent-bit.conf || {
    echo "❌ Failed to start container"
    echo "📋 Checking logs..."
    docker logs fluent-bit 2>&1 | tail -20
    exit 1
}

# Wait a moment
sleep 3

# Check if container is running
if docker ps | grep -q fluent-bit; then
    echo "✅ Fluent Bit started successfully!"
    echo ""
    echo "📊 Container Status:"
    docker ps | grep fluent-bit
    echo ""
    echo "📝 Container Logs:"
    docker logs fluent-bit --tail 10
    echo ""
    echo "📁 Log file location: $OUTPUT_DIR/fluent-bit-output.jsonl"
else
    echo "❌ Container failed to start"
    echo "📋 Logs:"
    docker logs fluent-bit 2>&1 | tail -30
    exit 1
fi

