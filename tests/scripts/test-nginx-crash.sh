#!/bin/bash
#
# Quick test script to crash nginx and verify logs are written
# This is a simpler version that focuses on writing CRITICAL logs
#

echo "🔴 Quick Nginx Crash Test"
echo "=========================="
echo ""

# Write multiple CRITICAL logs with priority 2
echo "Writing CRITICAL priority logs..."
TIMESTAMP=$(date -Is)

# Method 1: Use logger (works without sudo but may not show in all queries)
for i in {1..5}; do
    logger -p 2 -t "nginx" "CRITICAL: Nginx service crash test #$i at ${TIMESTAMP} - This MUST appear in dashboard!"
    echo "✓ CRITICAL log #$i written via logger"
    sleep 0.1
done

# Method 2: Use systemd-cat with CRITICAL priority
if command -v systemd-cat &> /dev/null; then
    for i in {1..3}; do
        echo "CRITICAL: Nginx crash test via systemd-cat #$i at ${TIMESTAMP}" | systemd-cat -t "nginx" -p "crit"
        echo "✓ CRITICAL log #$i written via systemd-cat"
        sleep 0.1
    done
fi

# Method 3: Use Python to write directly (most reliable)
python3 << 'PYEOF'
import subprocess
import datetime

timestamp = datetime.datetime.now().isoformat()
for i in range(3):
    message = f"CRITICAL: Nginx crash test via Python #{(i+1)} at {timestamp}"
    try:
        # Use systemd-cat with CRITICAL priority
        subprocess.run(
            ['systemd-cat', '-t', 'nginx', '-p', 'crit'],
            input=message.encode(),
            check=False,
            timeout=5
        )
        print(f"✓ CRITICAL log #{(i+1)} written via Python/systemd-cat")
    except Exception as e:
        print(f"⚠️  Error writing log #{(i+1)}: {e}")
PYEOF

# Verify logs were written
echo ""
echo "Verifying logs..."
if sudo journalctl -p 2 --since '1 minute ago' | grep -qi nginx; then
    COUNT=$(sudo journalctl -p 2 --since '1 minute ago' | grep -ci nginx)
    echo "✅ Found $COUNT nginx-related CRITICAL logs in journal!"
else
    echo "⚠️  No nginx CRITICAL logs found in journal yet (may take a moment)"
fi

echo ""
echo "✅ Test logs written!"
echo ""
echo "Verify logs with:"
echo "  sudo journalctl -p 2 --since '1 minute ago' | grep -i nginx"
echo "  sudo journalctl SYSLOG_IDENTIFIER=nginx -p 2 -n 10 --no-pager"
echo ""

