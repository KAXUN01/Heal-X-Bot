#!/usr/bin/env python3
"""
Test script for Auto-Restart Feature
Tests that the system automatically restarts stopped services
"""

import requests
import subprocess
import sys
import time
from typing import Dict, List, Optional, Tuple

# Configuration
BASE_URL = "http://localhost:5001"  # Default healing dashboard API port
API_ENDPOINT = f"{BASE_URL}/api/services"
CONFIG_ENDPOINT = f"{BASE_URL}/api/config"
SERVICES_TO_TEST = ["nginx", "mysql", "ssh", "docker", "postgresql"]
AUTO_RESTART_CHECK_INTERVAL = 2  # Check every 2 seconds
MAX_WAIT_TIME = 30  # Maximum time to wait for auto-restart (seconds)

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")

def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def print_info(text: str):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")

def print_step(text: str):
    """Print step message"""
    print(f"{Colors.CYAN}➜ {text}{Colors.RESET}")

def check_service_status(service_name: str) -> Tuple[bool, str]:
    """Check if a service is running
    
    Returns:
        (is_active, status_message)
    """
    try:
        result = subprocess.run(
            ["systemctl", "is-active", service_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        is_active = result.returncode == 0 and result.stdout.strip() == "active"
        status = "running" if is_active else "stopped"
        return is_active, status
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:
        return False, f"error: {str(e)}"

def stop_service(service_name: str) -> bool:
    """Stop a service"""
    try:
        print_step(f"Stopping service: {service_name}")
        result = subprocess.run(
            ["sudo", "systemctl", "stop", service_name],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print_success(f"Service {service_name} stopped successfully")
            return True
        else:
            print_error(f"Failed to stop {service_name}: {result.stderr}")
            return False
    except Exception as e:
        print_error(f"Error stopping service {service_name}: {str(e)}")
        return False

def start_service(service_name: str) -> bool:
    """Start a service"""
    try:
        print_step(f"Starting service: {service_name}")
        result = subprocess.run(
            ["sudo", "systemctl", "start", service_name],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print_success(f"Service {service_name} started successfully")
            return True
        else:
            print_error(f"Failed to start {service_name}: {result.stderr}")
            return False
    except Exception as e:
        print_error(f"Error starting service {service_name}: {str(e)}")
        return False

def wait_for_auto_restart(service_name: str, max_wait: int = MAX_WAIT_TIME) -> Tuple[bool, float]:
    """Wait for a service to be automatically restarted
    
    Returns:
        (was_restarted, time_taken)
    """
    print_info(f"Waiting for auto-restart of {service_name} (max {max_wait}s)...")
    
    start_time = time.time()
    check_count = 0
    
    while time.time() - start_time < max_wait:
        time.sleep(AUTO_RESTART_CHECK_INTERVAL)
        check_count += 1
        
        is_active, status = check_service_status(service_name)
        
        if is_active:
            elapsed = time.time() - start_time
            print_success(f"Service {service_name} was automatically restarted after {elapsed:.1f} seconds")
            return True, elapsed
        
        # Show progress every 5 checks (10 seconds)
        if check_count % 5 == 0:
            elapsed = time.time() - start_time
            print_info(f"  Still waiting... ({elapsed:.1f}s elapsed, status: {status})")
    
    elapsed = time.time() - start_time
    print_error(f"Service {service_name} was NOT automatically restarted after {elapsed:.1f} seconds")
    return False, elapsed

def check_api_connection() -> bool:
    """Check if API is accessible"""
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_auto_restart_config() -> Optional[bool]:
    """Get auto-restart configuration"""
    try:
        response = requests.get(CONFIG_ENDPOINT, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("auto_restart", None)
    except:
        pass
    return None

def enable_auto_restart() -> bool:
    """Enable auto-restart in configuration"""
    try:
        response = requests.post(
            CONFIG_ENDPOINT,
            json={"auto_restart": True},
            timeout=5
        )
        return response.status_code == 200
    except:
        return False

def test_single_service_auto_restart(service_name: str) -> bool:
    """Test auto-restart for a single service"""
    print_header(f"Testing Auto-Restart: {service_name}")
    
    # Step 1: Check initial status
    print_step("Step 1: Checking initial service status")
    is_active, status = check_service_status(service_name)
    if is_active:
        print_success(f"Service {service_name} is currently running")
    else:
        print_warning(f"Service {service_name} is currently {status}")
        # Start it first
        if not start_service(service_name):
            print_error(f"Cannot proceed - service {service_name} cannot be started")
            return False
        time.sleep(2)  # Wait for service to fully start
    
    # Step 2: Stop the service
    print_step("Step 2: Stopping the service")
    if not stop_service(service_name):
        return False
    
    # Verify it's stopped
    time.sleep(1)
    is_active, status = check_service_status(service_name)
    if is_active:
        print_error(f"Service {service_name} is still running after stop command")
        return False
    print_success(f"Service {service_name} confirmed stopped")
    
    # Step 3: Wait for auto-restart
    print_step("Step 3: Waiting for automatic restart")
    was_restarted, elapsed = wait_for_auto_restart(service_name)
    
    if was_restarted:
        print_success(f"✅ Auto-restart test PASSED for {service_name}")
        return True
    else:
        print_error(f"❌ Auto-restart test FAILED for {service_name}")
        print_warning("The service was not automatically restarted")
        print_info("Possible reasons:")
        print_info("  - Auto-restart is disabled in configuration")
        print_info("  - Monitoring loop is not running")
        print_info("  - Service is not in the monitored services list")
        return False

def test_multiple_services_auto_restart(service_names: List[str]) -> bool:
    """Test auto-restart for multiple services"""
    print_header(f"Testing Auto-Restart: Multiple Services ({', '.join(service_names)})")
    
    # Step 1: Check and start all services
    print_step("Step 1: Ensuring all services are running")
    for service in service_names:
        is_active, status = check_service_status(service)
        if not is_active:
            print_info(f"Starting {service}...")
            start_service(service)
            time.sleep(1)
    
    time.sleep(2)  # Wait for all services to be fully started
    
    # Step 2: Stop all services
    print_step("Step 2: Stopping all services")
    stopped_services = []
    for service in service_names:
        if stop_service(service):
            stopped_services.append(service)
        time.sleep(0.5)
    
    if not stopped_services:
        print_error("Failed to stop any services")
        return False
    
    print_success(f"Stopped {len(stopped_services)} service(s)")
    time.sleep(2)  # Wait a bit before checking
    
    # Step 3: Monitor all services for auto-restart
    print_step("Step 3: Monitoring for automatic restart")
    print_info(f"Monitoring {len(stopped_services)} service(s) for up to {MAX_WAIT_TIME} seconds...")
    
    start_time = time.time()
    restarted_services = []
    failed_services = []
    
    while time.time() - start_time < MAX_WAIT_TIME:
        for service in stopped_services[:]:  # Copy list to modify during iteration
            is_active, status = check_service_status(service)
            if is_active:
                elapsed = time.time() - start_time
                print_success(f"✅ {service} was automatically restarted after {elapsed:.1f}s")
                restarted_services.append(service)
                stopped_services.remove(service)
        
        if not stopped_services:
            break
        
        time.sleep(AUTO_RESTART_CHECK_INTERVAL)
        
        # Show progress
        elapsed = time.time() - start_time
        if int(elapsed) % 5 == 0:
            print_info(f"  Progress: {len(restarted_services)}/{len(stopped_services) + len(restarted_services)} restarted ({elapsed:.0f}s)")
    
    # Check final status
    for service in stopped_services:
        is_active, status = check_service_status(service)
        if not is_active:
            failed_services.append(service)
    
    # Results
    print_header("Test Results")
    print_success(f"Successfully auto-restarted: {len(restarted_services)}/{len(restarted_services) + len(failed_services)}")
    
    if restarted_services:
        print("\nRestarted services:")
        for service in restarted_services:
            print_success(f"  ✅ {service}")
    
    if failed_services:
        print("\nFailed to auto-restart:")
        for service in failed_services:
            print_error(f"  ❌ {service}")
    
    return len(failed_services) == 0

def main():
    """Run auto-restart tests"""
    print_header("Auto-Restart Feature Test Suite")
    
    print_info("This script tests that the system automatically restarts stopped services")
    print_info(f"Testing against: {BASE_URL}")
    print_info(f"Services to test: {', '.join(SERVICES_TO_TEST)}")
    print_warning("This script will STOP services. Make sure you're in a test environment!")
    
    # Check API connection
    print_step("Checking API connection...")
    if not check_api_connection():
        print_error(f"Cannot connect to {BASE_URL}")
        print_warning("Make sure the healing dashboard API is running:")
        print_warning("  python monitoring/server/healing_dashboard_api.py")
        return 1
    
    print_success("API is accessible")
    
    # Check auto-restart configuration
    print_step("Checking auto-restart configuration...")
    auto_restart_enabled = get_auto_restart_config()
    if auto_restart_enabled is None:
        print_warning("Could not determine auto-restart configuration")
    elif auto_restart_enabled:
        print_success("Auto-restart is ENABLED")
    else:
        print_warning("Auto-restart is DISABLED - enabling it for test...")
        if enable_auto_restart():
            print_success("Auto-restart enabled")
        else:
            print_error("Failed to enable auto-restart")
            return 1
    
    # Ask user which test to run
    print("\n" + "="*70)
    print("Select test mode:")
    print("  1. Test single service (nginx)")
    print("  2. Test two services (nginx, mysql)")
    print("  3. Test all services")
    print("  4. Custom service selection")
    print("="*70)
    
    try:
        choice = input("\nEnter choice (1-4) [default: 1]: ").strip() or "1"
    except KeyboardInterrupt:
        print_warning("\nTest cancelled by user")
        return 1
    
    results = []
    
    if choice == "1":
        # Test single service
        results.append(("Single Service Test (nginx)", test_single_service_auto_restart("nginx")))
    
    elif choice == "2":
        # Test two services
        results.append(("Two Services Test (nginx, mysql)", 
                        test_multiple_services_auto_restart(["nginx", "mysql"])))
    
    elif choice == "3":
        # Test all services
        results.append(("All Services Test", 
                        test_multiple_services_auto_restart(SERVICES_TO_TEST)))
    
    elif choice == "4":
        # Custom selection
        print("\nAvailable services:", ", ".join(SERVICES_TO_TEST))
        service_input = input("Enter service names (comma-separated): ").strip()
        selected_services = [s.strip() for s in service_input.split(",") if s.strip() in SERVICES_TO_TEST]
        
        if not selected_services:
            print_error("No valid services selected")
            return 1
        
        if len(selected_services) == 1:
            results.append((f"Custom Service Test ({selected_services[0]})", 
                           test_single_service_auto_restart(selected_services[0])))
        else:
            results.append((f"Custom Services Test ({', '.join(selected_services)})", 
                           test_multiple_services_auto_restart(selected_services)))
    
    else:
        print_error("Invalid choice")
        return 1
    
    # Summary
    print_header("Test Summary")
    
    for test_name, result in results:
        if result:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.RESET}")
    
    if passed == total:
        print_success("All tests passed! ✅")
        return 0
    else:
        print_error("Some tests failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print_warning("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

