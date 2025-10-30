#!/bin/bash

# Automatic Log Cleanup Script
# Keeps log files small and prevents disk space issues

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║                    🧹 LOG CLEANUP UTILITY 🧹                          ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo ""

# Check current log size
echo "📊 Current log directory size:"
du -sh "$LOG_DIR" 2>/dev/null || echo "  Log directory not found"
echo ""

# Function to truncate large log files
truncate_logs() {
    local max_size_mb=$1
    local max_size_bytes=$((max_size_mb * 1024 * 1024))
    
    echo "🔄 Truncating log files larger than ${max_size_mb}MB..."
    
    find "$LOG_DIR" -name "*.log" -type f | while read -r logfile; do
        size=$(stat -f%z "$logfile" 2>/dev/null || stat -c%s "$logfile" 2>/dev/null || echo 0)
        
        if [ "$size" -gt "$max_size_bytes" ]; then
            echo "  ✂️  Truncating: $logfile ($(($size / 1024 / 1024))MB)"
            
            # Keep last 1000 lines
            tail -n 1000 "$logfile" > "$logfile.tmp"
            mv "$logfile.tmp" "$logfile"
        fi
    done
}

# Function to delete old log files
delete_old_logs() {
    local days=$1
    
    echo "🗑️  Deleting log files older than $days days..."
    
    find "$LOG_DIR" -name "*.log.*" -type f -mtime +$days -delete 2>/dev/null || true
    find "$LOG_DIR" -name "*.log.old" -type f -mtime +$days -delete 2>/dev/null || true
}

# Function to compress old logs
compress_old_logs() {
    echo "📦 Compressing old log files..."
    
    find "$LOG_DIR" -name "*.log.*" -type f ! -name "*.gz" -mtime +1 | while read -r logfile; do
        if [ -f "$logfile" ]; then
            echo "  📦 Compressing: $logfile"
            gzip -f "$logfile" 2>/dev/null || true
        fi
    done
}

# Main cleanup
case "${1:-}" in
    --aggressive)
        echo "🚨 AGGRESSIVE CLEANUP MODE"
        truncate_logs 1  # Truncate files > 1MB
        delete_old_logs 1  # Delete files > 1 day
        compress_old_logs
        ;;
    --moderate)
        echo "⚡ MODERATE CLEANUP MODE"
        truncate_logs 5  # Truncate files > 5MB
        delete_old_logs 3  # Delete files > 3 days
        compress_old_logs
        ;;
    *)
        echo "🧹 NORMAL CLEANUP MODE"
        truncate_logs 10  # Truncate files > 10MB
        delete_old_logs 7  # Delete files > 7 days
        compress_old_logs
        ;;
esac

echo ""
echo "✅ Cleanup complete!"
echo ""
echo "📊 New log directory size:"
du -sh "$LOG_DIR" 2>/dev/null || echo "  Log directory not found"
echo ""

# Show largest log files
echo "📋 Largest log files (top 5):"
find "$LOG_DIR" -name "*.log" -type f -exec ls -lh {} \; 2>/dev/null | sort -k5 -hr | head -5 | awk '{print "  " $5 " - " $9}'
echo ""

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║  💡 TIP: Run './cleanup_logs.sh --aggressive' for deep cleanup       ║"
echo "║  💡 Add to cron for automatic cleanup: 0 2 * * * ./cleanup_logs.sh  ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"

