# 📋 Critical Log File Feature

## Overview

The Critical Services Monitor now includes a **file-based logging system** that continuously writes all critical system errors (priority 0-3: EMERG, ALERT, CRIT, ERR) to a persistent log file with automatic rotation.

## ✨ Features

### 1. **Continuous Critical Log Collection**
- ✅ Automatically logs all **critical system errors** (journalctl -p 0..3)
- ✅ Uses cursor-based tracking to avoid duplicates
- ✅ Runs every 10 seconds (configurable via monitoring interval)

### 2. **Persistent Log File**
- ✅ Default location: `/var/log/critical_monitor.log`
- ✅ Falls back to `~/critical_monitor.log` if `/var/log` is not writable
- ✅ Human-readable format with timestamps and service information

### 3. **Automatic Log Rotation**
- ✅ Maximum size: **10 MB** (configurable)
- ✅ Automatic truncation when size exceeds limit
- ✅ Keeps last **50%** of logs (most recent entries)
- ✅ Prevents disk space issues

### 4. **Cursor-Based Tracking**
- ✅ Tracks last processed log entry using journalctl cursor
- ✅ State file: `/var/tmp/journalctl_cursor_critical.state`
- ✅ Ensures no duplicate entries
- ✅ Resumes from last position after restart

## 📁 File Format

The log file format is human-readable:

```
[2025-01-20 14:30:15] --- New Critical Errors on hostname ---
Jan 20 14:30:10 hostname nginx[nginx]: CRIT: Nginx service failure detected
Jan 20 14:30:11 hostname docker[docker]: ERR: Container runtime error
----------------------------------------------
[2025-01-20 14:30:25] --- New Critical Errors on hostname ---
...
```

## 🔧 Implementation Details

### Integration

The file logging is automatically integrated into the existing `CriticalServicesMonitor` class:

- **`_init_log_file()`**: Initializes the log file and loads the last cursor
- **`_write_critical_logs_to_file()`**: Writes new critical logs to the file
- **`_maintain_log_file_size()`**: Truncates log file when it exceeds 10 MB
- **`get_log_file_path()`**: Returns the path to the log file

### Monitoring Loop

The file logging runs automatically in the monitoring loop:

```python
def _monitoring_loop(self, interval_seconds: int):
    while self.running:
        self.collect_all_service_logs()
        self.check_service_status()
        # File logging (NEW)
        self._write_critical_logs_to_file()
        self._maintain_log_file_size()
        time.sleep(interval_seconds)
```

## 📊 API Endpoints

### 1. Get Log File Statistics
```http
GET /api/critical-services/statistics
```

Returns statistics including log file information:
```json
{
  "status": "success",
  "statistics": {
    "total_logs": 500,
    "by_category": {...},
    "by_level": {...},
    "log_file": {
      "path": "/var/log/critical_monitor.log",
      "size_bytes": 5242880,
      "size_mb": 5.0,
      "exists": true
    }
  }
}
```

### 2. Get Log File Contents
```http
GET /api/critical-services/log-file?tail_lines=100
```

Returns the last N lines from the log file:
```json
{
  "status": "success",
  "file_path": "/var/log/critical_monitor.log",
  "total_lines": 1250,
  "returned_lines": 100,
  "lines": [
    "[2025-01-20 14:30:15] --- New Critical Errors on hostname ---",
    "Jan 20 14:30:10 hostname nginx[nginx]: CRIT: Nginx service failure detected",
    ...
  ]
}
```

## 🔍 Manual Inspection

You can manually view the log file:

```bash
# View last 50 lines
sudo tail -n 50 /var/log/critical_monitor.log

# Follow in real-time
sudo tail -f /var/log/critical_monitor.log

# View file size
ls -lh /var/log/critical_monitor.log

# Check if rotation occurred
grep "truncated" /var/log/critical_monitor.log
```

## ⚙️ Configuration

You can customize the behavior by modifying `critical_services_monitor.py`:

```python
# In __init__():
self.log_file = '/var/log/critical_monitor.log'  # Log file path
self.state_file = '/var/tmp/journalctl_cursor_critical.state'  # Cursor state file
self.max_log_size = 10 * 1024 * 1024  # 10 MB (adjust as needed)
```

## 🔐 Permissions

The monitor attempts to:
1. Create log file in `/var/log/` with proper permissions (640)
2. Fall back to user's home directory if `/var/log/` is not writable
3. Use existing file if it already exists

For production use, ensure proper permissions:
```bash
sudo chown root:adm /var/log/critical_monitor.log
sudo chmod 640 /var/log/critical_monitor.log
```

## 🚀 Benefits

1. **Persistent History**: All critical errors are preserved even after system restarts
2. **Disk Space Protection**: Automatic rotation prevents log files from growing indefinitely
3. **Easy Access**: Simple text file format for easy analysis and debugging
4. **Zero Configuration**: Works out of the box with sensible defaults
5. **No Duplicates**: Cursor-based tracking ensures each log entry is written only once

## 📝 Notes

- The file logging runs **in addition to** the existing in-memory log storage
- **Logs written to the file are automatically added to the dashboard** - The `_write_critical_logs_to_file()` function now parses logs for both file storage AND dashboard display
- Logs written to the file will appear in the "Critical Errors Only" section
- Duplicate checking ensures logs aren't added twice to `service_logs`
- The API endpoints continue to work with in-memory data
- The file provides a persistent backup and long-term history
- Log rotation is automatic and requires no manual intervention

## 🔄 Differences from Shell Script Approach

This implementation:
- ✅ Integrated directly into Python monitor (no separate cron job needed)
- ✅ Uses Python's exception handling (more robust)
- ✅ Automatically falls back to user directory if no sudo
- ✅ Works seamlessly with existing API endpoints
- ✅ Provides programmatic access via API
- ✅ Shares the same monitoring interval (10 seconds) as service checks

The shell script approach is still valid for standalone use, but this Python implementation provides better integration with the existing system.

