# 📜 Healing-Bot Scripts

Utility and deployment scripts for the Healing-Bot system.

---

## 📁 Directory Structure

```
scripts/
├── README.md (this file)
├── setup/                       # Setup and initialization scripts
├── maintenance/                 # Maintenance and housekeeping scripts
└── deployment/                  # Deployment and launcher scripts
```

---

## 🗂️ Script Categories

### 🚀 Setup Scripts (`setup/`)

Scripts for initial setup and configuration:

| Script | Purpose | Usage |
|--------|---------|-------|
| **start-with-venv.sh** | Activate venv and start services | `./scripts/setup/start-with-venv.sh` |
| **setup_env.py** | Environment configuration utility | `python scripts/setup/setup_env.py` |
| **demo-healing-bot.py** | Demo/test run of the system | `python scripts/setup/demo-healing-bot.py` |

### 🛠️ Maintenance Scripts (`maintenance/`)

Scripts for system maintenance:

| Script | Purpose | Usage |
|--------|---------|-------|
| **cleanup_logs.sh** | Log rotation and cleanup | `./scripts/maintenance/cleanup_logs.sh` |
| **list_services.sh** | List all running services | `./scripts/maintenance/list_services.sh` |

### 🚢 Deployment Scripts (`deployment/`)

Scripts for deploying and launching the system:

| Script | Purpose | Platform | Usage |
|--------|---------|----------|-------|
| **start-dev.sh** | Development launcher | Linux/Mac | `./scripts/deployment/start-dev.sh` |
| **start-dev.bat** | Development launcher | Windows | `scripts\deployment\start-dev.bat` |
| **start-healing-bot.sh** | Production launcher | Linux/Mac | `./scripts/deployment/start-healing-bot.sh` |
| **start-healing-bot.bat** | Production launcher | Windows | `scripts\deployment\start-healing-bot.bat` |
| **start-healing-bot-ubuntu.sh** | Ubuntu-specific launcher | Ubuntu | `./scripts/deployment/start-healing-bot-ubuntu.sh` |

---

## 🚀 Quick Start

### First Time Setup

```bash
# 1. Setup virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
python scripts/setup/setup_env.py

# 4. Start the system
./scripts/setup/start-with-venv.sh
```

### Development Mode

```bash
# Linux/Mac
./scripts/deployment/start-dev.sh

# Windows
scripts\deployment\start-dev.bat
```

### Production Mode

```bash
# Linux/Mac
./scripts/deployment/start-healing-bot.sh

# Windows
scripts\deployment\start-healing-bot.bat
```

---

## 📖 Script Details

### Setup Scripts

#### start-with-venv.sh
Activates Python virtual environment and starts the main launcher.

```bash
#!/bin/bash
# Activates venv and runs run-healing-bot.py

Usage:
  ./scripts/setup/start-with-venv.sh [options]

Features:
  - Auto-activates virtual environment
  - Loads environment variables from .env
  - Starts main launcher with parameters
```

#### setup_env.py
Interactive environment configuration utility.

```python
# Setup environment variables
# Creates/updates .env file
# Validates configuration

Usage:
  python scripts/setup/setup_env.py
```

#### demo-healing-bot.py
Demonstration script for testing the system.

```python
# Runs system in demo mode
# Tests all components
# Generates sample data

Usage:
  python scripts/setup/demo-healing-bot.py
```

---

### Maintenance Scripts

#### cleanup_logs.sh
Log file management and rotation.

```bash
#!/bin/bash
# Manages log file sizes
# Rotates old logs
# Compresses archived logs

Usage:
  ./scripts/maintenance/cleanup_logs.sh [--aggressive]

Options:
  --aggressive  Performs deep cleanup (deletes all old logs)

Features:
  - Truncates logs larger than 10MB
  - Deletes logs older than 7 days
  - Compresses old log files
  - Shows disk usage statistics
```

#### list_services.sh
Lists all running Healing-Bot services.

```bash
#!/bin/bash
# Shows running services
# Displays ports and PIDs
# Checks service health

Usage:
  ./scripts/maintenance/list_services.sh

Output:
  Service Name    | Port | PID   | Status
  Monitoring      | 5000 | 12345 | Running
  Dashboard       | 3001 | 12346 | Running
  Prometheus      | 9090 | 12347 | Running
```

---

### Deployment Scripts

#### start-dev.sh / start-dev.bat
Development environment launcher.

```bash
# Features:
  - Starts services in development mode
  - Enables debug logging
  - Hot-reload for code changes
  - Verbose output

# Usage:
  ./scripts/deployment/start-dev.sh
```

#### start-healing-bot.sh / start-healing-bot.bat
Production launcher.

```bash
# Features:
  - Optimized for production
  - Background service mode
  - Log rotation enabled
  - Health checks

# Usage:
  ./scripts/deployment/start-healing-bot.sh
```

#### start-healing-bot-ubuntu.sh
Ubuntu-specific comprehensive launcher with advanced service management.

```bash
# Features:
  - System requirements check (Python, pip, curl, etc.)
  - Automatic dependency installation (system + Python)
  - Environment configuration wizard
  - Service management (start/stop/status/logs)
  - Development mode (separate terminals)
  - PID-based process tracking
  - Port conflict detection
  - Health monitoring
  - Graceful shutdown handling

# Usage:
  ./scripts/deployment/start-healing-bot-ubuntu.sh [OPTIONS]

# Options:
  --install-deps    Install all dependencies (requires sudo)
  --setup-env       Run environment setup wizard
  --dev             Start in development mode  
  --stop            Stop all running services
  --status          Check service status
  --logs            View logs from all services
  --help            Show help message

# Examples:
  # Start all services
  ./scripts/deployment/start-healing-bot-ubuntu.sh

  # Install dependencies first time
  sudo ./scripts/deployment/start-healing-bot-ubuntu.sh --install-deps

  # Development mode (separate terminals)
  ./scripts/deployment/start-healing-bot-ubuntu.sh --dev

  # Check status
  ./scripts/deployment/start-healing-bot-ubuntu.sh --status

  # View logs
  ./scripts/deployment/start-healing-bot-ubuntu.sh --logs

  # Stop all services
  ./scripts/deployment/start-healing-bot-ubuntu.sh --stop
```

**Managed Services:**
- Model API (port 8080)
- Network Analyzer (port 8000)
- Monitoring Server (port 5000)
- Dashboard (port 3001)
- Incident Bot (port 8001)

---

## 🔧 Common Tasks

### 1. Clean Up Old Logs

```bash
# Normal cleanup (safe)
./scripts/maintenance/cleanup_logs.sh

# Aggressive cleanup (removes all old logs)
./scripts/maintenance/cleanup_logs.sh --aggressive
```

### 2. Check Running Services

```bash
./scripts/maintenance/list_services.sh
```

### 3. Restart All Services

```bash
# Stop services
pkill -f "python.*app.py"

# Start services
./scripts/deployment/start-healing-bot.sh
```

### 4. Deploy New Version

```bash
# 1. Pull latest code
git pull

# 2. Update dependencies
pip install -r requirements.txt

# 3. Run database migrations (if any)
# python migrate.py

# 4. Restart services
./scripts/deployment/start-healing-bot.sh
```

---

## 🛡️ Best Practices

### For Setup Scripts

1. **Check dependencies** before running
2. **Validate environment** variables
3. **Provide clear error messages**
4. **Log setup progress**

### For Maintenance Scripts

1. **Always backup** before destructive operations
2. **Show disk usage** before/after
3. **Provide dry-run** options
4. **Log all actions**

### For Deployment Scripts

1. **Check if services are running** before starting
2. **Handle port conflicts** gracefully
3. **Provide status updates**
4. **Support graceful shutdown**

---

## 📝 Creating New Scripts

### Script Template

```bash
#!/bin/bash
# Script Name: example.sh
# Purpose: Brief description
# Usage: ./scripts/category/example.sh [options]

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() { echo -e "${GREEN}✅ $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }

# Main function
main() {
    log_info "Starting script..."
    
    # Script logic here
    
    log_info "Script complete!"
}

# Run main function
main "$@"
```

---

## 🔍 Troubleshooting

### Script Won't Execute

```bash
# Make script executable
chmod +x scripts/category/script.sh

# Check shebang
head -1 scripts/category/script.sh  # Should be #!/bin/bash or #!/usr/bin/env python3
```

### Permission Denied

```bash
# Run with sudo (if needed)
sudo ./scripts/maintenance/cleanup_logs.sh

# Or add user to appropriate group
sudo usermod -a -G adm $USER
```

### Service Won't Start

```bash
# Check if port is already in use
lsof -i:5000

# Kill existing process
lsof -ti:5000 | xargs kill -9

# Try again
./scripts/deployment/start-healing-bot.sh
```

---

## 📚 Related Documentation

- **Deployment Guide** - `../docs/guides/UBUNTU_DEPLOYMENT_GUIDE.md`
- **Launcher README** - `../docs/guides/UNIFIED_LAUNCHER_README.md`
- **Quick Reference** - `../docs/guides/UBUNTU_QUICK_REFERENCE.md`

---

## 🤝 Contributing

When adding new scripts:

1. Place in appropriate category folder
2. Make executable (`chmod +x`)
3. Add shebang line (`#!/bin/bash` or `#!/usr/bin/env python3`)
4. Include usage documentation in header
5. Use colored output for clarity
6. Add entry to this README
7. Test on target platforms

---

**Last Updated:** October 29, 2025  
**Total Scripts:** 8  
**Categories:** Setup (3), Maintenance (2), Deployment (4)

