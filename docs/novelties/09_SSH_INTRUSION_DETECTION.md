# Novelty 9: SSH Intrusion Detection & Auto-Blocking

## Overview

Heal-X-Bot implements real-time SSH intrusion detection by monitoring authentication logs and automatically blocking IP addresses that exceed failed login thresholds.

## Why This Is Novel

| Traditional Approach | Heal-X-Bot Innovation |
|---------------------|----------------------|
| Manual log review | Real-time monitoring |
| Delayed response | Instant blocking |
| External tools (fail2ban) | Integrated solution |
| No visibility | Dashboard integration |
| Configure separately | Part of unified system |

---

## Problem Statement

### Challenges Addressed
1. **Brute Force Attacks**: Repeated login attempts
2. **Delayed Detection**: Manual log review takes time
3. **Tool Fragmentation**: Separate SSH protection tools
4. **No Visibility**: Limited attack awareness
5. **Manual Blocking**: Slow IP blocking process

---

## Solution Architecture

### Detection Pipeline
```
┌─────────────────┐
│ /var/log/auth   │
│     .log        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Log Watcher    │
│  (tail -f)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Pattern Matcher │
│ - Failed login  │
│ - Invalid user  │
│ - Break-in      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Attempt Counter │
│ Per IP address  │
└────────┬────────┘
         │
         ▼ (> threshold)
┌─────────────────┐
│  IP Blocker     │
│  (iptables)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Discord Alert   │
└─────────────────┘
```

---

## Technical Deep Dive

### Log Patterns Detected
```python
SSH_PATTERNS = [
    # Failed password
    r'Failed password for (?:invalid user )?(\S+) from (\d+\.\d+\.\d+\.\d+)',
    
    # Invalid user
    r'Invalid user (\S+) from (\d+\.\d+\.\d+\.\d+)',
    
    # Authentication failure
    r'authentication failure.*rhost=(\d+\.\d+\.\d+\.\d+)',
    
    # Break-in attempt
    r'POSSIBLE BREAK-IN ATTEMPT.*from (\d+\.\d+\.\d+\.\d+)',
    
    # Connection closed by authenticating user
    r'Connection closed by authenticating user .* (\d+\.\d+\.\d+\.\d+)',
    
    # Disconnected from invalid user
    r'Disconnected from invalid user .* (\d+\.\d+\.\d+\.\d+)',
]
```

### SSH Intrusion Detector
```python
class SSHIntrusionDetector:
    """Monitor SSH authentication and block attackers"""
    
    def __init__(self):
        self.auth_log = '/var/log/auth.log'
        self.attempt_counter = defaultdict(int)
        self.blocked_ips = set()
        self.max_attempts = 5
        self.block_duration_hours = 24
    
    async def start_monitoring(self):
        """Start real-time log monitoring"""
        process = await asyncio.create_subprocess_exec(
            'tail', '-f', '-n', '0', self.auth_log,
            stdout=asyncio.subprocess.PIPE
        )
        
        while True:
            line = await process.stdout.readline()
            if line:
                await self.process_line(line.decode())
    
    async def process_line(self, line: str):
        """Process a single log line"""
        for pattern in SSH_PATTERNS:
            match = re.search(pattern, line)
            if match:
                ip = match.group(match.lastindex)  # IP is last group
                await self.record_attempt(ip, line)
                break
    
    async def record_attempt(self, ip: str, log_line: str):
        """Record failed attempt and block if threshold exceeded"""
        
        if ip in self.blocked_ips:
            return  # Already blocked
        
        self.attempt_counter[ip] += 1
        attempts = self.attempt_counter[ip]
        
        logger.info(f"SSH attempt {attempts}/{self.max_attempts} from {ip}")
        
        if attempts >= self.max_attempts:
            await self.block_ip(ip)
    
    async def block_ip(self, ip: str):
        """Block an IP address"""
        
        # Add to iptables
        cmd = f"iptables -A INPUT -s {ip} -j DROP"
        await asyncio.create_subprocess_shell(cmd)
        
        # Record block
        self.blocked_ips.add(ip)
        
        # Store in database
        await self.store_blocked_ip(ip, reason="SSH brute force")
        
        # Send alert
        send_discord_alert(
            f"🔒 Blocked IP {ip} after {self.max_attempts} failed SSH attempts",
            severity="warning",
            alert_type="ssh_intrusion"
        )
        
        # Schedule unblock
        asyncio.create_task(
            self.schedule_unblock(ip, self.block_duration_hours * 3600)
        )
```

### Geo-Location Lookup
```python
async def get_ip_location(ip: str) -> Dict:
    """Get geographic location of IP"""
    try:
        response = await httpx.get(f"http://ip-api.com/json/{ip}")
        data = response.json()
        return {
            'country': data.get('country', 'Unknown'),
            'city': data.get('city', 'Unknown'),
            'isp': data.get('isp', 'Unknown'),
            'lat': data.get('lat'),
            'lon': data.get('lon')
        }
    except Exception:
        return {'country': 'Unknown'}
```

---

## API Reference

### Get SSH Intrusion Status
```http
GET /api/ssh/status
```

**Response:**
```json
{
  "monitoring": true,
  "blocked_count": 15,
  "recent_attempts": [
    {
      "ip": "192.168.1.100",
      "attempts": 3,
      "last_attempt": "2026-01-16T15:30:00Z",
      "location": "Russia, Moscow"
    }
  ]
}
```

### Get Blocked IPs
```http
GET /api/ssh/blocked
```

### Manual Block
```http
POST /api/ssh/block
Content-Type: application/json

{
  "ip": "192.168.1.100",
  "reason": "Manual block - suspicious activity"
}
```

### Unblock IP
```http
POST /api/ssh/unblock
Content-Type: application/json

{
  "ip": "192.168.1.100"
}
```

---

## Configuration

### SSH Detection Settings
```json
{
  "ssh_detection": {
    "enabled": true,
    "auth_log_path": "/var/log/auth.log",
    "max_attempts": 5,
    "block_duration_hours": 24,
    "whitelist": ["127.0.0.1", "10.0.0.0/8"],
    "notify_discord": true,
    "geo_lookup": true
  }
}
```

---

## Dashboard Integration

### SSH Security Panel
- Real-time attempt counter
- Blocked IP list with location
- Unblock button
- Attempt history timeline
- Geographic attack map

### Alert Integration
- SSH alerts appear in Active Alerts
- Severity-based coloring
- One-click blocking from alerts

---

## Blocking Methods

### iptables (Default)
```bash
# Block IP
iptables -A INPUT -s {ip} -j DROP

# Unblock IP
iptables -D INPUT -s {ip} -j DROP
```

### UFW (Alternative)
```bash
# Block IP
ufw deny from {ip}

# Unblock IP
ufw delete deny from {ip}
```

### fail2ban Integration
```ini
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 5
bantime = 86400
```

---

## Statistics Tracked

| Metric | Description |
|--------|-------------|
| Total Attempts | All failed login attempts |
| Unique IPs | Number of distinct attacking IPs |
| Blocked IPs | Currently blocked count |
| Top Countries | Most common attack origins |
| Attempt Timeline | Attempts over time |

---

## Use Cases

### 1. Brute Force Protection
Automatically block IPs attempting to guess passwords.

### 2. Bot Detection
Identify automated login attempts.

### 3. Compliance
Log all authentication attempts for audit.

### 4. Threat Intelligence
Geographic analysis of attack sources.

---

## Future Enhancements

1. **Reputation Database**: Check IP reputation
2. **Adaptive Thresholds**: Dynamic attempt limits
3. **Attack Patterns**: ML-based attack detection
4. **Auto-Escalation**: Progressive blocking
5. **Threat Feed Integration**: External threat intelligence
