# 🛡️ Healing-bot: AI-Powered DDoS Detection & IP Blocking System

A comprehensive cybersecurity system that automatically detects DDoS attacks, blocks malicious IPs, and provides real-time monitoring with AI-powered incident response.

## ✨ Features

### 🧠 **AI-Powered DDoS Detection**
- **Machine Learning Model**: Advanced DDoS detection using TensorFlow
- **Real-time Analysis**: Continuous monitoring of network traffic
- **Threat Level Assessment**: Automatic risk scoring (Low/Medium/High/Critical)
- **Pattern Recognition**: Detects HTTP Flood, SYN Flood, Bot Activity, and more

### 🔮 **Predictive Maintenance & Proactive Intelligence** (NEW)
- **Failure Prediction**: Predicts system failures 1-24 hours before they occur
- **Early Warning System**: Real-time risk scoring and early warning indicators
- **Time-to-Failure Estimation**: Forecasts when failures will occur
- **XGBoost Models**: Dual model approach (classification + regression)
- **Dashboard Integration**: Real-time predictions in monitoring dashboard
- **Automated Retraining**: Scheduled model updates with new data

### 🚫 **Automatic IP Blocking**
- **Auto-blocking**: Automatically blocks IPs when threat level ≥ 80%
- **Manual Management**: Admin interface for manual IP blocking/unblocking
- **Statistics Tracking**: Comprehensive analytics on blocking effectiveness
- **Persistent Storage**: SQLite database for blocked IP management

### 📊 **Real-time Dashboard**
- **Live Monitoring**: Real-time system metrics and threat detection
- **Blocked IP Management**: View, manage, and unblock IPs
- **Statistics Dashboard**: Detailed analytics and reporting
- **Interactive Interface**: Modern, responsive web interface

### 🤖 **AI Incident Response & Log Analysis**
- **Smart Suggestions**: Google Gemini AI-powered recommendations
- **Concise Analysis**: 70% shorter, 3-section format (What Happened, Quick Fix, Prevention)
- **Modern UI**: Beautiful gradient cards with emoji icons
- **Self-healing**: Automated response to common security issues
- **Slack Integration**: Real-time notifications and alerts
- **Cloud Storage**: Automatic log upload to AWS S3

### 🔍 **System Monitoring & Critical Services**
- **13 Critical Services**: Docker, systemd, dbus, cron, rsyslog, and more
- **Real-time Monitoring**: Automatic log collection every 30 seconds
- **Anomaly Detection**: Smart multi-source detection with fallback
- **Health Scoring**: Overall system health assessment
- **Log Management**: Automatic rotation and cleanup (10MB limit)

## 🚀 Quick Start

### ⚡ **Unified Startup Script (Recommended)**

**The simplest way to start Heal-X-Bot - one command does everything:**

```bash
# Start all services (first time setup included)
./start.sh

# Check service status
./start.sh status

# Stop all services
./start.sh stop

# Restart all services
./start.sh restart

# Get help
./start.sh --help
```

**What the script does automatically:**
- ✅ Checks Python version (requires 3.8+)
- ✅ Creates virtual environment
- ✅ Installs all dependencies
- ✅ Sets up environment file
- ✅ Starts all services in correct order
- ✅ Verifies health of each service
- ✅ Handles port conflicts
- ✅ Provides clear error messages

**Access Points:**
- 🛡️ **Healing Dashboard**: http://localhost:5001
- 📈 **Monitoring Server**: http://localhost:5000
- 🤖 **DDoS Model API**: http://localhost:8080
- 🔍 **Network Analyzer**: http://localhost:8000
- 🚨 **Incident Bot**: http://localhost:8001

📖 **See [QUICK_START.md](QUICK_START.md) for detailed setup instructions**

---

### 🎯 **Alternative: Modular CLI Interface**

**Python-based command-line interface:**

```bash
# Start all services
python3 -m healx start

# Stop all services
python3 -m healx stop

# Check service status
python3 -m healx status

# View service logs
python3 -m healx logs <service_name>
```

The modular structure provides:
- **Unified configuration**: Centralized config management via `monitoring/server/core/config.py`
- **Service manager**: Unified service initialization and health checking
- **Modular healing**: Healing actions organized in `monitoring/server/healing/actions/`
- **Easy extensibility**: Add new healing actions by extending the actions package

### 🛡️ **Unified Dashboard (Alternative)**

**Complete ML Monitoring + System Healing Control Center:**

   # Stop current server, then:
   cd /home/cdrditgis/Documents/Healing-bot
   source venv/bin/activate
   python3 monitoring/server/healing_dashboard_api.py

**Combined Features:**
- 📊 ML Model Performance Metrics
- 🎯 DDoS Attack Detection  
- 🚫 IP Blocking Management
- ⚙️ Service Auto-Restart
- 🔍 Resource Hog Detection
- 🔐 SSH Intrusion Detection
- 🧹 Automated Disk Cleanup
- 🔔 Discord Alerts (replacing Slack)
- 🤖 AI Log Analysis (TF-IDF)
- ⚡ CLI Terminal Integration

**Healing Dashboard:**
- **Main Dashboard**: `http://localhost:5001` (All features including ML monitoring, healing, and system management)

📖 **[Healing Dashboard Guide](docs/guides/HEALING_DASHBOARD_GUIDE.md)**

---

### 🎯 **Alternative: Unified Launcher**

**Single Command to Run Everything:**

**Windows:**
```cmd
scripts\deployment\start-healing-bot.bat
```

**Linux/Mac:**
```bash
./scripts/deployment/start-healing-bot.sh
```

**Direct Python:**
```bash
python3 run-healing-bot.py
```

**With Virtual Environment:**
```bash
./scripts/setup/start-with-venv.sh
```

**Ubuntu Comprehensive Launcher:**
```bash
# Full-featured launcher with dependency management
./scripts/deployment/start-healing-bot-ubuntu.sh

# Install dependencies first (one-time)
sudo ./scripts/deployment/start-healing-bot-ubuntu.sh --install-deps

# View all options
./scripts/deployment/start-healing-bot-ubuntu.sh --help
```

### Prerequisites
- **Python 3.8 or higher** (check with `python3 --version`)
- **pip** (Python package manager)
- **curl** (for health checks, usually pre-installed)
- Docker (optional, for containerized deployment)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Heal-X-Bot
   ```

2. **Start the system:**
   ```bash
   ./start.sh
   ```
   
   That's it! The script handles everything automatically.

3. **Alternative methods:**
   ```bash
   # Python launcher
   python3 run-healing-bot.py
   
   # Or use the CLI module
   python3 -m healx start
   ```

### 🌐 Access Points

Once running, access the system at:

- **🛡️ Healing Dashboard**: http://localhost:5001 (Main UI)
- **📈 Monitoring Server**: http://localhost:5000
- **🤖 DDoS Model API**: http://localhost:8080
- **🔍 Network Analyzer**: http://localhost:8000
- **🚨 Incident Bot**: http://localhost:8001
- **📊 Prometheus**: http://localhost:9090 (Docker mode only)

### 🎛️ **Unified Launcher Features**

The new unified launcher (`run-healing-bot.py`) provides:

- **🎯 Single Command**: Run entire system with one command
- **🐳 Docker Support**: Full containerized deployment
- **🐍 Native Python**: Direct execution for development
- **🤖 Auto-Detection**: Automatically chooses best execution method
- **🔧 Smart Setup**: Automatic dependency installation and configuration
- **🛠️ Auto-Fix**: Automatically fixes missing dependencies and retries failed services
- **📊 Health Monitoring**: Waits for services to become healthy
- **🛑 Graceful Shutdown**: Clean shutdown of all services
- **🌐 Cross-Platform**: Works on Windows, Linux, and macOS
- **🚀 Zero-Config**: No separate setup scripts needed

**Usage Examples:**
```bash
# Auto-detect and start everything
python run-healing-bot.py

# Force Docker execution
python run-healing-bot.py --mode docker

# Force native Python execution  
python run-healing-bot.py --mode native

# Start specific services
python run-healing-bot.py --services model dashboard

# Setup only (don't start services)
python run-healing-bot.py --setup-only
```

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Dashboard     │    │  Network        │    │   ML Model      │
│   (Port 5001)   │◄──►│  Analyzer       │◄──►│   (Port 8080)   │
│                 │    │  (Port 8000)    │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Incident Bot   │    │   IP Blocker    │    │   Prometheus    │
│  (Port 8000)    │    │   (SQLite)      │    │   (Port 9090)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Slack Integration
SLACK_WEBHOOK=your_slack_webhook_url_here

# AWS S3 (Optional)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your_bucket_name

```

### Port Configuration

The system uses the following ports by default:
- **Healing Dashboard**: 5001 (Main UI)
- **Model API**: 8080
- **Incident Bot**: 8001
- **Network Analyzer**: 8000
- **Monitoring Server**: 5000 (API-only)
- **Prometheus**: 9090

## 📊 Dashboard Features

### **IP Blocking Management**
- **Blocked IPs Table**: View all currently blocked IPs
- **Statistics Cards**: Real-time blocking statistics
- **Manual Blocking**: Block IPs with custom reasons
- **Unblock Actions**: One-click IP unblocking

### **Threat Detection**
- **Real-time Alerts**: Live threat detection updates
- **Attack Patterns**: Visual representation of attack types
- **Source IP Tracking**: Monitor suspicious IP addresses
- **Threat Level Indicators**: Color-coded risk assessment

### **System Monitoring**
- **Performance Metrics**: CPU, Memory, Network usage
- **ML Model Stats**: Accuracy, Precision, Recall, F1-Score
- **Throughput Monitoring**: Requests per second tracking
- **Health Status**: Service health indicators

## 🛡️ Security Features

### **Automatic Protection**
- **High Threat Auto-block**: Blocks IPs with threat level ≥ 80%
- **Pattern-based Detection**: Identifies attack patterns automatically
- **Repeat Offender Handling**: Enhanced blocking for repeat offenders
- **Real-time Response**: Immediate protection against threats

### **Manual Controls**
- **Admin Interface**: Full control over IP blocking
- **Custom Reasons**: Specify blocking reasons
- **Threat Level Setting**: Manual threat level assignment
- **Bulk Operations**: Manage multiple IPs efficiently

## 📈 Analytics & Reporting

### **Blocking Statistics**
- **Total Blocked**: All-time blocked IP count
- **Auto vs Manual**: Breakdown of blocking methods
- **Blocking Rate**: Efficiency percentage
- **Recent Activity**: Last 24 hours activity
- **Attack Types**: Distribution of attack types
- **Threat Levels**: Risk level categorization

### **Performance Metrics**
- **Detection Accuracy**: ML model performance
- **Response Time**: System response metrics
- **Throughput**: System capacity metrics
- **Uptime**: Service availability tracking

## 🔧 Development

### **Project Structure**
```
Healing-bot/
├── incident-bot/              # AI incident response bot
├── model/                     # ML DDoS detection model
├── monitoring/
│   ├── dashboard/             # Web dashboard
│   ├── server/                # Monitoring server
│   │   ├── core/              # Core modules (NEW)
│   │   │   ├── config.py      # Configuration management
│   │   │   └── service_manager.py  # Service initialization
│   │   ├── healing/           # Auto-healing system (NEW)
│   │   │   ├── orchestrator.py  # Main healing orchestration
│   │   │   ├── actions/         # Healing actions
│   │   │   │   ├── system.py    # System actions
│   │   │   │   ├── container.py # Container actions
│   │   │   │   └── resource.py  # Resource actions
│   │   │   ├── verification.py  # Verification logic
│   │   │   ├── notifications.py # Notification logic
│   │   │   ├── instructions.py  # Manual instructions
│   │   │   └── history.py       # Healing history
│   │   ├── app.py             # Flask API
│   │   └── network_analyzer.py # Network analyzer
│   └── prometheus/            # Metrics collection
├── healx/                     # CLI package (NEW)
│   ├── cli.py                 # Command-line interface
│   └── __main__.py            # Module entry point
├── setup.py                   # Setup script
├── requirements.txt           # Dependencies
└── README.md                  # This file
```

### **Key Components**

1. **CLI Interface** (`healx/cli.py`) (NEW)
   - Unified command-line interface
   - Start, stop, status, and logs commands
   - Easy service management

2. **Configuration Management** (`monitoring/server/core/config.py`) (NEW)
   - Centralized configuration loading
   - Environment variable management
   - Configuration validation

3. **Service Manager** (`monitoring/server/core/service_manager.py`) (NEW)
   - Unified service initialization
   - Dependency management
   - Health checking

4. **Auto-Healing System** (`monitoring/server/healing/`) (NEW - Modularized)
   - **Orchestrator**: Main healing coordination (`orchestrator.py`)
   - **Actions**: Modular healing actions
     - System actions: service restart, permissions, cache clearing
     - Container actions: container restart, start, recreate
     - Resource actions: resource cleanup, network restore
   - **Verification**: Healing verification logic
   - **Notifications**: Discord/notification integration
   - **Instructions**: Manual instruction generation
   - **History**: Healing attempt tracking

5. **IP Blocker** (`monitoring/server/ip_blocker.py`)
   - Automatic IP blocking logic
   - SQLite database management
   - Statistics tracking

6. **Monitoring Server** (`monitoring/server/app.py`)
   - System log collection and analysis
   - Critical services monitoring
   - API endpoints for IP management
   - AI-powered log analysis
   - WebSocket integration

7. **Dashboard** (`monitoring/dashboard/`)
   - React-based web interface
   - Real-time updates
   - IP management controls

8. **ML Model** (`model/`)
   - TensorFlow-based DDoS detection
   - XGBoost-based Predictive Maintenance (NEW)
   - Feature extraction and analysis
   - Prediction and confidence scoring
   - Failure prediction and early warnings

## 🚨 Troubleshooting

### **Common Issues**

1. **Port Conflicts**: Ensure ports 5001, 8080, 8000, 8001 are available
2. **Python Dependencies**: Run `pip install -r requirements.txt`
3. **Database Issues**: Check SQLite file permissions
4. **API Connectivity**: Verify service communication

### **Logs**
- Check console output for error messages
- Logs are stored in respective service directories
- Use `--verbose` flag for detailed logging

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the documentation in `docs/`

## 📚 Documentation

Comprehensive documentation is available in the `docs/` directory:

### Quick Links
- **📖 Setup Guide** - `docs/guides/UBUNTU_DEPLOYMENT_GUIDE.md`
- **⚙️ Configuration** - `docs/guides/ENV_SETUP_GUIDE.md`
- **🚀 Launcher Guide** - `docs/guides/UNIFIED_LAUNCHER_README.md`
- **🔍 Monitoring** - `docs/guides/SYSTEM_MONITORING_QUICK_REF.md`
- **🤖 AI Features** - `docs/guides/GEMINI_LOG_ANALYSIS_COMPLETE.md`
- **🧪 Testing** - `docs/guides/TEST_ANOMALIES_README.md`

See `docs/README.md` for the complete documentation index.

---
# 1. Start all services
docker-compose -f config/docker-compose.yml up -d

# 2. Wait 2-3 minutes for initialization

# 3. Test service health
curl http://localhost:8080/health    # Model API
curl http://localhost:8000/health    # Network Analyzer
curl http://localhost:5001/api/health # Healing Dashboard
curl http://localhost:5000/health    # Monitoring Server
curl http://localhost:8001/health    # Incident Bot

# 4. Test metrics endpoints
curl http://localhost:8080/metrics   # Model API metrics
curl http://localhost:8000/metrics   # Network Analyzer metrics
curl http://localhost:5001/metrics   # Healing Dashboard metrics
curl http://localhost:5000/metrics   # Monitoring Server metrics

# 5. Access Prometheus (Docker mode)
http://localhost:9090/targets       # Prometheus targets
http://localhost:9090/graph         # Prometheus metrics & queries



**🛡️ Stay Protected with AI-Powered Security!**