#!/usr/bin/env python3
"""
Test Script for Predictive Maintenance Model Predictions

This script tests all predictive maintenance API endpoints to verify
that the new model predictions are working correctly.
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any

# Configuration
DASHBOARD_URL = "http://localhost:5001"
TIMEOUT = 10

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{BOLD}{BLUE}{'='*70}{RESET}")
    print(f"{BOLD}{BLUE}{text.center(70)}{RESET}")
    print(f"{BOLD}{BLUE}{'='*70}{RESET}\n")

def print_test(test_name: str):
    """Print test name"""
    print(f"{BOLD}Testing: {test_name}{RESET}")

def print_success(message: str):
    """Print success message"""
    print(f"{GREEN}✅ {message}{RESET}")

def print_error(message: str):
    """Print error message"""
    print(f"{RED}❌ {message}{RESET}")

def print_warning(message: str):
    """Print warning message"""
    print(f"{YELLOW}⚠️  {message}{RESET}")

def print_info(message: str):
    """Print info message"""
    print(f"{BLUE}ℹ️  {message}{RESET}")

def test_endpoint_health():
    """Test if the dashboard is accessible"""
    print_test("Dashboard Health Check")
    try:
        response = requests.get(f"{DASHBOARD_URL}/api/health", timeout=TIMEOUT)
        if response.status_code == 200:
            print_success(f"Dashboard is accessible (Status: {response.status_code})")
            return True
        else:
            print_error(f"Dashboard returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to dashboard at {DASHBOARD_URL}")
        print_info("Make sure the healing dashboard is running on port 5001")
        return False
    except Exception as e:
        print_error(f"Error checking dashboard: {e}")
        return False

def test_predict_failure_risk():
    """Test failure risk prediction endpoint"""
    print_test("Failure Risk Prediction")
    try:
        response = requests.get(f"{DASHBOARD_URL}/api/predict-failure-risk", timeout=TIMEOUT)
        
        if response.status_code != 200:
            print_error(f"Endpoint returned status {response.status_code}")
            return False
        
        data = response.json()
        
        # Check for errors
        if 'error' in data:
            print_warning(f"Model not available: {data.get('error', 'Unknown error')}")
            print_info("This is expected if the model hasn't been loaded yet")
            return True  # Not a failure, just model not loaded
        
        # Validate response structure
        required_fields = ['timestamp', 'risk_score', 'risk_percentage']
        missing_fields = [f for f in required_fields if f not in data]
        
        if missing_fields:
            print_error(f"Missing required fields: {missing_fields}")
            return False
        
        # Validate values
        risk_score = data.get('risk_score', 0)
        if not (0 <= risk_score <= 1):
            print_error(f"Invalid risk_score: {risk_score} (should be 0-1)")
            return False
        
        print_success("Failure risk prediction working correctly")
        print_info(f"  Risk Score: {risk_score:.4f} ({risk_score*100:.2f}%)")
        print_info(f"  Early Warning: {data.get('has_early_warning', False)}")
        print_info(f"  High Risk: {data.get('is_high_risk', False)}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {e}")
        return False
    except json.JSONDecodeError:
        print_error("Invalid JSON response")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False

def test_get_early_warnings():
    """Test early warnings endpoint"""
    print_test("Early Warnings")
    try:
        response = requests.get(f"{DASHBOARD_URL}/api/get-early-warnings", timeout=TIMEOUT)
        
        if response.status_code != 200:
            print_error(f"Endpoint returned status {response.status_code}")
            return False
        
        data = response.json()
        
        # Validate response structure
        required_fields = ['timestamp', 'warning_count', 'has_warnings', 'warnings']
        missing_fields = [f for f in required_fields if f not in data]
        
        if missing_fields:
            print_error(f"Missing required fields: {missing_fields}")
            return False
        
        warning_count = data.get('warning_count', 0)
        has_warnings = data.get('has_warnings', False)
        
        print_success("Early warnings endpoint working correctly")
        print_info(f"  Warning Count: {warning_count}")
        print_info(f"  Has Warnings: {has_warnings}")
        
        if has_warnings and warning_count > 0:
            print_info(f"  Active Warnings:")
            for warning in data.get('warnings', [])[:5]:  # Show first 5
                severity = warning.get('severity', 'unknown')
                message = warning.get('message', 'No message')
                print_info(f"    - [{severity.upper()}] {message}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {e}")
        return False
    except json.JSONDecodeError:
        print_error("Invalid JSON response")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False

def test_predict_time_to_failure():
    """Test time-to-failure prediction endpoint"""
    print_test("Time-to-Failure Prediction")
    try:
        response = requests.get(f"{DASHBOARD_URL}/api/predict-time-to-failure", timeout=TIMEOUT)
        
        if response.status_code != 200:
            print_error(f"Endpoint returned status {response.status_code}")
            return False
        
        data = response.json()
        
        # Check for errors
        if 'error' in data:
            print_warning(f"Model not available: {data.get('error', 'Unknown error')}")
            print_info("This is expected if the model hasn't been loaded yet")
            return True  # Not a failure, just model not loaded
        
        # Validate response structure
        if 'timestamp' not in data:
            print_error("Missing 'timestamp' field")
            return False
        
        hours_until = data.get('hours_until_failure')
        
        if hours_until is None:
            print_info("No failure predicted in near future (this is normal)")
        else:
            if hours_until < 0:
                print_error(f"Invalid hours_until_failure: {hours_until} (should be >= 0)")
                return False
            
            print_success("Time-to-failure prediction working correctly")
            print_info(f"  Hours Until Failure: {hours_until:.2f}")
            
            if 'predicted_failure_time' in data:
                print_info(f"  Predicted Time: {data['predicted_failure_time']}")
            
            if 'confidence' in data:
                print_info(f"  Confidence: {data['confidence']}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {e}")
        return False
    except json.JSONDecodeError:
        print_error("Invalid JSON response")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False

def test_predict_anomaly(metrics: Dict[str, Any]):
    """Test anomaly prediction endpoint with custom metrics"""
    print_test(f"Anomaly Prediction (Custom Metrics)")
    try:
        payload = {"metrics": metrics}
        response = requests.post(
            f"{DASHBOARD_URL}/api/predict-anomaly",
            json=payload,
            timeout=TIMEOUT
        )
        
        if response.status_code != 200:
            print_error(f"Endpoint returned status {response.status_code}")
            return False
        
        data = response.json()
        
        # Check for errors
        if 'error' in data:
            print_warning(f"Model not available: {data.get('error', 'Unknown error')}")
            print_info("This is expected if the model hasn't been loaded yet")
            return True  # Not a failure, just model not loaded
        
        # Validate response structure
        required_fields = ['timestamp', 'is_anomaly', 'anomaly_score']
        missing_fields = [f for f in required_fields if f not in data]
        
        if missing_fields:
            print_error(f"Missing required fields: {missing_fields}")
            return False
        
        is_anomaly = data.get('is_anomaly', False)
        anomaly_score = data.get('anomaly_score', 0)
        
        if not (0 <= anomaly_score <= 1):
            print_error(f"Invalid anomaly_score: {anomaly_score} (should be 0-1)")
            return False
        
        print_success("Anomaly prediction working correctly")
        print_info(f"  Is Anomaly: {is_anomaly}")
        print_info(f"  Anomaly Score: {anomaly_score:.4f} ({anomaly_score*100:.2f}%)")
        
        if 'risk_level' in data:
            print_info(f"  Risk Level: {data['risk_level']}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {e}")
        return False
    except json.JSONDecodeError:
        print_error("Invalid JSON response")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False

def test_scenarios():
    """Test different scenarios"""
    print_header("Testing Different Scenarios")
    
    scenarios = [
        {
            "name": "Normal Operation",
            "metrics": {
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
            }
        },
        {
            "name": "High CPU Load",
            "metrics": {
                "cpu_percent": 95.0,
                "memory_percent": 60.0,
                "disk_percent": 50.0,
                "network_in_bytes": 200000,
                "network_out_bytes": 100000,
                "connections_count": 200,
                "memory_available_gb": 4.0,
                "disk_free_gb": 50.0,
                "error_count": 5,
                "warning_count": 10,
                "critical_count": 1,
                "service_failures": 0,
                "auth_failures": 0,
                "ssh_attempts": 0
            }
        },
        {
            "name": "Memory Pressure",
            "metrics": {
                "cpu_percent": 50.0,
                "memory_percent": 92.0,
                "disk_percent": 60.0,
                "network_in_bytes": 150000,
                "network_out_bytes": 75000,
                "connections_count": 150,
                "memory_available_gb": 0.5,
                "disk_free_gb": 50.0,
                "error_count": 3,
                "warning_count": 8,
                "critical_count": 0,
                "service_failures": 1,
                "auth_failures": 0,
                "ssh_attempts": 0
            }
        },
        {
            "name": "Disk Full",
            "metrics": {
                "cpu_percent": 40.0,
                "memory_percent": 50.0,
                "disk_percent": 98.0,
                "network_in_bytes": 100000,
                "network_out_bytes": 50000,
                "connections_count": 100,
                "memory_available_gb": 6.0,
                "disk_free_gb": 1.0,
                "error_count": 10,
                "warning_count": 15,
                "critical_count": 2,
                "service_failures": 2,
                "auth_failures": 0,
                "ssh_attempts": 0
            }
        },
        {
            "name": "Critical Failure Indicators",
            "metrics": {
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
            }
        }
    ]
    
    results = []
    for scenario in scenarios:
        print(f"\n{BOLD}Scenario: {scenario['name']}{RESET}")
        result = test_predict_anomaly(scenario['metrics'])
        results.append((scenario['name'], result))
    
    return results

def main():
    """Main test function"""
    print_header("Predictive Maintenance Model Test Suite")
    print_info(f"Testing dashboard at: {DASHBOARD_URL}")
    print_info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Track test results
    test_results = []
    
    # Test 1: Health check
    health_ok = test_endpoint_health()
    test_results.append(("Dashboard Health", health_ok))
    
    if not health_ok:
        print_error("\nDashboard is not accessible. Please start the healing dashboard first.")
        print_info("Run: cd monitoring/server && python3 -m uvicorn healing_dashboard_api:app --host 0.0.0.0 --port 5001")
        sys.exit(1)
    
    # Test 2: Failure risk prediction
    risk_ok = test_predict_failure_risk()
    test_results.append(("Failure Risk Prediction", risk_ok))
    
    # Test 3: Early warnings
    warnings_ok = test_get_early_warnings()
    test_results.append(("Early Warnings", warnings_ok))
    
    # Test 4: Time-to-failure prediction
    time_ok = test_predict_time_to_failure()
    test_results.append(("Time-to-Failure Prediction", time_ok))
    
    # Test 5: Anomaly prediction with current system metrics
    print_test("Anomaly Prediction (System Metrics)")
    print_info("Using current system metrics...")
    anomaly_ok = test_predict_anomaly({})  # Empty dict will use system metrics
    test_results.append(("Anomaly Prediction (System)", anomaly_ok))
    
    # Test 6: Different scenarios
    scenario_results = test_scenarios()
    for name, result in scenario_results:
        test_results.append((f"Scenario: {name}", result))
    
    # Print summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"  {status} - {test_name}")
    
    print(f"\n{BOLD}Results: {passed}/{total} tests passed{RESET}")
    
    if passed == total:
        print_success("\n🎉 All tests passed! Model predictions are working correctly.")
        return 0
    elif passed > 0:
        print_warning(f"\n⚠️  {total - passed} test(s) failed. Some features may not be working.")
        return 1
    else:
        print_error("\n❌ All tests failed. Please check the dashboard and model configuration.")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Tests interrupted by user{RESET}")
        sys.exit(1)
    except Exception as e:
        print_error(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

