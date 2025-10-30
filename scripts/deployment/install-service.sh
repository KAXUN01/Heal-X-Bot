#!/bin/bash

# Install Healing-bot as a systemd service
# This allows the system to run with proper permissions and auto-start on boot

set -e

PROJECT_ROOT="/home/cdrditgis/Documents/Healing-bot"
SERVICE_FILE="$PROJECT_ROOT/scripts/deployment/healing-bot.service"
SYSTEMD_PATH="/etc/systemd/system/healing-bot.service"

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║           Installing Healing-bot Systemd Service                     ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ This script must be run as root (use sudo)"
    echo "   Usage: sudo bash scripts/deployment/install-service.sh"
    exit 1
fi

# Stop existing service if running
if systemctl is-active --quiet healing-bot; then
    echo "🛑 Stopping existing healing-bot service..."
    systemctl stop healing-bot
fi

# Copy service file
echo "📋 Installing service file..."
cp "$SERVICE_FILE" "$SYSTEMD_PATH"
chmod 644 "$SYSTEMD_PATH"

# Reload systemd
echo "🔄 Reloading systemd daemon..."
systemctl daemon-reload

# Enable service to start on boot
echo "✅ Enabling service to start on boot..."
systemctl enable healing-bot

# Start the service
echo "🚀 Starting healing-bot service..."
systemctl start healing-bot

# Wait a moment for startup
sleep 3

# Check status
echo ""
echo "📊 Service Status:"
systemctl status healing-bot --no-pager || true

echo ""
echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                 ✅ Installation Complete! ✅                          ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Useful Commands:"
echo "  Start:   sudo systemctl start healing-bot"
echo "  Stop:    sudo systemctl stop healing-bot"
echo "  Restart: sudo systemctl restart healing-bot"
echo "  Status:  sudo systemctl status healing-bot"
echo "  Logs:    sudo journalctl -u healing-bot -f"
echo ""
echo "Service will now start automatically on system boot!"
echo ""

