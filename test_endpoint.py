import time
import urllib.request
import json
import socket

def wait_for_port(port, host='localhost', timeout=10.0):
    start_time = time.perf_counter()
    while True:
        try:
            with socket.create_connection((host, port), timeout=1.0):
                return True
        except OSError:
            time.sleep(0.5)
            if time.perf_counter() - start_time >= timeout:
                return False

def test_endpoint():
    url = "http://localhost:5001/api/processes/top"
    for i in range(5):
        start = time.time()
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=3.0) as response:
                data = json.loads(response.read().decode())
                print(f"Request {i+1}: {time.time() - start:.3f}s - {len(data)} processes loaded")
        except urllib.error.URLError as e:
            print(f"Request {i+1} failed: {e}")
        time.sleep(1)

if __name__ == "__main__":
    if wait_for_port(5001, timeout=2.0):
        print("Server is running on port 5001. Testing endpoint...")
        test_endpoint()
    else:
        print("Server is not running on port 5001. Starting it...")
        import subprocess
        import sys
        
        proc = subprocess.Popen([sys.executable, "monitoring/server/healing_dashboard_api.py"])
        if wait_for_port(5001, timeout=10.0):
            print("Server started. Testing endpoint...")
            test_endpoint()
            proc.terminate()
            proc.wait()
        else:
            print("Server failed to start.")
            proc.terminate()
