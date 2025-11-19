#!/usr/bin/env python3
"""
Demo script that sends metrics and triggers dashboard updates

This script sends test scenarios to the dashboard API, and when
demo mode is enabled in the dashboard, it will show the predictions.
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
        # Send to both endpoints
        response1 = requests.post(
            f"{DASHBOARD_URL}/api/predict-anomaly",
            json={"metrics": metrics},
            timeout=10
        )
        response2 = requests.post(
            f"{DASHBOARD_URL}/api/predict-failure-risk-custom",
            json={"metrics": metrics},
            timeout=10
        )
        
        if response2.ok:
            data = response2.json()
            if 'error' not in data:
                risk = data.get('risk_score', 0) * 100
                return True, risk
        return False, 0
    except Exception as e:
        print(f"  {RED}Error: {e}{RESET}")
        return False, 0

def main():
    print(f"{BOLD}{CYAN}{'='*70}{RESET}")
    print(f"{BOLD}{CYAN}Predictive Maintenance Dashboard Demo{RESET}")
    print(f"{BOLD}{CYAN}{'='*70}{RESET}\n")
    
    # Check dashboard
    try:
        requests.get(f"{DASHBOARD_URL}/api/health", timeout=5)
        print(f"{GREEN}✅ Dashboard is accessible{RESET}\n")
    except:
        print(f"{RED}❌ Dashboard not accessible. Please start it first.{RESET}")
        return
    
    print(f"{YELLOW}📋 Instructions:{RESET}")
    print(f"  1. Open: http://localhost:5001")
    print(f"  2. Go to: Predictive Maintenance tab")
    print(f"  3. {BOLD}Enable 'Demo Mode' checkbox{RESET} (top right)")
    print(f"  4. Watch predictions update in real-time!\n")
    
    input(f"{BOLD}Press Enter when demo mode is enabled in dashboard...{RESET}\n")
    
    scenarios = [
        ("Normal Operation", {
            "cpu_percent": 30.0, "memory_percent": 40.0, "disk_percent": 50.0,
            "network_in_bytes": 100000, "network_out_bytes": 50000,
            "connections_count": 50, "memory_available_gb": 8.0,
            "disk_free_gb": 50.0, "error_count": 0, "warning_count": 1,
            "critical_count": 0, "service_failures": 0, "auth_failures": 0, "ssh_attempts": 0
        }, 8),
        ("Moderate Load", {
            "cpu_percent": 60.0, "memory_percent": 65.0, "disk_percent": 55.0,
            "network_in_bytes": 200000, "network_out_bytes": 100000,
            "connections_count": 150, "memory_available_gb": 5.0,
            "disk_free_gb": 45.0, "error_count": 2, "warning_count": 5,
            "critical_count": 0, "service_failures": 0, "auth_failures": 0, "ssh_attempts": 0
        }, 8),
        ("High Load", {
            "cpu_percent": 85.0, "memory_percent": 88.0, "disk_percent": 75.0,
            "network_in_bytes": 400000, "network_out_bytes": 200000,
            "connections_count": 300, "memory_available_gb": 1.5,
            "disk_free_gb": 30.0, "error_count": 10, "warning_count": 20,
            "critical_count": 2, "service_failures": 1, "auth_failures": 5, "ssh_attempts": 3
        }, 10),
        ("Critical Failure", {
            "cpu_percent": 98.0, "memory_percent": 96.0, "disk_percent": 95.0,
            "network_in_bytes": 500000, "network_out_bytes": 250000,
            "connections_count": 500, "memory_available_gb": 0.1,
            "disk_free_gb": 0.5, "error_count": 50, "warning_count": 100,
            "critical_count": 10, "service_failures": 5, "auth_failures": 20, "ssh_attempts": 15
        }, 12),
        ("System Recovery", {
            "cpu_percent": 25.0, "memory_percent": 35.0, "disk_percent": 45.0,
            "network_in_bytes": 80000, "network_out_bytes": 40000,
            "connections_count": 40, "memory_available_gb": 10.0,
            "disk_free_gb": 60.0, "error_count": 0, "warning_count": 0,
            "critical_count": 0, "service_failures": 0, "auth_failures": 0, "ssh_attempts": 0
        }, 8)
    ]
    
    print(f"{BOLD}Starting scenarios...{RESET}\n")
    
    for name, metrics, duration in scenarios:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{CYAN}[{timestamp}] {BOLD}{name}{RESET}")
        
        success, risk = send_scenario(name, metrics)
        
        if success:
            color = RED if risk > 70 else YELLOW if risk > 50 else GREEN
            print(f"  {color}Risk Score: {risk:.2f}%{RESET}")
            print(f"  {YELLOW}⏱️  Running for {duration} seconds...{RESET}")
            print(f"  {BLUE}💡 Check dashboard - predictions should update!{RESET}\n")
        else:
            print(f"  {RED}❌ Failed to send scenario{RESET}\n")
        
        time.sleep(duration)
    
    print(f"\n{BOLD}{GREEN}✅ Demo complete!{RESET}\n")
    print(f"{CYAN}💡 You can disable demo mode to see real system metrics{RESET}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Demo interrupted{RESET}")
        sys.exit(0)

