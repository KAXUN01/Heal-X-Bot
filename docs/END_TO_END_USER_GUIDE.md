# 📖 Heal-X-Bot: End-to-End User Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Installation Guide](#installation-guide)
3. [Configuration Guide](#configuration-guide)
4. [Getting Started](#getting-started)
5. [Daily Operations](#daily-operations)
6. [Advanced Usage](#advanced-usage)
7. [Dashboard Usage](#dashboard-usage)
8. [API Usage](#api-usage)
9. [Troubleshooting](#troubleshooting)
10. [Best Practices](#best-practices)
11. [Maintenance](#maintenance)
12. [FAQs](#faqs)

---

## Introduction

This guide provides step-by-step instructions for installing, configuring, and using Heal-X-Bot. Whether you're a system administrator, DevOps engineer, or security professional, this guide will help you get the most out of Heal-X-Bot.

### Prerequisites

Before starting, ensure you have:

- **Operating System**: Linux (Ubuntu 18.04+ recommended), macOS, or Windows
- **Python**: Version 3.8 or higher
- **Memory**: Minimum 2GB RAM (4GB+ recommended)
- **Disk Space**: At least 5GB free space
- **Network**: Internet connection for initial setup
- **Permissions**: sudo/administrator access for service management

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | 2 cores | 4+ cores |
| **RAM** | 2GB | 4GB+ |
| **Disk** | 5GB | 10GB+ |
| **Network** | 10 Mbps | 100 Mbps+ |

---

## Installation Guide

### Method 1: Quick Start (Recommended)

The fastest way to get started with Heal-X-Bot:

```bash
# Clone the repository
git clone <repository-url>
cd Heal-X-Bot

# Run the unified startup script
./start.sh
```

That's it! The script will:
- ✅ Check Python version
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Set up environment file
- ✅ Start all services
- ✅ Verify health of each service

### Method 2: Manual Installation

For more control over the installation process:

#### Step 1: Clone Repository

```bash
git clone <repository-url>
cd Heal-X-Bot
```

#### Step 2: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

#### Step 4: Set Up Environment File

```bash
cp config/env.template .env
# Edit .env with your configuration
nano .env
```

#### Step 5: Start Services

```bash
# Start all services
python3 -m healx start

# Or start individually
python3 model/main.py &
python3 monitoring/server/network_analyzer.py &
python3 monitoring/server/app.py &
python3 incident-bot/main.py &
python3 monitoring/server/healing_dashboard_api.py &
```

### Method 3: Docker Installation

For containerized deployment:

```bash
# Build and start all services
docker-compose -f config/docker-compose.yml up -d

# Check service status
docker-compose -f config/docker-compose.yml ps

# View logs
docker-compose -f config/docker-compose.yml logs -f
```

### Verification

After installation, verify all services are running:

```bash
# Check service health
curl http://localhost:8080/health    # Model API
curl http://localhost:8000/health    # Network Analyzer
curl http://localhost:5000/health    # Monitoring Server
curl http://localhost:8001/health    # Incident Bot
curl http://localhost:5001/api/health # Healing Dashboard
```

All services should return `{"status": "healthy"}`.

---

## Configuration Guide

### Environment Variables

Create a `.env` file in the project root:

```bash
# AI Configuration (Optional but recommended)
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Notification Configuration
DISCORD_WEBHOOK=your_discord_webhook_url_here
SLACK_WEBHOOK=your_slack_webhook_url_here  # Optional

# AWS S3 Configuration (Optional)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your_bucket_name

# Port Configuration (Optional - defaults shown)
DASHBOARD_PORT=5001
MODEL_API_PORT=8080
MONITORING_SERVER_PORT=5000
NETWORK_ANALYZER_PORT=8000
INCIDENT_BOT_PORT=8001

# Threshold Configuration (Optional - defaults shown)
CPU_WARNING_THRESHOLD=75
CPU_CRITICAL_THRESHOLD=90
MEMORY_WARNING_THRESHOLD=80
MEMORY_CRITICAL_THRESHOLD=85
DISK_WARNING_THRESHOLD=80
DISK_CRITICAL_THRESHOLD=90

# DDoS Detection Configuration
DDOS_AUTO_BLOCK_THRESHOLD=0.8
DDOS_DETECTION_THRESHOLD=0.5

# Predictive Maintenance Configuration
PREDICTIVE_RISK_THRESHOLD=0.7
PREDICTION_HORIZON=1,6,24
```

### Service Configuration

Edit `config/services.yaml` to configure services:

```yaml
services:
  nginx:
    auto_restart: true
    health_check: true
    check_interval: 30
  mysql:
    auto_restart: true
    health_check: true
    check_interval: 60
  docker:
    auto_restart: true
    health_check: true
```

### ML Model Configuration

#### DDoS Model

The DDoS model is pre-trained and ready to use. No additional configuration needed.

#### Predictive Maintenance Model

Train the model if needed:

```bash
cd model
python3 train_xgboost_model.py --enable-regression
```

### Notification Configuration

#### Discord Setup

1. Create a Discord webhook:
   - Go to Discord Server Settings → Integrations → Webhooks
   - Create New Webhook
   - Copy Webhook URL

2. Add to `.env`:
   ```bash
   DISCORD_WEBHOOK=https://discord.com/api/webhooks/...
   ```

3. Test notification:
   ```bash
   curl -X POST http://localhost:5001/api/discord/test
   ```

---

## Getting Started

### First-Time Setup

1. **Start Services**:
   ```bash
   ./start.sh
   ```

2. **Access Dashboard**:
   Open browser: `http://localhost:5001`

3. **Verify Services**:
   Check that all services show "Healthy" status

4. **Configure Notifications** (Optional):
   - Go to Dashboard → Settings → Notifications
   - Add Discord webhook
   - Test notification

5. **Review Default Settings**:
   - Check thresholds in Dashboard → Settings
   - Adjust if needed for your environment

### Basic Operations

#### Start Services

```bash
# Start all services
./start.sh

# Or using Python CLI
python3 -m healx start
```

#### Stop Services

```bash
# Stop all services
./start.sh stop

# Or using Python CLI
python3 -m healx stop
```

#### Check Status

```bash
# Check service status
./start.sh status

# Or using Python CLI
python3 -m healx status
```

#### View Logs

```bash
# View logs for specific service
python3 -m healx logs <service_name>

# View all logs
tail -f logs/*.log
```

---

## Daily Operations

### Monitoring Dashboard

#### Accessing the Dashboard

1. Open browser: `http://localhost:5001`
2. Dashboard loads automatically
3. Real-time updates every 2 seconds

#### Dashboard Tabs

1. **Overview**: System status and key metrics
2. **Attacks**: DDoS attack detection and statistics
3. **Blocking**: IP blocking management
4. **Geographic**: Attack source mapping
5. **Analytics**: Historical data analysis
6. **Logs**: System and AI logs

#### Key Metrics to Monitor

- **CPU Usage**: Should stay below 75% (warning), 90% (critical)
- **Memory Usage**: Should stay below 80% (warning), 85% (critical)
- **Disk Usage**: Should stay below 80% (warning), 90% (critical)
- **DDoS Attacks**: Monitor attack frequency and blocked IPs
- **Service Health**: All services should show "Running"

### IP Blocking Management

#### View Blocked IPs

1. Go to Dashboard → Blocking tab
2. View blocked IPs table
3. Use search/filter to find specific IPs

#### Unblock IP

1. Find IP in blocked IPs table
2. Click "Unblock" button
3. Confirm action
4. IP is immediately unblocked

#### Manual Block IP

1. Go to Dashboard → Blocking tab
2. Click "Block IP" button
3. Enter IP address and reason
4. Click "Block"
5. IP is immediately blocked

### Service Management

#### View Service Status

1. Go to Dashboard → Services tab
2. View all monitored services
3. Status indicators:
   - 🟢 Green: Running
   - 🔴 Red: Stopped
   - 🟡 Yellow: Restarting

#### Restart Service

1. Find service in services table
2. Click "Restart" button
3. Service restarts automatically
4. Status updates in real-time

#### Enable Auto-Restart

1. Go to Dashboard → Settings → Services
2. Toggle "Auto-Restart" ON
3. Services restart automatically if they fail

### Resource Management

#### View Resource Usage

1. Go to Dashboard → Overview
2. View CPU, Memory, Disk metrics
3. Check for warnings/critical alerts

#### Process Management

1. Go to Dashboard → Processes tab
2. View top CPU/Memory processes
3. Kill processes if needed:
   - Click "Kill" button
   - Confirm action

#### Disk Cleanup

1. Go to Dashboard → Disk tab
2. View disk usage
3. Click "Cleanup" if usage > threshold
4. Cleanup runs automatically if enabled

---

## Advanced Usage

### ML Model Management

#### Train Predictive Maintenance Model

```bash
cd model

# Basic training
python3 train_xgboost_model.py

# With regression model
python3 train_xgboost_model.py --enable-regression

# With custom data
python3 train_xgboost_model.py --data-path /path/to/data.csv
```

#### Verify Models

```bash
cd model
python3 verify_model.py
```

#### Collect Training Data

```bash
cd model

# Collect for 24 hours
python3 collect_training_data.py --duration 24 --interval 60

# Collect once
python3 collect_training_data.py --once
```

#### Automated Retraining

```bash
cd model

# Check if retraining needed
python3 automated_retraining.py

# Force retraining
python3 automated_retraining.py --force
```

### API Usage

#### REST API Examples

**Get System Metrics**:
```bash
curl http://localhost:5001/api/metrics
```

**Get Failure Risk**:
```bash
curl http://localhost:5001/api/predict-failure-risk
```

**Block IP**:
```bash
curl -X POST http://localhost:5001/api/blocking/block \
  -H "Content-Type: application/json" \
  -d '{"ip": "192.168.1.100", "reason": "Suspicious activity"}'
```

**Restart Service**:
```bash
curl -X POST http://localhost:5001/api/services/nginx/restart
```

#### WebSocket Connection

```javascript
const ws = new WebSocket('ws://localhost:5001/ws/healing');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Metrics:', data);
};
```

### Custom Configuration

**Service-Specific Settings**:
Edit `config/services.yaml`:
```yaml
services:
  nginx:
    auto_restart: true
    max_retries: 3
    retry_delay: 5
```

**Threshold Configuration**:
Edit `.env`:
```bash
CPU_WARNING_THRESHOLD=75
CPU_CRITICAL_THRESHOLD=90
```

---

## Dashboard Usage

### Overview Tab

**Purpose**: System status and key metrics at a glance.

**Key Information**:
- Real-time CPU, Memory, Disk, Network usage
- Service health status
- Recent alerts
- System health score

**Actions**:
- View detailed metrics
- Access service management
- Check recent alerts

### Attacks Tab

**Purpose**: DDoS attack detection and statistics.

**Key Information**:
- Recent attacks detected
- Attack types and frequencies
- Threat levels
- Attack timeline

**Actions**:
- View attack details
- Analyze attack patterns
- Export attack data

### Blocking Tab

**Purpose**: IP blocking management.

**Key Information**:
- Blocked IPs list
- Blocking statistics
- Block reasons
- Block timestamps

**Actions**:
- Block/unblock IPs
- Search and filter
- Export blocked IPs
- View statistics

### Geographic Tab

**Purpose**: Attack source mapping.

**Key Information**:
- Attack sources by country
- City-level tracking
- Attack frequency map
- Geographic distribution

**Actions**:
- View geographic data
- Filter by country
- Export geographic data

### Analytics Tab

**Purpose**: Historical data analysis.

**Key Information**:
- Historical trends
- Performance metrics
- Attack patterns over time
- System health history

**Actions**:
- Select time range
- View charts
- Export analytics data
- Generate reports

### Logs Tab

**Purpose**: System and AI logs.

**Key Information**:
- Recent log entries
- Log severity levels
- AI analysis results
- Search and filter

**Actions**:
- Search logs
- Filter by severity
- View AI analysis
- Export logs

---

## API Usage

### Authentication

Currently, the API does not require authentication for local access. For production deployments, implement authentication.

### Endpoints

#### Health Check

```bash
GET /api/health
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-19T12:00:00"
}
```

#### System Metrics

```bash
GET /api/metrics
```

**Response**:
```json
{
  "cpu": 45.2,
  "memory": 62.8,
  "disk": 58.3,
  "network": {
    "bytes_sent": 1234567,
    "bytes_recv": 7654321
  }
}
```

#### DDoS Prediction

```bash
POST /api/predict
Content-Type: application/json

{
  "metrics": {
    "Protocol": 6,
    "Flow Duration": 120.5,
    ...
  }
}
```

#### Failure Risk Prediction

```bash
GET /api/predict-failure-risk
```

**Response**:
```json
{
  "risk_score": 0.75,
  "risk_percentage": 75.0,
  "has_early_warning": true
}
```

#### Block IP

```bash
POST /api/blocking/block
Content-Type: application/json

{
  "ip": "192.168.1.100",
  "reason": "Suspicious activity",
  "threat_level": 0.9
}
```

#### Unblock IP

```bash
POST /api/blocking/unblock
Content-Type: application/json

{
  "ip": "192.168.1.100"
}
```

---

## Troubleshooting

### Common Issues

#### Services Won't Start

**Symptoms**: Services fail to start or crash immediately.

**Solutions**:
1. Check Python version: `python3 --version` (should be 3.8+)
2. Check port availability: `lsof -i :5001`
3. Check logs: `tail -f logs/*.log`
4. Verify dependencies: `pip install -r requirements.txt`
5. Check permissions: Ensure you have necessary permissions

#### Port Already in Use

**Symptoms**: Error message about port being in use.

**Solutions**:
```bash
# Find process using port
lsof -i :5001

# Kill process
kill -9 <PID>

# Or stop all services first
./start.sh stop
```

#### Model Not Loading

**Symptoms**: "Model not available" error.

**Solutions**:
1. Check model file exists: `ls -la model/ddos_model.keras`
2. Train model if missing: `cd model && python3 train_ddos_model.py`
3. Check permissions: `chmod -R 755 model/`
4. Verify model format: Ensure .keras file is valid

#### Dashboard Not Loading

**Symptoms**: Dashboard shows errors or won't load.

**Solutions**:
1. Check service health: `curl http://localhost:5001/api/health`
2. Check browser console for errors
3. Clear browser cache
4. Verify WebSocket connection
5. Check firewall settings

#### High CPU/Memory Usage

**Symptoms**: System resources exhausted.

**Solutions**:
1. Check resource hogs: Dashboard → Processes
2. Kill high-usage processes
3. Adjust update intervals in configuration
4. Reduce log retention period
5. Scale up resources if needed

#### DDoS Detection Not Working

**Symptoms**: Attacks not being detected.

**Solutions**:
1. Verify model is loaded: `curl http://localhost:8080/health`
2. Check network analyzer: `curl http://localhost:8000/health`
3. Verify thresholds in configuration
4. Check logs for errors
5. Test with known attack pattern

### Debug Mode

Enable debug logging:

```bash
# Set environment variable
export LOG_LEVEL=DEBUG

# Restart services
./start.sh restart
```

### Log Analysis

**View Recent Logs**:
```bash
tail -f logs/healing_dashboard.log
tail -f logs/model.log
tail -f logs/monitoring_server.log
```

**Search Logs**:
```bash
grep -r "ERROR" logs/
grep -r "WARNING" logs/
```

**Log Locations**:
- Dashboard: `logs/healing_dashboard.log`
- Model API: `logs/model.log`
- Monitoring: `logs/monitoring_server.log`
- Network Analyzer: `logs/network_analyzer.log`
- Incident Bot: `logs/incident_bot.log`

---

## Best Practices

### Security

1. **Change Default Ports**: Use non-standard ports in production
2. **Enable Authentication**: Implement API authentication
3. **Use HTTPS**: Enable SSL/TLS for production
4. **Regular Updates**: Keep system and dependencies updated
5. **Monitor Logs**: Regularly review security logs

### Performance

1. **Resource Monitoring**: Monitor system resources regularly
2. **Optimize Thresholds**: Adjust thresholds based on your environment
3. **Regular Cleanup**: Schedule regular disk cleanup
4. **Model Retraining**: Retrain models periodically
5. **Database Maintenance**: Regularly backup and optimize database

### Operations

1. **Backup Configuration**: Regularly backup configuration files
2. **Document Changes**: Document any custom configurations
3. **Test Changes**: Test changes in staging before production
4. **Monitor Alerts**: Respond to alerts promptly
5. **Regular Reviews**: Review system health weekly

### Maintenance

1. **Update Dependencies**: Keep dependencies updated
2. **Model Updates**: Retrain models with new data
3. **Log Rotation**: Implement log rotation
4. **Database Backup**: Regular database backups
5. **Health Checks**: Regular health check reviews

---

## Maintenance

### Regular Tasks

#### Daily

- Check dashboard for alerts
- Review blocked IPs
- Monitor system health

#### Weekly

- Review system logs
- Check model performance
- Review blocked IP statistics
- Verify backups

#### Monthly

- Retrain predictive model
- Review and optimize thresholds
- Update dependencies
- Review security logs

### Backup

**Configuration Backup**:
```bash
# Backup configuration files
tar -czf backup-config-$(date +%Y%m%d).tar.gz \
  .env config/ logs/ model/artifacts/
```

**Database Backup**:
```bash
# Backup SQLite database
cp monitoring/server/data/blocked_ips.db \
  backups/blocked_ips-$(date +%Y%m%d).db
```

### Updates

**Update System**:
```bash
# Pull latest changes
git pull

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart services
./start.sh restart
```

**Update Models**:
```bash
cd model
python3 train_xgboost_model.py --enable-regression
```

---

## FAQs

### General

**Q: What operating systems are supported?**  
A: Linux (Ubuntu 18.04+), macOS, and Windows.

**Q: How much resources does it need?**  
A: Minimum 2GB RAM, 2 CPU cores, 5GB disk. Recommended: 4GB+ RAM, 4+ cores.

**Q: Is it free?**  
A: Yes, Heal-X-Bot is open-source and free to use.

**Q: Can I use it in production?**  
A: Yes, but ensure proper security configuration and testing.

### Technical

**Q: How accurate is DDoS detection?**  
A: 92-95% accuracy with <5% false positive rate.

**Q: How far in advance can failures be predicted?**  
A: 1-24 hours with 85-90% early detection rate.

**Q: What ports does it use?**  
A: Default ports: 5001 (Dashboard), 8080 (Model), 5000 (Monitoring), 8000 (Network), 8001 (Incident Bot).

**Q: Can I customize thresholds?**  
A: Yes, all thresholds are configurable via `.env` file.

### Operations

**Q: How do I add a new service to monitor?**  
A: Edit `config/services.yaml` and add service configuration.

**Q: How do I change notification settings?**  
A: Update `.env` file with new webhook URLs or use dashboard settings.

**Q: How do I export data?**  
A: Use dashboard export features or API endpoints for programmatic access.

**Q: How do I scale the system?**  
A: Use Docker Compose for horizontal scaling or deploy multiple instances.

---

## Getting Help

### Documentation

- [System Documentation](COMPREHENSIVE_SYSTEM_DOCUMENTATION.md)
- [ML Models Documentation](ML_MODELS_DOCUMENTATION.md)
- [Features Documentation](FEATURES_DOCUMENTATION.md)
- [Use Cases Guide](USE_CASES_GUIDE.md)

### Support

- Check logs for error messages
- Review troubleshooting section
- Check GitHub issues
- Community forums

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-19  
**Maintained By**: Heal-X-Bot Development Team

