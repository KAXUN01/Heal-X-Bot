#!/bin/bash
"""
Setup script for automated model retraining via cron

This script sets up a cron job to automatically retrain the predictive maintenance model.
"""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRON_LOG="$SCRIPT_DIR/automated_retraining.log"

echo "Setting up automated model retraining..."

# Create cron job entry
CRON_ENTRY="0 2 * * 0 cd $SCRIPT_DIR && python3 automated_retraining.py --no-tuning --no-shap >> $CRON_LOG 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "automated_retraining.py"; then
    echo "Cron job already exists. Removing old entry..."
    crontab -l 2>/dev/null | grep -v "automated_retraining.py" | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

echo "✅ Cron job added successfully!"
echo "   Schedule: Every Sunday at 2:00 AM"
echo "   Log file: $CRON_LOG"
echo ""
echo "To view cron jobs: crontab -l"
echo "To remove cron job: crontab -e (then delete the line)"

