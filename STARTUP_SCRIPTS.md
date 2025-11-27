# Startup Scripts Guide

## 🚀 Recommended: `start-all-services.sh`

**Primary startup script** - Use this for starting all services.

```bash
./start-all-services.sh
```

**Features:**
- ✅ Sets up virtual environment automatically
- ✅ Installs all dependencies
- ✅ Fixes protobuf compatibility
- ✅ Starts all services with health checks
- ✅ Graceful shutdown (Ctrl+C)

## 🔄 Alternative: `start-managed.sh`

**Self-managing startup script** - Use this for production with auto-restart.

```bash
./start-managed.sh
```

**Features:**
- ✅ Auto-restart on crash
- ✅ Health monitoring
- ✅ Status tracking
- ✅ Smart restart limits

## 📁 Other Scripts

### Legacy Scripts (kept for compatibility)
- `start.sh` - Basic startup (legacy)
- `run-healing-bot.py` - Python launcher (legacy)
- `start_dashboard.sh` - Dashboard only (legacy)

### Deployment Scripts
Located in `scripts/deployment/`:
- `start-healing-bot.sh` - Ubuntu deployment script
- `start-healing-bot-ubuntu.sh` - Comprehensive Ubuntu launcher
- `start-dev.sh` / `start-dev.bat` - Development scripts
- `install-service.sh` - Systemd service installation

## 📝 Recommendation

**For development:** Use `start-all-services.sh`  
**For production:** Use `start-managed.sh`  
**For deployment:** Use scripts in `scripts/deployment/`

