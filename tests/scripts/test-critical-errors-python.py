#!/usr/bin/env python3
"""
Python-based Critical Errors Test Script
Generates critical errors and verifies they appear in the dashboard
"""

import subprocess
import time
import requests
import json
import sys
from datetime import datetime

# Configure requests to be more patient with slow servers
requests.adapters.DEFAULT_TIMEOUT = 30

# Configuration
API_URL = "http://localhost:5001/api/critical-services/issues"
WAIT_TIME = 15  # Wait 15 seconds for monitor to collect
SERVICES_TO_TEST = ["nginx", "docker", "dbus", "test-critical-service"]
SERVICES_TO_STOP = ["nginx", "docker"]  # Only these services will be stopped

def check_api():
    """Check if API is accessible"""
    try:
        # Try with a longer timeout and allow slower responses
        print("   Checking API accessibility...")
        response = requests.get(API_URL, timeout=30)
        response.raise_for_status()
        print("✅ API is accessible")
        return True
    except requests.exceptions.Timeout:
        print(f"❌ Error: API request timed out after 30 seconds")
        print(f"   URL: {API_URL}")
        print("   The server may be overloaded or slow to respond")
        print("   Try checking if the server is running:")
        print("      curl http://localhost:5001/api/health")
        return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Error: Cannot connect to API at {API_URL}")
        print("   Make sure the dashboard server is running on port 5001")
        print("   Check with: curl http://localhost:5001/api/health")
        return False
    except Exception as e:
        print(f"❌ Error: Cannot connect to API at {API_URL}")
        print(f"   Error: {e}")
        print("   Make sure the dashboard server is running on port 5001")
        return False

def get_issue_count():
    """Get current issue count from API"""
    try:
        response = requests.get(API_URL, timeout=30)
        data = response.json()
        return data.get('count', 0)
    except requests.exceptions.Timeout:
        print(f"   ⚠️  Timeout getting issue count (API may be slow)")
        return 0
    except Exception as e:
        print(f"   ⚠️  Error getting issue count: {e}")
        return 0

def generate_critical_log(service_name, message):
    """Generate a CRITICAL priority log for a service"""
    # Use the original message as-is (without adding CRITICAL prefix or timestamp)
    # The dashboard will display severity and timestamp separately
    original_message = message
    
    # Method 1: Use logger command
    try:
        subprocess.run(
            ['logger', '-p', '2', '-t', service_name, original_message],
            check=False,
            capture_output=True,
            timeout=5
        )
    except Exception as e:
        print(f"   Warning: logger failed for {service_name}: {e}")
    
    # Method 2: Use systemd-cat
    try:
        proc = subprocess.Popen(
            ['systemd-cat', '-t', service_name, '-p', 'crit'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        proc.communicate(input=original_message.encode(), timeout=5)
    except Exception as e:
        print(f"   Warning: systemd-cat failed for {service_name}: {e}")

def stop_service(service_name):
    """Attempt to stop a service"""
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', service_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.stdout.strip() == 'active':
            print(f"   → Stopping {service_name} service...")
            subprocess.run(
                ['sudo', 'systemctl', 'stop', service_name],
                check=False,
                capture_output=True,
                timeout=10
            )
            time.sleep(1)
            return True
        else:
            print(f"   → {service_name} is not running, generating logs anyway...")
            return False
    except Exception as e:
        print(f"   → Error checking {service_name}: {e}")
        return False

def verify_service_errors(service_name):
    """Verify errors for a specific service appear in API"""
    try:
        response = requests.get(API_URL, timeout=30)
        data = response.json()
        
        if data.get('status') != 'success':
            print(f"   ⚠️  API returned error status")
            return False
        
        issues = data.get('issues', [])
        service_issues = [i for i in issues if service_name.lower() in str(i).lower()]
        critical_issues = [i for i in service_issues if i.get('severity', '').upper() == 'CRITICAL']
        
        if critical_issues:
            print(f"   ✅ Found {len(critical_issues)} CRITICAL {service_name} error(s)")
            return True
        elif service_issues:
            print(f"   ⚠️  Found {len(service_issues)} {service_name} issue(s) but not marked CRITICAL")
            return False
        else:
            print(f"   ⚠️  No {service_name} errors found yet")
            return False
    except Exception as e:
        print(f"   ❌ Error verifying {service_name}: {e}")
        return False

def main():
    print("=" * 60)
    print("🔴 CRITICAL ERRORS TEST SCRIPT (Python)")
    print("=" * 60)
    print("")
    print("This script will:")
    print("  1. Generate CRITICAL priority logs for various services")
    print(f"  2. Stop services: {', '.join(SERVICES_TO_STOP)} (to generate real errors)")
    print("  3. Wait for monitor to collect logs")
    print("  4. Verify errors appear in API")
    print("")
    
    # Quick check if port is open
    print("🔍 Pre-check: Verifying server is running...")
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('localhost', 5001))
        sock.close()
        if result != 0:
            print("   ⚠️  Port 5001 is not open. Server may not be running.")
            print("   → Try starting the server first:")
            print("      cd monitoring/server && python3 healing_dashboard_api.py")
            response = input("\n   Continue anyway? (y/n): ").lower().strip()
            if response != 'y':
                print("   Exiting...")
                sys.exit(1)
    except Exception as e:
        print(f"   ⚠️  Could not check port: {e}")
    
    print("")
    
    # Check API (with longer timeout)
    print("📡 Checking API connection...")
    if not check_api():
        print("")
        print("💡 Troubleshooting tips:")
        print("   1. Check if server is running:")
        print("      ps aux | grep healing_dashboard_api")
        print("   2. Check if port 5001 is in use:")
        print("      lsof -i :5001")
        print("   3. Try starting the server:")
        print("      cd monitoring/server")
        print("      python3 -m uvicorn healing_dashboard_api:app --host 0.0.0.0 --port 5001")
        sys.exit(1)
    
    # Get baseline
    print("")
    print("📊 Getting baseline issue count...")
    baseline_count = get_issue_count()
    print(f"   Baseline issues: {baseline_count}")
    
    # Generate critical errors
    print("")
    print("=" * 60)
    print("⚠️  GENERATING CRITICAL ERRORS")
    print("=" * 60)
    print("")
    
    stopped_services = []
    
    for service in SERVICES_TO_TEST:
        print(f"📝 Testing: {service}")
        
        # Stop service only if it's in the stop list (nginx and docker only)
        if service in SERVICES_TO_STOP:
            stopped = stop_service(service)
            if stopped:
                stopped_services.append(service)
        
        # Generate critical logs (original messages without prefixes)
        generate_critical_log(service, f"{service} service failure test - Critical error for testing")
        generate_critical_log(service, f"{service} crash detected - This MUST appear in dashboard")
        
        print(f"   ✓ Generated CRITICAL logs for {service}")
        time.sleep(0.3)
    
    # Generate additional generic errors
    print("")
    print("📝 Generating generic CRITICAL errors...")
    for i in range(1, 6):
        generate_critical_log("test-critical-service", f"Generic test error #{i} - MUST appear in Critical Errors Only")
        time.sleep(0.1)
    print("   ✓ Generated additional CRITICAL logs")
    
    # Wait for monitor to collect
    print("")
    print("=" * 60)
    print(f"⏳ Waiting {WAIT_TIME} seconds for monitor to collect logs...")
    print("   (Monitor runs every 10 seconds)")
    print("=" * 60)
    time.sleep(WAIT_TIME)
    
    # Verify errors
    print("")
    print("=" * 60)
    print("🔍 VERIFICATION")
    print("=" * 60)
    print("")
    
    verification_results = {}
    for service in SERVICES_TO_TEST:
        verification_results[service] = verify_service_errors(service)
    
    # Show API summary
    print("")
    print("📊 API Response Summary:")
    try:
        response = requests.get(API_URL, timeout=30)
        data = response.json()
        
        final_count = data.get('count', 0)
        issues = data.get('issues', [])
        
        # Count by severity
        severity_counts = {}
        for issue in issues:
            severity = issue.get('severity', issue.get('level', 'UNKNOWN'))
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        print(f"   Status: {data.get('status')}")
        print(f"   Total Issues: {final_count}")
        print(f"   By Severity: {severity_counts}")
        
        # Show first 5 issues
        if issues:
            print("")
            print("   First 5 issues:")
            for issue in issues[:5]:
                service = issue.get('service', 'unknown')
                severity = issue.get('severity', issue.get('level', 'UNKNOWN'))
                message = (issue.get('message', '')[:60] + '...') if len(issue.get('message', '')) > 60 else issue.get('message', '')
                print(f"     - [{severity}] {service}: {message}")
    except Exception as e:
        print(f"   ❌ Error getting API summary: {e}")
    
    # Final verification
    print("")
    print("=" * 60)
    print("📋 FINAL RESULTS")
    print("=" * 60)
    print("")
    
    final_count = get_issue_count()
    print(f"   Baseline issues: {baseline_count}")
    print(f"   Final issues: {final_count}")
    
    new_issues = final_count - baseline_count
    
    if new_issues > 0:
        print("")
        print("✅ SUCCESS: New critical errors were detected!")
        print(f"   → Issues increased by {new_issues}")
        print("")
        print("✅ The 'Critical Errors Only' section should now show:")
        print("   → New CRITICAL severity issues")
        print("   → Check your dashboard at http://localhost:5001")
    else:
        print("")
        print("⚠️  WARNING: No new issues detected")
        print("   → This could mean:")
        print("     1. Monitor hasn't collected logs yet (wait another 10 seconds)")
        print("     2. Logs are being filtered out")
        print("     3. Services weren't actually stopped")
        print("")
        print("   → Check the dashboard manually and look at server logs")
    
    # Show verification summary
    print("")
    print("Verification by service:")
    for service, verified in verification_results.items():
        status = "✅ PASS" if verified else "⚠️  NOT FOUND"
        print(f"   {service}: {status}")
    
    # Restart services if needed
    if stopped_services:
        print("")
        print("=" * 60)
        restart = input("Restart stopped services? (y/n): ").lower().strip()
        if restart == 'y':
            print("")
            print("🔄 Restarting stopped services...")
            for service in stopped_services:
                try:
                    subprocess.run(
                        ['sudo', 'systemctl', 'start', service],
                        check=False,
                        capture_output=True,
                        timeout=10
                    )
                    print(f"   ✓ Restarted {service}")
                except Exception as e:
                    print(f"   ⚠️  Could not restart {service}: {e}")
    
    print("")
    print("=" * 60)
    print("✅ Test complete!")
    print("=" * 60)
    print("")
    print("Next steps:")
    print("1. Open dashboard: http://localhost:5001")
    print("2. Scroll to 'Critical Errors Only' section")
    print("3. Verify errors are displayed")
    print("4. Check log file: tail -n 50 ~/critical_monitor.log")
    print("")

if __name__ == "__main__":
    main()

