#!/usr/bin/env python3
"""
Script to generate a CRITICAL error log entry for testing the Critical Errors section.

This script writes a CRITICAL severity log entry to the system log,
which should be picked up by the critical services monitor and displayed
in the dashboard's "Critical Errors Only" section.
"""

import logging
import sys
from datetime import datetime
import subprocess
import os

def generate_critical_error():
    """Generate a CRITICAL error log entry"""
    
    # Method 1: Use Python logger with CRITICAL level
    print("📝 Generating CRITICAL error using Python logger...")
    
    # Configure logger to write to syslog
    logging.basicConfig(
        level=logging.CRITICAL,
        format='%(asctime)s %(name)s %(levelname)s: %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )
    
    logger = logging.getLogger('test-critical-service')
    
    # Generate a CRITICAL error
    critical_message = (
        "CRITICAL: Test critical error generated at {}. "
        "This is a test error to verify the Critical Errors section is working correctly. "
        "Service: test-critical-service, Priority: 1"
    ).format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    logger.critical(critical_message)
    
    # Method 2: Write directly to system log using logger command
    print("📝 Generating CRITICAL error using system logger command...")
    
    try:
        # Use logger command to write to system log
        test_message = (
            f"test-critical-service: CRITICAL ERROR - Test critical error generated at "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. "
            f"This is a test error to verify the Critical Errors section is working correctly."
        )
        
        # Write to syslog with priority 2 (CRITICAL)
        # Priority levels: 0=EMERG, 1=ALERT, 2=CRIT, 3=ERR, 4=WARNING
        subprocess.run(
            ['logger', '-p', '2', '-t', 'test-critical-service', test_message],
            check=True
        )
        print("✅ CRITICAL error written to system log using logger command")
        
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Failed to use logger command: {e}")
        print("   Trying alternative method...")
        
    except FileNotFoundError:
        print("⚠️  logger command not found. Trying alternative method...")
    
    # Method 3: Write directly to journald if available
    print("📝 Attempting to write to systemd journal...")
    
    try:
        journal_message = (
            f"CRITICAL: Test critical error - Service test-critical-service failed. "
            f"Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} for testing purposes."
        )
        
        subprocess.run(
            ['journalctl', '--user', '--priority=2', '--facility=syslog'],
            check=False,  # Don't fail if journalctl doesn't work
            capture_output=True
        )
        
        # Try to write using systemd-cat
        try:
            subprocess.run(
                ['systemd-cat', '-t', 'test-critical-service', '-p', 'crit', 'echo', journal_message],
                check=True,
                timeout=5
            )
            print("✅ CRITICAL error written to systemd journal")
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            print("⚠️  systemd-cat not available, skipped")
            
    except Exception as e:
        print(f"⚠️  Journal writing failed: {e}")
    
    # Method 4: Create a test log file in /var/log/ if accessible
    print("📝 Attempting to write test log file...")
    
    test_log_paths = [
        '/var/log/test-critical.log',
        '/tmp/test-critical.log',
        os.path.expanduser('~/test-critical.log')
    ]
    
    log_entry = (
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} "
        f"test-critical-service CRITICAL: Test critical error - "
        f"Service failure detected. This is a test entry for dashboard verification.\n"
    )
    
    for log_path in test_log_paths:
        try:
            with open(log_path, 'a') as f:
                f.write(log_entry)
            print(f"✅ Test log entry written to: {log_path}")
            break
        except PermissionError:
            continue
        except Exception as e:
            print(f"⚠️  Failed to write to {log_path}: {e}")
    
    print("\n" + "="*60)
    print("✅ Critical error generation complete!")
    print("="*60)
    print("\nThe generated errors should appear in the dashboard within:")
    print("  - 30 seconds (system log collection interval)")
    print("  - Or refresh the dashboard manually")
    print("\nCheck the 'Critical Errors Only' section in the dashboard.")
    print("\nTo view recent logs, run:")
    print("  sudo journalctl -p crit -n 20")
    print("  or")
    print("  sudo tail -f /var/log/syslog | grep -i critical")

if __name__ == "__main__":
    print("="*60)
    print("🔴 CRITICAL ERROR GENERATOR")
    print("="*60)
    print("\nThis script will generate test CRITICAL errors for testing")
    print("the 'Critical Errors Only' section in the dashboard.\n")
    
    try:
        generate_critical_error()
    except KeyboardInterrupt:
        print("\n\n❌ Script interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

