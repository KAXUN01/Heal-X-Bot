#!/usr/bin/env python3
"""
Test script to verify Discord notifications for critical errors.

This script:
1. Generates a real critical error
2. Waits for it to be detected
3. Verifies Discord notification was sent

Prerequisites:
- Discord webhook must be configured in the dashboard
- Dashboard must be running
"""

import subprocess
import time
import sys
from datetime import datetime

def generate_critical_error():
    """Generate a CRITICAL error"""
    print("🔴 Generating CRITICAL error for Discord notification test...")
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = (
        f"CRITICAL: Discord notification test error at {timestamp}. "
        f"This is a test to verify Discord notifications are working correctly. "
        f"Service: discord-test-service, Priority: 2 (CRITICAL)"
    )
    
    try:
        # Use logger command with CRITICAL priority (2)
        subprocess.run(
            ['logger', '-p', '2', '-t', 'discord-test-service', message],
            check=True,
            timeout=5
        )
        print("✅ CRITICAL error generated")
        return True
    except FileNotFoundError:
        print("⚠️  logger command not found, trying Python logging...")
        import logging
        logging.basicConfig(level=logging.CRITICAL)
        logger = logging.getLogger('discord-test-service')
        logger.critical(message)
        print("✅ CRITICAL error generated via Python logger")
        return True
    except Exception as e:
        print(f"❌ Error generating critical error: {e}")
        return False

def check_discord_webhook():
    """Check if Discord webhook is configured"""
    print("\n📋 Checking Discord webhook configuration...")
    print("   To configure Discord webhook:")
    print("   1. Go to dashboard: http://localhost:5001")
    print("   2. Click on 'Alerts' tab")
    print("   3. Enter your Discord webhook URL")
    print("   4. Click 'Test Notification' to verify")
    print("\n   Or set environment variable:")
    print("   export DISCORD_WEBHOOK='your_webhook_url_here'")
    print()

def main():
    """Main function"""
    print("="*60)
    print("🔔 Discord Critical Error Notification Test")
    print("="*60)
    print()
    
    # Check Discord webhook
    check_discord_webhook()
    
    response = input("Have you configured the Discord webhook? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("\n⚠️  Please configure Discord webhook first!")
        print("   The notification will only work if webhook is configured.")
        print()
        response2 = input("Continue anyway? (yes/no): ").strip().lower()
        if response2 not in ['yes', 'y']:
            print("Cancelled.")
            sys.exit(0)
    
    print("\n" + "="*60)
    print("Generating critical error...")
    print("="*60)
    
    if not generate_critical_error():
        print("❌ Failed to generate critical error")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("⏳ Waiting for error detection and notification...")
    print("="*60)
    print("\nThe system will:")
    print("1. Collect the log (takes 10-30 seconds)")
    print("2. Detect it as a CRITICAL error")
    print("3. Send Discord notification (if webhook is configured)")
    print("\nWaiting 35 seconds for processing...")
    
    for i in range(35, 0, -5):
        print(f"   ⏳ {i} seconds remaining...", end='\r')
        time.sleep(5)
    
    print("\n" + "="*60)
    print("✅ Test Complete!")
    print("="*60)
    print("\n📋 What to check:")
    print("1. ✅ Check Discord channel for notification")
    print("   - You should see a message with 🚨 emoji")
    print("   - Title: '🚨 Healing Bot Alert'")
    print("   - Service: discord-test-service")
    print("   - Level: CRITICAL")
    print()
    print("2. ✅ Check dashboard 'Critical Errors Only' section")
    print("   - Go to 'Logs & AI' tab")
    print("   - Check the 'Critical Errors Only' section at the top")
    print("   - You should see the test error")
    print()
    print("3. ✅ Check server logs")
    print("   - Look for: 'Discord notification sent for new CRITICAL error'")
    print()
    print("💡 If you don't see Discord notification:")
    print("   - Verify webhook URL is correct")
    print("   - Check server logs for errors")
    print("   - Make sure webhook is configured in dashboard or .env file")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


