#!/usr/bin/env python3
"""Quick test to verify the issue detection logic works"""

# Simulate the logs we're seeing
test_logs = [
    {
        'level': 'WARNING',
        'category': 'IMPORTANT',
        'service': 'systemd-resolved',
        'message': 'Using degraded feature set UDP instead of TCP for DNS server 172.16.0.21.',
        'timestamp': '2025-10-31T10:00:00',
        'priority': 4
    },
    {
        'level': 'INFO',
        'category': 'IMPORTANT',
        'service': 'cron',
        'message': 'pam_unix(cron:session): session closed for user root',
        'timestamp': '2025-10-31T10:00:00',
        'priority': 6
    }
]

problem_keywords = ['error', 'fail', 'failed', 'exception', 'critical', 'warning', 
                   'timeout', 'crash', 'abort', 'denied', 'refused', 'unavailable',
                   'not found', 'cannot', 'unable', 'broken', 'invalid', 'degraded']

issues = []

for log in test_logs:
    level = log.get('level', '').upper()
    category = log.get('category', '')
    message = (log.get('message', '') or '').lower()
    
    is_error_or_warning = level in ['ERROR', 'WARNING', 'ERR', 'WARN', 'CRITICAL', 'CRIT']
    is_critical_or_important = category in ['CRITICAL', 'IMPORTANT']
    has_problem_keyword = is_critical_or_important and any(keyword in message for keyword in problem_keywords)
    
    if (is_critical_or_important and is_error_or_warning) or has_problem_keyword:
        issue = log.copy()
        if level in ['ERROR', 'ERR', 'CRITICAL', 'CRIT']:
            issue['severity'] = 'CRITICAL' if log.get('priority', 6) <= 2 else 'ERROR'
        elif level in ['WARNING', 'WARN']:
            issue['severity'] = 'WARNING'
        elif has_problem_keyword:
            issue['severity'] = 'WARNING'
        else:
            issue['severity'] = level or 'UNKNOWN'
        issues.append(issue)
        print(f"✅ Found issue: {issue['service']} - {issue['severity']} - {issue['message'][:60]}")

print(f"\nTotal issues found: {len(issues)}")

