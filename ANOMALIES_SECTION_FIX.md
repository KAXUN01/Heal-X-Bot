# Anomalies Section Fix Summary

## Issue
The "Detected Anomalies & Errors" section was not showing any output even though logs were being collected.

## Root Cause
The `get_critical_issues()` function was too restrictive:
- Only included logs from **CRITICAL** category services
- Only included **ERROR** and **WARNING** levels
- Ignored important issues from **IMPORTANT** category services

## Solution
Updated `monitoring/server/critical_services_monitor.py` to:

1. **Include IMPORTANT category**: Now includes ERROR/WARNING from both CRITICAL and IMPORTANT categories
2. **Smart keyword detection**: Includes logs with problem keywords (error, fail, degraded, etc.) even from INFO level
3. **Better severity mapping**: Properly maps levels to severity (ERROR → CRITICAL/ERROR, WARNING → WARNING)

## Changes Made

### File: `monitoring/server/critical_services_monitor.py`

**Function: `get_critical_issues()`**

**Before:**
```python
if (log.get('category') == 'CRITICAL' and 
    log.get('level') in ['ERROR', 'WARNING']):
```

**After:**
```python
# Include ERROR and WARNING from CRITICAL and IMPORTANT categories
is_error_or_warning = level in ['ERROR', 'WARNING', 'ERR', 'WARN', 'CRITICAL', 'CRIT']
is_critical_or_important = category in ['CRITICAL', 'IMPORTANT']

# Also include logs with problem keywords
has_problem_keyword = is_critical_or_important and any(keyword in message for keyword in problem_keywords)

if (is_critical_or_important and is_error_or_warning) or has_problem_keyword:
```

### File: `monitoring/dashboard/static/healing-dashboard.html`

1. **Added auto-refresh**: Anomalies refresh every 30 seconds
2. **Added initial load**: Anomalies load on page load
3. **Better error handling**: Shows user-friendly error messages
4. **Improved compatibility**: Handles both `severity` and `level` fields

## How to Apply

1. **Restart the dashboard server** to load the updated code:
   ```bash
   # Stop current server (Ctrl+C if running in foreground)
   # Then restart:
   cd /home/cdrditgis/Documents/Healing-bot
   source venv/bin/activate
   python3 monitoring/server/healing_dashboard_api.py
   ```

2. **Verify it's working**:
   ```bash
   # Test the endpoint
   curl http://localhost:5001/api/critical-services/issues
   
   # Or use the test script
   python3 test_anomalies_section.py
   ```

## What Will Now Appear

The section will now show:
- ✅ **ERROR** logs from CRITICAL category services (e.g., Docker, systemd-journald, dbus)
- ✅ **WARNING** logs from CRITICAL category services
- ✅ **ERROR** logs from IMPORTANT category services (e.g., cron, rsyslog, systemd-resolved)
- ✅ **WARNING** logs from IMPORTANT category services (e.g., systemd-resolved DNS issues)
- ✅ **INFO** logs with problem keywords (error, fail, degraded, timeout, etc.)

## Example Issues That Will Now Show

1. **systemd-resolved WARNING**: "Using degraded feature set UDP instead of TCP for DNS server"
2. **Docker errors**: Container failures, image pull errors
3. **systemd-journald errors**: Logging system failures
4. **Service restart failures**: Any ERROR/WARNING from critical services

## Testing

Run the test script to verify:
```bash
python3 test_anomalies_section.py
```

Expected output: Issues detected from systemd-resolved and other services.

