# 🚀 Quick Start Guide - Heal-X-Bot

This guide will help you get Heal-X-Bot up and running in minutes.

## Prerequisites

- **Python 3.8 or higher** (check with `python3 --version`)
- **pip** (Python package manager)
- **curl** (for health checks, usually pre-installed)

## First-Time Setup

### Step 1: Clone and Navigate

```bash
cd /path/to/Heal-X-Bot
```

### Step 2: Start the System

Simply run:

```bash
./start.sh
```

That's it! The script will:
- ✅ Check Python version
- ✅ Create virtual environment (if needed)
- ✅ Install all dependencies
- ✅ Set up environment file (if needed)
- ✅ Start all services in the correct order
- ✅ Verify health of each service

### Step 3: Access the Dashboards

Once started, access the services at:

- **🛡️ Healing Dashboard**: http://localhost:5001
- **📈 Monitoring Server**: http://localhost:5000
- **🤖 DDoS Model API**: http://localhost:8080
- **🔍 Network Analyzer**: http://localhost:8000
- **🚨 Incident Bot**: http://localhost:8001

## Common Commands

### Start Services
```bash
./start.sh
```

### Check Status
```bash
./start.sh status
```

### Stop Services
```bash
./start.sh stop
```

### Restart Services
```bash
./start.sh restart
```

### Get Help
```bash
./start.sh --help
```

## Troubleshooting

### Port Already in Use

If you see an error about ports being in use:

```bash
# Check what's using the port
lsof -i :5000

# Or stop all services first
./start.sh stop
```

The script will automatically attempt to stop existing services, but if that fails, you may need to manually stop the process.

### Python Version Issues

Ensure you have Python 3.8+:

```bash
python3 --version
```

If you need to install Python 3.8+:
- **Ubuntu/Debian**: `sudo apt install python3.8`
- **macOS**: `brew install python3`
- **Windows**: Download from python.org

### Dependency Installation Fails

If dependency installation fails:

```bash
# Activate virtual environment manually
source .venv/bin/activate

# Try installing again
pip install -r requirements.txt
```

### Services Not Starting

1. **Check logs**: Look in `logs/` directory for error messages
2. **Check status**: Run `./start.sh status` to see which services are running
3. **Verify ports**: Ensure ports 5000, 5001, 8080, 8000, 8001 are available

### Virtual Environment Issues

If the virtual environment is corrupted:

```bash
# Remove and recreate
rm -rf .venv
./start.sh
```

## Configuration (Optional)

### Environment Variables

The system will create a `.env` file from template on first run. To configure API keys:

1. Edit `.env` file:
```bash
nano .env
```

2. Add your API keys (optional, for AI features):
```env
GEMINI_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here
```

3. Restart services:
```bash
./start.sh restart
```

## Service Details

### Service Startup Order

Services start in this order to respect dependencies:

1. **Model API** (Port 8080) - DDoS detection model
2. **Network Analyzer** (Port 8000) - Network traffic analysis
3. **Monitoring Server** (Port 5000) - System metrics
4. **Incident Bot** (Port 8001) - AI incident response
5. **Healing Dashboard** (Port 5001) - Main dashboard

### Health Checks

Each service has a health endpoint that's automatically checked:
- Model API: `http://localhost:8080/health`
- Network Analyzer: `http://localhost:8000/health`
- Monitoring Server: `http://localhost:5000/health`
- Incident Bot: `http://localhost:8001/health`
- Healing Dashboard: `http://localhost:5001/api/health`

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [docs/guides/](docs/guides/) for advanced configuration
- Explore the dashboard at http://localhost:5001

## Getting Help

- Check logs in `logs/` directory
- Run `./start.sh status` to see service status
- Review error messages in the console output
- See [README.md](README.md) for more troubleshooting tips

---

**That's it!** You should now have Heal-X-Bot running. 🎉
