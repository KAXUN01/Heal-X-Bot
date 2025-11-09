# Quick Start: Fluent Bit Log Collection

## Current Status
- ✅ Fluent Bit configuration: Ready
- ✅ Log directory: Created at `logs/fluent-bit/`
- ⚠️  Docker access: Requires sudo or docker group membership

## Start Fluent Bit (Choose One)

### Option 1: Using Sudo (Quick Fix)
```bash
sudo ./scripts/start-fluent-bit.sh
```

### Option 2: Add to Docker Group (Permanent Fix)
```bash
# Add yourself to docker group
sudo usermod -aG docker $USER

# Activate in current session
newgrp docker

# Then start Fluent Bit
./scripts/start-fluent-bit.sh
```

## Verify Fluent Bit is Running
```bash
# Check container status
docker ps | grep fluent-bit

# View logs
docker logs fluent-bit

# Check output file
ls -lh logs/fluent-bit/fluent-bit-output.jsonl
```

## Access Logs in Dashboard
1. Open: http://localhost:5001
2. Go to "Logs & AI Analysis" tab
3. Select "Fluent Bit" from log source dropdown
4. Logs will appear automatically once Fluent Bit is running

## Troubleshooting

### Permission Denied
- Run: `sudo ./scripts/start-fluent-bit.sh`
- Or add user to docker group (see Option 2 above)

### Container Not Starting
```bash
# Check Docker daemon
sudo systemctl status docker

# View container logs
docker logs fluent-bit

# Check network
docker network ls | grep healing-network
```

### No Logs Appearing
- Wait 10-30 seconds for Fluent Bit to start collecting
- Check: `tail -f logs/fluent-bit/fluent-bit-output.jsonl`
- Verify container is running: `docker ps | grep fluent-bit`
