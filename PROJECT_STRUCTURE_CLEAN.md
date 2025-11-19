# Heal-X-Bot Project Structure

## 📁 Directory Structure

```
Heal-X-Bot/
├── config/                 # Configuration files
│   ├── docker-compose.yml
│   ├── docker-compose-fluent-bit.yml
│   ├── env.template
│   └── fluent-bit/
│
├── data/                   # Data storage
│   └── exports/
│
├── docs/                   # Documentation
│   ├── changelog/         # Change logs
│   ├── guides/            # User guides
│   └── README.md
│
├── incident-bot/           # AI Incident Response Bot
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── infra/                  # Infrastructure as Code
│   └── creates3user/
│
├── logs/                   # Application logs
│   └── fluent-bit/
│
├── model/                  # ML Model Services
│   ├── main.py            # DDoS Model API
│   ├── ddos_detector.py
│   ├── train_xgboost_model.py
│   ├── automated_retraining.py
│   ├── artifacts/         # Model artifacts (latest kept)
│   ├── ddos_model/        # Model files
│   └── requirements.txt
│
├── monitoring/             # Monitoring Services
│   ├── dashboard/         # Web Dashboard
│   ├── prometheus/        # Prometheus config
│   ├── alertmanager/      # Alertmanager config
│   └── server/            # Monitoring Server
│       ├── app.py         # Flask monitoring API
│       ├── healing_dashboard_api.py  # FastAPI dashboard
│       ├── network_analyzer.py
│       └── requirements.txt
│
├── scripts/                # Utility Scripts
│   ├── deployment/        # Deployment scripts
│   ├── maintenance/       # Maintenance scripts
│   ├── setup/             # Setup scripts
│   └── testing/           # Test scripts
│
├── tests/                 # Test Suite
│   ├── debug/
│   └── scripts/
│
├── .venv/                 # Virtual Environment (gitignored)
├── .pids/                 # Process ID files (gitignored)
│
├── start-all-services.sh  # 🚀 Main startup script
├── start-managed.sh       # 🔄 Self-managing startup
├── cleanup.sh             # 🧹 Cleanup script
├── stop-services.sh       # 🛑 Stop all services
├── check-services.sh      # ✅ Check service status
│
├── README.md              # Main documentation
├── LICENSE                # License file
├── requirements.txt       # Root dependencies
└── setup.py              # Setup script
```

## 🚀 Quick Start

### Start All Services
```bash
./start-all-services.sh
```

### Stop All Services
```bash
./stop-services.sh
```

### Check Service Status
```bash
./check-services.sh
```

### Clean Project
```bash
./cleanup.sh
```

## 📊 Service Ports

| Service | Port | Endpoint |
|---------|------|----------|
| Healing Dashboard | 5001 | http://localhost:5001 |
| DDoS Model API | 8080 | http://localhost:8080 |
| Network Analyzer | 8000 | http://localhost:8000 |
| Monitoring Server | 5000 | http://localhost:5000 |
| Incident Bot | 8001 | http://localhost:8001 |

## 🧹 Cleanup

The `cleanup.sh` script removes:
- ✅ Python cache files (`__pycache__`, `*.pyc`)
- ✅ Old log files (truncates large ones)
- ✅ Temporary files (`.swp`, `.swo`, `*~`)
- ✅ Demo/test files from model directory
- ✅ Redundant documentation files
- ✅ Old model artifacts (keeps latest 2 versions)
- ✅ Empty directories

Run regularly to keep the project clean:
```bash
./cleanup.sh
```

## 📝 Key Files

### Startup Scripts
- **`start-all-services.sh`** - Main comprehensive startup script
- **`start-managed.sh`** - Auto-restart enabled startup
- **`run-healing-bot.py`** - Python-based launcher (legacy)

### Configuration
- **`config/env.template`** - Environment variables template
- **`config/docker-compose.yml`** - Docker Compose configuration
- **`.env`** - Your environment variables (create from template)

### Documentation
- **`README.md`** - Main project documentation
- **`docs/guides/`** - Detailed guides
- **`SERVICES_STATUS.md`** - Service status information
- **`STARTUP_SCRIPTS.md`** - Startup scripts guide

## 🔒 Git Ignored

The following are automatically ignored (see `.gitignore`):
- `.venv/` - Virtual environment
- `*.log` - Log files
- `__pycache__/` - Python cache
- `.pids/` - Process ID files
- `*.db` - Database files
- `.env` - Environment variables

