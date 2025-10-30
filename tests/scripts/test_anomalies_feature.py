#!/usr/bin/env python3
"""
Test Script for Anomalies & Errors Detection Feature

This script tests:
1. API endpoints for anomalies
2. Data retrieval and formatting
3. Dashboard integration
4. AI analysis capability
"""

import requests
import json
import sys
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama for colored output
init(autoreset=True)

# Configuration
MONITORING_SERVER = "http://localhost:5000"
DASHBOARD_URL = "http://localhost:3001"

def print_header(text):
    """Print a formatted header"""
    print(f"\n{Fore.CYAN}{'=' * 70}")
    print(f"{Fore.CYAN}{text:^70}")
    print(f"{Fore.CYAN}{'=' * 70}{Style.RESET_ALL}\n")

def print_success(text):
    """Print success message"""
    print(f"{Fore.GREEN}✅ {text}{Style.RESET_ALL}")

def print_error(text):
    """Print error message"""
    print(f"{Fore.RED}❌ {text}{Style.RESET_ALL}")

def print_info(text):
    """Print info message"""
    print(f"{Fore.BLUE}ℹ️  {text}{Style.RESET_ALL}")

def print_warning(text):
    """Print warning message"""
    print(f"{Fore.YELLOW}⚠️  {text}{Style.RESET_ALL}")

def test_server_connectivity():
    """Test if monitoring server is running"""
    print_header("TEST 1: Server Connectivity")
    
    try:
        response = requests.get(f"{MONITORING_SERVER}/health", timeout=5)
        if response.status_code == 200:
            print_success(f"Monitoring server is running on {MONITORING_SERVER}")
            return True
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to monitoring server at {MONITORING_SERVER}")
        print_info("Please ensure the monitoring server is running:")
        print_info("  cd monitoring/server && python app.py")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_critical_services_endpoint():
    """Test /api/critical-services/issues endpoint"""
    print_header("TEST 2: Critical Services Issues Endpoint")
    
    endpoint = f"{MONITORING_SERVER}/api/critical-services/issues"
    print_info(f"Testing: GET {endpoint}")
    
    try:
        response = requests.get(endpoint, timeout=5)
        data = response.json()
        
        if data.get('status') == 'success':
            print_success("Endpoint is responding correctly")
            print_info(f"Response: {json.dumps(data, indent=2)}")
            
            issues_count = data.get('count', 0)
            if issues_count > 0:
                print_warning(f"Found {issues_count} critical issues!")
                for i, issue in enumerate(data.get('issues', [])[:3], 1):
                    print(f"  {i}. {issue.get('service')} - {issue.get('level')}: {issue.get('message')[:50]}...")
            else:
                print_success("No critical issues found - system is healthy!")
            
            return True, data.get('issues', [])
        else:
            print_error(f"Endpoint returned error: {data.get('message')}")
            return False, []
            
    except Exception as e:
        print_error(f"Failed to test endpoint: {e}")
        return False, []

def test_system_logs_endpoint():
    """Test /api/system-logs/recent endpoint (fallback)"""
    print_header("TEST 3: System Logs Endpoint (Fallback)")
    
    endpoint = f"{MONITORING_SERVER}/api/system-logs/recent?level=ERROR&limit=10"
    print_info(f"Testing: GET {endpoint}")
    
    try:
        response = requests.get(endpoint, timeout=5)
        data = response.json()
        
        if data.get('status') == 'success':
            print_success("Fallback endpoint is responding correctly")
            print_info(f"Response: {json.dumps(data, indent=2)}")
            
            logs_count = data.get('count', 0)
            if logs_count > 0:
                print_warning(f"Found {logs_count} ERROR level logs")
                for i, log in enumerate(data.get('logs', [])[:3], 1):
                    print(f"  {i}. {log.get('service')} - {log.get('level')}: {log.get('message')[:50]}...")
            else:
                print_success("No ERROR logs found - system is clean!")
            
            return True, data.get('logs', [])
        else:
            print_error(f"Endpoint returned error: {data.get('message')}")
            return False, []
            
    except Exception as e:
        print_error(f"Failed to test endpoint: {e}")
        return False, []

def test_ai_analysis(sample_log):
    """Test AI analysis on a sample log"""
    print_header("TEST 4: AI Analysis Integration")
    
    endpoint = f"{MONITORING_SERVER}/api/gemini/analyze-log"
    print_info(f"Testing: POST {endpoint}")
    
    # Use provided sample or create a test log
    if not sample_log:
        sample_log = {
            "service": "systemd-test",
            "message": "Test error for anomaly detection",
            "level": "ERROR",
            "timestamp": datetime.now().isoformat()
        }
    
    print_info(f"Analyzing log: {sample_log.get('service')} - {sample_log.get('message')[:50]}...")
    
    try:
        response = requests.post(
            endpoint,
            json=sample_log,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        data = response.json()
        
        if data.get('status') == 'success':
            print_success("AI analysis completed successfully!")
            
            analysis = data.get('analysis', {})
            
            # Display analysis sections
            print(f"\n{Fore.CYAN}📊 AI Analysis Result:{Style.RESET_ALL}")
            print(f"{Fore.BLUE}{'─' * 70}{Style.RESET_ALL}")
            
            if analysis.get('full_analysis'):
                full_text = analysis['full_analysis']
                
                # Extract sections
                sections = [
                    ('🔍 WHAT HAPPENED', Fore.BLUE),
                    ('💡 QUICK FIX', Fore.GREEN),
                    ('🛡️ PREVENTION', Fore.YELLOW)
                ]
                
                for section_name, color in sections:
                    if section_name in full_text:
                        start_idx = full_text.find(section_name)
                        end_idx = full_text.find('\n\n', start_idx + len(section_name))
                        if end_idx == -1:
                            end_idx = len(full_text)
                        
                        section_content = full_text[start_idx:end_idx].strip()
                        print(f"\n{color}{section_content}{Style.RESET_ALL}")
            
            print(f"\n{Fore.BLUE}{'─' * 70}{Style.RESET_ALL}")
            return True
        else:
            print_error(f"AI analysis failed: {data.get('message')}")
            
            # Check if it's an API key issue
            if 'API key' in str(data.get('message', '')):
                print_warning("Gemini API key not configured or invalid")
                print_info("Set GEMINI_API_KEY in your .env file")
                print_info("Get a free key at: https://aistudio.google.com/app/apikey")
            
            return False
            
    except requests.exceptions.Timeout:
        print_error("AI analysis timed out (took > 30 seconds)")
        return False
    except Exception as e:
        print_error(f"Failed to test AI analysis: {e}")
        return False

def test_dashboard_availability():
    """Test if dashboard is accessible"""
    print_header("TEST 5: Dashboard Availability")
    
    try:
        response = requests.get(DASHBOARD_URL, timeout=5)
        if response.status_code == 200:
            print_success(f"Dashboard is accessible at {DASHBOARD_URL}")
            print_info("Open in browser to test UI:")
            print_info(f"  {DASHBOARD_URL}")
            print_info("  → Click 'Logs & AI Analysis' tab")
            print_info("  → Scroll to 'Detected Anomalies & Errors'")
            return True
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to dashboard at {DASHBOARD_URL}")
        print_info("Please ensure the dashboard is running:")
        print_info("  cd monitoring/dashboard && python app.py")
        return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def inject_test_errors():
    """Inject multiple test errors into the system"""
    print_header("STEP 0: Injecting Test Errors")
    
    test_errors = [
        {
            "service": "systemd-resolved",
            "message": "Failed to connect to DNS server 8.8.8.8 on TCP port 53. Network unreachable.",
            "level": "ERROR",
            "source": "systemd"
        },
        {
            "service": "docker",
            "message": "Container 'web-server' failed to start: port 8080 already in use",
            "level": "CRITICAL",
            "source": "docker"
        },
        {
            "service": "apache2",
            "message": "SSL certificate for example.com expired on 2025-10-15. HTTPS connections failing.",
            "level": "ERROR",
            "source": "apache"
        },
        {
            "service": "systemd-journald",
            "message": "Journal file size limit reached (100MB). Rotating logs.",
            "level": "WARNING",
            "source": "systemd"
        },
        {
            "service": "cron",
            "message": "Failed to execute backup script /usr/local/bin/backup.sh: Permission denied",
            "level": "ERROR",
            "source": "syslog"
        }
    ]
    
    endpoint = f"{MONITORING_SERVER}/api/test/inject-error"
    injected_count = 0
    
    for error in test_errors:
        try:
            response = requests.post(endpoint, json=error, timeout=5)
            if response.status_code == 200:
                injected_count += 1
                print_success(f"Injected: {error['service']} - {error['level']}")
            else:
                print_warning(f"Failed to inject: {error['service']}")
        except Exception as e:
            print_error(f"Error injecting {error['service']}: {e}")
    
    print(f"\n{Fore.CYAN}📝 Injected {injected_count}/{len(test_errors)} test errors{Style.RESET_ALL}")
    print_info("These errors will now appear in the 'Detected Anomalies & Errors' section")
    print_info(f"View them at: {DASHBOARD_URL} → Logs & AI Analysis tab")
    
    return injected_count > 0

def run_all_tests():
    """Run all tests"""
    print(f"{Fore.MAGENTA}")
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║        🧪 ANOMALIES & ERRORS FEATURE - TEST SUITE 🧪                ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print(f"{Style.RESET_ALL}")
    
    results = {
        'total': 0,
        'passed': 0,
        'failed': 0
    }
    
    # Step 0: Inject test errors first
    if not inject_test_errors():
        print_warning("Failed to inject test errors, but continuing with tests...")
    
    print("\n")  # Add spacing
    
    # Test 1: Server connectivity
    results['total'] += 1
    if test_server_connectivity():
        results['passed'] += 1
    else:
        results['failed'] += 1
        print_error("\nCannot proceed without monitoring server. Exiting.")
        return results
    
    # Test 2: Critical services endpoint
    results['total'] += 1
    success, issues = test_critical_services_endpoint()
    if success:
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Test 3: System logs endpoint (fallback)
    results['total'] += 1
    success, logs = test_system_logs_endpoint()
    if success:
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    # Test 4: AI analysis (use first issue/log if available)
    results['total'] += 1
    sample = None
    if issues:
        sample = issues[0]
    elif logs:
        sample = logs[0]
    
    if test_ai_analysis(sample):
        results['passed'] += 1
    else:
        results['failed'] += 1
        print_warning("AI analysis failed - feature may still work with valid API key")
    
    # Test 5: Dashboard availability
    results['total'] += 1
    if test_dashboard_availability():
        results['passed'] += 1
    else:
        results['failed'] += 1
    
    return results

def print_summary(results):
    """Print test summary"""
    print_header("TEST SUMMARY")
    
    total = results['total']
    passed = results['passed']
    failed = results['failed']
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"Total Tests:   {total}")
    print(f"{Fore.GREEN}Passed:        {passed}{Style.RESET_ALL}")
    print(f"{Fore.RED}Failed:        {failed}{Style.RESET_ALL}")
    print(f"Success Rate:  {success_rate:.1f}%\n")
    
    if success_rate == 100:
        print(f"{Fore.GREEN}{'🎉 ALL TESTS PASSED! 🎉':^70}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}{'The anomalies feature is working perfectly!':^70}{Style.RESET_ALL}\n")
    elif success_rate >= 60:
        print(f"{Fore.YELLOW}{'⚠️  MOST TESTS PASSED ⚠️':^70}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{'Some features may need attention':^70}{Style.RESET_ALL}\n")
    else:
        print(f"{Fore.RED}{'❌ MULTIPLE TESTS FAILED ❌':^70}{Style.RESET_ALL}")
        print(f"{Fore.RED}{'Please check the errors above':^70}{Style.RESET_ALL}\n")
    
    print_info("Next Steps:")
    print("  1. Review any failed tests above")
    print("  2. Ensure all services are running:")
    print("     - Monitoring Server (port 5000)")
    print("     - Dashboard (port 3001)")
    print("  3. Test manually in browser:")
    print(f"     {DASHBOARD_URL}")
    print("")

if __name__ == "__main__":
    try:
        results = run_all_tests()
        print_summary(results)
        
        # Exit with appropriate code
        if results['passed'] == results['total']:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Test interrupted by user{Style.RESET_ALL}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Fore.RED}Unexpected error: {e}{Style.RESET_ALL}")
        sys.exit(1)

