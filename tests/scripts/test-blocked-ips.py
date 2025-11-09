#!/usr/bin/env python3
"""
Test script for Blocked IPs Database functionality
"""

import requests
import json
import sys

BASE_URL = "http://localhost:5001"

def test_endpoint(name, method, url, data=None):
    """Test an endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    
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
            print(json.dumps(result, indent=2)[:500])  # Limit output
            return True
        else:
            print(f"❌ FAILED")
            print(f"Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ CONNECTION ERROR - Is the server running?")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("Blocked IPs Database Test Suite")
    print("="*60)
    
    passed = 0
    failed = 0
    
    # Test 1: Block an IP
    print("\n\n### Test 1: Block IP ###")
    data = {
        "ip": "192.0.2.50",
        "attack_count": 5,
        "threat_level": "High",
        "attack_type": "TCP SYN Flood",
        "reason": "Test block",
        "blocked_by": "test_script"
    }
    if test_endpoint("Block IP", "POST", f"{BASE_URL}/api/blocking/block", data):
        passed += 1
    else:
        failed += 1
    
    # Test 2: Get blocked IPs list
    print("\n\n### Test 2: Get Blocked IPs List ###")
    if test_endpoint("Get Blocked IPs", "GET", f"{BASE_URL}/api/blocked-ips"):
        passed += 1
    else:
        failed += 1
    
    # Test 3: Get IP details
    print("\n\n### Test 3: Get IP Details ###")
    if test_endpoint("Get IP Info", "GET", f"{BASE_URL}/api/blocked-ips/192.0.2.50"):
        passed += 1
    else:
        failed += 1
    
    # Test 4: Get blocked IPs statistics
    print("\n\n### Test 4: Get Statistics ###")
    if test_endpoint("Get Statistics", "GET", f"{BASE_URL}/api/blocked-ips/statistics"):
        passed += 1
    else:
        failed += 1
    
    # Test 5: Unblock the IP
    print("\n\n### Test 5: Unblock IP ###")
    data = {
        "ip": "192.0.2.50",
        "unblocked_by": "test_script",
        "reason": "Test completed"
    }
    if test_endpoint("Unblock IP", "POST", f"{BASE_URL}/api/blocked-ips/unblock", data):
        passed += 1
    else:
        failed += 1
    
    # Test 6: Get blocked IPs (including unblocked)
    print("\n\n### Test 6: Get All IPs (including unblocked) ###")
    if test_endpoint("Get All IPs", "GET", f"{BASE_URL}/api/blocked-ips?include_unblocked=true"):
        passed += 1
    else:
        failed += 1
    
    # Test 7: Block multiple IPs for testing
    print("\n\n### Test 7: Block Multiple IPs ###")
    test_ips = [
        {"ip": "203.0.113.100", "attack_count": 12, "threat_level": "Critical"},
        {"ip": "198.51.100.50", "attack_count": 7, "threat_level": "High"},
        {"ip": "192.0.2.25", "attack_count": 3, "threat_level": "Medium"},
    ]
    
    for ip_data in test_ips:
        ip_data["blocked_by"] = "test_script"
        ip_data["reason"] = "Test data"
        if test_endpoint(f"Block {ip_data['ip']}", "POST", f"{BASE_URL}/api/blocking/block", ip_data):
            passed += 1
        else:
            failed += 1
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Tests Passed: {passed}")
    print(f"Tests Failed: {failed}")
    print(f"Total Tests: {passed + failed}")
    
    if failed == 0:
        print("\n✅ All tests passed!")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)

