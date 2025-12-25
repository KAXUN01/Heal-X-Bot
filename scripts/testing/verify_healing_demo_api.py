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

    # 2. Poll Status & Interact
    print("\n2. Polling Status...")
    for i in range(15):
        try:
            status_res = requests.get(f"{BASE_URL}/demo/healing/status")
            data = status_res.json()
            print(f"[{i}] Step: {data.get('step')}, Waiting: {data.get('waiting_for_user')}")
            
            if data.get('waiting_for_user'):
                print(f"   Action required! Scenario: {data.get('scenario')}")
                action = "auto_heal" if data.get('scenario') == 'auto-heal' else "manual_steps"
                print(f"   Triggering action: {action}")
                
                solve_res = requests.post(f"{BASE_URL}/demo/healing/solve", json={"action": action})
                print(f"   Solve Response: {solve_res.json()}")
            
            if data.get('step') == 'Done':
                print("   Demo iteration complete.")
                break
                
        except Exception as e:
            print(f"Error polling: {e}")
            
        time.sleep(2)

    # 3. Stop Demo
    print("\n3. Stopping Demo...")
    stop_res = requests.post(f"{BASE_URL}/demo/healing/stop")
    print(f"Stop Response: {stop_res.json()}")

if __name__ == "__main__":
    test_healing_demo()
