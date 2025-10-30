# Log Management & Disk Space Optimization Guide

## Overview

Your Healing-Bot now has **automatic log management** to prevent log files from consuming disk space!

## 🎯 What Has Been Optimized

### 1. **Automatic Log Rotation**
- Each log file is limited to **5 MB**
- Keeps **3 backup files** (total: 20 MB per service)
- Old logs are automatically compressed
- Very old logs are deleted

### 2. **Memory Optimization**
- System logs in memory: **1,000 logs** (reduced from 10,000)
- Only keeps recent logs in RAM
- Older logs are automatically discarded

### 3. **Collection Limits**
- Docker: Only last **10 lines** per container (reduced from 50)
- systemd: Only last **20 entries** (reduced from 100)
- Collection interval: **30 seconds**

### 4. **Automatic Cleanup**
- Old log files deleted after **7 days**
- Compressed logs saved for archival
- Manual cleanup script available

## 📊 Current Disk Usage

```bash
# Check current log size
du -sh logs/

# List largest log files
ls -lh logs/*.log
```

**Current Status:** ~260KB (very small!)

**Maximum Expected:** ~100MB total (with all services running for weeks)

## 🧹 Manual Cleanup

### Run Cleanup Script

```bash
# Normal cleanup (truncate files > 10MB, delete logs > 7 days)
./cleanup_logs.sh

# Moderate cleanup (truncate files > 5MB, delete logs > 3 days)
./cleanup_logs.sh --moderate

# Aggressive cleanup (truncate files > 1MB, delete logs > 1 day)
./cleanup_logs.sh --aggressive
```

### What the Cleanup Script Does:

1. ✂️  **Truncates large log files** - Keeps only last 1000 lines
2. 🗑️  **Deletes old rotated logs** - Removes files older than threshold
3. 📦 **Compresses old logs** - Saves disk space (gzip compression)
4. 📊 **Shows before/after sizes** - Visual feedback

## ⚙️ Configuration

Edit `log_config.json` to customize:

```json
{
  "log_rotation": {
    "max_file_size_mb": 5,      // Change to 10 for larger logs
    "backup_count": 3,           // Change to 5 for more backups
    "auto_cleanup_days": 7       // Change to 30 for longer retention
  },
  "memory_limits": {
    "system_logs_in_memory": 1000,  // Increase for more logs in RAM
    "max_log_entry_size_bytes": 10240
  },
  "collection_settings": {
    "docker_tail_lines": 10,     // Increase for more Docker logs
    "systemd_tail_lines": 20,    // Increase for more systemd logs
    "collection_interval_seconds": 30  // Increase to reduce frequency
  }
}
```

## 🔄 Automatic Rotation

Log files automatically rotate when they reach 5 MB:

```
dashboard.log           (current file, 5 MB)
dashboard.log.1         (1st backup, 5 MB)
dashboard.log.2         (2nd backup, 5 MB)
dashboard.log.3         (3rd backup, 5 MB)
```

**Total space per service:** 5 MB × 4 = 20 MB

## 📅 Schedule Automatic Cleanup

Add to cron for daily cleanup at 2 AM:

```bash
# Edit crontab
crontab -e

# Add this line:
0 2 * * * cd /home/cdrditgis/Documents/Healing-bot && ./cleanup_logs.sh
```

Or weekly cleanup on Sunday at 3 AM:

```bash
0 3 * * 0 cd /home/cdrditgis/Documents/Healing-bot && ./cleanup_logs.sh --moderate
```

## 💡 Best Practices

### 1. **Monitor Disk Space**

```bash
# Check disk usage
df -h

# Check log directory size
du -sh logs/

# Find largest files
find logs/ -type f -exec ls -lh {} \; | sort -k5 -hr | head -10
```

### 2. **Regular Cleanup**

Run cleanup weekly or monthly depending on usage:

```bash
# Weekly
./cleanup_logs.sh

# Monthly with aggressive mode
./cleanup_logs.sh --aggressive
```

### 3. **Adjust Collection Frequency**

If logs grow too fast, increase collection interval:

Edit `monitoring/server/system_log_collector.py`:
```python
system_log_collector.start_collection(interval_seconds=60)  # Changed from 30 to 60
```

### 4. **Reduce Docker Log Lines**

Edit `monitoring/server/system_log_collector.py`:
```python
['docker', 'logs', '--tail', '5', '--timestamps', container]  # Changed from 10 to 5
```

## 📈 Disk Space Breakdown

### Per Service (with rotation):
- Dashboard: ~20 MB max
- Model API: ~20 MB max
- Monitoring Server: ~20 MB max
- Network Analyzer: ~20 MB max
- Incident Bot: ~20 MB max

### Total Maximum:
- **Service logs:** ~100 MB
- **System logs (in memory):** ~10 MB
- **Compressed archives:** ~50 MB (if kept)

**Grand Total:** ~160 MB maximum

## 🚨 Emergency Cleanup

If disk space is critically low:

```bash
# 1. Immediate aggressive cleanup
./cleanup_logs.sh --aggressive

# 2. Delete all old rotated logs
find logs/ -name "*.log.[0-9]" -delete
find logs/ -name "*.log.*.gz" -delete

# 3. Truncate current logs to 100 lines
for log in logs/*.log; do
    tail -n 100 "$log" > "$log.tmp" && mv "$log.tmp" "$log"
done

# 4. Clear system log cache
curl -X POST http://localhost:5000/api/system-logs/clear-cache
```

## 🔍 Monitoring Log Growth

### Real-time monitoring:

```bash
# Watch log directory size
watch -n 5 'du -sh logs/'

# Monitor specific log file
tail -f logs/monitoring-server.log

# Check log rotation status
ls -lh logs/*.log*
```

### API endpoint for log stats:

```bash
# Get system log statistics
curl http://localhost:5000/api/system-logs/statistics | jq '.statistics'
```

## 🎛️ Advanced Configuration

### Disable Specific Log Sources

If a source generates too many logs, disable it:

Edit `monitoring/server/system_log_collector.py`:
```python
self.log_sources = {
    'docker': {'enabled': True, 'parser': self.parse_docker_logs},
    'syslog': {'enabled': False, 'parser': self.parse_syslog},  # Disabled
    'systemd': {'enabled': True, 'parser': self.parse_systemd_journal},
}
```

### Reduce In-Memory Storage

Edit `monitoring/server/system_log_collector.py`:
```python
self.max_logs = 500  # Reduced from 1000 to 500
```

### Change Log Level

Reduce verbosity by changing log level:

```python
import logging
logging.basicConfig(level=logging.WARNING)  # Only warnings and errors
```

## 📋 Log Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│                   LOG LIFECYCLE                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Log Entry Created                                        │
│     ↓                                                        │
│  2. Written to file.log                                      │
│     ↓                                                        │
│  3. File reaches 5 MB                                        │
│     ↓                                                        │
│  4. Rotated to file.log.1                                    │
│     ↓                                                        │
│  5. After 24 hours → Compressed to file.log.1.gz            │
│     ↓                                                        │
│  6. After 7 days → Deleted                                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## ✅ Summary of Improvements

| Aspect | Before | After | Savings |
|--------|--------|-------|---------|
| System logs in RAM | 10,000 | 1,000 | 90% |
| Docker tail lines | 50 | 10 | 80% |
| systemd tail lines | 100 | 20 | 80% |
| Max file size | Unlimited | 5 MB | ∞ |
| Log retention | Forever | 7 days | Significant |
| Auto cleanup | Manual | Automatic | N/A |

## 🛠️ Troubleshooting

### Logs still growing too fast?

1. Check which service is logging heavily:
   ```bash
   find logs/ -name "*.log" -exec ls -lh {} \; | sort -k5 -hr
   ```

2. Reduce that service's log level or tail lines

3. Run aggressive cleanup:
   ```bash
   ./cleanup_logs.sh --aggressive
   ```

### Need to keep logs longer?

Edit `log_config.json`:
```json
{
  "log_rotation": {
    "auto_cleanup_days": 30  // Keep for 30 days instead of 7
  }
}
```

### Want to archive logs?

Before cleanup, copy to archive:
```bash
# Create archive
mkdir -p archives/logs-$(date +%Y-%m-%d)
cp -r logs/* archives/logs-$(date +%Y-%m-%d)/

# Then run cleanup
./cleanup_logs.sh
```

## 📞 Quick Reference

```bash
# Check log size
du -sh logs/

# Run cleanup
./cleanup_logs.sh

# Aggressive cleanup
./cleanup_logs.sh --aggressive

# View largest logs
ls -lh logs/*.log | sort -k5 -hr

# Truncate specific log
tail -n 500 logs/dashboard.log > logs/dashboard.log.tmp && mv logs/dashboard.log.tmp logs/dashboard.log

# Delete old backups
find logs/ -name "*.log.[0-9]" -mtime +7 -delete
```

---

**Your logs are now optimized and won't fill up your disk! 🎉**

