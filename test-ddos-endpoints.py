#!/usr/bin/env python3
"""
Test script for DDoS Detection endpoints in the Healing Dashboard
"""

import requests
import json
import sys
import time

# API base URL
BASE_URL = "http://localhost:5001"

def test_endpoint(name, url, method="GET", data=None):
    """Test a single endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print(f"Method: {method}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        else:
            print(f"❌ Unsupported method: {method}")
            return False
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS")
            print(f"Response:")
            print(json.dumps(result, indent=2))
            return True
        else:
            print(f"❌ FAILED")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ CONNECTION ERROR - Is the server running on {BASE_URL}?")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("DDoS Detection Endpoints Test Suite")
    print("=" * 60)
    
    # Test counter
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Health check
    if test_endpoint("Health Check", f"{BASE_URL}/api/health"):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test 2: ML Metrics
    if test_endpoint("ML Metrics", f"{BASE_URL}/api/metrics/ml"):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test 3: Attack Statistics
    if test_endpoint("Attack Statistics", f"{BASE_URL}/api/metrics/attacks"):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test 4: ML History
    if test_endpoint("ML History", f"{BASE_URL}/api/history/ml"):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test 5: Block IP (test with sample IP)
    test_data = {"ip": "192.0.2.1"}
    if test_endpoint("Block IP", f"{BASE_URL}/api/blocking/block", "POST", test_data):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test 6: Report DDoS Detection
    ddos_data = {
        "is_ddos": True,
        "source_ip": "203.0.113.50",
        "attack_type": "TCP SYN Flood",
        "confidence": 0.92,
        "prediction": 0.88
    }
    if test_endpoint("Report DDoS", f"{BASE_URL}/api/ddos/report", "POST", ddos_data):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests Passed: {tests_passed}")
    print(f"Tests Failed: {tests_failed}")
    print(f"Total Tests: {tests_passed + tests_failed}")
    
    if tests_failed == 0:
        print("\n✅ All tests passed!")
        return 0
    else:
        print(f"\n❌ {tests_failed} test(s) failed")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)

