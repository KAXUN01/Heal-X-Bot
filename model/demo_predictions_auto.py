#!/usr/bin/env python3
"""
Predictive Maintenance Auto Demo Script

This script automatically simulates different system conditions
and shows predictions without requiring user input.
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, Any

# Configuration
DASHBOARD_URL = "http://localhost:5001"
UPDATE_INTERVAL = 2  # seconds between updates

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(text: str):
    """Print formatted header"""
    print(f"\n{BOLD}{CYAN}{'='*70}{RESET}")
    print(f"{BOLD}{CYAN}{text.center(70)}{RESET}")
    print(f"{BOLD}{CYAN}{'='*70}{RESET}\n")

def print_status(message: str, color=BLUE):
    """Print status message"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{color}[{timestamp}]{RESET} {message}")

def get_predictions() -> Dict[str, Any]:
    """Get current predictions from dashboard"""
    try:
        risk_response = requests.get(f"{DASHBOARD_URL}/api/predict-failure-risk", timeout=5)
        time_response = requests.get(f"{DASHBOARD_URL}/api/predict-time-to-failure", timeout=5)
        warnings_response = requests.get(f"{DASHBOARD_URL}/api/get-early-warnings", timeout=5)
        
        return {
            'risk': risk_response.json() if risk_response.ok else None,
            'time': time_response.json() if time_response.ok else None,
            'warnings': warnings_response.json() if warnings_response.ok else None
        }
    except Exception as e:
        return None

def send_custom_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Send custom metrics for prediction"""
    try:
        response = requests.post(
            f"{DASHBOARD_URL}/api/predict-anomaly",
            json={"metrics": metrics},
            timeout=5
        )
        if response.ok:
            return response.json()
        return None
    except:
        return None

def display_predictions(predictions: Dict[str, Any], scenario_name: str = "Current System"):
    """Display predictions in a formatted way"""
    print(f"\n{BOLD}{scenario_name}{RESET}")
    print("-" * 70)
    
    # Risk Score
    if predictions.get('risk'):
        risk_data = predictions['risk']
        if 'error' in risk_data:
            print(f"  {RED}❌ Risk Score: Error - {risk_data.get('error', 'Unknown')}{RESET}")
        else:
            risk_score = risk_data.get('risk_score', 0) * 100
            risk_level = risk_data.get('risk_level', 'Unknown')
            
            # Color based on risk
            if risk_score > 70:
                color = RED
                icon = "🔴"
            elif risk_score > 50:
                color = YELLOW
                icon = "🟡"
            elif risk_score > 30:
                color = YELLOW
                icon = "🟠"
            else:
                color = GREEN
                icon = "🟢"
            
            print(f"  {icon} {BOLD}Failure Risk Score:{RESET} {color}{risk_score:.2f}%{RESET} ({risk_level})")
            print(f"     Early Warning: {'Yes' if risk_data.get('has_early_warning') else 'No'}")
            print(f"     High Risk: {'Yes' if risk_data.get('is_high_risk') else 'No'}")
    
    # Time to Failure
    if predictions.get('time'):
        time_data = predictions['time']
        if 'error' in time_data:
            print(f"  {YELLOW}⏱️  Time to Failure: {time_data.get('message', 'N/A')}{RESET}")
        elif time_data.get('hours_until_failure'):
            hours = time_data['hours_until_failure']
            print(f"  {YELLOW}⏱️  Time to Failure: {hours:.2f} hours{RESET}")
        else:
            print(f"  {GREEN}✅ No failure predicted in near future{RESET}")
    
    # Warnings
    if predictions.get('warnings'):
        warnings_data = predictions['warnings']
        warning_count = warnings_data.get('warning_count', 0)
        if warning_count > 0:
            print(f"  {RED}⚠️  Active Warnings: {warning_count}{RESET}")
            for warning in warnings_data.get('warnings', [])[:3]:
                severity = warning.get('severity', 'unknown')
                message = warning.get('message', 'No message')
                severity_color = RED if severity == 'high' else YELLOW
                print(f"     {severity_color}[{severity.upper()}]{RESET} {message}")
        else:
            print(f"  {GREEN}✅ No active warnings{RESET}")
    
    print()

def simulate_scenario(name: str, metrics: Dict[str, Any], duration: int = 5):
    """Simulate a scenario and show predictions"""
    print_status(f"📊 Scenario: {name}", CYAN)
    
    # Send metrics
    result = send_custom_metrics(metrics)
    if result:
        anomaly_score = result.get('anomaly_score', 0) * 100
        is_anomaly = result.get('is_anomaly', False)
        color = RED if is_anomaly else GREEN
        print_status(f"   Anomaly Score: {anomaly_score:.2f}% ({'Anomaly Detected' if is_anomaly else 'Normal'})", color)
    
    # Wait for dashboard to update
    time.sleep(2)
    
    # Get and display predictions
    predictions = get_predictions()
    if predictions:
        display_predictions(predictions, name)
    
    # Show updates
    print_status(f"   Monitoring for {duration} seconds...", YELLOW)
    for i in range(duration):
        time.sleep(1)
        if (i + 1) % 2 == 0:
            predictions = get_predictions()
            if predictions and predictions.get('risk'):
                risk_score = predictions['risk'].get('risk_score', 0) * 100
                print(f"   [{i+1}s] Risk: {risk_score:.2f}%", end='\r')
    
    print()  # New line

def main():
    """Main demo function"""
    print_header("Predictive Maintenance Auto Demo")
    
    # Check dashboard availability
    print_status("Checking dashboard...", BLUE)
    try:
        response = requests.get(f"{DASHBOARD_URL}/api/health", timeout=5)
        if response.status_code != 200:
            print_status(f"❌ Dashboard returned status {response.status_code}", RED)
            return
        print_status("✅ Dashboard is accessible", GREEN)
    except requests.exceptions.ConnectionError:
        print_status(f"❌ Cannot connect to dashboard at {DASHBOARD_URL}", RED)
        print_status("Please start the dashboard first:", YELLOW)
        print_status("cd monitoring/server && python3 -m uvicorn healing_dashboard_api:app --host 0.0.0.0 --port 5001", CYAN)
        return
    except Exception as e:
        print_status(f"❌ Error: {e}", RED)
        return
    
    print_status("🌐 Open dashboard: http://localhost:5001 → Predictive Maintenance tab", YELLOW)
    print_status("Starting automatic demo scenarios...", GREEN)
    time.sleep(2)
    
    # Scenario 1: Normal Operation
    simulate_scenario(
        "1. Normal Operation",
        {
            "cpu_percent": 30.0,
            "memory_percent": 40.0,
            "disk_percent": 50.0,
            "network_in_bytes": 100000,
            "network_out_bytes": 50000,
            "connections_count": 50,
            "memory_available_gb": 8.0,
            "disk_free_gb": 50.0,
            "error_count": 0,
            "warning_count": 1,
            "critical_count": 0,
            "service_failures": 0,
            "auth_failures": 0,
            "ssh_attempts": 0
        },
        duration=5
    )
    
    time.sleep(1)
    
    # Scenario 2: Moderate Load
    simulate_scenario(
        "2. Moderate Load (CPU: 60%)",
        {
            "cpu_percent": 60.0,
            "memory_percent": 65.0,
            "disk_percent": 55.0,
            "network_in_bytes": 200000,
            "network_out_bytes": 100000,
            "connections_count": 150,
            "memory_available_gb": 5.0,
            "disk_free_gb": 45.0,
            "error_count": 2,
            "warning_count": 5,
            "critical_count": 0,
            "service_failures": 0,
            "auth_failures": 0,
            "ssh_attempts": 0
        },
        duration=5
    )
    
    time.sleep(1)
    
    # Scenario 3: High Load
    simulate_scenario(
        "3. High Load (CPU: 85%)",
        {
            "cpu_percent": 85.0,
            "memory_percent": 88.0,
            "disk_percent": 75.0,
            "network_in_bytes": 400000,
            "network_out_bytes": 200000,
            "connections_count": 300,
            "memory_available_gb": 1.5,
            "disk_free_gb": 30.0,
            "error_count": 10,
            "warning_count": 20,
            "critical_count": 2,
            "service_failures": 1,
            "auth_failures": 5,
            "ssh_attempts": 3
        },
        duration=5
    )
    
    time.sleep(1)
    
    # Scenario 4: Critical Failure Indicators
    simulate_scenario(
        "4. Critical Failure Indicators (CPU: 98%)",
        {
            "cpu_percent": 98.0,
            "memory_percent": 96.0,
            "disk_percent": 95.0,
            "network_in_bytes": 500000,
            "network_out_bytes": 250000,
            "connections_count": 500,
            "memory_available_gb": 0.1,
            "disk_free_gb": 0.5,
            "error_count": 50,
            "warning_count": 100,
            "critical_count": 10,
            "service_failures": 5,
            "auth_failures": 20,
            "ssh_attempts": 15
        },
        duration=8
    )
    
    time.sleep(1)
    
    # Scenario 5: Recovery
    simulate_scenario(
        "5. System Recovery (Normal)",
        {
            "cpu_percent": 25.0,
            "memory_percent": 35.0,
            "disk_percent": 45.0,
            "network_in_bytes": 80000,
            "network_out_bytes": 40000,
            "connections_count": 40,
            "memory_available_gb": 10.0,
            "disk_free_gb": 60.0,
            "error_count": 0,
            "warning_count": 0,
            "critical_count": 0,
            "service_failures": 0,
            "auth_failures": 0,
            "ssh_attempts": 0
        },
        duration=5
    )
    
    # Final summary
    print_header("Demo Complete")
    print_status("✅ All scenarios completed!", GREEN)
    print_status("📊 Check your dashboard to see the predictions", CYAN)
    print_status("The dashboard should show:", YELLOW)
    print("  • Risk scores changing from low → high → low")
    print("  • Early warnings appearing during high load")
    print("  • Anomaly detection working correctly")
    print("  • Real-time updates every 30 seconds")
    
    print(f"\n{BOLD}{GREEN}🎉 Predictive Maintenance System Demo Complete!{RESET}\n")
    print_status("💡 Tip: Keep the dashboard open to see continuous updates", CYAN)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Demo interrupted by user{RESET}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{RED}Error: {e}{RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

