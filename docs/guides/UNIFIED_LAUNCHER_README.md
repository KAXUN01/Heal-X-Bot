# 🛡️ Healing-bot: Unified System Launcher

A single script to run the entire healing-bot system with support for both Docker and native Python execution.

## 🚀 Quick Start

### Option 1: Simple Launcher (Recommended)

**Windows:**
```cmd
start-healing-bot.bat
```

**Linux/Mac:**
```bash
./start-healing-bot.sh
```

### Option 2: Direct Python Execution

```bash
python run-healing-bot.py
```

## 📋 Features

### 🎯 **Unified Execution**
- **Single Script**: Run the entire system with one command
- **Auto-Detection**: Automatically chooses Docker or native Python execution
- **Cross-Platform**: Works on Windows, Linux, and macOS
- **Service Management**: Handles starting, stopping, and monitoring all services

### 🐳 **Docker Support**
- **Full Stack**: Runs all services in containers
- **Production Ready**: Includes Prometheus, Grafana, and monitoring
- **Isolated Environment**: Clean, reproducible deployments
- **Easy Scaling**: Simple horizontal scaling

### 🐍 **Native Python Support**
- **Development Friendly**: Direct Python execution for development
- **Fast Startup**: Quick iteration and testing
- **Debug Support**: Easy debugging and logging
- **Resource Efficient**: Lower resource usage

### 🔧 **Smart Features**
- **Dependency Checking**: Automatically checks and installs dependencies
- **Port Validation**: Ensures required ports are available
- **Health Monitoring**: Waits for services to become healthy
- **Graceful Shutdown**: Clean shutdown of all services
- **Environment Setup**: Creates .env files and directories

## 🎛️ Usage Options

### Basic Usage
```bash
# Auto-detect best execution method
python run-healing-bot.py

# Force Docker execution
python run-healing-bot.py --mode docker

# Force native Python execution
python run-healing-bot.py --mode native

# Start only specific services
python run-healing-bot.py --services model dashboard
```

### Advanced Options
```bash
# Setup environment only (don't start services)
python run-healing-bot.py --setup-only

# Start with specific services
python run-healing-bot.py --services model network-analyzer dashboard

# Use wrapper scripts
./start-healing-bot.sh --mode docker
start-healing-bot.bat --services model dashboard
```

## 🌐 Service Architecture

### Core Services
| Service | Port | Description | Docker Service |
|---------|------|-------------|----------------|
| **Model API** | 8080 | DDoS detection ML model | `model` |
| **Network Analyzer** | 8000 | Traffic analysis & IP blocking | `network-analyzer` |
| **Dashboard** | 3001 | Main monitoring interface | `dashboard` |
| **Incident Bot** | 8000 | AI incident response | `incident-bot` |
| **Monitoring Server** | 5000 | System metrics & health | `server` |

### Monitoring Services (Docker only)
| Service | Port | Description |
|---------|------|-------------|
| **Prometheus** | 9090 | Metrics collection |
| **Grafana** | 3000 | Advanced dashboards |

## 🔧 Configuration

### Environment Variables
The system automatically creates a `.env` file from `env.template` if it doesn't exist. Configure these variables:

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

# Grafana (Optional)
GRAFANA_ADMIN_PASSWORD=admin
```

### Port Configuration
Default ports can be overridden in the `.env` file:
```env
MODEL_PORT=8080
DASHBOARD_PORT=3001
NETWORK_ANALYZER_PORT=8000
INCIDENT_BOT_PORT=8000
```

## 🚀 Execution Modes

### 🐳 Docker Mode (Production)
- **Full Stack**: All services including monitoring
- **Isolated**: Each service runs in its own container
- **Scalable**: Easy to scale individual services
- **Production Ready**: Includes Prometheus, Grafana, and alerting

**Requirements:**
- Docker
- Docker Compose

**Usage:**
```bash
python run-healing-bot.py --mode docker
```

### 🐍 Native Mode (Development)
- **Fast Startup**: Direct Python execution
- **Easy Debugging**: Direct access to logs and processes
- **Resource Efficient**: Lower memory and CPU usage
- **Development Friendly**: Quick iteration and testing

**Requirements:**
- Python 3.8+
- pip

**Usage:**
```bash
python run-healing-bot.py --mode native
```

### 🤖 Auto Mode (Recommended)
- **Smart Detection**: Automatically chooses the best method
- **Fallback Support**: Falls back to native if Docker unavailable
- **User Friendly**: No need to specify execution method

**Usage:**
```bash
python run-healing-bot.py  # or just use the wrapper scripts
```

## 📊 Access Points

Once the system is running, access these endpoints:

### Core Services
- **📊 Dashboard**: http://localhost:3001 - Main monitoring interface
- **🤖 Model API**: http://localhost:8080 - DDoS detection model
- **🔍 Network Analyzer**: http://localhost:8000 - Traffic analysis
- **🚨 Incident Bot**: http://localhost:8000 - AI incident response
- **📈 Monitoring Server**: http://localhost:5000 - System metrics

### Monitoring (Docker only)
- **📊 Prometheus**: http://localhost:9090 - Metrics collection
- **📈 Grafana**: http://localhost:3000 - Advanced dashboards

## 🛠️ Troubleshooting

### Common Issues

#### Port Conflicts
```bash
# Check what's using the ports
netstat -tulpn | grep :8080
netstat -tulpn | grep :3001
netstat -tulpn | grep :8000

# Kill processes using the ports (Linux/Mac)
sudo lsof -ti:8080 | xargs kill -9
```

#### Docker Issues
```bash
# Check Docker status
docker --version
docker-compose --version

# Restart Docker services
docker-compose down
docker-compose up -d
```

#### Python Dependencies
```bash
# Install dependencies manually
pip install -r requirements.txt
pip install -r model/requirements.txt
pip install -r monitoring/server/requirements.txt
pip install -r monitoring/dashboard/requirements.txt
pip install -r incident-bot/requirements.txt
```

#### Service Health Checks
```bash
# Check if services are responding
curl http://localhost:8080/health
curl http://localhost:8000/active-threats
curl http://localhost:3001/api/health
curl http://localhost:5000/health
```

### Logs and Debugging

#### Docker Logs
```bash
# View all service logs
docker-compose logs

# View specific service logs
docker-compose logs model
docker-compose logs dashboard
```

#### Native Python Logs
- Check console output for each service
- Logs are displayed in the terminal where the script is running
- Use `--verbose` flag for detailed logging

## 🔄 Service Management

### Starting Services
```bash
# Start all services
python run-healing-bot.py

# Start specific services
python run-healing-bot.py --services model dashboard
```

### Stopping Services
- **Ctrl+C**: Graceful shutdown of all services
- **Docker**: `docker-compose down`
- **Native**: Automatic process termination

### Restarting Services
```bash
# Stop and start again
python run-healing-bot.py --mode docker
```

## 📈 Performance Monitoring

### System Metrics
- **CPU Usage**: Real-time CPU monitoring
- **Memory Usage**: RAM consumption tracking
- **Network Traffic**: Bandwidth and connection monitoring
- **Service Health**: Individual service status

### ML Model Metrics
- **Accuracy**: Model prediction accuracy
- **Precision**: True positive rate
- **Recall**: Detection rate
- **F1-Score**: Balanced performance metric

## 🔒 Security Features

### Automatic Protection
- **DDoS Detection**: Real-time attack detection
- **IP Blocking**: Automatic malicious IP blocking
- **Threat Assessment**: Risk level evaluation
- **Pattern Recognition**: Attack pattern identification

### Manual Controls
- **Admin Interface**: Web-based management
- **IP Management**: Block/unblock IPs manually
- **Statistics**: Detailed blocking analytics
- **Alerts**: Real-time security notifications

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with both Docker and native modes
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the troubleshooting section
- Review service logs
- Create an issue in the repository
- Check the main README.md for detailed documentation

---

**🛡️ Stay Protected with AI-Powered Security!**
