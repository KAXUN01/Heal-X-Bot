# Novelty 6: Real-Time Log Intelligence System

## Overview

Heal-X-Bot implements a centralized log intelligence system that aggregates logs from multiple sources (systemd, Docker, syslog, auth.log, kernel) and provides AI-powered analysis for instant root cause identification.

## Why This Is Novel

| Traditional Approach | Heal-X-Bot Innovation |
|---------------------|----------------------|
| Separate log viewers | Unified aggregation |
| Manual log analysis | AI-powered insights |
| Delayed processing | Real-time streaming |
| Text search only | Pattern recognition |
| No context | Service correlation |

---

## Problem Statement

### Challenges Addressed
1. **Log Fragmentation**: Logs scattered across multiple sources
2. **Manual Analysis**: Time-consuming log investigation
3. **Pattern Detection**: Hard to spot correlations manually
4. **Alert Fatigue**: Too many logs, not enough insights
5. **Context Loss**: Individual logs lack system context

---

## Solution Architecture

### Log Collection Pipeline
```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│    systemd      │  │    Docker       │  │    syslog       │
│    journald     │  │    containers   │  │    /var/log     │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │    Fluent Bit       │
                   │  Log Aggregator     │
                   └──────────┬──────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │  Centralized Logger │
                   │  Python Collector   │
                   └──────────┬──────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
       ┌──────────┐    ┌──────────┐    ┌──────────┐
       │ TF-IDF   │    │ Gemini   │    │Dashboard │
       │ Analysis │    │ AI       │    │ Display  │
       └──────────┘    └──────────┘    └──────────┘
```

### Log Sources
| Source | Path/Method | Content |
|--------|-------------|---------|
| **systemd** | journalctl | Service logs |
| **Docker** | docker logs | Container output |
| **syslog** | /var/log/syslog | System messages |
| **auth** | /var/log/auth.log | Authentication events |
| **kernel** | /var/log/kern.log | Kernel messages |
| **nginx** | /var/log/nginx/ | Web server access/error |
| **application** | Custom paths | App-specific logs |

---

## Technical Deep Dive

### Fluent Bit Configuration
```ini
[SERVICE]
    Flush        1
    Daemon       Off
    Log_Level    info
    HTTP_Server  On
    HTTP_Listen  0.0.0.0
    HTTP_Port    2020

[INPUT]
    Name         systemd
    Tag          systemd.*
    Systemd_Filter  _SYSTEMD_UNIT=docker.service
    Systemd_Filter  _SYSTEMD_UNIT=nginx.service
    Read_From_Tail  On

[INPUT]
    Name         tail
    Path         /var/log/syslog
    Tag          syslog
    Parser       syslog
    Refresh_Interval  5

[INPUT]
    Name         tail
    Path         /var/log/auth.log
    Tag          auth
    Parser       syslog

[OUTPUT]
    Name         http
    Match        *
    Host         localhost
    Port         5001
    URI          /api/logs/ingest
    Format       json
```

### Centralized Logger
```python
class SystemLogCollector:
    """Collect logs from multiple system sources"""
    
    def __init__(self):
        self.sources = {
            'systemd': SystemdCollector(),
            'docker': DockerLogCollector(),
            'syslog': FileLogCollector('/var/log/syslog'),
            'auth': FileLogCollector('/var/log/auth.log'),
            'kernel': FileLogCollector('/var/log/kern.log'),
        }
        self.logs = deque(maxlen=10000)
    
    async def collect_all(self) -> List[LogEntry]:
        """Collect logs from all sources"""
        all_logs = []
        
        for source_name, collector in self.sources.items():
            try:
                logs = await collector.collect()
                for log in logs:
                    log.source = source_name
                all_logs.extend(logs)
            except Exception as e:
                logger.error(f"Failed to collect from {source_name}: {e}")
        
        # Sort by timestamp
        all_logs.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Store in memory
        self.logs.extend(all_logs)
        
        return all_logs
```

### TF-IDF Analysis
```python
from sklearn.feature_extraction.text import TfidfVectorizer

class LogAnalyzer:
    """Analyze logs using TF-IDF and pattern detection"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
    
    def extract_keywords(self, logs: List[str]) -> List[str]:
        """Extract important keywords from logs"""
        
        if not logs:
            return []
        
        # Fit and transform
        tfidf_matrix = self.vectorizer.fit_transform(logs)
        
        # Get feature names and scores
        feature_names = self.vectorizer.get_feature_names_out()
        scores = tfidf_matrix.sum(axis=0).A1
        
        # Sort by importance
        sorted_indices = scores.argsort()[::-1]
        
        return [feature_names[i] for i in sorted_indices[:20]]
    
    def detect_anomalies(self, logs: List[LogEntry]) -> List[Anomaly]:
        """Detect anomalies in log patterns"""
        
        # Count error types
        error_counts = Counter(
            log.message for log in logs if log.level == 'error'
        )
        
        # Find spikes
        anomalies = []
        for message, count in error_counts.most_common(10):
            if count > self.threshold:
                anomalies.append(Anomaly(
                    type='error_spike',
                    message=message,
                    count=count
                ))
        
        return anomalies
```

### AI-Powered Analysis
```python
async def analyze_logs_with_ai(logs: List[LogEntry]) -> AIAnalysis:
    """Use Gemini/Groq to analyze logs"""
    
    # Prepare log summary
    error_logs = [l for l in logs if l.level in ['error', 'critical']]
    log_text = "\n".join([
        f"[{l.timestamp}] [{l.source}] {l.message}"
        for l in error_logs[:50]
    ])
    
    prompt = f"""
    Analyze these system logs and provide:
    
    1. **What Happened** (one paragraph)
    2. **Quick Fix** (executable commands)
    3. **Prevention** (one sentence)
    
    Logs:
    {log_text}
    """
    
    response = await ai_analyzer.analyze(prompt)
    
    return AIAnalysis(
        what_happened=response.sections['what_happened'],
        quick_fix=response.sections['quick_fix'],
        prevention=response.sections['prevention']
    )
```

---

## API Reference

### Get Logs (Fluent Bit)
```http
GET /api/logs/fluent-bit?limit=100&level=error
```

### Get Logs (Centralized)
```http
GET /api/logs/centralized?service=nginx&hours=1
```

### Log Statistics
```http
GET /api/logs/stats
```

**Response:**
```json
{
  "total_logs": 15420,
  "unique_services": 12,
  "error_count": 45,
  "warning_count": 230,
  "by_source": {
    "systemd": 5000,
    "docker": 8000,
    "syslog": 2420
  }
}
```

### AI Quick Analyze
```http
POST /api/gemini/quick-analyze
Content-Type: application/json

{
  "logs": [
    {"message": "Connection refused", "level": "error", "service": "nginx"}
  ]
}
```

---

## Configuration

### Log Collection Settings
```json
{
  "log_collection": {
    "enabled": true,
    "sources": ["systemd", "docker", "syslog", "auth"],
    "max_logs_memory": 10000,
    "collection_interval_seconds": 30,
    "retention_hours": 24
  }
}
```

### Fluent Bit Settings
```json
{
  "fluent_bit": {
    "enabled": true,
    "http_port": 2020,
    "flush_interval": 1,
    "parsers": ["syslog", "docker", "json"]
  }
}
```

---

## Log Display Features

### Filtering
- **By Level**: error, warning, info, debug
- **By Source**: systemd, docker, syslog, auth
- **By Service**: nginx, mysql, docker, etc.
- **By Time**: Last hour, 6 hours, 24 hours
- **By Search**: Text search in messages

### Highlighting
| Level | Color | Icon |
|-------|-------|------|
| CRITICAL | Dark Red | 🔴 |
| ERROR | Red | 🔴 |
| WARNING | Yellow | 🟡 |
| INFO | Blue | 🔵 |
| DEBUG | Gray | ⚪ |

---

## Performance Metrics

| Metric | Value |
|--------|-------|
| Log Ingestion Rate | 1000+ logs/sec |
| Search Latency | < 100ms |
| Memory Usage | ~100MB for 10K logs |
| AI Analysis Time | 2-5 seconds |

---

## Use Cases

### 1. Incident Investigation
Quickly find related logs across all services during incidents.

### 2. Root Cause Analysis
AI provides instant root cause identification.

### 3. Security Monitoring
Track auth failures and suspicious activities.

### 4. Performance Debugging
Correlate performance issues with log events.

---

## Future Enhancements

1. **Log Streaming**: Real-time WebSocket log streaming
2. **Smart Alerts**: AI-generated alert rules
3. **Log Correlation**: Auto-link related logs
4. **Dashboards**: Custom log visualizations
5. **Long-term Storage**: Elasticsearch integration
