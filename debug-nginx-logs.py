#!/usr/bin/env python3
"""
Debug script to check if nginx CRITICAL logs are being collected
"""

import subprocess
import json
import sys

def check_nginx_logs():
    """Check if nginx CRITICAL logs exist and would be detected"""
    
    print("=" * 60)
    print("🔍 DEBUGGING NGINX LOGS")
    print("=" * 60)
    
    # Check 1: Systemd unit logs
    print("\n1. Checking systemd unit logs (journalctl -u nginx -p 2):")
    try:
        result = subprocess.run(
            ['sudo', 'journalctl', '-u', 'nginx', '-p', '2', '-n', '10', '--output=json', '--no-pager'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            lines = [l for l in result.stdout.strip().split('\n') if l.strip()]
            print(f"   ✅ Found {len(lines)} CRITICAL priority logs from nginx unit")
            if lines:
                entry = json.loads(lines[0])
                print(f"   Sample: {entry.get('MESSAGE', 'N/A')[:80]}")
        else:
            print("   ⚠️  No CRITICAL logs found from nginx unit")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Check 2: SYSLOG_IDENTIFIER logs
    print("\n2. Checking SYSLOG_IDENTIFIER logs (journalctl SYSLOG_IDENTIFIER=nginx -p 2):")
    try:
        result = subprocess.run(
            ['sudo', 'journalctl', 'SYSLOG_IDENTIFIER=nginx', '-p', '2', '-n', '10', '--output=json', '--no-pager'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            lines = [l for l in result.stdout.strip().split('\n') if l.strip()]
            print(f"   ✅ Found {len(lines)} CRITICAL priority logs with SYSLOG_IDENTIFIER=nginx")
            if lines:
                entry = json.loads(lines[0])
                print(f"   Sample: {entry.get('MESSAGE', 'N/A')[:80]}")
        else:
            print("   ⚠️  No CRITICAL logs found with SYSLOG_IDENTIFIER=nginx")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Check 3: All CRITICAL logs from last 2 minutes
    print("\n3. Checking all CRITICAL logs from last 2 minutes (journalctl -p 2 --since '2 minutes ago'):")
    try:
        result = subprocess.run(
            ['sudo', 'journalctl', '-p', '2', '--since', '2 minutes ago', '-n', '50', '--output=json', '--no-pager'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            lines = [l for l in result.stdout.strip().split('\n') if l.strip()]
            nginx_logs = []
            for line in lines:
                try:
                    entry = json.loads(line)
                    syslog_id = entry.get('SYSLOG_IDENTIFIER', '')
                    systemd_unit = entry.get('_SYSTEMD_UNIT', '')
                    if 'nginx' in syslog_id.lower() or 'nginx' in systemd_unit.lower():
                        nginx_logs.append(entry)
                except:
                    continue
            print(f"   ✅ Found {len(nginx_logs)} nginx-related CRITICAL logs out of {len(lines)} total CRITICAL logs")
            if nginx_logs:
                print(f"   Sample nginx log: {nginx_logs[0].get('MESSAGE', 'N/A')[:80]}")
                print(f"   SYSLOG_IDENTIFIER: {nginx_logs[0].get('SYSLOG_IDENTIFIER', 'N/A')}")
                print(f"   _SYSTEMD_UNIT: {nginx_logs[0].get('_SYSTEMD_UNIT', 'N/A')}")
                print(f"   PRIORITY: {nginx_logs[0].get('PRIORITY', 'N/A')}")
        else:
            print("   ⚠️  No CRITICAL logs found in last 2 minutes")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS:")
    print("=" * 60)
    print("1. Run: ./test-nginx-crash.sh (to write test CRITICAL logs)")
    print("2. Restart the monitoring server (to pick up nginx in the monitor list)")
    print("3. Wait 10-15 seconds for the monitor to collect logs")
    print("4. Refresh the dashboard")
    print("")

if __name__ == "__main__":
    check_nginx_logs()

