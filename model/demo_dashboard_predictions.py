#!/usr/bin/env python3
"""
Dashboard Predictive Maintenance Demo Script

This script continuously sends different system scenarios to the dashboard
so you can see the predictions update in real-time on the dashboard.

Usage:
    python3 demo_dashboard_predictions.py
    
Then open http://localhost:5001 → Predictive Maintenance tab
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, Any

DASHBOARD_URL = "http://localhost:5001"

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
MAGENTA = '\033[95m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(text: str):
    print(f"\n{BOLD}{CYAN}{'='*70}{RESET}")
    print(f"{BOLD}{CYAN}{text.center(70)}{RESET}")
    print(f"{BOLD}{CYAN}{'='*70}{RESET}\n")

def print_status(message: str, color=BLUE):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{color}[{timestamp}]{RESET} {message}")

def send_metrics(metrics: Dict[str, Any]) -> bool:
    """Send metrics to dashboard for prediction"""
    try:
        response = requests.post(
            f"{DASHBOARD_URL}/api/predict-anomaly",
            json={"metrics": metrics},
            timeout=10
        )
        if response.ok:
            data = response.json()
            risk_score = data.get('anomaly_score', 0) * 100
            return True
        return False
    except Exception as e:
        print_status(f"Error: {e}", RED)
        return False

def get_current_predictions():
    """Get current predictions to display"""
    try:
        risk = requests.get(f"{DASHBOARD_URL}/api/predict-failure-risk", timeout=10)
        if risk.ok:
            data = risk.json()
            if 'error' not in data:
                return data.get('risk_score', 0) * 100
        return None
    except:
        return None

def run_scenario(name: str, metrics: Dict[str, Any], duration: int = 10):
    """Run a scenario for specified duration"""
    print_status(f"📊 Running: {name}", CYAN)
    
    # Send metrics
    if send_metrics(metrics):
        print_status(f"   ✅ Metrics sent successfully", GREEN)
    else:
        print_status(f"   ❌ Failed to send metrics", RED)
        return
    
    # Wait for dashboard to process
    time.sleep(2)
    
    # Show updates
    print_status(f"   ⏱️  Running for {duration} seconds...", YELLOW)
    print_status(f"   💡 Check dashboard: http://localhost:5001 → Predictive Maintenance tab", MAGENTA)
    
    for i in range(duration):
        time.sleep(1)
        if (i + 1) % 3 == 0:
            risk = get_current_predictions()
            if risk is not None:
                color = RED if risk > 70 else YELLOW if risk > 50 else GREEN
                print(f"   [{i+1}s] Current Risk: {color}{risk:.2f}%{RESET}", end='\r')
    
    print()  # New line

def main():
    """Main demo function"""
    print_header("Dashboard Predictive Maintenance Demo")
    
    # Check dashboard
    print_status("Checking dashboard availability...", BLUE)
    try:
        response = requests.get(f"{DASHBOARD_URL}/api/health", timeout=10)
        if response.status_code != 200:
            print_status(f"❌ Dashboard returned status {response.status_code}", RED)
            return
        print_status("✅ Dashboard is accessible", GREEN)
    except requests.exceptions.ConnectionError:
        print_status(f"❌ Cannot connect to dashboard at {DASHBOARD_URL}", RED)
        print_status("Please start the dashboard:", YELLOW)
        print_status("cd monitoring/server && python3 -m uvicorn healing_dashboard_api:app --host 0.0.0.0 --port 5001", CYAN)
        return
    except Exception as e:
        print_status(f"❌ Error: {e}", RED)
        return
    
    print_status("🌐 Open dashboard: http://localhost:5001", YELLOW)
    print_status("📋 Navigate to: Predictive Maintenance tab", YELLOW)
    print_status("👀 Watch the predictions update in real-time!", CYAN)
    
    input(f"\n{BOLD}Press Enter when dashboard is open and ready...{RESET}\n")
    
    scenarios = [
        ("Normal Operation", {
            "cpu_percent": 30.0, "memory_percent": 40.0, "disk_percent": 50.0,
            "network_in_bytes": 100000, "network_out_bytes": 50000,
            "connections_count": 50, "memory_available_gb": 8.0,
            "disk_free_gb": 50.0, "error_count": 0, "warning_count": 1,
            "critical_count": 0, "service_failures": 0, "auth_failures": 0, "ssh_attempts": 0
        }, 8),
        
        ("Moderate Load (CPU: 60%)", {
            "cpu_percent": 60.0, "memory_percent": 65.0, "disk_percent": 55.0,
            "network_in_bytes": 200000, "network_out_bytes": 100000,
            "connections_count": 150, "memory_available_gb": 5.0,
            "disk_free_gb": 45.0, "error_count": 2, "warning_count": 5,
            "critical_count": 0, "service_failures": 0, "auth_failures": 0, "ssh_attempts": 0
        }, 8),
        
        ("High Load (CPU: 80%)", {
            "cpu_percent": 80.0, "memory_percent": 85.0, "disk_percent": 70.0,
            "network_in_bytes": 350000, "network_out_bytes": 175000,
            "connections_count": 250, "memory_available_gb": 2.0,
            "disk_free_gb": 35.0, "error_count": 8, "warning_count": 15,
            "critical_count": 1, "service_failures": 1, "auth_failures": 3, "ssh_attempts": 2
        }, 8),
        
        ("Critical Load (CPU: 95%)", {
            "cpu_percent": 95.0, "memory_percent": 94.0, "disk_percent": 90.0,
            "network_in_bytes": 500000, "network_out_bytes": 250000,
            "connections_count": 450, "memory_available_gb": 0.2,
            "disk_free_gb": 1.0, "error_count": 40, "warning_count": 80,
            "critical_count": 8, "service_failures": 4, "auth_failures": 15, "ssh_attempts": 10
        }, 12),
        
        ("System Recovery", {
            "cpu_percent": 25.0, "memory_percent": 35.0, "disk_percent": 45.0,
            "network_in_bytes": 80000, "network_out_bytes": 40000,
            "connections_count": 40, "memory_available_gb": 10.0,
            "disk_free_gb": 60.0, "error_count": 0, "warning_count": 0,
            "critical_count": 0, "service_failures": 0, "auth_failures": 0, "ssh_attempts": 0
        }, 8)
    ]
    
    print_header("Starting Demo Scenarios")
    print_status("The dashboard will update automatically every 30 seconds", CYAN)
    print_status("You should see risk scores changing in real-time!", GREEN)
    print()
    
    for i, (name, metrics, duration) in enumerate(scenarios, 1):
        print(f"\n{BOLD}{'='*70}{RESET}")
        print(f"{BOLD}Scenario {i}/{len(scenarios)}: {name}{RESET}")
        print(f"{BOLD}{'='*70}{RESET}\n")
        
        run_scenario(name, metrics, duration)
        
        if i < len(scenarios):
            time.sleep(2)
    
    print_header("Demo Complete")
    print_status("✅ All scenarios completed!", GREEN)
    print_status("📊 Check your dashboard to see the final predictions", CYAN)
    print_status("💡 The dashboard continues to update every 30 seconds", YELLOW)
    print(f"\n{BOLD}{GREEN}🎉 Predictive Maintenance Demo Complete!{RESET}\n")

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

