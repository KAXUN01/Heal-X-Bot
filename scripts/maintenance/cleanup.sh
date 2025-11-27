#!/bin/bash
# Cleanup script for Heal-X-Bot project
# Removes unnecessary files and keeps structure clean

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}🧹 Starting cleanup of Heal-X-Bot project...${NC}"
echo ""

# 1. Remove Python cache files
echo -e "${YELLOW}1. Removing Python cache files (__pycache__, *.pyc, *.pyo)...${NC}"
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
find . -type f -name "*.pyd" -delete 2>/dev/null || true
echo -e "${GREEN}   ✅ Python cache files removed${NC}"

# 2. Clean old log files (keep directory structure)
echo -e "${YELLOW}2. Cleaning old log files...${NC}"
if [ -d "logs" ]; then
    find logs -type f -name "*.log" -size +10M -delete 2>/dev/null || true
    # Keep recent logs but truncate very large ones
    find logs -type f -name "*.log" -exec truncate -s 1M {} \; 2>/dev/null || true
    echo -e "${GREEN}   ✅ Log files cleaned${NC}"
fi

# 3. Remove temporary files
echo -e "${YELLOW}3. Removing temporary files...${NC}"
rm -rf .pids/*.pid 2>/dev/null || true
rm -rf /tmp/startup*.log 2>/dev/null || true
rm -rf .DS_Store ._* *~ 2>/dev/null || true
find . -type f -name ".DS_Store" -delete 2>/dev/null || true
find . -type f -name "*.swp" -delete 2>/dev/null || true
find . -type f -name "*.swo" -delete 2>/dev/null || true
find . -type f -name "*~" -delete 2>/dev/null || true
echo -e "${GREEN}   ✅ Temporary files removed${NC}"

# 4. Remove old/demo files from model directory (keep essential ones)
echo -e "${YELLOW}4. Cleaning model directory (removing demo/test files)...${NC}"
cd model
# Remove demo files but keep main functionality
DEMO_FILES=(
    "demo_dashboard_predictions.py"
    "demo_predictions_auto.py"
    "demo_predictions.py"
    "demo_with_dashboard.py"
    "demo_with_visual_updates.py"
    "continuous_demo.py"
    "show_predictions.py"
    "test_dashboard_updates.py"
    "test_dashboard_visualization.sh"
    "test_predictions.py"
    "test_predictive_model.py"
    "test_training.py"
    "example_usage.py"
)

for file in "${DEMO_FILES[@]}"; do
    if [ -f "$file" ]; then
        rm -f "$file"
        echo -e "${GREEN}   ✅ Removed: $file${NC}"
    fi
done
cd "$SCRIPT_DIR"
echo -e "${GREEN}   ✅ Model directory cleaned${NC}"

# 5. Remove redundant documentation files (keep main ones)
echo -e "${YELLOW}5. Cleaning documentation (removing redundant files)...${NC}"
REDUNDANT_DOCS=(
    "FIX_APPLIED.md"
    "FLUENT_BIT_COMMANDS.md"
    "model/COMPLETE_TASK_LIST.md"
    "model/DASHBOARD_DEMO_GUIDE.md"
    "model/DASHBOARD_FIX_SUMMARY.md"
    "model/DEMO_INSTRUCTIONS.md"
    "model/FINAL_SUMMARY.md"
    "model/IMPLEMENTATION_SUMMARY.md"
)

for doc in "${REDUNDANT_DOCS[@]}"; do
    if [ -f "$doc" ]; then
        rm -f "$doc"
        echo -e "${GREEN}   ✅ Removed: $doc${NC}"
    fi
done
echo -e "${GREEN}   ✅ Documentation cleaned${NC}"

# 6. Clean monitoring/server logs directory if it exists
echo -e "${YELLOW}6. Cleaning monitoring server logs...${NC}"
if [ -d "monitoring/server/logs" ]; then
    find monitoring/server/logs -type f -name "*.log" -delete 2>/dev/null || true
    echo -e "${GREEN}   ✅ Monitoring server logs cleaned${NC}"
fi

# 7. Remove old incident bot log if it exists and is large
echo -e "${YELLOW}7. Cleaning incident bot logs...${NC}"
if [ -f "incident-bot/incident_bot.log" ]; then
    if [ -s "incident-bot/incident_bot.log" ]; then
        truncate -s 0 "incident-bot/incident_bot.log" 2>/dev/null || true
        echo -e "${GREEN}   ✅ Incident bot log cleared${NC}"
    fi
fi

# 8. Clean up old model artifacts (keep only latest)
echo -e "${YELLOW}8. Cleaning old model artifacts (keeping latest)...${NC}"
if [ -d "model/artifacts" ]; then
    # Keep only the 2 most recent artifact versions
    cd model/artifacts
    ls -td v* 2>/dev/null | tail -n +3 | xargs rm -rf 2>/dev/null || true
    cd "$SCRIPT_DIR"
    echo -e "${GREEN}   ✅ Old model artifacts cleaned${NC}"
fi

# 9. Remove empty directories
echo -e "${YELLOW}9. Removing empty directories...${NC}"
find . -type d -empty -delete 2>/dev/null || true
echo -e "${GREEN}   ✅ Empty directories removed${NC}"

# 10. Clean Python test cache
echo -e "${YELLOW}10. Cleaning test cache...${NC}"
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".coverage" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name ".coverage" -delete 2>/dev/null || true
echo -e "${GREEN}   ✅ Test cache cleaned${NC}"

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                    ✅ CLEANUP COMPLETE! ✅                   ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Project structure is now clean and organized!${NC}"
echo ""

