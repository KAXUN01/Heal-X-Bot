import requests
import json

BASE_URL = "http://localhost:5001"

def test_ip_blocking_fix():
    print("Testing IP blocking fix with string threat_level...")
    data = {
        "ip": "192.168.1.100",
        "threat_level": "High",
        "attack_count": 5,
        "reason": "Verification test"
    }
    try:
        response = requests.post(f"{BASE_URL}/api/blocking/block", json=data)
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200 and result.get("success"):
            print("✅ Test PASSED: IP blocking with string threat_level works!")
            return True
        else:
            print(f"❌ Test FAILED: {result.get('message', 'No message')}")
            return False
    except Exception as e:
        print(f"❌ Test ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    test_ip_blocking_fix()
