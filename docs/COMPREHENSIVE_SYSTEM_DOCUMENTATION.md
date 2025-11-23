# 🛡️ Heal-X-Bot: Comprehensive System Documentation

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [System Architecture](#system-architecture)
4. [Core Components](#core-components)
5. [Technology Stack](#technology-stack)
6. [System Flow Diagrams](#system-flow-diagrams)
7. [Service Architecture](#service-architecture)
8. [Data Flow Architecture](#data-flow-architecture)
9. [Security Architecture](#security-architecture)
10. [Deployment Architecture](#deployment-architecture)

---

## Executive Summary

**Heal-X-Bot** is an advanced, AI-powered cybersecurity and system management platform that provides:

- **Real-time DDoS Detection**: Machine learning-based threat detection with automatic IP blocking
- **Predictive Maintenance**: Proactive system failure prediction using XGBoost models
- **Autonomous Self-Healing**: Automated system recovery and service management
- **Intelligent Incident Response**: AI-powered log analysis and remediation suggestions
- **Comprehensive Monitoring**: Real-time system metrics, health scoring, and alerting

The system combines multiple cutting-edge technologies including TensorFlow for DDoS detection, XGBoost for predictive analytics, FastAPI for high-performance APIs, and modern web technologies for real-time dashboards.

**Key Statistics:**
- **5 Core Services**: Model API, Network Analyzer, Monitoring Server, Incident Bot, Healing Dashboard
- **2 ML Models**: DDoS Detection (TensorFlow) and Predictive Maintenance (XGBoost)
- **13+ Critical Services Monitored**: Docker, systemd, dbus, cron, rsyslog, and more
- **Real-time Updates**: WebSocket-based 2-second refresh rate
- **99%+ Uptime Target**: Through automated healing and monitoring

---

## System Overview

### What is Heal-X-Bot?

Heal-X-Bot is a comprehensive cybersecurity and system management solution that provides:

1. **Threat Detection & Mitigation**
   - Real-time DDoS attack detection using deep learning
   - Automatic malicious IP blocking
   - Pattern-based attack recognition
   - Geographic threat analysis

2. **Predictive Intelligence**
   - System failure prediction 1-24 hours in advance
   - Early warning indicators
   - Time-to-failure estimation
   - Risk scoring and assessment

3. **Autonomous Operations**
   - Automatic service restart
   - Resource hog detection and termination
   - Disk space management
   - SSH intrusion detection and blocking

4. **Intelligent Analysis**
   - AI-powered log analysis using Google Gemini
   - Anomaly detection
   - Incident response recommendations
   - Automated remediation suggestions

5. **Comprehensive Monitoring**
   - Real-time system metrics
   - Health scoring
   - Centralized logging
   - Performance analytics

### System Goals

- **Zero-Downtime Operations**: Automatic detection and recovery from failures
- **Proactive Security**: Early threat detection and automatic mitigation
- **Intelligent Automation**: AI-driven decision making for system management
- **Comprehensive Visibility**: Real-time monitoring and historical analytics
- **Easy Management**: Single-command deployment and intuitive dashboards

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Heal-X-Bot System                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Web UI     │  │   Mobile     │  │   API        │         │
│  │  Dashboard   │  │   Access    │  │   Clients    │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                 │                 │                  │
│         └─────────────────┴─────────────────┘                  │
│                           │                                     │
│                           ▼                                     │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │              Healing Dashboard API (Port 5001)            │ │
│  │  - REST API Endpoints                                     │ │
│  │  - WebSocket Server                                       │ │
│  │  - Static File Serving                                    │ │
│  └───────────────┬──────────────────────────────────────────┘ │
│                  │                                              │
│      ┌───────────┴───────────┐                                 │
│      │                       │                                 │
│      ▼                       ▼                                 │
│  ┌──────────────┐    ┌──────────────┐                         │
│  │  Monitoring  │    │  Network     │                         │
│  │   Server     │    │  Analyzer    │                         │
│  │  (Port 5000) │    │  (Port 8000) │                         │
│  └──────┬───────┘    └──────┬───────┘                         │
│         │                   │                                  │
│         └───────────┬───────┘                                  │
│                     │                                           │
│                     ▼                                           │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │              ML Model API (Port 8080)                      │ │
│  │  - DDoS Detection Model (TensorFlow)                      │ │
│  │  - Predictive Maintenance Model (XGBoost)                │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │              Incident Bot (Port 8001)                      │ │
│  │  - AI Log Analysis (Google Gemini)                       │ │
│  │  - Incident Response                                      │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │              Data Layer                                    │ │
│  │  - SQLite (Blocked IPs)                                   │ │
│  │  - File System (Logs, Models)                             │ │
│  │  - In-Memory Cache (Metrics)                              │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │              External Integrations                         │ │
│  │  - Discord (Notifications)                               │ │
│  │  - AWS S3 (Log Storage)                                  │ │
│  │  - Prometheus (Metrics)                                  │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
User Request
    │
    ▼
┌─────────────────┐
│  Dashboard UI   │
└────────┬────────┘
         │ HTTP/WebSocket
         ▼
┌─────────────────────────┐
│  Healing Dashboard API  │
│  (FastAPI - Port 5001)  │
└────────┬────────────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────────┐ ┌──────────────┐
│ Monitor │ │   Network    │
│ Server  │ │   Analyzer   │
└────┬────┘ └──────┬───────┘
     │             │
     └─────┬───────┘
           │
           ▼
    ┌──────────────┐
    │  ML Model API │
    │  (Port 8080)  │
    └──────┬───────┘
           │
    ┌──────┴───────┐
    │              │
    ▼              ▼
┌─────────┐  ┌──────────────┐
│ DDoS    │  │ Predictive   │
│ Model   │  │ Maintenance  │
│(TF/Keras)│  │  (XGBoost)   │
└─────────┘  └──────────────┘
```

---

## Core Components

### 1. Healing Dashboard API (`monitoring/server/healing_dashboard_api.py`)

**Purpose**: Main API server providing REST endpoints and WebSocket connections for the dashboard.

**Key Features**:
- FastAPI-based REST API
- WebSocket support for real-time updates
- Static file serving for dashboard UI
- Service orchestration
- Health monitoring endpoints

**Port**: 5001

**Key Endpoints**:
- `/api/health` - Health check
- `/api/metrics` - System metrics
- `/api/services` - Service management
- `/api/processes` - Process management
- `/api/ssh` - SSH security
- `/api/disk` - Disk management
- `/api/logs` - Log access
- `/api/cli` - CLI execution
- `/ws/healing` - WebSocket for real-time updates

### 2. Monitoring Server (`monitoring/server/app.py`)

**Purpose**: System metrics collection, log aggregation, and health monitoring.

**Key Features**:
- Real-time system metrics (CPU, Memory, Disk, Network)
- Centralized log collection
- Critical services monitoring
- Health scoring
- Log analysis

**Port**: 5000

**Key Endpoints**:
- `/api/metrics` - System metrics
- `/api/logs/recent` - Recent logs
- `/api/logs/statistics` - Log statistics
- `/api/logs/health` - Health score
- `/api/critical-services` - Critical services status

### 3. ML Model API (`model/main.py`)

**Purpose**: Serves machine learning models for DDoS detection and predictive maintenance.

**Key Features**:
- DDoS detection using TensorFlow/Keras
- Predictive maintenance using XGBoost
- Real-time prediction endpoints
- Model metrics and monitoring

**Port**: 8080

**Key Endpoints**:
- `/health` - Model health check
- `/predict` - DDoS prediction
- `/predict-failure-risk` - Failure risk prediction
- `/predict-time-to-failure` - Time-to-failure estimation
- `/metrics` - Model performance metrics

### 4. Network Analyzer (`monitoring/server/network_analyzer.py`)

**Purpose**: Network traffic analysis, IP blocking, and threat detection.

**Key Features**:
- Real-time network traffic analysis
- IP blocking/unblocking
- Threat level assessment
- Geographic IP analysis
- Attack pattern detection

**Port**: 8000

**Key Endpoints**:
- `/health` - Health check
- `/analyze` - Network analysis
- `/block-ip` - Block IP address
- `/unblock-ip` - Unblock IP address
- `/threats` - Threat statistics

### 5. Incident Bot (`incident-bot/main.py`)

**Purpose**: AI-powered incident response and log analysis.

**Key Features**:
- Google Gemini AI integration
- Log analysis and summarization
- Incident response recommendations
- Automated remediation suggestions

**Port**: 8001

**Key Endpoints**:
- `/health` - Health check
- `/analyze` - Log analysis
- `/incident` - Incident response
- `/suggest` - Remediation suggestions

### 6. Auto-Healing System (`monitoring/server/healing/`)

**Purpose**: Autonomous system recovery and service management.

**Components**:
- `orchestrator.py` - Main healing orchestration
- `actions/system.py` - System-level healing actions
- `actions/container.py` - Container healing actions
- `actions/resource.py` - Resource management actions
- `verification.py` - Healing verification
- `notifications.py` - Notification management
- `history.py` - Healing history tracking

**Key Features**:
- Automatic service restart
- Resource cleanup
- Container management
- Network restoration
- Healing history tracking

### 7. Blocked IPs Database (`monitoring/server/blocked_ips_db.py`)

**Purpose**: Persistent storage for blocked IP addresses.

**Technology**: SQLite

**Features**:
- IP blocking/unblocking
- Statistics tracking
- Reason tracking
- Timestamp management
- Export capabilities

### 8. Centralized Logger (`monitoring/server/centralized_logger.py`)

**Purpose**: Aggregates logs from all system components.

**Features**:
- Multi-source log collection
- JSON and text output formats
- Full-text search
- Service filtering
- Automatic rotation

---

## Technology Stack

### Backend Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **API Framework** | FastAPI | High-performance REST API and WebSocket server |
| **ML Framework** | TensorFlow/Keras | DDoS detection deep learning model |
| **ML Framework** | XGBoost | Predictive maintenance gradient boosting |
| **Data Processing** | NumPy, Pandas | Data manipulation and analysis |
| **System Monitoring** | psutil | System metrics collection |
| **Database** | SQLite | Blocked IPs storage |
| **Log Analysis** | scikit-learn | TF-IDF analysis |
| **AI Integration** | Google Gemini API | Intelligent log analysis |

### Frontend Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **UI Framework** | HTML5, CSS3 | Dashboard interface |
| **JavaScript** | Vanilla ES6+ | Client-side logic |
| **Charts** | Chart.js | Data visualization |
| **Real-time** | WebSocket API | Live updates |
| **Styling** | Custom CSS | Modern, responsive design |

### Infrastructure

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Containerization** | Docker | Service containerization |
| **Orchestration** | Docker Compose | Multi-container management |
| **Log Aggregation** | Fluent Bit | Log collection and forwarding |
| **Metrics** | Prometheus | Metrics collection |
| **Notifications** | Discord Webhooks | Alert delivery |

### Development Tools

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Language** | Python 3.8+ | Primary development language |
| **Package Management** | pip | Dependency management |
| **Virtual Environment** | venv | Environment isolation |
| **Version Control** | Git | Source code management |

---

## System Flow Diagrams

### DDoS Detection Flow

```
Network Traffic
    │
    ▼
┌─────────────────┐
│ Network Analyzer│
│  (Port 8000)    │
└────────┬────────┘
         │ Extract Features
         ▼
┌─────────────────┐
│  Feature        │
│  Extraction     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ML Model API   │
│  (Port 8080)    │
│  DDoS Model     │
└────────┬────────┘
         │ Prediction + Confidence
         ▼
┌─────────────────┐
│ Threat Level    │
│ Assessment      │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────────┐ ┌──────────────┐
│ Threat  │ │ Auto-Block   │
│ < 80%   │ │ Threat ≥ 80% │
└─────────┘ └──────┬───────┘
                   │
                   ▼
            ┌──────────────┐
            │ IP Blocked    │
            │ (SQLite DB)   │
            └──────────────┘
```

### Predictive Maintenance Flow

```
System Metrics Collection
    │
    ▼
┌─────────────────┐
│ Monitoring      │
│ Server          │
│ (Every 60s)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Feature         │
│ Engineering     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ML Model API    │
│ XGBoost Models  │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────────┐ ┌──────────────┐
│ Failure │ │ Time-to-     │
│ Risk    │ │ Failure      │
│ Score   │ │ Estimation   │
└────┬────┘ └──────┬───────┘
     │             │
     └─────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Early Warning│
    │ Indicators   │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Dashboard     │
    │ Alert         │
    └──────────────┘
```

### Auto-Healing Flow

```
System Anomaly Detected
    │
    ▼
┌─────────────────┐
│ Healing         │
│ Orchestrator    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Identify       │
│ Issue Type     │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼         ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│ Service │ │ Resource│ │ Network │
│ Action  │ │ Action  │ │ Action  │
└────┬────┘ └────┬────┘ └────┬────┘
     │           │           │
     └───────────┴───────────┘
                 │
                 ▼
         ┌──────────────┐
         │ Execute      │
         │ Healing      │
         │ Action       │
         └──────┬───────┘
                │
                ▼
         ┌──────────────┐
         │ Verify       │
         │ Resolution   │
         └──────┬───────┘
                │
         ┌──────┴──────┐
         │             │
         ▼             ▼
    ┌─────────┐  ┌──────────────┐
    │ Success │  │ Retry/Fallback│
    └────┬────┘  └──────┬───────┘
         │              │
         └──────┬───────┘
                │
                ▼
         ┌──────────────┐
         │ Log & Notify │
         └──────────────┘
```

---

## Service Architecture

### Service Dependencies

```
┌─────────────────┐
│  Healing        │
│  Dashboard      │
│  (Port 5001)    │
└────────┬────────┘
         │ Depends on
         ▼
┌─────────────────┐
│  Monitoring     │
│  Server         │
│  (Port 5000)    │
└────────┬────────┘
         │ Depends on
         ▼
┌─────────────────┐
│  ML Model API   │
│  (Port 8080)    │
└─────────────────┘
         ▲
         │ Depends on
┌────────┴────────┐
│  Network        │
│  Analyzer       │
│  (Port 8000)    │
└─────────────────┘
```

### Service Startup Order

1. **ML Model API** (Port 8080) - No dependencies
2. **Network Analyzer** (Port 8000) - Depends on Model API
3. **Monitoring Server** (Port 5000) - Depends on Model API
4. **Incident Bot** (Port 8001) - Depends on Model API
5. **Healing Dashboard** (Port 5001) - Depends on Monitoring Server

---

## Data Flow Architecture

### Real-Time Metrics Flow

```
System (OS)
    │
    ▼
┌─────────────────┐
│ psutil          │
│ (System APIs)   │
└────────┬────────┘
         │ Every 2 seconds
         ▼
┌─────────────────┐
│ Monitoring      │
│ Server          │
│ (Collector)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ WebSocket       │
│ Broadcast       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Dashboard UI    │
│ (Real-time      │
│  Updates)       │
└─────────────────┘
```

### Log Aggregation Flow

```
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Service  │  │ Service  │  │ Service  │
│ Logs     │  │ Logs     │  │ Logs     │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │              │
     └─────────────┴──────────────┘
                   │
                   ▼
          ┌─────────────────┐
          │ Centralized     │
          │ Logger          │
          └────────┬────────┘
                   │
          ┌─────────┴─────────┐
          │                    │
          ▼                    ▼
    ┌──────────┐        ┌──────────┐
    │ JSON      │        │ Text     │
    │ Format    │        │ Format   │
    └──────────┘        └──────────┘
          │                    │
          └──────────┬─────────┘
                     │
                     ▼
            ┌─────────────────┐
            │ Dashboard/API   │
            │ Access          │
            └─────────────────┘
```

---

## Security Architecture

### Security Layers

```
┌─────────────────────────────────────────┐
│         Security Perimeter              │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  Network Security                │  │
│  │  - IP Blocking (iptables)        │  │
│  │  - Firewall Rules                 │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  Application Security            │  │
│  │  - CORS Configuration            │  │
│  │  - Input Validation              │  │
│  │  - Rate Limiting                 │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  Access Control                  │  │
│  │  - CLI Command Whitelist        │  │
│  │  - Service Permissions          │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  Data Security                   │  │
│  │  - SQLite Database               │  │
│  │  - Encrypted Logs (optional)    │  │
│  └──────────────────────────────────┘  │
│                                         │
└─────────────────────────────────────────┘
```

### Threat Detection Pipeline

```
Network Traffic
    │
    ▼
┌─────────────────┐
│ Pattern         │
│ Detection       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ML Model        │
│ Analysis        │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌─────────┐ ┌──────────────┐
│ Legitimate│ │ Threat       │
│ Traffic  │ │ Detected     │
└─────────┘ └──────┬───────┘
                   │
                   ▼
            ┌──────────────┐
            │ Auto-Block   │
            │ IP Address   │
            └──────┬───────┘
                   │
                   ▼
            ┌──────────────┐
            │ Notification │
            │ (Discord)    │
            └──────────────┘
```

---

## Deployment Architecture

### Single-Server Deployment

```
┌─────────────────────────────────────┐
│         Single Server               │
│                                     │
│  ┌──────────────────────────────┐ │
│  │  Healing Dashboard (5001)    │ │
│  └──────────────────────────────┘ │
│  ┌──────────────────────────────┐ │
│  │  Monitoring Server (5000)    │ │
│  └──────────────────────────────┘ │
│  ┌──────────────────────────────┐ │
│  │  ML Model API (8080)         │ │
│  └──────────────────────────────┘ │
│  ┌──────────────────────────────┐ │
│  │  Network Analyzer (8000)     │ │
│  └──────────────────────────────┘ │
│  ┌──────────────────────────────┐ │
│  │  Incident Bot (8001)         │ │
│  └──────────────────────────────┘ │
│                                     │
│  ┌──────────────────────────────┐ │
│  │  SQLite Database             │ │
│  └──────────────────────────────┘ │
│  ┌──────────────────────────────┐ │
│  │  Log Files                   │ │
│  └──────────────────────────────┘ │
└─────────────────────────────────────┘
```

### Docker Deployment

```
┌─────────────────────────────────────┐
│      Docker Compose Network        │
│                                     │
│  ┌──────────┐  ┌──────────┐       │
│  │ Dashboard│  │ Monitor  │       │
│  │ Container│  │ Container │       │
│  └──────────┘  └──────────┘       │
│                                     │
│  ┌──────────┐  ┌──────────┐       │
│  │ Model    │  │ Network   │       │
│  │ Container│  │ Container │       │
│  └──────────┘  └──────────┘       │
│                                     │
│  ┌──────────┐  ┌──────────┐       │
│  │ Prometheus│  │ Fluent   │       │
│  │ Container│  │ Bit      │       │
│  └──────────┘  └──────────┘       │
│                                     │
│  ┌──────────────────────────────┐  │
│  │  Shared Volumes              │  │
│  │  - Logs                      │  │
│  │  - Models                    │  │
│  │  - Database                  │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
```

---

## System Capabilities Summary

### Detection Capabilities
- ✅ DDoS attack detection (HTTP Flood, SYN Flood, Bot Activity)
- ✅ System failure prediction (1-24 hours ahead)
- ✅ Anomaly detection in logs and metrics
- ✅ SSH intrusion detection
- ✅ Resource exhaustion detection

### Automation Capabilities
- ✅ Automatic IP blocking (threat level ≥ 80%)
- ✅ Automatic service restart
- ✅ Automatic resource cleanup
- ✅ Automatic disk space management
- ✅ Automatic healing actions

### Monitoring Capabilities
- ✅ Real-time system metrics (CPU, Memory, Disk, Network)
- ✅ Service health monitoring (13+ critical services)
- ✅ Log aggregation and analysis
- ✅ Performance metrics tracking
- ✅ Historical data analysis

### Intelligence Capabilities
- ✅ AI-powered log analysis (Google Gemini)
- ✅ Incident response recommendations
- ✅ Automated remediation suggestions
- ✅ Pattern recognition in attacks
- ✅ Predictive failure analysis

---

## Next Steps

For detailed information on specific components, refer to:
- **ML Models**: See `ML_MODELS_DOCUMENTATION.md`
- **Features**: See `FEATURES_DOCUMENTATION.md`
- **Use Cases**: See `USE_CASES_GUIDE.md`
- **User Guide**: See `END_TO_END_USER_GUIDE.md`
- **Technical Details**: See `ADVANCED_TECHNICAL_DETAILS.md`

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-19  
**Maintained By**: Heal-X-Bot Development Team

