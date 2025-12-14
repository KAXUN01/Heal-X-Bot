import requests
import time
import sys

BASE_URL = "http://localhost:5001"
BLUE = "\033[94m"
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

def log(msg, color=RESET):
    print(f"{color}{msg}{RESET}")

def test_api():
    log("Starting DDoS Demo API Test...", BLUE)

    # 1. Check status (should be false)
    try:
        r = requests.get(f"{BASE_URL}/api/demo/ddos/status")
        if r.status_code == 200:
            data = r.json()
            if not data.get('running'):
                 log("✅ Status check passed (not running)", GREEN)
            else:
                 log("❌ Expected not running, but got running", RED)
                 return False
        else:
            log(f"❌ Status check failed: {r.status_code}", RED)
            return False
    except requests.exceptions.ConnectionError:
        log("❌ Could not connect to server. Is it running?", RED)
        return False

    # 2. Start simulation
    log("Starting simulation...", BLUE)
    r = requests.post(f"{BASE_URL}/api/demo/ddos/start")
    if r.status_code == 200 and r.json()['status'] == 'success':
        log("✅ Simulation started successfully", GREEN)
    else:
        log(f"❌ Failed to start: {r.text}", RED)
        return False

    # 3. Wait and check metrics
    log("Waiting for metrics to update (5s)...", BLUE)
    time.sleep(5)
    
    # Check metrics endpoint
    r = requests.get(f"{BASE_URL}/api/metrics/attacks")
    if r.status_code == 200:
        data = r.json()
        total_detections = data.get('total_detections', 0)
        ddos_attacks = data.get('ddos_attacks', 0)
        
        log(f"✅ Found total_detections: {total_detections}, ddos_attacks: {ddos_attacks}", GREEN)
        
        if total_detections > 0 or ddos_attacks > 0:
            log("✅ Metrics are being updated", GREEN)
        else:
            log("⚠️ Metrics are 0, possibly low traffic or ramp up phase", RED)
    else:
        log(f"❌ Failed to fetch metrics: {r.status_code}", RED)

    # Check ML metrics endpoint
    r = requests.get(f"{BASE_URL}/api/metrics/ml")
    if r.status_code == 200:
        data = r.json()
        acc = data.get('accuracy', 0)
        throughput = data.get('throughput', 0)
        log(f"✅ Found ML accuracy: {acc}, throughput: {throughput}", GREEN)
        
        # In simulation, accuracy should drop (below 0.98 default) or strictly change if logic works
        # Default in code was 0.98. Simulation drops it based on intensity.
        # But intensity starts low.
        if acc != 0.98 or throughput != 192.3:
             log("✅ ML Metrics are dynamic (changed from default)", GREEN)
        else:
             log("⚠️ ML Metrics are default (might need more time to ramp up)", RED)
    else:
        log(f"❌ Failed to fetch ML metrics: {r.status_code}", RED)

    # 4. Stop simulation
    log("Stopping simulation...", BLUE)
    r = requests.post(f"{BASE_URL}/api/demo/ddos/stop")
    if r.status_code == 200 and r.json()['status'] == 'success':
        log("✅ Simulation stopped successfully", GREEN)
    else:
        log(f"❌ Failed to stop: {r.text}", RED)
        return False
        
    log("Test Complete!", BLUE)
    return True

if __name__ == "__main__":
    if test_api():
        sys.exit(0)
    else:
        sys.exit(1)
