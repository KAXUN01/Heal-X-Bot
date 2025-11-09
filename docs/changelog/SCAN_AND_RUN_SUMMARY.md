# Project Scan and Run Summary

## Project Overview
**Heal-X-Bot** - AI-Powered DDoS Detection & IP Blocking System

### Project Structure Scanned:
- **41 Python files** found across the project
- **Main Components:**
  - `model/` - DDoS detection ML model (TensorFlow)
  - `monitoring/server/` - Network analyzer, IP blocker, monitoring server
  - `monitoring/dashboard/` - Web dashboard
  - `incident-bot/` - AI-powered incident response
  - `config/` - Docker and configuration files

### Main Entry Points:
1. **Unified Dashboard** (Recommended): `monitoring/server/healing_dashboard_api.py`
2. **Unified Launcher**: `run-healing-bot.py`
3. **Individual Services**: See README.md for details

## Current Status

### ✅ Completed:
- Project structure scanned
- Python 3.10.12 detected
- Project files identified

### ❌ Missing:
- **pip** (Python package manager) - NOT INSTALLED
- **Dependencies** - Most required packages missing:
  - ✗ fastapi - MISSING
  - ✗ flask - MISSING  
  - ✗ uvicorn - MISSING
  - ✗ numpy - MISSING
  - ✗ pandas - MISSING
  - ✓ requests - AVAILABLE

## How to Run the Project (Without Tests)

### Step 1: Install pip
```bash
# Option 1: Using apt (requires sudo)
sudo apt update
sudo apt install python3-pip

# Option 2: Using get-pip.py
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3 get-pip.py --user
```

### Step 2: Install Dependencies
```bash
cd /home/kasun/Documents/Heal-X-Bot

# Install main requirements
python3 -m pip install --user -r requirements.txt

# Install component-specific requirements
python3 -m pip install --user -r model/requirements.txt
python3 -m pip install --user -r monitoring/server/requirements.txt
python3 -m pip install --user -r monitoring/dashboard/requirements.txt
python3 -m pip install --user -r incident-bot/requirements.txt
```

### Step 3: Create .env file (if not exists)
```bash
cp config/env.template .env
# Edit .env and add your API keys (optional for basic functionality)
```

### Step 4: Run the Project

#### Option A: Unified Dashboard (Simplest)
```bash
python3 monitoring/server/healing_dashboard_api.py
```
Access at: http://localhost:5001

#### Option B: Unified Launcher (All Services)
```bash
python3 run-healing-bot.py --mode native
```
This will start:
- Dashboard: http://localhost:3001
- Model API: http://localhost:8080
- Network Analyzer: http://localhost:8000
- Monitoring Server: http://localhost:5000

#### Option C: Individual Services
```bash
# Model API
cd model && python3 main.py &

# Network Analyzer  
cd monitoring/server && python3 network_analyzer.py &

# Dashboard
cd monitoring/dashboard && python3 app.py &

# Monitoring Server
cd monitoring/server && python3 app.py &
```

## Important Notes

1. **No Test Scripts**: The main launchers (`run-healing-bot.py`, `healing_dashboard_api.py`) do NOT run test scripts automatically. Tests must be run manually if needed.

2. **Ports Used:**
   - 3001 - Dashboard
   - 5000 - Monitoring Server
   - 5001 - Unified Dashboard (healing_dashboard_api.py)
   - 8080 - Model API
   - 8000 - Network Analyzer / Incident Bot

3. **Environment Variables**: The `.env` file is optional for basic functionality, but required for:
   - AI log analysis (GEMINI_API_KEY)
   - Slack notifications (SLACK_WEBHOOK)
   - AWS S3 uploads (AWS credentials)

## Quick Start Script

See `quick-start-ubuntu.sh` for automated setup:
```bash
# First-time setup (requires sudo)
sudo ./quick-start-ubuntu.sh --first-time

# Run the project
./quick-start-ubuntu.sh
```

