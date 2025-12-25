import requests
import time
import json

BASE_URL = "http://localhost:5001/api"

def test_healing_demo():
    print("Testing Self-Healing Demo Endpoints...")
    
    # 1. Start Demo
    print("\n1. Starting Demo...")
    try:
        start_res = requests.post(f"{BASE_URL}/demo/healing/start")
        print(f"Start Response: {start_res.json()}")
        if start_res.status_code != 200:
            print("Failed to start demo")
            return
    except Exception as e:
        print(f"Error connecting to dashboard: {e}")
        return

    # 2. Poll Status
    print("\n2. Polling Status for 15 seconds...")
    for i in range(8):
        status_res = requests.get(f"{BASE_URL}/demo/healing/status")
        data = status_res.json()
        print(f"Step: {data.get('step')}, Message: {data.get('message')}")
        if data.get('manual_instructions'):
            print(f"Manual Instructions detected!")
        time.sleep(2)

    # 3. Stop Demo
    print("\n3. Stopping Demo...")
    stop_res = requests.post(f"{BASE_URL}/demo/healing/stop")
    print(f"Stop Response: {stop_res.json()}")

    # 4. Final Status Check
    print("\n4. Final Status Check...")
    final_res = requests.get(f"{BASE_URL}/demo/healing/status")
    print(f"Final Status: {final_res.json()}")

if __name__ == "__main__":
    test_healing_demo()
