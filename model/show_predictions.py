#!/usr/bin/env python3
"""
Show Current Predictive Maintenance Predictions

This script displays the current predictions from the dashboard
and tests different scenarios to show how predictions change.
"""

import requests
import json
import time
import sys
from datetime import datetime

DASHBOARD_URL = "http://localhost:5001"

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(text):
    print(f"\n{BOLD}{CYAN}{'='*70}{RESET}")
    print(f"{BOLD}{CYAN}{text.center(70)}{RESET}")
    print(f"{BOLD}{CYAN}{'='*70}{RESET}\n")

def get_current_predictions():
    """Get current predictions from dashboard"""
    try:
        print(f"{BLUE}Fetching predictions from dashboard...{RESET}")
        
        risk = requests.get(f"{DASHBOARD_URL}/api/predict-failure-risk", timeout=10).json()
        time_to_failure = requests.get(f"{DASHBOARD_URL}/api/predict-time-to-failure", timeout=10).json()
        warnings = requests.get(f"{DASHBOARD_URL}/api/get-early-warnings", timeout=10).json()
        
        return {
            'risk': risk,
            'time': time_to_failure,
            'warnings': warnings
        }
    except Exception as e:
        print(f"{RED}Error: {e}{RESET}")
        return None

def test_scenario(name, metrics):
    """Test a scenario and show prediction"""
    try:
        print(f"\n{BOLD}Testing: {name}{RESET}")
        print(f"Metrics: CPU={metrics['cpu_percent']}%, Memory={metrics['memory_percent']}%, Disk={metrics['disk_percent']}%")
        
        response = requests.post(
            f"{DASHBOARD_URL}/api/predict-anomaly",
            json={"metrics": metrics},
            timeout=10
        )
        
        if response.ok:
            data = response.json()
            risk_score = data.get('anomaly_score', 0) * 100
            is_anomaly = data.get('is_anomaly', False)
            
            if risk_score > 70:
                color = RED
                status = "HIGH RISK"
            elif risk_score > 50:
                color = YELLOW
                status = "MEDIUM RISK"
            else:
                color = GREEN
                status = "LOW RISK"
            
            print(f"  {color}Risk Score: {risk_score:.2f}% ({status}){RESET}")
            print(f"  Anomaly Detected: {'Yes' if is_anomaly else 'No'}")
            if 'risk_level' in data:
                print(f"  Risk Level: {data['risk_level']}")
            return True
        else:
            print(f"  {RED}Failed: Status {response.status_code}{RESET}")
            return False
    except Exception as e:
        print(f"  {RED}Error: {e}{RESET}")
        return False

def display_current_predictions(predictions):
    """Display current predictions"""
    print_header("Current System Predictions")
    
    # Risk Score
    risk_data = predictions.get('risk', {})
    if 'error' in risk_data:
        print(f"{RED}❌ Risk Score: {risk_data.get('error', 'Error')}{RESET}")
    else:
        risk_score = risk_data.get('risk_score', 0) * 100
        risk_level = risk_data.get('risk_level', 'Unknown')
        color = RED if risk_score > 70 else YELLOW if risk_score > 50 else GREEN
        print(f"{color}🔮 Failure Risk Score: {risk_score:.2f}% ({risk_level}){RESET}")
        print(f"   Early Warning: {'Yes' if risk_data.get('has_early_warning') else 'No'}")
        print(f"   High Risk: {'Yes' if risk_data.get('is_high_risk') else 'No'}")
    
    # Time to Failure
    time_data = predictions.get('time', {})
    if 'error' in time_data:
        print(f"{YELLOW}⏱️  Time to Failure: {time_data.get('message', 'N/A')}{RESET}")
    elif time_data.get('hours_until_failure'):
        hours = time_data['hours_until_failure']
        print(f"{YELLOW}⏱️  Time to Failure: {hours:.2f} hours{RESET}")
    else:
        print(f"{GREEN}✅ No failure predicted{RESET}")
    
    # Warnings
    warnings_data = predictions.get('warnings', {})
    warning_count = warnings_data.get('warning_count', 0)
    if warning_count > 0:
        print(f"{RED}⚠️  Active Warnings: {warning_count}{RESET}")
        for warning in warnings_data.get('warnings', [])[:5]:
            print(f"   • {warning.get('message', 'No message')}")
    else:
        print(f"{GREEN}✅ No active warnings{RESET}")
    
    print()

def main():
    print_header("Predictive Maintenance - Current Predictions")
    
    # Check dashboard
    try:
        health = requests.get(f"{DASHBOARD_URL}/api/health", timeout=10)
        if health.status_code != 200:
            print(f"{RED}Dashboard not responding{RESET}")
            return
        print(f"{GREEN}✅ Dashboard is accessible{RESET}\n")
    except Exception as e:
        print(f"{RED}❌ Cannot connect to dashboard: {e}{RESET}")
        print(f"{YELLOW}Please start the dashboard first{RESET}")
        return
    
    # Get current predictions
    predictions = get_current_predictions()
    if predictions:
        display_current_predictions(predictions)
    
    # Test scenarios
    print_header("Testing Different Scenarios")
    
    scenarios = [
        ("Normal Operation", {
            "cpu_percent": 30.0, "memory_percent": 40.0, "disk_percent": 50.0,
            "network_in_bytes": 100000, "network_out_bytes": 50000,
            "connections_count": 50, "memory_available_gb": 8.0,
            "disk_free_gb": 50.0, "error_count": 0, "warning_count": 1,
            "critical_count": 0, "service_failures": 0, "auth_failures": 0, "ssh_attempts": 0
        }),
        ("High CPU Load", {
            "cpu_percent": 95.0, "memory_percent": 60.0, "disk_percent": 50.0,
            "network_in_bytes": 200000, "network_out_bytes": 100000,
            "connections_count": 200, "memory_available_gb": 4.0,
            "disk_free_gb": 50.0, "error_count": 5, "warning_count": 10,
            "critical_count": 1, "service_failures": 0, "auth_failures": 0, "ssh_attempts": 0
        }),
        ("Memory Pressure", {
            "cpu_percent": 50.0, "memory_percent": 92.0, "disk_percent": 60.0,
            "network_in_bytes": 150000, "network_out_bytes": 75000,
            "connections_count": 150, "memory_available_gb": 0.5,
            "disk_free_gb": 50.0, "error_count": 3, "warning_count": 8,
            "critical_count": 0, "service_failures": 1, "auth_failures": 0, "ssh_attempts": 0
        }),
        ("Critical Failure", {
            "cpu_percent": 98.0, "memory_percent": 96.0, "disk_percent": 95.0,
            "network_in_bytes": 500000, "network_out_bytes": 250000,
            "connections_count": 500, "memory_available_gb": 0.1,
            "disk_free_gb": 0.5, "error_count": 50, "warning_count": 100,
            "critical_count": 10, "service_failures": 5, "auth_failures": 20, "ssh_attempts": 15
        })
    ]
    
    results = []
    for name, metrics in scenarios:
        result = test_scenario(name, metrics)
        results.append((name, result))
        time.sleep(1)
    
    # Summary
    print_header("Test Summary")
    passed = sum(1 for _, r in results if r)
    for name, result in results:
        status = f"{GREEN}✅ PASS{RESET}" if result else f"{RED}❌ FAIL{RESET}"
        print(f"  {status} - {name}")
    
    print(f"\n{BOLD}Results: {passed}/{len(results)} scenarios tested successfully{RESET}")
    print(f"\n{GREEN}💡 Open dashboard at http://localhost:5001 → Predictive Maintenance tab{RESET}")
    print(f"{CYAN}   The dashboard will show real-time predictions based on current system metrics{RESET}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Interrupted{RESET}")
        sys.exit(0)

