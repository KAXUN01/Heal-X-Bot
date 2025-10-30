# 🐧 Ubuntu Deployment Guide - Automatic Self-Healing Bot

Complete guide for deploying and running the Healing-bot system on Ubuntu/Debian Linux.

---

## 📋 Table of Contents

1. [System Requirements](#system-requirements)
2. [Quick Start (3 Commands)](#quick-start)
3. [Detailed Setup](#detailed-setup)
4. [Running the System](#running-the-system)
5. [Service Management](#service-management)
6. [Troubleshooting](#troubleshooting)
7. [Production Deployment](#production-deployment)
8. [Systemd Service Setup](#systemd-service-setup)

---

## 🖥️ System Requirements

### Minimum Requirements
- **OS**: Ubuntu 20.04+ or Debian 11+
- **CPU**: 2 cores
- **RAM**: 4 GB
- **Disk**: 10 GB free space
- **Python**: 3.8+

### Recommended Requirements
- **OS**: Ubuntu 22.04 LTS
- **CPU**: 4+ cores
- **RAM**: 8+ GB
- **Disk**: 20+ GB SSD
- **Python**: 3.10+

### Required Software
- Python 3.8+
- pip
- git
- curl
- build-essential

---

## 🚀 Quick Start (3 Commands)

### First-Time Setup

```bash
# 1. Run first-time setup (installs dependencies)
sudo ./quick-start-ubuntu.sh --first-time

# 2. Configure environment variables (add your Gemini API key)
python3 setup_env.py

# 3. Start the system
./quick-start-ubuntu.sh
```

**That's it!** 🎉

Access the dashboard at: http://localhost:3001

---

## 📦 Detailed Setup

### Step 1: Install System Dependencies

```bash
# Update package list
sudo apt update

# Install required packages
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    curl \
    git \
    net-tools \
    lsof

# Verify installation
python3 --version  # Should be 3.8+
pip3 --version
```

### Step 2: Clone Repository (if not done)

```bash
# If you haven't cloned the repo yet
git clone https://github.com/your-repo/healing-bot.git
cd healing-bot
```

### Step 3: Install Python Dependencies

```bash
# Upgrade pip
python3 -m pip install --upgrade pip

# Install all requirements
pip3 install -r requirements.txt
pip3 install -r monitoring/server/requirements.txt
pip3 install -r monitoring/dashboard/requirements.txt
pip3 install -r incident-bot/requirements.txt
pip3 install -r model/requirements.txt
```

### Step 4: Configure Environment Variables

**Option A: Interactive Setup (Recommended)**

```bash
python3 setup_env.py
```

This will guide you through:
- Adding Gemini API key (required)
- Configuring Slack webhook (optional)
- Setting up AWS S3 (optional)
- Port configuration (optional)

**Option B: Manual Setup**

```bash
# Copy template
cp env.template .env

# Edit with your favorite editor
nano .env
# or
vim .env
# or
code .env

# Add your Gemini API key:
# GEMINI_API_KEY=your_actual_key_here
```

Get your free Gemini API key: https://makersuite.google.com/app/apikey

### Step 5: Make Scripts Executable

```bash
chmod +x start-healing-bot-ubuntu.sh
chmod +x quick-start-ubuntu.sh
```

---

## 🎮 Running the System

### Method 1: Quick Start (Recommended)

```bash
./quick-start-ubuntu.sh
```

This will:
- Check dependencies
- Verify environment configuration
- Start all services in background
- Show access points

### Method 2: Full Control Script

```bash
# Start all services
./start-healing-bot-ubuntu.sh

# Or with options:
./start-healing-bot-ubuntu.sh --dev      # Development mode (separate terminals)
./start-healing-bot-ubuntu.sh --status   # Check status
./start-healing-bot-ubuntu.sh --stop     # Stop all services
./start-healing-bot-ubuntu.sh --logs     # View logs
./start-healing-bot-ubuntu.sh --help     # Show help
```

### Method 3: Development Mode

Opens each service in a separate terminal window:

```bash
./start-healing-bot-ubuntu.sh --dev
```

Requires: `gnome-terminal`, `xterm`, or `konsole`

### Method 4: Manual Start (Individual Services)

```bash
# Terminal 1: Model API
cd model
python3 main.py

# Terminal 2: Network Analyzer
cd monitoring/server
python3 network_analyzer.py

# Terminal 3: Monitoring Server
cd monitoring/server
python3 app.py

# Terminal 4: Dashboard
cd monitoring/dashboard
python3 app.py

# Terminal 5: Incident Bot
cd incident-bot
python3 main.py
```

---

## 🔧 Service Management

### Check Service Status

```bash
./start-healing-bot-ubuntu.sh --status
```

Output example:
```
Service                   Status
-------                   ------
model                     ✅ Running (PID: 12345, Port: 8080)
network-analyzer          ✅ Running (PID: 12346, Port: 8000)
monitoring-server         ✅ Running (PID: 12347, Port: 5000)
dashboard                 ✅ Running (PID: 12348, Port: 3001)
incident-bot              ✅ Running (PID: 12349, Port: 8001)
```

### View Logs

```bash
# View all logs
./start-healing-bot-ubuntu.sh --logs

# Follow specific service log
tail -f logs/dashboard.log

# Follow all logs in real-time
tail -f logs/*.log
```

### Stop Services

```bash
# Stop all services gracefully
./start-healing-bot-ubuntu.sh --stop

# Force stop if needed
pkill -f "model/main.py"
pkill -f "network_analyzer.py"
pkill -f "monitoring/server/app.py"
pkill -f "monitoring/dashboard/app.py"
pkill -f "incident-bot/main.py"
```

### Restart Services

```bash
# Stop and start
./start-healing-bot-ubuntu.sh --stop
./start-healing-bot-ubuntu.sh
```

---

## 🐛 Troubleshooting

### Problem 1: Port Already in Use

**Error:** `Address already in use` or `Port XXXX is already in use`

**Solution:**

```bash
# Find process using port (e.g., 3001)
sudo lsof -i :3001

# Kill the process
kill -9 <PID>

# Or kill all healing-bot processes
pkill -f healing-bot
```

### Problem 2: Permission Denied

**Error:** `Permission denied` when running scripts

**Solution:**

```bash
# Make scripts executable
chmod +x start-healing-bot-ubuntu.sh
chmod +x quick-start-ubuntu.sh

# Or run with bash
bash start-healing-bot-ubuntu.sh
```

### Problem 3: Python Module Not Found

**Error:** `ModuleNotFoundError: No module named 'X'`

**Solution:**

```bash
# Reinstall dependencies
pip3 install -r requirements.txt
pip3 install -r monitoring/server/requirements.txt
pip3 install -r monitoring/dashboard/requirements.txt
pip3 install -r incident-bot/requirements.txt
pip3 install -r model/requirements.txt

# Or install specific module
pip3 install <module-name>
```

### Problem 4: GEMINI_API_KEY Not Found

**Error:** `WARNING: GEMINI_API_KEY not found in .env file`

**Solution:**

```bash
# Run setup wizard
python3 setup_env.py

# Or manually edit .env
nano .env
# Add: GEMINI_API_KEY=your_key_here

# Verify
grep GEMINI_API_KEY .env
```

### Problem 5: Service Fails to Start

**Check logs:**

```bash
# View logs
cat logs/<service-name>.log

# Common issues:
# - Port in use: Change port in .env
# - Missing dependency: pip3 install <package>
# - Permission issue: Check file permissions
```

### Problem 6: Can't Access Dashboard

**Error:** Cannot connect to http://localhost:3001

**Solution:**

```bash
# Check if dashboard is running
./start-healing-bot-ubuntu.sh --status

# Check logs
tail -f logs/dashboard.log

# Try different port
# Edit .env: DASHBOARD_PORT=3002
```

---

## 🏭 Production Deployment

### 1. Use Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
# ... install other requirements

# Run services
./start-healing-bot-ubuntu.sh
```

### 2. Use Screen or Tmux

**Using Screen:**

```bash
# Install screen
sudo apt install screen

# Create new screen session
screen -S healing-bot

# Start services
./start-healing-bot-ubuntu.sh

# Detach: Ctrl+A then D
# Reattach: screen -r healing-bot
```

**Using Tmux:**

```bash
# Install tmux
sudo apt install tmux

# Create new tmux session
tmux new -s healing-bot

# Start services
./start-healing-bot-ubuntu.sh

# Detach: Ctrl+B then D
# Reattach: tmux attach -t healing-bot
```

### 3. Set Up Reverse Proxy (Nginx)

```bash
# Install nginx
sudo apt install nginx

# Create config
sudo nano /etc/nginx/sites-available/healing-bot

# Add configuration:
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api/ {
        proxy_pass http://localhost:5000;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/healing-bot /etc/nginx/sites-enabled/

# Test config
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

### 4. Set Up SSL (Let's Encrypt)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is set up automatically
```

---

## 🔄 Systemd Service Setup

Create systemd services for automatic startup on boot.

### Create Service File

```bash
sudo nano /etc/systemd/system/healing-bot.service
```

Add:

```ini
[Unit]
Description=Automatic Self-Healing Bot
After=network.target

[Service]
Type=forking
User=your-username
Group=your-username
WorkingDirectory=/path/to/healing-bot
ExecStart=/path/to/healing-bot/start-healing-bot-ubuntu.sh
ExecStop=/path/to/healing-bot/start-healing-bot-ubuntu.sh --stop
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable healing-bot

# Start service now
sudo systemctl start healing-bot

# Check status
sudo systemctl status healing-bot

# View logs
sudo journalctl -u healing-bot -f
```

### Service Management Commands

```bash
# Start
sudo systemctl start healing-bot

# Stop
sudo systemctl stop healing-bot

# Restart
sudo systemctl restart healing-bot

# Status
sudo systemctl status healing-bot

# Disable (don't start on boot)
sudo systemctl disable healing-bot

# View logs
sudo journalctl -u healing-bot -f
```

---

## 📊 Monitoring & Logs

### Log Locations

```
logs/
├── model.log              # ML model API
├── network-analyzer.log   # Network analyzer
├── monitoring-server.log  # Monitoring server
├── dashboard.log          # Dashboard
└── incident-bot.log       # Incident bot
```

### PID Files

```
.pids/
├── model.pid
├── network-analyzer.pid
├── monitoring-server.pid
├── dashboard.pid
└── incident-bot.pid
```

### View Real-Time Logs

```bash
# All logs
tail -f logs/*.log

# Specific service
tail -f logs/dashboard.log

# Last 100 lines
tail -n 100 logs/dashboard.log

# Search logs
grep "ERROR" logs/*.log
```

---

## 🔒 Security Best Practices

### 1. Firewall Configuration

```bash
# Install ufw
sudo apt install ufw

# Allow SSH
sudo ufw allow ssh

# Allow HTTP/HTTPS (if using Nginx)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow dashboard (if exposing publicly)
sudo ufw allow 3001/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

### 2. Run as Non-Root User

```bash
# Create dedicated user
sudo useradd -r -s /bin/bash -d /opt/healing-bot healing-bot

# Set ownership
sudo chown -R healing-bot:healing-bot /opt/healing-bot

# Run as healing-bot user
sudo -u healing-bot ./start-healing-bot-ubuntu.sh
```

### 3. Secure .env File

```bash
# Set restrictive permissions
chmod 600 .env

# Verify
ls -la .env
# Should show: -rw------- (only owner can read/write)
```

### 4. Keep System Updated

```bash
# Update packages
sudo apt update
sudo apt upgrade -y

# Update Python packages
pip3 list --outdated
pip3 install --upgrade <package>
```

---

## 📞 Support & Resources

### Access Points

- **Dashboard**: http://localhost:3001
- **Model API**: http://localhost:8080
- **Network Analyzer**: http://localhost:8000
- **Monitoring Server**: http://localhost:5000
- **Incident Bot**: http://localhost:8001

### Documentation

- `README.md` - Main documentation
- `ENV_SETUP_GUIDE.md` - Environment setup
- `GEMINI_LOG_ANALYSIS_COMPLETE.md` - AI log analysis
- `CENTRALIZED_LOGGING_COMPLETE.md` - Centralized logging

### Useful Commands

```bash
# Check all listening ports
sudo netstat -tulpn

# Check system resources
htop
# or
top

# Check disk space
df -h

# Check memory
free -h

# Check process tree
pstree -p

# Find healing-bot processes
ps aux | grep healing-bot
```

---

## 🎉 You're Ready!

Your Automatic Self-Healing Bot is now set up on Ubuntu!

**Next Steps:**
1. Access dashboard: http://localhost:3001
2. Click "Logs & AI Analysis" tab
3. Monitor your system with AI-powered insights
4. Configure alerts and auto-healing

**For help:** See troubleshooting section or check logs in `logs/` directory.

---

**🐧 Happy Ubuntu Deployment!** 🚀

