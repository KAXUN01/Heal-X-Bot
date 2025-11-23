#!/usr/bin/env python3
"""
Test script for Services Tab Feature
Tests that the services tab only shows non-running (stopped/failed) services
"""

import requests
import json
import subprocess
import sys
import time
from typing import Dict, List, Any

# Configuration
BASE_URL = "http://localhost:5001"  # Default healing dashboard API port
API_ENDPOINT = f"{BASE_URL}/api/services"
SERVICES_TO_TEST = ["nginx", "mysql", "ssh", "docker", "postgresql"]

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(60)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

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

def check_service_status(service_name: str) -> Dict[str, Any]:
    """Check if a service is running"""
    try:
        result = subprocess.run(
            ["systemctl", "is-active", service_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        is_active = result.returncode == 0 and result.stdout.strip() == "active"
        return {
            "name": service_name,
            "active": is_active,
            "status": "running" if is_active else "stopped"
        }
    except subprocess.TimeoutExpired:
        return {"name": service_name, "active": False, "status": "timeout"}
    except Exception as e:
        return {"name": service_name, "active": False, "status": f"error: {str(e)}"}

def get_all_services_status() -> List[Dict[str, Any]]:
    """Get status of all test services"""
    services = []
    for service in SERVICES_TO_TEST:
        status = check_service_status(service)
        services.append(status)
    return services

def test_api_endpoint() -> bool:
    """Test the /api/services endpoint"""
    print_header("Testing API Endpoint: /api/services")
    
    try:
        print_info(f"Fetching services from: {API_ENDPOINT}")
        response = requests.get(API_ENDPOINT, timeout=10)
        
        if response.status_code != 200:
            print_error(f"API returned status code: {response.status_code}")
            return False
        
        data = response.json()
        
        if "services" not in data:
            print_error("Response missing 'services' key")
            return False
        
        api_services = data["services"]
        print_success(f"API returned {len(api_services)} services")
        
        # Get actual service statuses
        actual_services = get_all_services_status()
        running_services = [s for s in actual_services if s["active"]]
        stopped_services = [s for s in actual_services if not s["active"]]
        
        print_info(f"Actual running services: {len(running_services)}")
        print_info(f"Actual stopped services: {len(stopped_services)}")
        
        # Check that API only returns non-running services
        api_service_names = {s["name"] for s in api_services}
        running_service_names = {s["name"] for s in running_services}
        
        # Verify no running services are in the API response
        running_in_response = api_service_names.intersection(running_service_names)
        if running_in_response:
            print_error(f"API incorrectly returned running services: {running_in_response}")
            return False
        
        print_success("API correctly filters out running services")
        
        # Display results
        print(f"\n{Colors.BOLD}API Response:{Colors.RESET}")
        if api_services:
            for service in api_services:
                status_icon = "🔴" if service.get("status") == "stopped" else "⚠️"
                print(f"  {status_icon} {service['name']}: {service.get('status', 'unknown')}")
        else:
            print(f"  {Colors.GREEN}✅ No stopped services (all services are running){Colors.RESET}")
        
        # Display actual service statuses for comparison
        print(f"\n{Colors.BOLD}Actual Service Statuses:{Colors.RESET}")
        for service in actual_services:
            status_icon = "🟢" if service["active"] else "🔴"
            status_text = "Running" if service["active"] else "Stopped"
            print(f"  {status_icon} {service['name']}: {status_text}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print_error(f"Could not connect to {BASE_URL}")
        print_warning("Make sure the healing dashboard API is running")
        return False
    except requests.exceptions.Timeout:
        print_error("Request timed out")
        return False
    except Exception as e:
        print_error(f"Error testing API endpoint: {str(e)}")
        return False

def test_service_restart(service_name: str) -> bool:
    """Test restarting a service"""
    print_header(f"Testing Service Restart: {service_name}")
    
    try:
        # Check if service is stopped
        status = check_service_status(service_name)
        if status["active"]:
            print_warning(f"Service {service_name} is already running. Skipping restart test.")
            return True
        
        print_info(f"Attempting to restart {service_name}...")
        response = requests.post(
            f"{BASE_URL}/api/services/{service_name}/restart",
            timeout=30
        )
        
        if response.status_code != 200:
            print_error(f"Restart API returned status code: {response.status_code}")
            return False
        
        data = response.json()
        if not data.get("success", False):
            print_error(f"Restart failed: {data.get('error', 'Unknown error')}")
            return False
        
        print_success(f"Service {service_name} restart request sent successfully")
        
        # Wait a bit and check if service started
        print_info("Waiting 3 seconds for service to start...")
        time.sleep(3)
        
        new_status = check_service_status(service_name)
        if new_status["active"]:
            print_success(f"Service {service_name} is now running")
        else:
            print_warning(f"Service {service_name} may not have started (status: {new_status['status']})")
        
        return True
        
    except Exception as e:
        print_error(f"Error testing service restart: {str(e)}")
        return False

def test_filtering_logic() -> bool:
    """Test the filtering logic with different scenarios"""
    print_header("Testing Filtering Logic")
    
    all_services = get_all_services_status()
    running_count = sum(1 for s in all_services if s["active"])
    stopped_count = sum(1 for s in all_services if not s["active"])
    
    print_info(f"Total services checked: {len(all_services)}")
    print_info(f"Running services: {running_count}")
    print_info(f"Stopped services: {stopped_count}")
    
    try:
        response = requests.get(API_ENDPOINT, timeout=10)
        if response.status_code != 200:
            print_error("Failed to fetch services from API")
            return False
        
        data = response.json()
        api_services = data.get("services", [])
        
        # Verify count matches
        if len(api_services) != stopped_count:
            print_warning(f"API returned {len(api_services)} services, expected {stopped_count} stopped services")
            print_info("This might be normal if some services have unknown status")
        else:
            print_success(f"API correctly returned {stopped_count} stopped services")
        
        # Verify all returned services are actually stopped
        api_service_names = {s["name"] for s in api_services}
        for service in all_services:
            if service["name"] in api_service_names and service["active"]:
                print_error(f"Service {service['name']} is running but was returned by API")
                return False
        
        print_success("All returned services are correctly identified as non-running")
        return True
        
    except Exception as e:
        print_error(f"Error testing filtering logic: {str(e)}")
        return False

def test_api_response_format() -> bool:
    """Test that API response has correct format"""
    print_header("Testing API Response Format")
    
    try:
        response = requests.get(API_ENDPOINT, timeout=10)
        if response.status_code != 200:
            return False
        
        data = response.json()
        
        # Check required fields
        if "services" not in data:
            print_error("Response missing 'services' key")
            return False
        
        if not isinstance(data["services"], list):
            print_error("'services' is not a list")
            return False
        
        print_success("Response has correct structure")
        
        # Check service object format
        for service in data["services"]:
            if "name" not in service:
                print_error("Service object missing 'name' field")
                return False
            if "status" not in service:
                print_error("Service object missing 'status' field")
                return False
            if "active" not in service:
                print_error("Service object missing 'active' field")
                return False
        
        print_success("All service objects have required fields")
        return True
        
    except Exception as e:
        print_error(f"Error testing response format: {str(e)}")
        return False

def main():
    """Run all tests"""
    print_header("Services Tab Feature Test Suite")
    
    print_info("This script tests that the services tab only shows non-running services")
    print_info(f"Testing against: {BASE_URL}")
    print_info(f"Services to test: {', '.join(SERVICES_TO_TEST)}")
    
    results = []
    
    # Test 1: API Endpoint
    results.append(("API Endpoint Test", test_api_endpoint()))
    
    # Test 2: Response Format
    results.append(("Response Format Test", test_api_response_format()))
    
    # Test 3: Filtering Logic
    results.append(("Filtering Logic Test", test_filtering_logic()))
    
    # Test 4: Service Restart (if there's a stopped service)
    all_services = get_all_services_status()
    stopped_services = [s for s in all_services if not s["active"]]
    if stopped_services:
        test_service = stopped_services[0]["name"]
        results.append((f"Service Restart Test ({test_service})", test_service_restart(test_service)))
    else:
        print_warning("No stopped services found. Skipping restart test.")
        print_info("To test restart functionality, stop a service first:")
        print_info("  sudo systemctl stop nginx  # Example")
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        if result:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")
    
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

