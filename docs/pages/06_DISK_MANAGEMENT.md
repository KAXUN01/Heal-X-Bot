# Disk Management Page

## Description
The Disk Management page provides comprehensive disk space monitoring, cleanup tools, and storage optimization features. It helps prevent disk-full situations and automates space recovery.

## Purpose
- Monitor disk space usage across all partitions
- Provide selective cleanup options
- Find and manage large files
- Analyze directory sizes
- Schedule automatic cleanup tasks

## Features

### 1. Disk Usage Overview
- **Total Space**: Total disk capacity
- **Used Space**: Currently occupied space
- **Free Space**: Available space
- **Usage Percentage**: Visual progress bar with color coding

### 2. Selective Cleanup Options
Checkboxes for different cleanup targets:

| Option | Description | Default |
|--------|-------------|---------|
| **APT Cache** | Clean apt-get cache and autoclean | ✅ Enabled |
| **Journal Logs** | Vacuum journal logs older than N days | ✅ Enabled |
| **Old Log Files** | Delete log files older than N days | ✅ Enabled |
| **Temporary Files** | Clean /tmp and /var/tmp | ❌ Disabled |
| **Docker Cleanup** | Remove unused images, containers, volumes | ❌ Disabled |
| **Snap Packages** | Remove old snap revisions | ❌ Disabled |
| **System Cache** | Drop pagecache, dentries, inodes | ❌ Disabled |

### 3. Cleanup Preview
- Shows estimated space to be freed
- Lists items to be cleaned
- Provides detailed breakdown by category

### 4. Large File Finder
- Lists top 20/50/100 largest files
- Sortable by path, size, modification date
- Quick actions to delete or move files

### 5. Directory Size Analysis
- Analyze any directory path
- Visual size breakdown
- Recursive size calculation

### 6. Cleanup Logs
- Real-time cleanup operation logs
- Historical cleanup records
- Space freed statistics

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/disk/usage` | GET | Get disk usage stats |
| `/api/disk/cleanup/preview` | POST | Preview cleanup results |
| `/api/disk/cleanup/run` | POST | Execute cleanup |
| `/api/disk/large-files` | GET | Find large files |
| `/api/disk/directory-sizes` | GET | Analyze directory |
| `/api/disk/config` | GET/POST | Cleanup configuration |
| `/api/disk/schedule` | POST | Schedule cleanup |

## Cleanup Operations

### APT Cache Cleanup
```bash
apt-get clean
apt-get autoclean
apt-get autoremove
```

### Journal Vacuum
```bash
journalctl --vacuum-time={days}d
```

### Log File Cleanup
```bash
find /var/log -name "*.log" -mtime +{days} -delete
find /var/log -name "*.gz" -mtime +{days} -delete
```

### Docker Prune
```bash
docker system prune -af
docker volume prune -f
docker image prune -af
```

### Snap Cleanup
```bash
snap list --all | while read snapname ver rev tracking publisher notes; do
  if [[ $notes == *disabled* ]]; then
    snap remove "$snapname" --revision="$rev"
  fi
done
```

## Technical Implementation

### Disk Usage Check
```python
import psutil

disk = psutil.disk_usage('/')
return {
    'total': disk.total,
    'used': disk.used,
    'free': disk.free,
    'percent': disk.percent
}
```

### Large File Finder
```python
def find_large_files(path='/', limit=50, min_size_mb=100):
    files = []
    for root, dirs, filenames in os.walk(path):
        for f in filenames:
            filepath = os.path.join(root, f)
            size = os.path.getsize(filepath)
            if size > min_size_mb * 1024 * 1024:
                files.append({'path': filepath, 'size': size})
    return sorted(files, key=lambda x: x['size'], reverse=True)[:limit]
```

### JavaScript Functions
```javascript
loadDiskUsage()          // Fetch disk stats
updateCleanupPreview()   // Generate preview
runCleanup()             // Execute cleanup
loadLargeFiles()         // Find large files
loadDirectorySizes()     // Analyze directory
saveCleanupConfig()      // Save configuration
openScheduleModal()      // Schedule cleanup
```

## Configuration

### Cleanup Config
```json
{
  "disk_threshold": 80,
  "journal_retention_days": 7,
  "log_file_age_days": 7,
  "cleanup_options": {
    "apt_cache": true,
    "journal": true,
    "log_files": true,
    "temp_files": false,
    "docker": false,
    "snap": false,
    "system_cache": false
  }
}
```

### Schedule Options
- Daily at specific time
- Weekly on specific day
- When disk usage exceeds threshold
- Manual only

## User Actions
- Configure cleanup options
- Preview cleanup results
- Run cleanup manually
- Schedule automatic cleanup
- Find and delete large files
- Analyze directory sizes

## Related Pages
- [Overview](01_OVERVIEW.md) - Disk usage metric
- [Processes](05_PROCESSES.md) - Process disk I/O
- [Auto Scaling](10_AUTO_SCALING.md) - Resource management
