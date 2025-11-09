#!/bin/bash

################################################################################
# Quick Start Script for Ubuntu
# One-command setup and launch for Healing-bot
################################################################################

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}🤖 Automatic Self-Healing Bot - Quick Start${NC}"
echo ""

# Check if running with sudo for first-time setup
if [ "$1" = "--first-time" ]; then
    if [ "$EUID" -ne 0 ]; then
        echo -e "${YELLOW}⚠️  First-time setup requires sudo${NC}"
        echo "Run: sudo $0 --first-time"
        exit 1
    fi
    
    echo -e "${GREEN}▶ Installing system dependencies...${NC}"
    apt update
    apt install -y python3 python3-pip python3-venv build-essential curl git net-tools lsof
    
    echo -e "${GREEN}▶ Installing Python packages...${NC}"
    pip3 install -r requirements.txt
    pip3 install -r monitoring/server/requirements.txt 2>/dev/null || true
    pip3 install -r monitoring/dashboard/requirements.txt 2>/dev/null || true
    pip3 install -r incident-bot/requirements.txt 2>/dev/null || true
    pip3 install -r model/requirements.txt 2>/dev/null || true
    
    echo ""
    echo -e "${GREEN}✅ Setup complete!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Configure your .env file:"
    echo "   python3 setup_env.py"
    echo ""
    echo "2. Start the system:"
    echo "   ./quick-start-ubuntu.sh"
    echo ""
    exit 0
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    echo ""
    echo "Options:"
    echo "1. Run setup wizard:"
    echo "   python3 setup_env.py"
    echo ""
    echo "2. Or manually create .env:"
    echo "   cp env.template .env"
    echo "   nano .env  # Edit and add your GEMINI_API_KEY"
    echo ""
    exit 1
fi

# Make main script executable
chmod +x start-healing-bot-ubuntu.sh

# Run the main script
./start-healing-bot-ubuntu.sh

