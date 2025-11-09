#!/bin/bash
# Healing-Bot Startup Script
# This script starts the entire healing-bot application

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    🛡️  HEALING-BOT  🛡️                      ║${NC}"
echo -e "${BLUE}║                                                              ║${NC}"
echo -e "${BLUE}║        AI-Powered DDoS Detection & IP Blocking System       ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check Python version
echo -e "${YELLOW}🔍 Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ ERROR: Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✅ Python ${PYTHON_VERSION} detected${NC}"

# Check if Python version is 3.8 or higher
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo -e "${RED}❌ ERROR: Python 3.8 or higher is required${NC}"
    exit 1
fi

# Check if run-healing-bot.py exists
if [ ! -f "run-healing-bot.py" ]; then
    echo -e "${RED}❌ ERROR: run-healing-bot.py not found${NC}"
    exit 1
fi

# Make run-healing-bot.py executable
chmod +x run-healing-bot.py

# Check for virtual environment
if [ -d "venv" ] || [ -d ".venv" ]; then
    echo -e "${YELLOW}📦 Virtual environment detected${NC}"
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        source .venv/bin/activate
    fi
    echo -e "${GREEN}✅ Virtual environment activated${NC}"
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  WARNING: .env file not found${NC}"
    if [ -f "config/env.template" ]; then
        echo -e "${YELLOW}📝 Creating .env file from template...${NC}"
        cp config/env.template .env
        echo -e "${GREEN}✅ Created .env file - please configure your API keys${NC}"
    else
        echo -e "${YELLOW}⚠️  No env.template found - continuing without .env${NC}"
    fi
fi

# Check for required directories
echo -e "${YELLOW}🔍 Checking project structure...${NC}"
REQUIRED_DIRS=("monitoring/server" "model" "incident-bot" "config")
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        echo -e "${RED}❌ ERROR: Required directory not found: $dir${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✅ Project structure verified${NC}"

# Check if ports are available
echo -e "${YELLOW}🔍 Checking port availability...${NC}"
PORTS=(8080 8000 3001 5000 5001)
OCCUPIED_PORTS=()

for port in "${PORTS[@]}"; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        OCCUPIED_PORTS+=($port)
    fi
done

if [ ${#OCCUPIED_PORTS[@]} -gt 0 ]; then
    echo -e "${YELLOW}⚠️  WARNING: Ports ${OCCUPIED_PORTS[@]} are already in use${NC}"
    echo -e "${YELLOW}   The application may not start properly if these ports are needed${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}❌ Startup cancelled${NC}"
        exit 1
    fi
fi

# Start the application
echo ""
echo -e "${GREEN}🚀 Starting Healing-Bot application...${NC}"
echo ""

# Run the Python launcher
python3 run-healing-bot.py "$@"

# If we get here, the application has stopped
echo ""
echo -e "${YELLOW}🛑 Application stopped${NC}"

