#!/bin/bash
#
# Force create a CRITICAL error that will definitely be detected
# This creates an error with priority 2 (CRITICAL) and ensures it's from a monitored service
#

echo "🔴 FORCING CRITICAL ERROR GENERATION"
echo "====================================="
echo ""

# Method 1: Use logger with priority 2 and ensure it's from a monitored service
# We'll use systemd-cat to inject directly into the journal as a monitored service

echo "📝 Method 1: Writing CRITICAL (priority 2) as systemd-journald..."

# Use systemd-cat to write directly as systemd-journald unit
if command -v systemd-cat &> /dev/null; then
    echo "CRITICAL: FORCED TEST CRITICAL ERROR - Service failure at $(date). This is a test error that MUST appear in dashboard." | \
        systemd-cat -t "systemd-journald" -p crit
    
    echo "CRITICAL: FORCED TEST CRITICAL ERROR - Docker failure at $(date). This is a test error that MUST appear in dashboard." | \
        systemd-cat -t "docker" -p crit
    
    echo "✅ CRITICAL errors written via systemd-cat"
else
    echo "⚠️  systemd-cat not available"
fi

# Method 2: Use logger with priority 2
echo ""
echo "📝 Method 2: Using logger with priority 2..."

if command -v logger &> /dev/null; then
    # Write multiple CRITICAL messages
    logger -p 2 -t "systemd-journald" "CRITICAL FORCED ERROR: Test critical error at $(date). Priority 2 = CRITICAL. MUST appear."
    logger -p 2 -t "docker" "CRITICAL FORCED ERROR: Test critical error at $(date). Priority 2 = CRITICAL. MUST appear."
    logger -p 2 -t "dbus" "CRITICAL FORCED ERROR: Test critical error at $(date). Priority 2 = CRITICAL. MUST appear."
    
    echo "✅ CRITICAL errors written via logger (priority 2)"
fi

# Method 3: Create a fake systemd unit log (more advanced)
echo ""
echo "📝 Method 3: Creating test log entries..."

# Write directly to journal using python if available
python3 << 'EOF'
import subprocess
import datetime

timestamp = datetime.datetime.now().isoformat()

# Use systemd-cat to write CRITICAL entries
test_message = f"CRITICAL: FORCED TEST ERROR at {timestamp}. This error MUST be detected by the monitor."
subprocess.run(['systemd-cat', '-t', 'systemd-journald', '-p', 'crit'], 
               input=test_message.encode(), check=False)

subprocess.run(['systemd-cat', '-t', 'docker', '-p', 'crit'],
               input=test_message.encode(), check=False)

print("✅ Python-written CRITICAL errors created")
EOF

echo ""
echo "====================================="
echo "✅ Critical errors generated!"
echo ""
echo "The monitor collects logs every 10 seconds now."
echo "Check the dashboard in 10-15 seconds."
echo ""
echo "To verify the logs were written:"
echo "  sudo journalctl -p 2 -n 5 --no-pager"
echo ""

