#!/usr/bin/env python3
"""
Simple script to test Critical Errors Only section in the dashboard.

This script generates CRITICAL severity log entries that should appear
in the "Critical Errors Only" section of the dashboard.
"""

import logging
import sys
from datetime import datetime
import subprocess
import os

def generate_critical_error():
    """Generate a CRITICAL error log entry"""
    
    print("🔴 Generating CRITICAL error for testing...")
    
    # Get current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Method 1: Use logger command (most reliable for system logs)
    print("📝 Method 1: Using logger command...")
    try:
        # Write CRITICAL error to syslog
        message = (
            f"CRITICAL: Test critical error generated at {timestamp}. "
            f"This is a test error to verify the Critical Errors Only section is working correctly. "
            f"Service: test-critical-service, Priority: 2 (CRITICAL)"
        )
        
        # Use logger command with priority 2 (CRITICAL)
        subprocess.run(
            ['logger', '-p', '2', '-t', 'test-critical-service', message],
            check=True
        )
        print("✅ CRITICAL error written to syslog using logger command")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error using logger command: {e}")
    except FileNotFoundError:
        print("⚠️  logger command not found, trying Python logger...")
        
        # Method 2: Use Python logger
        try:
            logging.basicConfig(
                level=logging.CRITICAL,
                format='%(asctime)s %(name)s %(levelname)s: %(message)s'
            )
            logger = logging.getLogger('test-critical-service')
            logger.critical(
                f"CRITICAL: Test critical error generated at {timestamp}. "
                f"This is a test error to verify the Critical Errors Only section is working correctly."
            )
            print("✅ CRITICAL error written using Python logger")
        except Exception as e:
            print(f"❌ Error using Python logger: {e}")
    
    # Method 3: Write directly to critical log file (if it exists)
    critical_log_path = "/var/log/critical_errors.log"
    if os.path.exists(critical_log_path) or os.access(os.path.dirname(critical_log_path), os.W_OK):
        try:
            with open(critical_log_path, 'a') as f:
                f.write(
                    f"{timestamp} test-critical-service CRITICAL: "
                    f"Test critical error generated. This is a test error to verify the Critical Errors Only section.\n"
                )
            print(f"✅ CRITICAL error written to {critical_log_path}")
        except Exception as e:
            print(f"⚠️  Could not write to {critical_log_path}: {e}")
    
    print("\n" + "="*60)
    print("✅ Test critical error generated!")
    print("="*60)
    print("\n📋 Next steps:")
    print("1. Wait 10-30 seconds for the log to be collected")
    print("2. Refresh the dashboard")
    print("3. Go to 'Logs & AI' tab")
    print("4. Check the 'Critical Errors Only' section at the top")
    print("5. You should see the test error with:")
    print("   - Service: test-critical-service")
    print("   - Severity: CRITICAL")
    print("   - Message: Test critical error generated...")
    print("\n💡 Tip: If you don't see it, try:")
    print("   - Wait a bit longer (logs are collected every 30 seconds)")
    print("   - Check browser console for any errors")
    print("   - Verify the dashboard API is running")

if __name__ == "__main__":
    try:
        generate_critical_error()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

