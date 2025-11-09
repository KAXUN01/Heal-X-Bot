#!/bin/bash
# Helper script to start Fluent Bit with sudo
echo "Starting Fluent Bit with sudo..."
cd "$(dirname "$0")/.."
sudo ./scripts/start-fluent-bit.sh
