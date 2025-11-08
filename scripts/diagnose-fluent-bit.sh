#!/bin/bash
# Diagnose Fluent Bit container issues

echo "🔍 Diagnosing Fluent Bit container issues..."
echo ""

# Check container status
echo "📊 Container Status:"
docker ps -a | grep fluent-bit || echo "Container not found"
echo ""

# Check container logs
echo "📝 Last 30 lines of logs:"
docker logs fluent-bit --tail 30 2>&1 || echo "Cannot read logs"
echo ""

# Check network
echo "📡 Network Status:"
docker network ls | grep healing-network || echo "Network 'healing-network' not found"
echo ""

# Check if output directory exists
echo "📁 Output Directory:"
ls -la logs/fluent-bit/ 2>&1 || echo "Output directory not found"
echo ""

# Check configuration files
echo "📋 Configuration Files:"
ls -la config/fluent-bit/ 2>&1
echo ""

# Check if log file is being created
echo "📄 Log File:"
ls -lh logs/fluent-bit/fluent-bit-output.jsonl 2>&1 || echo "Log file not created yet"
echo ""

# Test configuration
echo "🧪 Testing Configuration:"
docker run --rm -v "$(pwd)/config/fluent-bit:/fluent-bit/etc:ro" fluent/fluent-bit:latest /fluent-bit/bin/fluent-bit -c /fluent-bit/etc/fluent-bit.conf --dry-run 2>&1 | tail -20
echo ""

# Check container inspect
echo "🔍 Container Details:"
docker inspect fluent-bit 2>&1 | grep -A 5 "State\|Mounts\|NetworkSettings" | head -30 || echo "Cannot inspect container"
echo ""

