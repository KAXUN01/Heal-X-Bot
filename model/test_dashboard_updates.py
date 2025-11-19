#!/usr/bin/env python3
"""
Test Dashboard Updates - Verify predictions are visible

This script sends test scenarios and checks if the dashboard API
is returning the correct data format for visualization.
"""

import requests
import json
import time

DASHBOARD_URL = "http://localhost:5001"

def test_api_endpoint(name, url, method="GET", data=None):
    """Test an API endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"{'='*60}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        else:
            response = requests.post(url, json=data, timeout=10)
        
        print(f"Status: {response.status_code}")
        
        if response.ok:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
            
            # Check for required fields
            if 'risk_score' in result:
                risk = result['risk_score'] * 100
                print(f"\n✅ Risk Score: {risk:.2f}%")
                if 'risk_level' in result:
                    print(f"✅ Risk Level: {result['risk_level']}")
                if 'risk_percentage' in result:
                    print(f"✅ Risk Percentage: {result['risk_percentage']:.2f}%")
                return True
            elif 'error' in result:
                print(f"⚠️ Error: {result['error']}")
                return False
            else:
                print("⚠️ No risk_score in response")
                return False
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("="*60)
    print("Dashboard API Test - Verify Predictions")
    print("="*60)
    
    # Test 1: Current system risk
    test_api_endpoint(
        "Current System Risk",
        f"{DASHBOARD_URL}/api/predict-failure-risk"
    )
    
    # Test 2: Custom metrics (normal)
    test_api_endpoint(
        "Normal Operation (Custom Metrics)",
        f"{DASHBOARD_URL}/api/predict-failure-risk-custom",
        method="POST",
        data={
            "metrics": {
                "cpu_percent": 30.0,
                "memory_percent": 40.0,
                "disk_percent": 50.0,
                "network_in_bytes": 100000,
                "network_out_bytes": 50000,
                "connections_count": 50,
                "memory_available_gb": 8.0,
                "disk_free_gb": 50.0,
                "error_count": 0,
                "warning_count": 1,
                "critical_count": 0,
                "service_failures": 0,
                "auth_failures": 0,
                "ssh_attempts": 0
            }
        }
    )
    
    # Test 3: Custom metrics (high load)
    test_api_endpoint(
        "High Load (Custom Metrics)",
        f"{DASHBOARD_URL}/api/predict-failure-risk-custom",
        method="POST",
        data={
            "metrics": {
                "cpu_percent": 95.0,
                "memory_percent": 90.0,
                "disk_percent": 85.0,
                "network_in_bytes": 500000,
                "network_out_bytes": 250000,
                "connections_count": 500,
                "memory_available_gb": 0.5,
                "disk_free_gb": 2.0,
                "error_count": 50,
                "warning_count": 100,
                "critical_count": 10,
                "service_failures": 5,
                "auth_failures": 20,
                "ssh_attempts": 15
            }
        }
    )
    
    print("\n" + "="*60)
    print("Test Complete!")
    print("="*60)
    print("\n💡 If all tests pass, the dashboard should display:")
    print("   - Risk scores updating")
    print("   - Progress bar filling")
    print("   - Risk levels changing")
    print("\n📋 Next steps:")
    print("   1. Open dashboard: http://localhost:5001")
    print("   2. Go to: Predictive Maintenance tab")
    print("   3. Open browser console (F12) to see refresh logs")
    print("   4. Click '🔄 Refresh Now' button")
    print("   5. Check if predictions update")

if __name__ == "__main__":
    main()

