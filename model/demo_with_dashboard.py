#!/usr/bin/env python3
"""
Predictive Maintenance Dashboard Demo Script

This script sends test scenarios to the dashboard API and shows
how predictions update in real-time. Run this while watching the dashboard.

Usage:
    python3 demo_with_dashboard.py
    
Then open http://localhost:5001 → Predictive Maintenance tab
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
MAGENTA = '\033[95m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(text):
    print(f"\n{BOLD}{CYAN}{'='*70}{RESET}")
    print(f"{BOLD}{CYAN}{text.center(70)}{RESET}")
    print(f"{BOLD}{CYAN}{'='*70}{RESET}\n")

def send_scenario_and_get_risk(name, metrics):
    """Send scenario and get risk prediction"""
    try:
        # Send to predict-anomaly endpoint
        response = requests.post(
            f"{DASHBOARD_URL}/api/predict-anomaly",
            json={"metrics": metrics},
            timeout=10
        )
        
        if response.ok:
            data = response.json()
            anomaly_score = data.get('anomaly_score', 0) * 100
            is_anomaly = data.get('is_anomaly', False)
            
            # Also get risk from custom endpoint
            risk_response = requests.post(
                f"{DASHBOARD_URL}/api/predict-failure-risk-custom",
                json={"metrics": metrics},
                timeout=10
            )
            
            risk_score = None
            if risk_response.ok:
                risk_data = risk_response.json()
                if 'error' not in risk_data:
                    risk_score = risk_data.get('risk_score', 0) * 100
            
            return True, anomaly_score, risk_score, is_anomaly
        return False, 0, None, False
    except Exception as e:
        return False, 0, None, False

def main():
    print_header("Predictive Maintenance Dashboard Demo")
    
    # Check dashboard
    try:
        requests.get(f"{DASHBOARD_URL}/api/health", timeout=5)
        print(f"{GREEN}✅ Dashboard is accessible{RESET}\n")
    except:
        print(f"{RED}❌ Dashboard not accessible. Please start it first.{RESET}")
        return
    
    print(f"{YELLOW}🌐 Open: http://localhost:5001 → Predictive Maintenance tab{RESET}")
    print(f"{CYAN}👀 Watch the predictions update in real-time!{RESET}\n")
    print(f"{YELLOW}💡 The dashboard auto-refreshes every 30 seconds{RESET}")
    print(f"{YELLOW}💡 Click the Refresh button for immediate updates{RESET}\n")
    
    input(f"{BOLD}Press Enter when dashboard is open...{RESET}\n")
    
    scenarios = [
        ("1. Normal Operation", {
            "cpu_percent": 30.0, "memory_percent": 40.0, "disk_percent": 50.0,
            "network_in_bytes": 100000, "network_out_bytes": 50000,
            "connections_count": 50, "memory_available_gb": 8.0,
            "disk_free_gb": 50.0, "error_count": 0, "warning_count": 1,
            "critical_count": 0, "service_failures": 0, "auth_failures": 0, "ssh_attempts": 0
        }, 10),
        
        ("2. Moderate Load (CPU: 60%)", {
            "cpu_percent": 60.0, "memory_percent": 65.0, "disk_percent": 55.0,
            "network_in_bytes": 200000, "network_out_bytes": 100000,
            "connections_count": 150, "memory_available_gb": 5.0,
            "disk_free_gb": 45.0, "error_count": 2, "warning_count": 5,
            "critical_count": 0, "service_failures": 0, "auth_failures": 0, "ssh_attempts": 0
        }, 10),
        
        ("3. High Load (CPU: 85%)", {
            "cpu_percent": 85.0, "memory_percent": 88.0, "disk_percent": 75.0,
            "network_in_bytes": 400000, "network_out_bytes": 200000,
            "connections_count": 300, "memory_available_gb": 1.5,
            "disk_free_gb": 30.0, "error_count": 10, "warning_count": 20,
            "critical_count": 2, "service_failures": 1, "auth_failures": 5, "ssh_attempts": 3
        }, 12),
        
        ("4. Critical Failure (CPU: 98%)", {
            "cpu_percent": 98.0, "memory_percent": 96.0, "disk_percent": 95.0,
            "network_in_bytes": 500000, "network_out_bytes": 250000,
            "connections_count": 500, "memory_available_gb": 0.1,
            "disk_free_gb": 0.5, "error_count": 50, "warning_count": 100,
            "critical_count": 10, "service_failures": 5, "auth_failures": 20, "ssh_attempts": 15
        }, 15),
        
        ("5. System Recovery", {
            "cpu_percent": 25.0, "memory_percent": 35.0, "disk_percent": 45.0,
            "network_in_bytes": 80000, "network_out_bytes": 40000,
            "connections_count": 40, "memory_available_gb": 10.0,
            "disk_free_gb": 60.0, "error_count": 0, "warning_count": 0,
            "critical_count": 0, "service_failures": 0, "auth_failures": 0, "ssh_attempts": 0
        }, 10)
    ]
    
    print_header("Starting Demo Scenarios")
    
    for name, metrics, duration in scenarios:
        print(f"\n{BOLD}{'='*70}{RESET}")
        print(f"{BOLD}{name}{RESET}")
        print(f"{BOLD}{'='*70}{RESET}\n")
        
        print(f"{CYAN}Sending scenario to dashboard...{RESET}")
        success, anomaly_score, risk_score, is_anomaly = send_scenario_and_get_risk(name, metrics)
        
        if success:
            if risk_score is not None:
                color = RED if risk_score > 70 else YELLOW if risk_score > 50 else GREEN
                print(f"{GREEN}✅ Scenario sent successfully{RESET}")
                print(f"   {BOLD}Risk Score:{RESET} {color}{risk_score:.2f}%{RESET}")
                print(f"   {BOLD}Anomaly Score:{RESET} {anomaly_score:.2f}%")
                print(f"   {BOLD}Anomaly Detected:{RESET} {'Yes' if is_anomaly else 'No'}")
            else:
                print(f"{GREEN}✅ Scenario sent successfully{RESET}")
                print(f"   {BOLD}Anomaly Score:{RESET} {anomaly_score:.2f}%")
        else:
            print(f"{RED}❌ Failed to send scenario{RESET}")
        
        print(f"\n{YELLOW}⏱️  Running for {duration} seconds...{RESET}")
        print(f"{MAGENTA}💡 Check your dashboard - predictions should update!{RESET}")
        print(f"{CYAN}   (Dashboard auto-refreshes every 30 seconds){RESET}\n")
        
        # Show progress
        for i in range(duration):
            time.sleep(1)
            if (i + 1) % 3 == 0:
                # Get current predictions
                try:
                    current_risk = requests.get(f"{DASHBOARD_URL}/api/predict-failure-risk", timeout=5)
                    if current_risk.ok:
                        data = current_risk.json()
                        if 'error' not in data:
                            risk = data.get('risk_score', 0) * 100
                            color = RED if risk > 70 else YELLOW if risk > 50 else GREEN
                            print(f"   [{i+1}s] Dashboard Risk: {color}{risk:.2f}%{RESET}", end='\r')
                except:
                    pass
        
        print()  # New line
        time.sleep(2)
    
    print_header("Demo Complete")
    print(f"{GREEN}✅ All scenarios completed!{RESET}\n")
    print(f"{CYAN}📊 Check your dashboard to see the final predictions{RESET}")
    print(f"{YELLOW}💡 The dashboard continues to update every 30 seconds{RESET}\n")
    print(f"{BOLD}{GREEN}🎉 Predictive Maintenance Demo Complete!{RESET}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Demo interrupted{RESET}")
        sys.exit(0)

