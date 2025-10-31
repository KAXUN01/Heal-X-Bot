#!/bin/bash
#
# Script to generate CRITICAL error log entries that will be detected by the monitor
# This version writes logs as if from a monitored critical service
#

echo "============================================================"
echo "🔴 CRITICAL ERROR GENERATOR (v2 - Monitored Services)"
echo "============================================================"
echo ""
echo "This script will generate test CRITICAL errors for monitored services"
echo ""

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Method 1: Write as systemd-journald (a monitored CRITICAL service)
echo "📝 Generating CRITICAL error as systemd-journald (monitored service)..."

if command -v logger &> /dev/null; then
    # Write with priority 2 (CRITICAL) as systemd-journald
    logger -p 2 -t "systemd-journald" \
        "CRITICAL: Test critical error generated at $TIMESTAMP. Service systemd-journald failed. This is a test error to verify the Critical Errors section is working correctly."
    
    echo "✅ CRITICAL error written as systemd-journald (priority 2)"
    
    # Also write as docker (another monitored CRITICAL service)
    logger -p 2 -t "docker" \
        "CRITICAL: Test critical error - Docker service failure at $TIMESTAMP. This is a test entry for dashboard verification."
    
    echo "✅ CRITICAL error written as docker (priority 2)"
    
    # Write as dbus (another monitored CRITICAL service)
    logger -p 2 -t "dbus" \
        "CRITICAL: Test critical error - D-Bus message bus failure at $TIMESTAMP. Test entry for dashboard."
    
    echo "✅ CRITICAL error written as dbus (priority 2)"
    
    # Write multiple CRITICAL errors
    for i in {1..3}; do
        logger -p 2 -t "systemd-journald" \
            "CRITICAL ERROR #$i: Test critical error batch at $TIMESTAMP. Service failure detected for testing purposes."
    done
    
    echo "✅ Additional CRITICAL errors written"
fi

# Method 2: Use systemd-cat to write directly as a monitored service
echo ""
echo "📝 Writing to systemd journal as monitored services..."

if command -v systemd-cat &> /dev/null; then
    echo "CRITICAL: systemd-journald test critical error at $TIMESTAMP. Service failure for testing." | \
        systemd-cat -t "systemd-journald" -p crit
    
    echo "CRITICAL: Docker test critical error at $TIMESTAMP. Container runtime failure for testing." | \
        systemd-cat -t "docker" -p crit
    
    echo "CRITICAL: dbus test critical error at $TIMESTAMP. Message bus failure for testing." | \
        systemd-cat -t "dbus" -p crit
    
    echo "✅ CRITICAL errors written to systemd journal"
fi

echo ""
echo "============================================================"
echo "✅ Critical error generation complete!"
echo "============================================================"
echo ""
echo "The generated errors should appear in the dashboard within:"
echo "  - 60 seconds (critical services monitor interval)"
echo "  - Or refresh the dashboard manually"
echo ""
echo "Check the 'Critical Errors Only' section in the dashboard."
echo ""
echo "These errors are written as monitored critical services:"
echo "  - systemd-journald (CRITICAL category)"
echo "  - docker (CRITICAL category)"
echo "  - dbus (CRITICAL category)"
echo ""

