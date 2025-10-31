#!/usr/bin/env python3
"""
Debug script to check what critical issues are being returned by the API
"""

import requests
import json
import sys

def debug_critical_issues():
    """Debug the critical issues endpoint"""
    
    url = "http://localhost:5000/api/critical-services/issues"
    
    print("=" * 60)
    print("🔍 DEBUGGING CRITICAL ISSUES ENDPOINT")
    print("=" * 60)
    print(f"\nFetching from: {url}\n")
    
    try:
        response = requests.get(url, timeout=5)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Error: {response.text}")
            return
        
        data = response.json()
        print(f"\nResponse Status: {data.get('status', 'unknown')}")
        print(f"Total Issues: {data.get('count', 0)}")
        
        issues = data.get('issues', [])
        
        if not issues:
            print("\n❌ No issues returned!")
            print("\nThis could mean:")
            print("  1. No critical services are generating errors")
            print("  2. The monitor hasn't collected any logs yet")
            print("  3. The logs don't match the CRITICAL criteria")
            return
        
        print(f"\n✅ Found {len(issues)} issues!")
        print("\n" + "=" * 60)
        print("DETAILED ISSUE ANALYSIS")
        print("=" * 60)
        
        for i, issue in enumerate(issues[:5], 1):  # Show first 5
            print(f"\n--- Issue #{i} ---")
            print(f"Service: {issue.get('service', 'N/A')}")
            print(f"Category: {issue.get('category', 'N/A')}")
            print(f"Level: {issue.get('level', 'N/A')}")
            print(f"Severity: {issue.get('severity', 'N/A')}")
            print(f"Priority: {issue.get('priority', 'N/A')}")
            print(f"Timestamp: {issue.get('timestamp', 'N/A')}")
            print(f"Message: {issue.get('message', 'N/A')[:100]}...")
            
            # Check if this would pass the frontend filter
            severity = (issue.get('severity') or issue.get('level') or '').upper()
            priority = issue.get('priority', 6)
            
            passes_filter = (
                severity == 'CRITICAL' or 
                severity == 'CRIT' or 
                priority <= 2
            )
            
            print(f"✓ Passes frontend filter: {passes_filter}")
            if not passes_filter:
                print(f"  ⚠️  This issue would be filtered out!")
        
        # Count by severity
        severity_counts = {}
        for issue in issues:
            severity = issue.get('severity', issue.get('level', 'UNKNOWN'))
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        print("\n" + "=" * 60)
        print("SEVERITY BREAKDOWN")
        print("=" * 60)
        for severity, count in severity_counts.items():
            print(f"  {severity}: {count}")
        
        # Count how many would pass the filter
        passing_count = sum(
            1 for issue in issues
            if (issue.get('severity', '').upper() in ['CRITICAL', 'CRIT']) or
               (issue.get('priority', 6) <= 2)
        )
        
        print(f"\nIssues that pass CRITICAL filter: {passing_count} / {len(issues)}")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API server!")
        print("   Make sure the server is running on port 5000")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_critical_issues()

