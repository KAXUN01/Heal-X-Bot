#!/usr/bin/env python3
"""
Diagnostic script to check why auto-restart might not be working
"""

import requests
import subprocess
import sys
import time

BASE_URL = "http://localhost:5001"

def check_api():
    """Check if API is running"""
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def check_config():
    """Check auto-restart configuration"""
    try:
        response = requests.get(f"{BASE_URL}/api/config", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("auto_restart", False)
    except:
        pass
    return None

def check_service_status(service_name):
    """Check service status"""
    try:
        result = subprocess.run(
            ["systemctl", "is-active", service_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0 and result.stdout.strip() == "active"
    except:
        return False

def main():
    print("="*60)
    print("Auto-Restart Diagnostic Tool")
    print("="*60)
    print()
    
    # Check 1: API running
    print("1. Checking if API is running...")
    if check_api():
        print("   ✅ API is running")
    else:
        print("   ❌ API is NOT running")
        print("   → Start it with: python monitoring/server/healing_dashboard_api.py")
        return 1
    
    # Check 2: Auto-restart config
    print("\n2. Checking auto-restart configuration...")
    auto_restart = check_config()
    if auto_restart is None:
        print("   ⚠️  Could not check configuration")
    elif auto_restart:
        print("   ✅ Auto-restart is ENABLED")
    else:
        print("   ❌ Auto-restart is DISABLED")
        print("   → Enable it via the dashboard or API")
        return 1
    
    # Check 3: Service status
    print("\n3. Checking service statuses...")
    services = ["nginx", "mysql", "ssh", "docker", "postgresql"]
    for service in services:
        is_running = check_service_status(service)
        status = "🟢 Running" if is_running else "🔴 Stopped"
        print(f"   {status} - {service}")
    
    # Check 4: Test service stop/restart
    print("\n4. Testing service detection...")
    test_service = "nginx"
    print(f"   Testing with: {test_service}")
    
    # Check if running
    if not check_service_status(test_service):
        print(f"   ⚠️  {test_service} is not running. Starting it...")
        subprocess.run(["sudo", "systemctl", "start", test_service], timeout=10)
        time.sleep(2)
    
    if check_service_status(test_service):
        print(f"   ✅ {test_service} is running")
        print(f"   → Now stop it manually: sudo systemctl stop {test_service}")
        print(f"   → Then check if it gets auto-restarted within 10 seconds")
    else:
        print(f"   ❌ {test_service} is not running and could not be started")
    
    print("\n" + "="*60)
    print("Diagnostic Complete")
    print("="*60)
    print("\nNext steps:")
    print("1. Make sure the monitoring loop is running (check API logs)")
    print("2. Stop a service: sudo systemctl stop nginx")
    print("3. Watch the API logs for auto-restart messages")
    print("4. Check service status after 10 seconds")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

