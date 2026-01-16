# Logs & AI Analysis Page

## Description
The Logs & AI Analysis page provides centralized log aggregation from multiple sources (systemd, Docker, syslog, auth, kernel) with AI-powered analysis using Gemini or Groq for intelligent insights and root cause detection.

## Purpose
- Aggregate logs from all system sources
- Provide intelligent AI-powered log analysis
- Enable real-time log streaming
- Filter and search across all logs
- Identify patterns and anomalies

## Features

### 1. Log Source Selector
Two primary log sources:

| Source | Description |
|--------|-------------|
| **Fluent Bit** | Lightweight log processor collecting from syslog, kernel, auth, systemd |
| **Centralized Logger** | Python-based custom log collector |

### 2. Log Statistics Cards
- **Total Logs**: Count of all collected logs
- **Services**: Number of unique services/sources
- **Errors**: Count of ERROR level logs
- **Warnings**: Count of WARNING level logs

### 3. Log Table
Each log entry displays:

| Column | Description |
|--------|-------------|
| **Timestamp** | Log entry time |
| **Service** | Originating service/container |
| **Level** | INFO/WARNING/ERROR/CRITICAL |
| **Source** | syslog/docker/auth/kernel |
| **Message** | Log message content |
| **Actions** | Analyze button |

### 4. Filtering Options
- **Search**: Text search across messages
- **Service Filter**: Filter by specific service
- **Level Filter**: Filter by log level
- **Source Filter**: Filter by log source
- **Logs Per Page**: 10/50/100/200/500

### 5. AI Analysis Panel
- **Quick Analyze Errors**: One-click analysis of recent errors
- **Individual Analysis**: Analyze specific log entries
- **Root Cause Detection**: AI identifies probable causes
- **Suggested Fixes**: AI provides remediation steps

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/logs` | GET | Get system logs |
| `/api/logs/fluent-bit` | GET | Get Fluent Bit logs |
| `/api/logs/centralized` | GET | Get centralized logger logs |
| `/api/logs/stats` | GET | Get log statistics |
| `/api/gemini/quick-analyze` | POST | AI quick analysis |
| `/api/analyze-log` | POST | Analyze specific log |

## Log Sources

### Fluent Bit Configuration
```ini
[SERVICE]
    Flush        1
    Daemon       Off
    Log_Level    info

[INPUT]
    Name         systemd
    Tag          host.*
    Systemd_Filter _SYSTEMD_UNIT=docker.service

[INPUT]
    Name         tail
    Path         /var/log/syslog
    Tag          syslog

[INPUT]
    Name         tail
    Path         /var/log/auth.log
    Tag          auth
```

### Centralized Logger
```python
class SystemLogCollector:
    def __init__(self):
        self.sources = [
            {'type': 'systemd', 'unit': '*'},
            {'type': 'docker', 'all': True},
            {'type': 'file', 'path': '/var/log/syslog'},
        ]
```

## AI Analysis

### Gemini Integration
```python
import google.generativeai as genai

model = genai.GenerativeModel('gemini-2.0-flash')
response = model.generate_content(
    f"Analyze this log entry and provide root cause and fix:\n{log_message}"
)
```

### Groq Fallback
```python
from groq import Groq

client = Groq(api_key=GROQ_API_KEY)
response = client.chat.completions.create(
    model="mixtral-8x7b-32768",
    messages=[{"role": "user", "content": analysis_prompt}]
)
```

### Analysis Output
```json
{
  "root_cause": "Description of the probable cause",
  "severity": "critical|high|medium|low",
  "affected_components": ["list", "of", "components"],
  "suggested_fix": "Step-by-step remediation",
  "commands": ["executable", "shell", "commands"],
  "prevention": "How to prevent recurrence"
}
```

## Technical Implementation

### Log Fetching
```javascript
async function refreshSystemLogs() {
    const source = document.getElementById('logSourceSelector').value;
    const endpoint = source === 'fluent-bit' ? 
        '/api/logs/fluent-bit' : '/api/logs/centralized';
    const response = await fetch(endpoint);
    const data = await response.json();
    displayLogs(data.logs);
}
```

### Auto-Refresh
- Toggle button for automatic refresh
- Default interval: 5 seconds
- Pauses when user is filtering/searching

### JavaScript Functions
```javascript
refreshSystemLogs()      // Fetch and display logs
filterLogs()             // Apply filters
clearFilters()           // Reset all filters
toggleAutoRefresh()      // Enable/disable auto-refresh
analyzeLog(logId)        // AI analyze single log
quickAnalyzeErrors()     // AI analyze recent errors
loadMoreLogs()           // Pagination
```

## Log Level Colors

| Level | Background Color | Text Color |
|-------|-----------------|------------|
| CRITICAL | Dark Red | White |
| ERROR | Red | White |
| WARNING | Yellow | Black |
| INFO | Blue | White |
| DEBUG | Gray | White |

## User Actions
- Switch between log sources
- Search and filter logs
- Analyze individual logs with AI
- Quick analyze all recent errors
- Enable auto-refresh
- Export logs

## Related Pages
- [Active Alerts](02_ACTIVE_ALERTS.md) - Alert integration
- [Self-Healing](11_SELF_HEALING.md) - Automatic remediation
- [Services](04_SERVICES.md) - Service logs
