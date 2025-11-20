# Fixes: Python3 and Docker Compose Compatibility

## Issues Fixed

1. **Python Command**: Changed all `python` references to `python3` for Linux compatibility
2. **Docker Compose**: Updated all scripts to support both `docker compose` (newer) and `docker-compose` (older) syntax

## Files Modified

### Scripts
- ✅ `run-demo.py` - Uses `python3` and handles both docker compose syntaxes
- ✅ `run-healing-bot.py` - Detects and uses appropriate docker compose command
- ✅ `scripts/setup/init-cloud-sim.sh` - Handles both docker compose syntaxes
- ✅ `scripts/demo/auto-demo-healing.py` - Updated error messages

### Server Code
- ✅ `monitoring/server/container_healer.py` - Tries `docker compose` first, falls back to `docker-compose`
- ✅ `monitoring/server/auto_healer.py` - Updated manual instructions

### Documentation
- ✅ `QUICK_START_CLOUD_SIM.md` - All commands use `python3` and show both docker compose options
- ✅ `docs/demo/DEMO_GUIDE.md` - Updated all examples
- ✅ `README.md` - Updated main command

## Usage

### Starting the System
```bash
# Use python3 (not python)
python3 run-healing-bot.py
```

### Docker Compose Commands
```bash
# Try newer syntax first (recommended)
docker compose -f config/docker-compose-cloud-sim.yml up -d

# Or use older syntax
docker-compose -f config/docker-compose-cloud-sim.yml up -d
```

### Setup Script
```bash
# The setup script automatically detects which docker compose to use
./scripts/setup/init-cloud-sim.sh
```

## Detection Logic

All scripts now:
1. Try `docker compose` (newer syntax) first
2. Fall back to `docker-compose` (older syntax) if needed
3. Show helpful error messages if neither is available

## Testing

To verify the fixes work:
```bash
# Check python3 is available
python3 --version

# Check docker compose (newer)
docker compose version

# Check docker-compose (older)
docker-compose --version

# Run the system
python3 run-healing-bot.py
```

