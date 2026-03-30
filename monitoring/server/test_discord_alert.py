import requests
import os
import json

def test_alert():
    url = "http://localhost:5000/api/alerts/discord"
    # This won't work because I don't have a POST endpoint.
    # I should instead trigger a situation that sends a discord alert.
    pass

if __name__ == "__main__":
    # Let's try to inject a fault that triggers a discord alert via FaultDetector
    fault_url = "http://localhost:5000/api/test/inject-error" # This is for log collector
    
    # Actually, I'll just check if the app is running and the new endpoint exists
    try:
        response = requests.get("http://localhost:5000/api/alerts/discord")
        print(f"API Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

