#!/bin/bash
# Install dependencies and run Heal-X-Bot without tests

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          🛡️  HEAL-X-BOT: Install & Run Script  🛡️          ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Python 3 found: $(python3 --version)"

# Check pip
if ! python3 -m pip --version &> /dev/null; then
    echo -e "${YELLOW}⚠️  pip is not installed${NC}"
    echo ""
    echo "Installing pip..."
    
    # Try ensurepip first
    if python3 -m ensurepip --user 2>/dev/null; then
        echo -e "${GREEN}✓${NC} pip installed via ensurepip"
    else
        echo -e "${YELLOW}⚠️  ensurepip not available. Please install pip manually:${NC}"
        echo "   sudo apt install python3-pip"
        echo "   OR"
        echo "   curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py"
        echo "   python3 get-pip.py --user"
        exit 1
    fi
else
    echo -e "${GREEN}✓${NC} pip is available"
fi

# Install dependencies
echo ""
echo -e "${BLUE}📦 Installing dependencies...${NC}"

# Main requirements
if [ -f "requirements.txt" ]; then
    echo "Installing main requirements..."
    python3 -m pip install --user -r requirements.txt 2>&1 | grep -E "(Successfully|ERROR|WARNING)" || true
fi

# Component requirements
for req_file in "model/requirements.txt" "monitoring/server/requirements.txt" "monitoring/dashboard/requirements.txt" "incident-bot/requirements.txt"; do
    if [ -f "$req_file" ]; then
        echo "Installing from $req_file..."
        python3 -m pip install --user -r "$req_file" 2>&1 | grep -E "(Successfully|ERROR|WARNING)" || true
    fi
done

echo -e "${GREEN}✓${NC} Dependencies installation completed"

# Create .env if not exists
if [ ! -f ".env" ]; then
    if [ -f "config/env.template" ]; then
        echo ""
        echo -e "${YELLOW}⚠️  Creating .env file from template...${NC}"
        cp config/env.template .env
        echo -e "${GREEN}✓${NC} .env file created (configure API keys if needed)"
    fi
fi

# Check critical dependencies
echo ""
echo -e "${BLUE}🔍 Verifying critical dependencies...${NC}"
python3 << 'EOF'
import sys
critical = ['fastapi', 'flask', 'uvicorn', 'requests']
missing = []
for m in critical:
    try:
        __import__(m)
        print(f"✓ {m}")
    except ImportError:
        print(f"✗ {m} - MISSING")
        missing.append(m)

if missing:
    print(f"\n⚠️  Missing: {', '.join(missing)}")
    print("Try: python3 -m pip install --user " + " ".join(missing))
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Critical dependencies missing. Please install them manually.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ All dependencies ready!${NC}"
echo ""

# Ask user which service to run
echo -e "${BLUE}Choose how to run the project:${NC}"
echo "1) Unified Dashboard (Recommended - Single service)"
echo "2) Unified Launcher (All services via run-healing-bot.py)"
echo "3) Exit"
echo ""
read -p "Enter choice [1-3]: " choice

case $choice in
    1)
        echo ""
        echo -e "${BLUE}🚀 Starting Unified Dashboard...${NC}"
        echo -e "${GREEN}Access at: http://localhost:5001${NC}"
        echo "Press Ctrl+C to stop"
        echo ""
        python3 monitoring/server/healing_dashboard_api.py
        ;;
    2)
        echo ""
        echo -e "${BLUE}🚀 Starting all services via Unified Launcher...${NC}"
        echo "This will start multiple services. Press Ctrl+C to stop all."
        echo ""
        python3 run-healing-bot.py --mode native
        ;;
    3)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

