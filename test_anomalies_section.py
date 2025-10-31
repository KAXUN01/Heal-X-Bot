#!/usr/bin/env python3
"""
Test Script for "Detected Anomalies & Errors" Section
======================================================
This script tests and demonstrates that the anomalies section is working correctly.
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Any

# Configuration
DASHBOARD_URL = "http://localhost:5001"
ENDPOINT = "/api/critical-services/issues"
FULL_URL = f"{DASHBOARD_URL}{ENDPOINT}"

def print_header(text: str):
    """Print a formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_success(text: str):
    """Print success message"""
    print(f"✅ {text}")

def print_error(text: str):
    """Print error message"""
    print(f"❌ {text}")

def print_info(text: str):
    """Print info message"""
    print(f"ℹ️  {text}")

def print_warning(text: str):
    """Print warning message"""
    print(f"⚠️  {text}")

def test_endpoint_connectivity() -> bool:
    """Test if the endpoint is accessible"""
    print_header("Testing Endpoint Connectivity")
    
    try:
        response = requests.get(FULL_URL, timeout=5)
        if response.status_code == 200:
            print_success(f"Endpoint is accessible (Status: {response.status_code})")
            return True
        else:
            print_error(f"Endpoint returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to {DASHBOARD_URL}")
        print_info("Make sure the dashboard is running on port 5001")
        return False
    except Exception as e:
        print_error(f"Error connecting to endpoint: {e}")
        return False

def test_response_format() -> bool:
    """Test if the response has the correct format"""
    print_header("Testing Response Format")
    
    try:
        response = requests.get(FULL_URL, timeout=5)
        if response.status_code != 200:
            print_error(f"Endpoint returned status {response.status_code}")
            return False
        
        data = response.json()
        
        # Check required fields
        required_fields = ['status', 'issues', 'count']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            print_error(f"Missing required fields: {missing_fields}")
            return False
        
        print_success("Response contains all required fields")
        print_info(f"Status: {data.get('status')}")
        print_info(f"Count: {data.get('count')}")
        print_info(f"Number of issues: {len(data.get('issues', []))}")
        
        # Check data types
        if not isinstance(data['status'], str):
            print_error("'status' should be a string")
            return False
        
        if not isinstance(data['issues'], list):
            print_error("'issues' should be a list")
            return False
        
        if not isinstance(data['count'], int):
            print_error("'count' should be an integer")
            return False
        
        print_success("All data types are correct")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {e}")
        return False
    except json.JSONDecodeError:
        print_error("Response is not valid JSON")
        return False
    except Exception as e:
        print_error(f"Error testing response format: {e}")
        return False

def test_issue_format(issues: List[Dict]) -> bool:
    """Test if issues have the correct format"""
    print_header("Testing Issue Format")
    
    if not issues:
        print_warning("No issues found (this is OK if system is healthy)")
        return True
    
    print_info(f"Testing format of {len(issues)} issue(s)")
    
    # Expected fields (some may be optional)
    expected_fields = ['timestamp', 'service', 'level', 'message']
    optional_fields = ['severity', 'category', 'priority', 'source', 'description']
    
    all_valid = True
    
    for i, issue in enumerate(issues[:5]):  # Test first 5 issues
        print(f"\n  Issue {i+1}:")
        
        # Check required fields
        missing = [field for field in expected_fields if field not in issue]
        if missing:
            print_error(f"    Missing fields: {missing}")
            all_valid = False
        else:
            print_success(f"    Has all required fields")
        
        # Print issue details
        print(f"    Service: {issue.get('service', 'N/A')}")
        print(f"    Level: {issue.get('level', 'N/A')}")
        severity = issue.get('severity') or issue.get('level', 'N/A')
        print(f"    Severity: {severity}")
        print(f"    Timestamp: {issue.get('timestamp', 'N/A')}")
        message = issue.get('message', 'N/A')
        if len(message) > 80:
            message = message[:80] + "..."
        print(f"    Message: {message}")
        
        # Check data types
        if issue.get('timestamp'):
            try:
                datetime.fromisoformat(issue['timestamp'].replace('Z', '+00:00'))
                print_success(f"    Timestamp is valid ISO format")
            except:
                print_warning(f"    Timestamp format may be invalid: {issue['timestamp']}")
    
    return all_valid

def test_severity_mapping() -> bool:
    """Test if severity field is properly mapped"""
    print_header("Testing Severity Mapping")
    
    try:
        response = requests.get(FULL_URL, timeout=5)
        data = response.json()
        issues = data.get('issues', [])
        
        if not issues:
            print_warning("No issues to test severity mapping")
            return True
        
        print_info(f"Checking severity mapping for {len(issues)} issue(s)")
        
        all_have_severity = True
        for issue in issues:
            severity = issue.get('severity')
            level = issue.get('level')
            
            if not severity:
                # Severity can be derived from level
                if level:
                    print_warning(f"Issue has 'level' ({level}) but no 'severity' (will use level as fallback)")
                else:
                    print_error(f"Issue missing both 'severity' and 'level'")
                    all_have_severity = False
            else:
                valid_severities = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']
                if severity in valid_severities:
                    print_success(f"Severity '{severity}' is valid")
                else:
                    print_warning(f"Severity '{severity}' is not standard (may be custom)")
        
        return all_have_severity
        
    except Exception as e:
        print_error(f"Error testing severity mapping: {e}")
        return False

def display_current_issues():
    """Display current issues from the system"""
    print_header("Current System Issues")
    
    try:
        response = requests.get(FULL_URL, timeout=5)
        data = response.json()
        issues = data.get('issues', [])
        
        if not issues:
            print_success("No anomalies detected - system is healthy! 🎉")
            print_info("The section is working correctly, but there are no critical issues.")
            return
        
        print(f"Found {len(issues)} critical issue(s):\n")
        
        for i, issue in enumerate(issues, 1):
            severity = issue.get('severity') or issue.get('level', 'UNKNOWN')
            service = issue.get('service', 'Unknown')
            timestamp = issue.get('timestamp', 'N/A')
            message = issue.get('message', 'No message')
            
            # Format severity color indicator
            if severity in ['CRITICAL', 'ERROR']:
                severity_icon = "🔴"
            elif severity == 'WARNING':
                severity_icon = "🟡"
            else:
                severity_icon = "🔵"
            
            print(f"{severity_icon} Issue #{i}")
            print(f"   Service: {service}")
            print(f"   Severity: {severity}")
            print(f"   Time: {timestamp}")
            if len(message) > 100:
                message = message[:100] + "..."
            print(f"   Message: {message}")
            print()
        
    except Exception as e:
        print_error(f"Error displaying issues: {e}")

def test_refresh_functionality():
    """Test that the endpoint can be called multiple times (simulating refresh)"""
    print_header("Testing Refresh Functionality")
    
    try:
        print_info("Making 3 consecutive requests (simulating auto-refresh)...")
        
        responses = []
        for i in range(3):
            response = requests.get(FULL_URL, timeout=5)
            if response.status_code == 200:
                data = response.json()
                responses.append(data)
                print_success(f"Request {i+1} successful - {data.get('count', 0)} issues")
            else:
                print_error(f"Request {i+1} failed with status {response.status_code}")
                return False
        
        # Check consistency
        if len(set(r.get('count', 0) for r in responses)) == 1:
            print_success("Response count is consistent across refreshes")
        else:
            print_warning("Response count changed (this is OK if new issues were detected)")
        
        return True
        
    except Exception as e:
        print_error(f"Error testing refresh: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print_header("Anomalies Section Test Suite")
    print(f"Testing endpoint: {FULL_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = []
    
    # Test 1: Connectivity
    results.append(("Endpoint Connectivity", test_endpoint_connectivity()))
    if not results[-1][1]:
        print_error("\nCannot continue - endpoint is not accessible")
        return False
    
    # Test 2: Response Format
    results.append(("Response Format", test_response_format()))
    
    # Test 3: Get current issues
    try:
        response = requests.get(FULL_URL, timeout=5)
        issues = response.json().get('issues', [])
    except:
        issues = []
    
    # Test 4: Issue Format
    results.append(("Issue Format", test_issue_format(issues)))
    
    # Test 5: Severity Mapping
    results.append(("Severity Mapping", test_severity_mapping()))
    
    # Test 6: Refresh Functionality
    results.append(("Refresh Functionality", test_refresh_functionality()))
    
    # Display current issues
    display_current_issues()
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print_success("All tests passed! The anomalies section is working correctly.")
        return True
    else:
        print_warning(f"Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

