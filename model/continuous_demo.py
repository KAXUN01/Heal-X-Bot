#!/usr/bin/env python3
"""
Continuous Predictive Maintenance Demo

This script continuously sends different scenarios to the dashboard
so you can see predictions update in real-time.

Run this script and keep it running while you watch the dashboard.
"""

import requests
import time
import sys
from datetime import datetime

DASHBOARD_URL = "http://localhost:5001"

GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'

def send_scenario(name, metrics):
    """Send a scenario to the dashboard"""
    try:
        response = requests.post(
            f"{DASHBOARD_URL}/api/predict-anomaly",
            json={"metrics": metrics},
            timeout=10
        )
        if response.ok:
            data = response.json()
            risk = data.get('anomaly_score', 0) * 100
            return True, risk
        return False, 0
    except:
        return False, 0

def main():
    print(f"{BOLD}{CYAN}{'='*70}{RESET}")
    print(f"{BOLD}{CYAN}Continuous Predictive Maintenance Demo{RESET}")
    print(f"{BOLD}{CYAN}{'='*70}{RESET}\n")
    
    # Check dashboard
    try:
        requests.get(f"{DASHBOARD_URL}/api/health", timeout=5)
        print(f"{GREEN}✅ Dashboard is accessible{RESET}\n")
    except:
        print(f"{RED}❌ Dashboard not accessible. Please start it first.{RESET}")
        return
    
    print(f"{YELLOW}🌐 Open: http://localhost:5001 → Predictive Maintenance tab{RESET}")
    print(f"{CYAN}👀 Watch the predictions update in real-time!{RESET}\n")
    print(f"{YELLOW}Press Ctrl+C to stop{RESET}\n")
    
    scenarios = [
        ("Normal", {
            "cpu_percent": 30.0, "memory_percent": 40.0, "disk_percent": 50.0,
            "network_in_bytes": 100000, "network_out_bytes": 50000,
            "connections_count": 50, "memory_available_gb": 8.0,
            "disk_free_gb": 50.0, "error_count": 0, "warning_count": 1,
            "critical_count": 0, "service_failures": 0, "auth_failures": 0, "ssh_attempts": 0
        }),
        ("Moderate", {
            "cpu_percent": 60.0, "memory_percent": 65.0, "disk_percent": 55.0,
            "network_in_bytes": 200000, "network_out_bytes": 100000,
            "connections_count": 150, "memory_available_gb": 5.0,
            "disk_free_gb": 45.0, "error_count": 2, "warning_count": 5,
            "critical_count": 0, "service_failures": 0, "auth_failures": 0, "ssh_attempts": 0
        }),
        ("High Load", {
            "cpu_percent": 85.0, "memory_percent": 88.0, "disk_percent": 75.0,
            "network_in_bytes": 400000, "network_out_bytes": 200000,
            "connections_count": 300, "memory_available_gb": 1.5,
            "disk_free_gb": 30.0, "error_count": 10, "warning_count": 20,
            "critical_count": 2, "service_failures": 1, "auth_failures": 5, "ssh_attempts": 3
        }),
        ("Critical", {
            "cpu_percent": 98.0, "memory_percent": 96.0, "disk_percent": 95.0,
            "network_in_bytes": 500000, "network_out_bytes": 250000,
            "connections_count": 500, "memory_available_gb": 0.1,
            "disk_free_gb": 0.5, "error_count": 50, "warning_count": 100,
            "critical_count": 10, "service_failures": 5, "auth_failures": 20, "ssh_attempts": 15
        })
    ]
    
    cycle = 0
    try:
        while True:
            cycle += 1
            for name, metrics in scenarios:
                timestamp = datetime.now().strftime("%H:%M:%S")
                success, risk = send_scenario(name, metrics)
                
                if success:
                    color = RED if risk > 70 else YELLOW if risk > 50 else GREEN
                    print(f"[{timestamp}] {BOLD}{name:12}{RESET} → Risk: {color}{risk:6.2f}%{RESET} (Cycle {cycle})")
                else:
                    print(f"[{timestamp}] {BOLD}{name:12}{RESET} → {RED}Failed{RESET}")
                
                time.sleep(8)  # Wait 8 seconds between scenarios
                
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Demo stopped{RESET}")

if __name__ == "__main__":
    main()

