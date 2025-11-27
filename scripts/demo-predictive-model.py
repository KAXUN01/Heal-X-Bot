#!/usr/bin/env python3
"""
Predictive Model Demo Script
Automated demonstration of predictive maintenance model capabilities.

This script runs through predefined scenarios (low, medium, high, extreme risk)
to demonstrate how the predictive model responds to different system conditions.

Usage:
    python scripts/demo-predictive-model.py                    # Auto-run all scenarios
    python scripts/demo-predictive-model.py --interactive      # Manual control
    python scripts/demo-predictive-model.py --loop             # Continuous loop
    python scripts/demo-predictive-model.py --scenario low     # Run specific scenario
"""

import sys
import os
import time
import json
import requests
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configuration
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://localhost:5001")
API_BASE = f"{DASHBOARD_URL}/api"

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Scenario Definitions
SCENARIOS = {
    "low": {
        "name": "Low Risk - Healthy System",
        "description": "System running normally with low resource usage",
        "metrics": {
            "cpu_percent": 15.5,
            "memory_percent": 35.2,
            "disk_percent": 42.8,
            "error_count": 0,
            "warning_count": 1,
            "service_failures": 0,
            "network_in_mbps": 5.2,
            "network_out_mbps": 3.1
        },
        "expected_risk": "Very Low",
        "color": Colors.OKGREEN
    },
    "medium": {
        "name": "Medium Risk - Elevated Load",
        "description": "System experiencing increased load, requires monitoring",
        "metrics": {
            "cpu_percent": 68.3,
            "memory_percent": 75.6,
            "disk_percent": 80.2,
            "error_count": 3,
            "warning_count": 8,
            "service_failures": 0,
            "network_in_mbps": 45.8,
            "network_out_mbps": 32.4
        },
        "expected_risk": "Low to Medium",
        "color": Colors.WARNING
    },
    "high": {
        "name": "High Risk - Critical Conditions",
        "description": "System under severe stress, failure likely without intervention",
        "metrics": {
            "cpu_percent": 89.7,
            "memory_percent": 92.3,
            "disk_percent": 93.5,
            "error_count": 15,
            "warning_count": 32,
            "service_failures": 2,
            "network_in_mbps": 128.5,
            "network_out_mbps": 95.3
        },
        "expected_risk": "High",
        "color": Colors.FAIL
    },
    "extreme": {
        "name": "Extreme Risk - Near Failure",
        "description": "System near failure point, immediate action required",
        "metrics": {
            "cpu_percent": 97.8,
            "memory_percent": 98.5,
            "disk_percent": 99.1,
            "error_count": 45,
            "warning_count": 89,
            "service_failures": 5,
            "network_in_mbps": 256.7,
            "network_out_mbps": 198.2
        },
        "expected_risk": "Critical",
        "color": Colors.FAIL
    }
}


def print_banner():
    """Print demo banner"""
    banner = f"""
{Colors.BOLD}{Colors.HEADER}╔══════════════════════════════════════════════════════════════╗
║         🔮 PREDICTIVE MODEL DEMO SCRIPT 🔮              ║
║                                                          ║
║    Automated Demonstration of Predictive Maintenance     ║
║                                                          ║
║  This script demonstrates how the predictive model       ║
║  responds to different system health scenarios.          ║
╚══════════════════════════════════════════════════════════════╝{Colors.ENDC}
"""
    print(banner)


def check_api_connection() -> bool:
    """Check if dashboard API is accessible (deprecated - use inline check in main)"""
    # This function is kept for backward compatibility but not used
    # Connection check is now done inline in main() with better error handling
    return True


def send_metrics_scenario(scenario_name: str, metrics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Send metrics to the dashboard API for prediction.
    
    Args:
        scenario_name: Name of the scenario
        metrics: Dictionary of system metrics
        
    Returns:
        Prediction response from API or None if failed
    """
    url = f"{API_BASE}/predict-failure-risk-custom"
    
    try:
        response = requests.post(
            url,
            json={"metrics": metrics},
            headers={"Content-Type": "application/json"},
            timeout=(3, 15)  # (connect timeout, read timeout) - allow longer for read
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"{Colors.FAIL}❌ API returned status {response.status_code}{Colors.ENDC}")
            return None
    except requests.exceptions.Timeout:
        print(f"{Colors.FAIL}❌ API request timed out (server may be slow){Colors.ENDC}")
        print(f"{Colors.WARNING}⚠️  Try refreshing the dashboard or check if the model is loading...{Colors.ENDC}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"{Colors.FAIL}❌ Failed to connect to API: {e}{Colors.ENDC}")
        return None


def get_time_to_failure(metrics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get time-to-failure prediction"""
    # First send metrics, then fetch prediction
    url = f"{API_BASE}/predict-failure-risk-custom"
    
    try:
        # Store metrics
        requests.post(url, json={"metrics": metrics}, timeout=2)
        time.sleep(0.5)
        
        # Get time-to-failure prediction
        response = requests.get(f"{API_BASE}/predict-time-to-failure", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException:
        return None


def get_early_warnings(metrics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get early warnings"""
    # First send metrics, then fetch warnings
    url = f"{API_BASE}/predict-failure-risk-custom"
    
    try:
        # Store metrics
        requests.post(url, json={"metrics": metrics}, timeout=2)
        time.sleep(0.5)
        
        # Get early warnings
        response = requests.get(f"{API_BASE}/get-early-warnings", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException:
        return None


def display_scenario_results(scenario_key: str, scenario: Dict[str, Any], 
                            risk_data: Dict[str, Any], 
                            time_data: Optional[Dict[str, Any]] = None,
                            warnings_data: Optional[Dict[str, Any]] = None):
    """Display formatted scenario results"""
    color = scenario["color"]
    
    print(f"\n{color}{'='*70}{Colors.ENDC}")
    print(f"{color}{Colors.BOLD}📊 Scenario: {scenario['name']}{Colors.ENDC}")
    print(f"{color}{scenario['description']}{Colors.ENDC}")
    print(f"{color}{'='*70}{Colors.ENDC}\n")
    
    # Display metrics
    print(f"{Colors.OKCYAN}📈 System Metrics:{Colors.ENDC}")
    metrics = scenario["metrics"]
    print(f"   CPU:      {metrics['cpu_percent']:6.1f}%")
    print(f"   Memory:   {metrics['memory_percent']:6.1f}%")
    print(f"   Disk:     {metrics['disk_percent']:6.1f}%")
    print(f"   Errors:   {metrics['error_count']:6d}")
    print(f"   Warnings: {metrics['warning_count']:6d}")
    print(f"   Failures: {metrics['service_failures']:6d}\n")
    
    # Display risk prediction
    if risk_data and not risk_data.get("error"):
        risk_score = risk_data.get("risk_score", 0)
        risk_percent = risk_data.get("risk_percentage", 0)
        risk_level = risk_data.get("risk_level", "Unknown")
        has_warning = risk_data.get("has_early_warning", False)
        is_high_risk = risk_data.get("is_high_risk", False)
        
        # Color code risk level
        if risk_percent > 70 or is_high_risk:
            risk_color = Colors.FAIL
        elif risk_percent > 30 or has_warning:
            risk_color = Colors.WARNING
        else:
            risk_color = Colors.OKGREEN
        
        print(f"{Colors.OKCYAN}🔮 Risk Prediction:{Colors.ENDC}")
        print(f"   Risk Score:    {risk_color}{risk_percent:6.2f}%{Colors.ENDC}")
        print(f"   Risk Level:    {risk_color}{risk_level}{Colors.ENDC}")
        print(f"   Early Warning: {'✅ Yes' if has_warning else '❌ No'}")
        print(f"   High Risk:     {'✅ Yes' if is_high_risk else '❌ No'}")
    else:
        error_msg = risk_data.get("error", "Unknown error") if risk_data else "No response"
        print(f"{Colors.FAIL}❌ Risk Prediction Error: {error_msg}{Colors.ENDC}")
    
    # Display time to failure
    if time_data:
        print(f"\n{Colors.OKCYAN}⏱️  Time to Failure:{Colors.ENDC}")
        if time_data.get("error"):
            print(f"   {Colors.WARNING}⚠️  {time_data.get('message', time_data.get('error', 'Unknown'))}{Colors.ENDC}")
        elif time_data.get("hours_until_failure") is not None:
            hours = time_data["hours_until_failure"]
            confidence = time_data.get("confidence", "Unknown")
            print(f"   Hours Until Failure: {Colors.WARNING}{hours:.1f}h{Colors.ENDC}")
            if time_data.get("predicted_failure_time"):
                failure_time = datetime.fromisoformat(time_data["predicted_failure_time"].replace('Z', '+00:00'))
                print(f"   Predicted Time:      {failure_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Confidence:          {confidence}")
        else:
            print(f"   {Colors.OKGREEN}✅ {time_data.get('message', 'No failure predicted in near future')}{Colors.ENDC}")
    
    # Display early warnings
    if warnings_data:
        print(f"\n{Colors.OKCYAN}⚠️  Early Warnings:{Colors.ENDC}")
        warning_count = warnings_data.get("warning_count", 0)
        warnings = warnings_data.get("warnings", [])
        
        if warning_count > 0:
            print(f"   Total Warnings: {Colors.WARNING}{warning_count}{Colors.ENDC}")
            for i, warning in enumerate(warnings[:5], 1):  # Show first 5
                severity = warning.get("severity", "unknown")
                msg = warning.get("message", "")
                severity_color = Colors.FAIL if severity == "high" else Colors.WARNING
                print(f"   {i}. [{severity_color}{severity.upper()}{Colors.ENDC}] {msg}")
            if len(warnings) > 5:
                print(f"   ... and {len(warnings) - 5} more warnings")
        else:
            print(f"   {Colors.OKGREEN}✅ No active warnings{Colors.ENDC}")
    
    print(f"\n{color}{'='*70}{Colors.ENDC}\n")


def run_scenario(scenario_key: str, scenario: Dict[str, Any], delay: float = 5.0) -> bool:
    """Run a single scenario and display results"""
    print(f"{Colors.OKBLUE}🚀 Running scenario: {scenario['name']}...{Colors.ENDC}")
    
    # Send metrics and get predictions
    risk_data = send_metrics_scenario(scenario_key, scenario["metrics"])
    
    if not risk_data:
        print(f"{Colors.FAIL}❌ Failed to get risk prediction{Colors.ENDC}")
        return False
    
    # Get additional predictions
    time_data = get_time_to_failure(scenario["metrics"])
    warnings_data = get_early_warnings(scenario["metrics"])
    
    # Display results
    display_scenario_results(scenario_key, scenario, risk_data, time_data, warnings_data)
    
    # Wait before next scenario
    if delay > 0:
        print(f"{Colors.OKCYAN}⏳ Waiting {delay} seconds before next scenario...{Colors.ENDC}\n")
        time.sleep(delay)
    
    return True


def run_demo_loop(scenario_order: List[str] = None, delay: float = 5.0, loop: bool = False):
    """Run all scenarios in sequence"""
    if scenario_order is None:
        scenario_order = ["low", "medium", "high", "extreme"]
    
    print(f"{Colors.BOLD}Starting automated demo...{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Dashboard URL: {DASHBOARD_URL}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Make sure Demo Mode is enabled in the dashboard!{Colors.ENDC}\n")
    time.sleep(2)
    
    iteration = 0
    while True:
        iteration += 1
        if iteration > 1:
            print(f"\n{Colors.BOLD}{Colors.HEADER}🔄 Starting iteration {iteration}{Colors.ENDC}\n")
        
        for scenario_key in scenario_order:
            if scenario_key not in SCENARIOS:
                print(f"{Colors.WARNING}⚠️  Unknown scenario: {scenario_key}{Colors.ENDC}")
                continue
            
            scenario = SCENARIOS[scenario_key]
            success = run_scenario(scenario_key, scenario, delay)
            
            if not success:
                print(f"{Colors.WARNING}⚠️  Scenario {scenario_key} failed, continuing...{Colors.ENDC}\n")
        
        if not loop:
            break
        
        print(f"\n{Colors.OKGREEN}✅ Completed all scenarios. Looping again...{Colors.ENDC}\n")
        time.sleep(3)


def interactive_mode():
    """Interactive mode - let user select scenarios"""
    print(f"{Colors.BOLD}🎮 Interactive Mode{Colors.ENDC}\n")
    print("Available scenarios:")
    
    for i, (key, scenario) in enumerate(SCENARIOS.items(), 1):
        print(f"  {i}. {scenario['name']}")
    
    print(f"  0. Run all scenarios")
    print(f"  q. Quit\n")
    
    while True:
        try:
            choice = input(f"{Colors.OKCYAN}Select scenario (0-{len(SCENARIOS)}, q to quit): {Colors.ENDC}").strip().lower()
            
            if choice == 'q':
                print(f"{Colors.OKGREEN}👋 Goodbye!{Colors.ENDC}")
                break
            
            if choice == '0':
                run_demo_loop()
                continue
            
            scenario_keys = list(SCENARIOS.keys())
            try:
                index = int(choice) - 1
                if 0 <= index < len(scenario_keys):
                    scenario_key = scenario_keys[index]
                    scenario = SCENARIOS[scenario_key]
                    run_scenario(scenario_key, scenario, delay=0)
                else:
                    print(f"{Colors.WARNING}⚠️  Invalid selection{Colors.ENDC}")
            except ValueError:
                print(f"{Colors.WARNING}⚠️  Invalid input{Colors.ENDC}")
        
        except KeyboardInterrupt:
            print(f"\n{Colors.OKGREEN}👋 Goodbye!{Colors.ENDC}")
            break


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Predictive Model Demo Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/demo-predictive-model.py              # Run all scenarios once
  python scripts/demo-predictive-model.py --loop       # Continuous loop
  python scripts/demo-predictive-model.py --interactive # Manual selection
  python scripts/demo-predictive-model.py --scenario high # Run specific scenario
        """
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode (manual scenario selection)"
    )
    
    parser.add_argument(
        "--loop", "-l",
        action="store_true",
        help="Continuously loop through all scenarios"
    )
    
    parser.add_argument(
        "--scenario", "-s",
        choices=list(SCENARIOS.keys()),
        help="Run a specific scenario"
    )
    
    parser.add_argument(
        "--delay", "-d",
        type=float,
        default=5.0,
        help="Delay between scenarios in seconds (default: 5.0)"
    )
    
    parser.add_argument(
        "--url",
        default=DASHBOARD_URL,
        help=f"Dashboard URL (default: {DASHBOARD_URL})"
    )
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Update module-level variables if URL changed
    # Note: Using nonlocal approach since these are module-level
    if args.url != DASHBOARD_URL:
        # Update the variables in module scope by reassigning
        globals()['DASHBOARD_URL'] = args.url
        globals()['API_BASE'] = f"{args.url}/api"
    
    # Check API connection with more lenient checking
    print(f"{Colors.OKCYAN}🔍 Checking API connection...{Colors.ENDC}")
    # Try to connect with a HEAD request first (faster, doesn't download body)
    try:
        test_response = requests.head(f"{DASHBOARD_URL}/", timeout=2, allow_redirects=True)
        print(f"{Colors.OKGREEN}✅ Dashboard accessible!{Colors.ENDC}\n")
    except requests.exceptions.Timeout:
        # Try API endpoint instead (smaller response)
        try:
            test_response = requests.get(f"{API_BASE}/get-last-demo-metrics", timeout=2)
            print(f"{Colors.OKGREEN}✅ API accessible!{Colors.ENDC}\n")
        except requests.exceptions.Timeout:
            print(f"{Colors.WARNING}⚠️  Dashboard may be slow or under load, continuing anyway...{Colors.ENDC}\n")
        except requests.exceptions.ConnectionError:
            print(f"{Colors.FAIL}❌ Cannot connect to dashboard API at {DASHBOARD_URL}{Colors.ENDC}")
            print(f"{Colors.WARNING}⚠️  Connection refused - is the dashboard running?{Colors.ENDC}")
            print(f"{Colors.WARNING}⚠️  Start it with: cd monitoring/server && python3 -m uvicorn healing_dashboard_api:app --host 0.0.0.0 --port 5001{Colors.ENDC}")
            sys.exit(1)
        except Exception:
            print(f"{Colors.WARNING}⚠️  Connection check had issues, continuing anyway...{Colors.ENDC}\n")
    except requests.exceptions.ConnectionError:
        print(f"{Colors.FAIL}❌ Cannot connect to dashboard API at {DASHBOARD_URL}{Colors.ENDC}")
        print(f"{Colors.WARNING}⚠️  Connection refused - is the dashboard running?{Colors.ENDC}")
        print(f"{Colors.WARNING}⚠️  Start it with: cd monitoring/server && python3 -m uvicorn healing_dashboard_api:app --host 0.0.0.0 --port 5001{Colors.ENDC}")
        sys.exit(1)
    except Exception:
        print(f"{Colors.WARNING}⚠️  Connection check had issues, continuing anyway...{Colors.ENDC}\n")
    
    # Run based on mode
    if args.interactive:
        interactive_mode()
    elif args.scenario:
        scenario = SCENARIOS[args.scenario]
        run_scenario(args.scenario, scenario, delay=0)
    else:
        run_demo_loop(delay=args.delay, loop=args.loop)
    
    print(f"\n{Colors.OKGREEN}✅ Demo completed!{Colors.ENDC}")
    print(f"{Colors.OKCYAN}💡 Check the dashboard at {DASHBOARD_URL} to see live updates{Colors.ENDC}")


if __name__ == "__main__":
    main()

