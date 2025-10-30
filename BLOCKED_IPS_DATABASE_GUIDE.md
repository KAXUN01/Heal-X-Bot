# Blocked IPs Database - Complete Implementation Guide 🛡️

## Overview

The Healing Bot Dashboard now includes a comprehensive blocked IPs database system that:
- ✅ Stores blocked IP addresses persistently in SQLite database
- ✅ Tracks attack counts, threat levels, and timestamps
- ✅ Provides block/unblock functionality with audit trail
- ✅ Shows block status in the DDoS Detection tab
- ✅ Supports manual and automatic IP management

---

## Features

### 1. Database Storage ✅
- SQLite database at `monitoring/server/data/blocked_ips.db`
- Persistent storage of all blocked/unblocked IPs
- Complete audit trail with history table

### 2. IP Management ✅
- Block IPs with metadata (attack count, threat level, attack type)
- Unblock IPs with reason tracking
- Update attack counts for repeat offenders
- View detailed IP information and history

### 3. Dashboard Integration ✅
- Real-time block status display
- Block/Unblock buttons in Top Source IPs table
- Visual indicators for blocked IPs
- Toast notifications for actions

### 4. API Endpoints ✅
- Complete REST API for IP management
- Statistics and reporting
- CSV export functionality
- Cleanup for old records

---

## Database Schema

### Table: `blocked_ips`

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| ip_address | TEXT | IP address (unique) |
| attack_count | INTEGER | Number of attacks detected |
| threat_level | TEXT | Critical/High/Medium/Low |
| attack_type | TEXT | Type of attack (TCP SYN, UDP Flood, etc) |
| first_seen | TIMESTAMP | First detection timestamp |
| last_seen | TIMESTAMP | Most recent detection |
| blocked_at | TIMESTAMP | When IP was blocked |
| blocked_by | TEXT | Who/what blocked the IP |
| reason | TEXT | Reason for blocking |
| is_blocked | BOOLEAN | Current block status (1=blocked, 0=unblocked) |
| unblocked_at | TIMESTAMP | When IP was unblocked |
| unblocked_by | TEXT | Who unblocked the IP |
| notes | TEXT | Additional notes |

### Table: `blocked_ips_history`

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| ip_address | TEXT | IP address |
| action | TEXT | Action taken (blocked/unblocked/updated) |
| timestamp | TIMESTAMP | When action occurred |
| performed_by | TEXT | Who performed the action |
| reason | TEXT | Reason for action |

---

## API Endpoints

### 1. Block an IP
**POST** `/api/blocking/block`

**Request:**
```json
{
  "ip": "192.0.2.50",
  "attack_count": 5,
  "threat_level": "High",
  "attack_type": "TCP SYN Flood",
  "reason": "Multiple DDoS attacks detected",
  "blocked_by": "dashboard"
}
```

**Response:**
```json
{
  "success": true,
  "ip": "192.0.2.50",
  "message": "IP blocked successfully"
}
```

### 2. Unblock an IP
**POST** `/api/blocked-ips/unblock`

**Request:**
```json
{
  "ip": "192.0.2.50",
  "unblocked_by": "admin",
  "reason": "False positive - legitimate traffic"
}
```

**Response:**
```json
{
  "success": true,
  "message": "IP 192.0.2.50 unblocked successfully",
  "ip": "192.0.2.50"
}
```

### 3. Get Blocked IPs List
**GET** `/api/blocked-ips?include_unblocked=false`

**Response:**
```json
{
  "success": true,
  "blocked_ips": [
    {
      "id": 1,
      "ip_address": "192.0.2.50",
      "attack_count": 5,
      "threat_level": "High",
      "attack_type": "TCP SYN Flood",
      "first_seen": "2025-10-30T12:00:00",
      "last_seen": "2025-10-30T12:15:00",
      "blocked_at": "2025-10-30T12:15:30",
      "blocked_by": "dashboard",
      "reason": "Multiple DDoS attacks detected",
      "is_blocked": 1
    }
  ],
  "count": 1
}
```

### 4. Get IP Details
**GET** `/api/blocked-ips/{ip_address}`

**Response:**
```json
{
  "success": true,
  "ip_info": {
    "id": 1,
    "ip_address": "192.0.2.50",
    "attack_count": 5,
    "threat_level": "High",
    ...
  },
  "history": [
    {
      "action": "blocked",
      "timestamp": "2025-10-30T12:15:30",
      "performed_by": "dashboard",
      "reason": "Multiple attacks"
    }
  ]
}
```

### 5. Get Statistics
**GET** `/api/blocked-ips/statistics`

**Response:**
```json
{
  "success": true,
  "statistics": {
    "total_blocked": 5,
    "total_unblocked": 2,
    "total_attacks": 47,
    "by_threat_level": {
      "Critical": 2,
      "High": 2,
      "Medium": 1
    }
  }
}
```

### 6. Cleanup Old Records
**POST** `/api/blocked-ips/cleanup`

Removes unblocked records older than specified days (default: 90)

**Response:**
```json
{
  "success": true,
  "message": "Cleaned up 5 old records",
  "deleted_count": 5
}
```

### 7. Export to CSV
**POST** `/api/blocked-ips/export`

```json
{
  "filepath": "blocked_ips_export.csv"
}
```

---

## Dashboard UI Changes

### Top Source IPs Table

The table now shows:

1. **Block Status Badge**
   - 🚫 BLOCKED badge for currently blocked IPs
   - Green background for active blocks

2. **Dynamic Buttons**
   - **Block** button (red) for unblocked IPs
   - **Unblock** button (green) for blocked IPs

3. **Real-time Updates**
   - Fetches block status from database every refresh
   - Shows accurate "Last Seen" timestamps from database
   - Updates automatically on block/unblock actions

### Example Table Rows

**Unblocked IP:**
```html
| IP Address    | Attacks | Last Seen  | Threat | Status |
|---------------|---------|------------|--------|--------|
| 192.168.1.100 | 12      | Just now   | Critical | [Block] |
```

**Blocked IP:**
```html
| IP Address    | Attacks | Last Seen       | Threat | Status         |
|---------------|---------|-----------------|--------|----------------|
| 192.168.1.100 | 12      | 10/30/25 12:15  | Critical | [Unblock] 🚫 BLOCKED |
```

### Notifications

Toast notifications appear for all actions:
- ✅ **Green**: Successful block/unblock
- ❌ **Red**: Failed operation
- ℹ️ **Blue**: Information messages

---

## Usage Examples

### Scenario 1: Block a High-Threat IP

1. Navigate to **🛡️ DDoS Detection** tab
2. Find the IP in the "Top Source IPs" table
3. Click **Block** button
4. Confirm the action in the dialog
5. See success notification
6. IP row updates to show 🚫 BLOCKED status

### Scenario 2: Unblock a False Positive

1. Find the blocked IP in the table (shows "BLOCKED" badge)
2. Click **Unblock** button
3. Confirm the action
4. See success notification
5. IP can now access the system again

### Scenario 3: View IP History

Use API to get detailed history:
```bash
curl http://localhost:5001/api/blocked-ips/192.0.2.50
```

### Scenario 4: Export Blocked IPs

```bash
curl -X POST http://localhost:5001/api/blocked-ips/export \
  -H "Content-Type: application/json" \
  -d '{"filepath": "my_blocked_ips.csv"}'
```

---

## Configuration

### Database Location

Default: `monitoring/server/data/blocked_ips.db`

To change, update in `healing_dashboard_api.py`:
```python
blocked_ips_db = BlockedIPsDatabase("path/to/your/database.db")
```

### Sudo Requirements

For iptables blocking to work, the user running the dashboard needs sudo permissions:

```bash
# Add to /etc/sudoers (use visudo)
your_user ALL=(ALL) NOPASSWD: /sbin/iptables
```

Or run the dashboard with sudo (not recommended):
```bash
sudo python3 monitoring/server/healing_dashboard_api.py
```

---

## Testing

### Run Test Suite

```bash
cd /home/cdrditgis/Documents/Healing-bot
python3 test-blocked-ips.py
```

### Manual Testing

1. **Block an IP:**
```bash
curl -X POST http://localhost:5001/api/blocking/block \
  -H "Content-Type: application/json" \
  -d '{
    "ip": "192.0.2.100",
    "attack_count": 5,
    "threat_level": "High",
    "attack_type": "TCP SYN Flood",
    "reason": "Testing block functionality"
  }'
```

2. **Check blocked IPs:**
```bash
curl http://localhost:5001/api/blocked-ips
```

3. **Unblock the IP:**
```bash
curl -X POST http://localhost:5001/api/blocked-ips/unblock \
  -H "Content-Type: application/json" \
  -d '{
    "ip": "192.0.2.100",
    "unblocked_by": "admin",
    "reason": "Testing complete"
  }'
```

---

## Database Management

### View Database Contents

```bash
sqlite3 monitoring/server/data/blocked_ips.db

# List tables
.tables

# View blocked IPs
SELECT * FROM blocked_ips;

# View history
SELECT * FROM blocked_ips_history ORDER BY timestamp DESC LIMIT 10;

# Get statistics
SELECT 
  threat_level, 
  COUNT(*) as count,
  SUM(attack_count) as total_attacks
FROM blocked_ips 
WHERE is_blocked = 1 
GROUP BY threat_level;
```

### Backup Database

```bash
cp monitoring/server/data/blocked_ips.db \
   monitoring/server/data/blocked_ips_backup_$(date +%Y%m%d).db
```

### Reset Database

```bash
rm monitoring/server/data/blocked_ips.db
# Restart server to recreate empty database
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Browser/Dashboard                         │
│              (healing-dashboard.html)                        │
└─────────────┬───────────────────────────────────────────────┘
              │
              │ REST API (Block/Unblock/Get IPs)
              ↓
┌─────────────────────────────────────────────────────────────┐
│            Healing Dashboard API Server                      │
│          (healing_dashboard_api.py)                          │
│                                                              │
│  ┌────────────────┐         ┌────────────────────┐         │
│  │  block_ip()    │◄───────►│  BlockedIPsDatabase│         │
│  │  unblock_ip()  │         │   (blocked_ips_db  │         │
│  └────────┬───────┘         │       .py)         │         │
│           │                 └──────────┬─────────┘         │
│           │                            │                    │
│           ↓                            ↓                    │
│  ┌────────────────┐         ┌──────────────────┐          │
│  │  iptables      │         │  SQLite Database │          │
│  │  (firewall)    │         │  blocked_ips.db  │          │
│  └────────────────┘         └──────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

---

## Files Modified/Created

### New Files
1. **`monitoring/server/blocked_ips_db.py`** - Database manager class
2. **`test-blocked-ips.py`** - Test suite for blocked IPs functionality
3. **`BLOCKED_IPS_DATABASE_GUIDE.md`** - This documentation

### Modified Files
1. **`monitoring/server/healing_dashboard_api.py`**
   - Added database integration
   - Updated `block_ip()` and `unblock_ip()` functions
   - Added 6 new API endpoints for IP management

2. **`monitoring/dashboard/static/healing-dashboard.html`**
   - Updated `updateSourceIpsTable()` to show block status
   - Added `blockIP()` function with parameters
   - Added `unblockIP()` function
   - Added `showNotification()` for user feedback
   - Added CSS animations for notifications

---

## Benefits

### 1. Persistence ✅
- IPs remain blocked across server restarts
- Complete history of all block/unblock actions
- No data loss

### 2. Audit Trail ✅
- Who blocked/unblocked each IP
- When actions were performed
- Why actions were taken

### 3. Intelligence ✅
- Track attack patterns per IP
- Identify repeat offenders
- Calculate threat levels

### 4. Flexibility ✅
- Easy to unblock false positives
- Manual override capability
- Automated blocking supported

### 5. Reporting ✅
- Export to CSV for analysis
- Statistics and metrics
- Historical trends

---

## Troubleshooting

### Issue: IPs not actually blocked

**Cause:** iptables requires sudo permissions

**Solution:**
```bash
# Option 1: Add sudo permissions for iptables
sudo visudo
# Add: your_user ALL=(ALL) NOPASSWD: /sbin/iptables

# Option 2: Run dashboard with sudo (not recommended)
sudo python3 monitoring/server/healing_dashboard_api.py
```

### Issue: Database locked error

**Cause:** Multiple processes accessing database

**Solution:** Ensure only one dashboard instance is running:
```bash
pkill -f healing_dashboard_api
```

### Issue: Block button doesn't update

**Cause:** Frontend not refreshing data

**Solution:** 
1. Clear browser cache
2. Check browser console for errors
3. Verify API endpoints are responding

### Issue: Can't see blocked IPs

**Cause:** Database query filtering out results

**Solution:** Use `include_unblocked=true` parameter:
```bash
curl 'http://localhost:5001/api/blocked-ips?include_unblocked=true'
```

---

## Security Considerations

### 1. Authentication
- Add authentication to API endpoints in production
- Protect unblock operations with admin privileges

### 2. Rate Limiting
- Implement rate limiting on block/unblock endpoints
- Prevent API abuse

### 3. Input Validation
- Validate IP address format
- Sanitize all inputs

### 4. Audit Logging
- All actions are logged in `blocked_ips_history` table
- Review logs regularly

### 5. Database Security
- Restrict database file permissions
- Regular backups
- Consider encryption for sensitive data

---

## Future Enhancements

### Planned Features
1. **Automatic Expiration** - Auto-unblock after specified time
2. **Whitelist** - Protect IPs from being blocked
3. **Geolocation** - Show country/region for IPs
4. **Reputation System** - Integration with IP reputation services
5. **Bulk Operations** - Block/unblock multiple IPs at once
6. **Email Alerts** - Notify on critical blocks
7. **Advanced Filtering** - Search and filter blocked IPs
8. **Dashboard Widget** - Blocked IPs summary on overview page

---

## API Client Examples

### Python Client

```python
import requests

BASE_URL = "http://localhost:5001"

def block_ip(ip, threat_level="High", attack_count=1):
    response = requests.post(
        f"{BASE_URL}/api/blocking/block",
        json={
            "ip": ip,
            "attack_count": attack_count,
            "threat_level": threat_level,
            "reason": f"Automated block - {threat_level} threat"
        }
    )
    return response.json()

def unblock_ip(ip, reason="Manual unblock"):
    response = requests.post(
        f"{BASE_URL}/api/blocked-ips/unblock",
        json={
            "ip": ip,
            "unblocked_by": "script",
            "reason": reason
        }
    )
    return response.json()

# Usage
result = block_ip("192.0.2.100", "Critical", 10)
print(result)
```

### Bash Script

```bash
#!/bin/bash
# block_ip.sh

IP=$1
THREAT=${2:-"Medium"}
COUNT=${3:-1}

curl -X POST http://localhost:5001/api/blocking/block \
  -H "Content-Type: application/json" \
  -d "{
    \"ip\": \"$IP\",
    \"threat_level\": \"$THREAT\",
    \"attack_count\": $COUNT,
    \"reason\": \"Blocked via script\"
  }"
```

Usage:
```bash
./block_ip.sh 192.0.2.100 High 5
```

---

## Conclusion

The Blocked IPs Database system provides a robust, persistent solution for managing malicious IP addresses with complete audit trails and easy unblock capability. The integration with the dashboard provides a seamless user experience for security operations.

**Status: ✅ Fully Functional**

**Database Location:** `monitoring/server/data/blocked_ips.db`

**Test Suite:** `test-blocked-ips.py`

**Documentation:** This file

For questions or issues, check the troubleshooting section or review the API endpoint logs.

---

**Last Updated:** October 30, 2025  
**Version:** 1.0.0  
**Status:** Production Ready ✅

