#!/bin/bash
# Pull Fluent Bit Docker image

set -e

echo "📥 Pulling Fluent Bit Docker image..."
echo "This may take a few minutes depending on your internet connection..."

docker pull fluent/fluent-bit:latest

echo ""
echo "✅ Fluent Bit image pulled successfully!"
echo ""
echo "📊 Image details:"
docker images | grep fluent-bit

echo ""
echo "🚀 You can now start Fluent Bit with:"
echo "   ./scripts/start-fluent-bit.sh"

