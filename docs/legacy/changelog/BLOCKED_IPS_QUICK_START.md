# Blocked IPs Database - Quick Start 🚀

## ✅ Feature is LIVE and Working!

Your Healing Bot Dashboard now has a complete blocked IPs database system!

---

## 🎯 What You Can Do Now

### 1. View Block Status
- Go to: **http://localhost:5001**
- Click: **🛡️ DDoS Detection** tab
- See: "Top Source IPs" table with block status

### 2. Block an IP
- Find IP in the table
- Click **[Block]** button (red)
- Confirm action
- See ✅ success notification
- IP now shows **🚫 BLOCKED** badge

### 3. Unblock an IP
- Find blocked IP (has **🚫 BLOCKED** badge)
- Click **[Unblock]** button (green)
- Confirm action
- See ✅ success notification
- IP is now unblocked

---

## 📊 What's in the Database

### IP Information Stored:
- IP Address
- Attack Count (how many attacks)
- Threat Level (Critical/High/Medium/Low)
- Attack Type (TCP SYN Flood, UDP Flood, etc.)
- First Seen timestamp
- Last Seen timestamp
- Blocked At timestamp
- Who blocked it
- Why it was blocked
- Block status (blocked/unblocked)
- Unblock information (when/who/why)

### Audit Trail:
Every block/unblock action is logged with:
- What happened
- When it happened
- Who did it
- Why they did it

---

## 🔌 API Examples

### Block an IP
```bash
curl -X POST http://localhost:5001/api/blocking/block \
  -H "Content-Type: application/json" \
  -d '{
    "ip": "192.0.2.100",
    "attack_count": 5,
    "threat_level": "High",
    "reason": "Multiple DDoS attacks detected"
  }'
```

### Unblock an IP
```bash
curl -X POST http://localhost:5001/api/blocked-ips/unblock \
  -H "Content-Type: application/json" \
  -d '{
    "ip": "192.0.2.100",
    "reason": "False positive - legitimate traffic"
  }'
```

### Get All Blocked IPs
```bash
curl http://localhost:5001/api/blocked-ips
```

### Get Statistics
```bash
curl http://localhost:5001/api/blocked-ips/statistics
```

---

## 💾 Database Location

**Path:** `monitoring/server/data/blocked_ips.db`

**Size:** ~28 KB (grows with more IPs)

**View Contents:**
```bash
cd /home/cdrditgis/Documents/Healing-bot
sqlite3 monitoring/server/data/blocked_ips.db

# Run SQL commands:
SELECT * FROM blocked_ips;
SELECT * FROM blocked_ips_history;
.exit
```

---

## ✅ Test It

### Run Automated Tests
```bash
cd /home/cdrditgis/Documents/Healing-bot
python3 test-blocked-ips.py
```

Expected output:
```
Tests Passed: 9
Tests Failed: 0
✅ All tests passed!
```

### Manual Test
1. Open dashboard: http://localhost:5001
2. Go to DDoS Detection tab
3. Click Block on any IP
4. Refresh page - should still show as blocked
5. Click Unblock
6. Verify IP is unblocked

---

## 🎨 Dashboard Changes

### New Features:
1. **Block Status Badge** - Shows "🚫 BLOCKED" for blocked IPs
2. **Dynamic Buttons** - Block (red) or Unblock (green) based on status
3. **Real Timestamps** - Shows actual "Last Seen" from database
4. **Toast Notifications** - Success/error messages slide in from right
5. **Live Updates** - Table refreshes automatically after actions

### Example Table:

**Before Block:**
```
| IP Address    | Attacks | Last Seen | Threat   | Status    |
|---------------|---------|-----------|----------|-----------|
| 192.168.1.100 | 12      | Just now  | Critical | [Block]   |
```

**After Block:**
```
| IP Address    | Attacks | Last Seen  | Threat   | Status                 |
|---------------|---------|------------|----------|------------------------|
| 192.168.1.100 | 12      | 12:15 PM   | Critical | [Unblock] 🚫 BLOCKED  |
```

---

## 📈 Use Cases

### Scenario 1: Block Attacker
**Problem:** IP 203.0.113.50 is sending DDoS attacks

**Solution:**
1. Find IP in Top Source IPs table
2. Click **Block** button
3. Done! IP is blocked and saved to database

**Result:** IP blocked in firewall + stored in database

### Scenario 2: Unblock False Positive
**Problem:** Legitimate IP was accidentally blocked

**Solution:**
1. Find IP in table (shows BLOCKED badge)
2. Click **Unblock** button
3. Done! IP can access system again

**Result:** IP unblocked + action logged for audit

### Scenario 3: Review History
**Problem:** Need to know who blocked an IP and why

**Solution:**
```bash
curl http://localhost:5001/api/blocked-ips/192.0.2.100
```

**Result:** Complete history with timestamps, reasons, and performers

### Scenario 4: Generate Report
**Problem:** Need list of all blocked IPs

**Solution:**
```bash
curl http://localhost:5001/api/blocked-ips > blocked_ips_report.json
# Or export to CSV:
curl -X POST http://localhost:5001/api/blocked-ips/export
```

**Result:** Complete report in JSON or CSV format

---

## 🔧 Configuration

### Change Database Location
Edit `monitoring/server/healing_dashboard_api.py`:
```python
blocked_ips_db = BlockedIPsDatabase("path/to/your/database.db")
```

### Enable sudo for iptables
For actual firewall blocking to work:
```bash
sudo visudo
# Add this line:
your_username ALL=(ALL) NOPASSWD: /sbin/iptables
```

---

## 📚 Documentation

- **Quick Start:** This file
- **Complete Guide:** `BLOCKED_IPS_DATABASE_GUIDE.md`
- **Summary:** `BLOCKED_IPS_SUMMARY.md`
- **Test Suite:** `test-blocked-ips.py`

---

## 🆘 Troubleshooting

### Q: Block button doesn't update status
**A:** Refresh the page or clear browser cache

### Q: IPs show as blocked but still can access
**A:** Need sudo permissions for iptables (see Configuration above)

### Q: Can't see blocked IPs in table
**A:** Make sure you're on the DDoS Detection tab, not SSH Security

### Q: Error when unblocking
**A:** Check that IP is actually blocked in database:
```bash
curl http://localhost:5001/api/blocked-ips/{ip_address}
```

### Q: Database error
**A:** Ensure only one dashboard instance is running:
```bash
pkill -f healing_dashboard_api
```

---

## 🎉 That's It!

You now have a complete, persistent blocked IPs database system!

### Key Points:
- ✅ All blocks survive server restarts
- ✅ Complete audit trail
- ✅ Easy to unblock
- ✅ Real-time dashboard updates
- ✅ Export for reporting
- ✅ Full API access

### Next Steps:
1. Try blocking/unblocking some IPs
2. Check the database contents
3. Run the test suite
4. Read the complete guide for advanced features

---

**Enjoy your enhanced security! 🛡️**

For detailed information, see: `BLOCKED_IPS_DATABASE_GUIDE.md`

