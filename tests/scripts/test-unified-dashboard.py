#!/usr/bin/env python3
"""
Test Script for Unified Dashboard
Tests all API endpoints to ensure everything works
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:3001"
TEST_RESULTS = []

def test_endpoint(name, method, endpoint, data=None, expected_keys=None):
    """Test an API endpoint"""
    print(f"\n🧪 Testing: {name}")
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data or {}, timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            
            if expected_keys:
                for key in expected_keys:
                    if key not in result:
                        print(f"   ❌ Missing key: {key}")
                        TEST_RESULTS.append((name, False))
                        return False
            
            print(f"   ✅ Success: {response.status_code}")
            TEST_RESULTS.append((name, True))
            return True
        else:
            print(f"   ❌ Failed: {response.status_code}")
            TEST_RESULTS.append((name, False))
            return False
    
    except requests.exceptions.ConnectionError:
        print(f"   ⚠️  Connection failed - Is the dashboard running?")
        TEST_RESULTS.append((name, False))
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        TEST_RESULTS.append((name, False))
        return False

def main():
    print("="*60)
    print("🛡️  Unified Healing Bot Dashboard - Test Suite")
    print("="*60)
    
    print("\n📡 Checking if dashboard is running...")
    if not test_endpoint("Health Check", "GET", "/api/health", expected_keys=["status"]):
        print("\n❌ Dashboard is not running!")
        print("   Start it with: ./start-unified-dashboard.sh")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("Testing Core Features")
    print("="*60)
    
    # Core API tests
    test_endpoint("System Metrics", "GET", "/api/metrics", expected_keys=["cpu", "memory", "disk"])
    test_endpoint("System Metrics (alt)", "GET", "/api/metrics/system", expected_keys=["cpu", "memory"])
    test_endpoint("Configuration", "GET", "/api/config")
    
    print("\n" + "="*60)
    print("Testing ML Monitoring Features")
    print("="*60)
    
    # ML Monitoring tests
    test_endpoint("ML Metrics", "GET", "/api/metrics/ml", expected_keys=["accuracy", "precision"])
    test_endpoint("Attack Statistics", "GET", "/api/metrics/attacks", expected_keys=["total_detections"])
    test_endpoint("ML History", "GET", "/api/history/ml", expected_keys=["timestamps", "accuracy"])
    test_endpoint("System History", "GET", "/api/history/system", expected_keys=["timestamps", "cpu_usage"])
    test_endpoint("Blocking Stats", "GET", "/api/blocking/stats", expected_keys=["total_blocked"])
    test_endpoint("Blocked IPs List", "GET", "/api/blocking/ips")
    
    print("\n" + "="*60)
    print("Testing System Healing Features")
    print("="*60)
    
    # System Healing tests
    test_endpoint("Services Status", "GET", "/api/services", expected_keys=["services"])
    test_endpoint("Top Processes", "GET", "/api/processes/top")
    test_endpoint("SSH Attempts", "GET", "/api/ssh/attempts", expected_keys=["attempts"])
    test_endpoint("Disk Status", "GET", "/api/disk/status", expected_keys=["total", "used", "free"])
    test_endpoint("Logs", "GET", "/api/logs", expected_keys=["logs"])
    
    print("\n" + "="*60)
    print("Testing CLI Features")
    print("="*60)
    
    # CLI tests
    test_endpoint("CLI Help", "POST", "/api/cli/execute", 
                 data={"command": "help"}, expected_keys=["output"])
    test_endpoint("CLI Status", "POST", "/api/cli/execute", 
                 data={"command": "status"}, expected_keys=["output"])
    test_endpoint("CLI Services", "POST", "/api/cli/execute", 
                 data={"command": "services"}, expected_keys=["output"])
    
    print("\n" + "="*60)
    print("Test Results Summary")
    print("="*60)
    
    passed = sum(1 for _, result in TEST_RESULTS if result)
    failed = len(TEST_RESULTS) - passed
    
    print(f"\n✅ Passed: {passed}/{len(TEST_RESULTS)}")
    print(f"❌ Failed: {failed}/{len(TEST_RESULTS)}")
    
    if failed > 0:
        print("\nFailed Tests:")
        for name, result in TEST_RESULTS:
            if not result:
                print(f"  • {name}")
    
    print("\n" + "="*60)
    print("Access Points:")
    print("="*60)
    print(f"  📊 ML Dashboard: {BASE_URL}")
    print(f"  🛡️  Healing Dashboard: {BASE_URL}/static/healing-dashboard.html")
    print("="*60)
    
    if failed == 0:
        print("\n🎉 All tests passed! Dashboard is fully functional!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

