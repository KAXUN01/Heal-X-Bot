#!/bin/bash
#
# Script to generate CRITICAL error log entries for testing the Critical Errors section
#
# This script writes CRITICAL severity log entries to the system log,
# which should be picked up by the critical services monitor and displayed
# in the dashboard's "Critical Errors Only" section.
#

echo "============================================================"
echo "🔴 CRITICAL ERROR GENERATOR"
echo "============================================================"
echo ""
echo "This script will generate test CRITICAL errors for testing"
echo "the 'Critical Errors Only' section in the dashboard."
echo ""

# Get current timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Method 1: Use logger command to write CRITICAL (priority 2) messages
echo "📝 Generating CRITICAL error using logger command..."

if command -v logger &> /dev/null; then
    # Priority 2 = CRITICAL (0=EMERG, 1=ALERT, 2=CRIT, 3=ERR, 4=WARNING)
    
    logger -p 2 -t "test-critical-service" \
        "CRITICAL ERROR: Test critical error generated at $TIMESTAMP. Service test-critical-service failed. This is a test error to verify the Critical Errors section is working correctly."
    
    echo "✅ CRITICAL error written to system log (priority 2)"
    
    # Also try with facility codes
    logger -p kern.crit -t "test-critical-service" \
        "CRITICAL: Kernel service failure test - Generated at $TIMESTAMP for dashboard testing."
    
    logger -p daemon.crit -t "test-critical-service" \
        "CRITICAL: Daemon service critical error - Test entry at $TIMESTAMP for verification."
    
    echo "✅ Additional CRITICAL errors written to system log"
else
    echo "⚠️  logger command not found. Trying alternative methods..."
fi

# Method 2: Try writing directly to /var/log/syslog if accessible
echo ""
echo "📝 Attempting to write directly to log files..."

if [ -w /var/log/syslog ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') test-critical-service CRITICAL: Test critical error - Service failure detected at $TIMESTAMP. This is a test entry for dashboard verification." >> /var/log/syslog
    echo "✅ Test log entry written to /var/log/syslog"
elif [ -w /var/log/messages ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') test-critical-service CRITICAL: Test critical error - Service failure detected at $TIMESTAMP. This is a test entry for dashboard verification." >> /var/log/messages
    echo "✅ Test log entry written to /var/log/messages"
else
    echo "⚠️  Cannot write to system log files (need sudo permissions)"
    echo "   Creating test log in /tmp/ instead..."
    echo "$(date '+%Y-%m-%d %H:%M:%S') test-critical-service CRITICAL: Test critical error - Service failure detected at $TIMESTAMP. This is a test entry for dashboard verification." >> /tmp/test-critical.log
    echo "✅ Test log entry written to /tmp/test-critical.log"
fi

# Method 3: Use systemd-cat if available
echo ""
echo "📝 Attempting to write to systemd journal..."

if command -v systemd-cat &> /dev/null; then
    echo "CRITICAL: Test critical error - Service test-critical-service failed at $TIMESTAMP. This is a test entry for dashboard verification." | \
        systemd-cat -t "test-critical-service" -p crit
    
    echo "✅ CRITICAL error written to systemd journal"
else
    echo "⚠️  systemd-cat not available, skipped"
fi

# Method 4: Try using journalctl directly (if we have permissions)
if command -v journalctl &> /dev/null && [ -w /run/systemd/journal ]; then
    echo ""
    echo "📝 Attempting direct journal write..."
    # This might not work without special permissions, but worth trying
    echo "CRITICAL: Direct journal test entry at $TIMESTAMP" 2>/dev/null | \
        systemd-cat -t "test-critical-service" -p crit || true
fi

echo ""
echo "============================================================"
echo "✅ Critical error generation complete!"
echo "============================================================"
echo ""
echo "The generated errors should appear in the dashboard within:"
echo "  - 30 seconds (system log collection interval)"
echo "  - Or refresh the dashboard manually"
echo ""
echo "Check the 'Critical Errors Only' section in the dashboard."
echo ""
echo "To view recent CRITICAL logs, run:"
echo "  sudo journalctl -p crit -n 20"
echo "  or"
echo "  sudo tail -f /var/log/syslog | grep -i critical"
echo ""
echo "To generate more errors, run this script again:"
echo "  ./test-critical-error.sh"
echo ""

