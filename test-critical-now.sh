#!/bin/bash
#
# Quick script to generate CRITICAL errors right now using monitored services
#

echo "🔴 Generating CRITICAL errors as monitored services..."

# Use logger to write CRITICAL priority (2) messages as monitored services
logger -p 2 -t "systemd-journald" "CRITICAL: Test critical error - systemd-journald service failure at $(date). This is a test."
logger -p 2 -t "docker" "CRITICAL: Test critical error - Docker service failure at $(date). This is a test."
logger -p 2 -t "dbus" "CRITICAL: Test critical error - dbus service failure at $(date). This is a test."

# Also use systemd-cat if available
if command -v systemd-cat &> /dev/null; then
    echo "CRITICAL: systemd-journald test critical error at $(date)" | systemd-cat -t "systemd-journald" -p crit
    echo "CRITICAL: docker test critical error at $(date)" | systemd-cat -t "docker" -p crit
fi

echo "✅ CRITICAL errors generated!"
echo ""
echo "The monitor collects logs every 60 seconds."
echo "To force immediate collection, check the dashboard logs or wait up to 60 seconds."
echo ""
echo "Verify with: journalctl -p 2 -n 5"

