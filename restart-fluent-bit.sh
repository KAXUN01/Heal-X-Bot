#!/bin/bash
echo "🔄 Restarting Fluent Bit with fixed configuration..."
cd "$(dirname "$0")"
sudo docker stop fluent-bit 2>/dev/null || true
sudo docker rm fluent-bit 2>/dev/null || true
sudo ./scripts/start-fluent-bit.sh
echo "✅ Fluent Bit restarted. Checking status..."
sleep 3
sudo docker ps | grep fluent-bit || echo "Container status check..."
