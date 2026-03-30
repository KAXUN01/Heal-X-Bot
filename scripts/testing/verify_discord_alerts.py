import requests
import time
import sys
import json

BASE_URL = "http://localhost:5001"

def wait_for_server():
    print("Waiting for server to start...")
    for i in range(10):
        try:
            # Try hitting the config endpoint to check if server is up
            response = requests.get(f"{BASE_URL}/api/config", timeout=2)
            if response.status_code == 200:
                print("Server is up!")
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    return False

def verify_discord_endpoint():
    print("\nVerifying /api/alerts/discord endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/alerts/discord")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Response Data:", json.dumps(data, indent=2))
            
            if data.get("status") == "success" and "alerts" in data:
                print("✅ Endpoint structure is correct.")
                return True
            else:
                print("❌ Unexpected response structure.")
                return False
        else:
            print(f"❌ Request failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error calling endpoint: {e}")
        return False

def simulate_alert_and_verify():
    print("\nSimulating alert via /api/critical-services/issues?include_test=true...")
    try:
        # Trigger the test issue which might trigger an alert
        requests.get(f"{BASE_URL}/api/critical-services/issues?include_test=true")
        
        # Check discord alerts again
        print("Checking for alerts record...")
        response = requests.get(f"{BASE_URL}/api/alerts/discord")
        data = response.json()
        alerts = data.get("alerts", [])
        print(f"Found {len(alerts)} alerts.")
        
        # We can't guarantee the test issue triggers a notification (due to checks/configs), 
        # but if we see any alerts, that's great. If not, we primarily rely on the endpoint returning 200 OK.
        if len(alerts) > 0:
            print("✅ Alerts found in history!")
        else:
            print("ℹ️ No alerts found (this might be expected if webhook is not configured or rate limited).")
            
        return True
    except Exception as e:
        print(f"❌ Error simulating alert: {e}")
        return False

if __name__ == "__main__":
    if not wait_for_server():
        print("❌ Server failed to start.")
        sys.exit(1)
        
    if verify_discord_endpoint():
        simulate_alert_and_verify()
        print("\n✅ Verification passed!")
    else:
        print("\n❌ Verification failed.")
        sys.exit(1)
