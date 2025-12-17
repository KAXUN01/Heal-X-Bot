# 📁 Heal-X-Bot - Clean Project Structure

This document describes the organized structure of the Heal-X-Bot project after cleanup and reorganization.

## 🎯 Quick Overview

```
Heal-X-Bot/
├── start.sh                    # ⭐ Main unified startup script
├── requirements.txt            # Unified dependencies
├── QUICK_START.md              # Quick start guide
├── README.md                   # Main documentation
│
├── config/                      # Configuration files
│   ├── services.yaml           # Service definitions and dependencies
│   ├── env.template            # Environment variables template
│   └── docker-compose*.yml     # Docker configurations
│
├── scripts/                     # Organized scripts
│   ├── startup/                # Startup/stop scripts
│   │   ├── stop.sh
│   │   └── status.sh
│   ├── maintenance/            # Maintenance scripts
│   └── deployment/             # Deployment scripts
│
├── model/                       # DDoS Detection Model
│   ├── main.py                 # Model API server
│   └── requirements.txt        # (deprecated - use root requirements.txt)
│
├── monitoring/                  # Monitoring & Dashboard
│   ├── server/                  # Monitoring server
│   │   ├── app.py              # Flask monitoring server
│   │   ├── healing_dashboard_api.py  # FastAPI dashboard
│   │   └── network_analyzer.py # Network analyzer
│   └── dashboard/              # Web dashboard
│
├── incident-bot/                # AI Incident Response
│   └── main.py                 # Incident bot server
│
├── logs/                        # Runtime logs (gitignored)
├── .pids/                       # Process ID files (gitignored)
├── .venv/                       # Virtual environment (gitignored)
└── .env                         # Environment variables (gitignored)
```

## 📋 Key Files

### Main Entry Points

- **`start.sh`** - Unified startup script (use this!)
  - Handles all setup, dependency installation, and service startup
  - Commands: `./start.sh`, `./start.sh status`, `./start.sh stop`, `./start.sh restart`

### Configuration

- **`config/services.yaml`** - Service definitions, ports, dependencies
- **`config/env.template`** - Environment variables template
- **`.env`** - Your environment variables (created from template)

### Dependencies

- **`requirements.txt`** - Unified requirements file (consolidated from all services)

## 🚀 Starting the System

### Single Command

```bash
./start.sh
```

This single command:
1. Checks Python version
2. Creates virtual environment
3. Installs all dependencies
4. Sets up environment file
5. Starts all services in correct order
6. Verifies health of each service

### Service Management

```bash
./start.sh status    # Check service status
./start.sh stop      # Stop all services
./start.sh restart   # Restart all services
```

## 📂 Directory Purposes

### `config/`
All configuration files:
- Service definitions
- Docker compose files
- Environment templates

### `scripts/`
Organized by purpose:
- **startup/** - Service management scripts
- **maintenance/** - Maintenance and cleanup
- **deployment/** - Deployment scripts

### `model/`
DDoS detection machine learning model:
- Model API server
- Trained models
- Training scripts

### `monitoring/`
Monitoring and dashboard components:
- **server/** - Backend services (Flask, FastAPI)
- **dashboard/** - Frontend dashboard

### `incident-bot/`
AI-powered incident response bot

### `logs/`
Runtime logs (auto-created, gitignored)

### `.pids/`
Process ID files for service management (gitignored)

## 🔄 Migration from Old Structure

Old scripts have been moved to `scripts/startup/` with `-old` suffix:
- `start-all-services.sh` → `scripts/startup/start-all-services-old.sh`
- `start-dashboard.sh` → `scripts/startup/start-dashboard-old.sh`
- etc.

**Use `./start.sh` instead!**

## 📝 Notes

- All dependencies are now in root `requirements.txt`
- Service configuration is in `config/services.yaml`
- Old startup scripts are preserved but deprecated
- Virtual environment is auto-managed by `start.sh`
- Logs are automatically organized in `logs/` directory

## 🎯 Best Practices

1. **Always use `./start.sh`** - It handles everything
2. **Check status** with `./start.sh status` before troubleshooting
3. **Check logs** in `logs/` directory if services fail
4. **Configure `.env`** for API keys (optional, for AI features)

---

For detailed setup instructions, see [QUICK_START.md](QUICK_START.md)
