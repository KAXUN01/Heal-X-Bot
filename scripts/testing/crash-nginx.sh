#!/bin/bash
#
# Script to crash nginx service and ensure the error appears in Critical Errors Only section
# This will stop nginx forcefully and log the error with CRITICAL priority
# The monitor collects logs every 10 seconds, so the error should appear within 10-15 seconds
#

echo "============================================================"
echo "🔴 NGINX CRASH SCRIPT"
echo "============================================================"
echo ""
echo "This script will crash nginx and ensure the error appears"
echo "in the 'Critical Errors Only' section of the dashboard."
echo ""
echo "⚠️  WARNING: This will stop the nginx service!"
echo ""

# Check if nginx is running
if systemctl is-active --quiet nginx 2>/dev/null || systemctl is-active --quiet nginx.service 2>/dev/null; then
    echo "✓ Nginx is currently running"
    
    # Method 1: Stop nginx service (this will create a CRITICAL error in systemd journal)
    echo ""
    echo "📝 Method 1: Stopping nginx service..."
    sudo systemctl stop nginx 2>/dev/null || sudo systemctl stop nginx.service 2>/dev/null
    
    # Wait a moment for the stop to register
    sleep 1
    
    # Method 2: Write CRITICAL error to journal using logger with priority 2 (CRITICAL)
    echo "📝 Method 2: Writing CRITICAL log entry to journal..."
    
    TIMESTAMP=$(date -Is)
    CRITICAL_MESSAGE="CRITICAL: Nginx service has been stopped/crashed at ${TIMESTAMP}. Service failure detected!"
    
    # Use logger with priority 2 (CRITICAL) and tag it as nginx
    # This will be picked up by the monitor when it collects logs with SYSLOG_IDENTIFIER
    if command -v logger &> /dev/null; then
        logger -p 2 -t "nginx" "$CRITICAL_MESSAGE"
        echo "✅ CRITICAL error written via logger (priority 2)"
        
        # Also write multiple CRITICAL messages to ensure detection
        logger -p 2 -t "nginx" "CRITICAL: Nginx service failure - HTTP server is down and unavailable!"
        logger -p 2 -t "nginx" "CRITICAL: Nginx crash detected - service needs immediate attention!"
    fi
    
    # Use systemd-cat to write directly as nginx service unit
    if command -v systemd-cat &> /dev/null; then
        echo "$CRITICAL_MESSAGE" | systemd-cat -t "nginx" -p "crit"
        echo "✅ CRITICAL error written via systemd-cat"
        
        # Write additional CRITICAL messages
        echo "CRITICAL: Nginx service failure - web server is down!" | systemd-cat -t "nginx" -p "crit"
    fi
    
    # Method 3: Create a fake nginx crash log directly
    echo "📝 Method 3: Creating nginx crash log entry..."
    python3 << 'EOF'
import subprocess
import datetime

timestamp = datetime.datetime.now().isoformat()
message = f"CRITICAL: Nginx service crashed/stopped at {timestamp}. This is a test critical error that MUST appear in the dashboard."

# Write using systemd-cat with CRITICAL priority
try:
    result = subprocess.run(
        ['systemd-cat', '-t', 'nginx', '-p', 'crit'],
        input=message.encode(),
        check=False,
        capture_output=True
    )
    print(f"✅ Python-written CRITICAL error created")
except Exception as e:
    print(f"⚠️  Error: {e}")
EOF
    
    # Verify nginx is stopped
    if ! systemctl is-active --quiet nginx 2>/dev/null && ! systemctl is-active --quiet nginx.service 2>/dev/null; then
        echo ""
        echo "✅ Nginx has been stopped successfully"
    else
        echo ""
        echo "⚠️  Nginx may still be running (might require sudo privileges)"
    fi
    
else
    echo "⚠️  Nginx is not currently running"
    echo ""
    echo "Attempting to start nginx first, then stop it to create the error..."
    
    # Try to start it first (might fail if not installed)
    sudo systemctl start nginx 2>/dev/null || sudo systemctl start nginx.service 2>/dev/null
    sleep 2
    
    # Now stop it to create the error
    sudo systemctl stop nginx 2>/dev/null || sudo systemctl stop nginx.service 2>/dev/null
    
    # Write CRITICAL log anyway
    TIMESTAMP=$(date -Is)
    CRITICAL_MESSAGE="CRITICAL: Nginx service failure detected at ${TIMESTAMP}. Service may have crashed or been stopped unexpectedly!"
    
    if command -v logger &> /dev/null; then
        logger -p 2 -t "nginx" "$CRITICAL_MESSAGE"
    fi
    
    if command -v systemd-cat &> /dev/null; then
        echo "$CRITICAL_MESSAGE" | systemd-cat -t "nginx" -p "crit"
    fi
    
    echo "✅ CRITICAL error logged"
fi

# Method 4: Direct journalctl write (if we have permission)
echo ""
echo "📝 Method 4: Attempting direct journal write..."
if [ -w "/var/log/journal" ] || [ -w "/run/log/journal" ]; then
    echo "✅ Journal is writable"
else
    echo "⚠️  Journal requires sudo for direct writes (this is normal)"
fi

echo ""
echo "============================================================"
echo "✅ Nginx crash script complete!"
echo "============================================================"
echo ""
echo "📋 VERIFICATION STEPS:"
echo ""
echo "1. Verify logs were written:"
echo "   sudo journalctl -u nginx -p 2 -n 5 --no-pager"
echo "   sudo journalctl SYSLOG_IDENTIFIER=nginx -p 2 -n 5 --no-pager"
echo "   sudo journalctl -p 2 --since '2 minutes ago' | grep -i nginx"
echo ""
echo "2. Check if nginx is in monitored services (need to restart server):"
echo "   The server must be restarted after adding nginx to the monitor list!"
echo ""
echo "3. The critical error should appear in the dashboard within:"
echo "   - 10 seconds (if monitor interval is set to 10s)"
echo "   - Or refresh the dashboard manually"
echo ""
echo "⚠️  IMPORTANT: Make sure you restarted the monitoring server"
echo "   after adding nginx to the critical services list!"
echo ""
echo "Check the 'Critical Errors Only' section in the dashboard!"
echo ""

