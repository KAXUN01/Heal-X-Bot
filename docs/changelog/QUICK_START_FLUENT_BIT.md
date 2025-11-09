# Quick Start Fluent Bit

## Current Issue
Docker requires sudo permissions or you need to be in the docker group.

## Quick Fix - Option 1: Use Sudo (Fastest)

Run this command in your terminal:

```bash
cd /home/kasun/Documents/Heal-X-Bot
sudo ./scripts/start-fluent-bit.sh
```

Or use the helper script:

```bash
cd /home/kasun/Documents/Heal-X-Bot
./start-fluent-bit-with-sudo.sh
```

## Option 2: Add User to Docker Group (No sudo needed later)

Run these commands in your terminal:

```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Apply changes (logout/login, or use newgrp)
newgrp docker

# Verify you're in docker group
groups | grep docker

# Start Fluent Bit (no sudo needed now)
cd /home/kasun/Documents/Heal-X-Bot
./scripts/start-fluent-bit.sh
```

**Note:** After adding to docker group, you may need to logout and login again for full effect.

## Option 3: Start Docker Daemon First

If Docker daemon is not running:

```bash
# Start Docker daemon
sudo systemctl start docker

# Enable Docker to start on boot (optional)
sudo systemctl enable docker

# Then start Fluent Bit
cd /home/kasun/Documents/Heal-X-Bot
sudo ./scripts/start-fluent-bit.sh
```

## Verify Fluent Bit is Running

After starting, check:

```bash
# Check container status
sudo docker ps | grep fluent-bit

# View Fluent Bit logs
sudo docker logs fluent-bit

# Check if log file is being created
ls -lh /home/kasun/Documents/Heal-X-Bot/logs/fluent-bit/fluent-bit-output.jsonl
```

## Wait for Logs

After starting Fluent Bit:
1. Wait 10-30 seconds for logs to appear
2. Refresh the dashboard
3. Switch to "Fluent Bit" log source
4. Logs should appear!

## Alternative: Use Centralized Logger (No Docker Needed)

If you don't want to use Docker:
1. Open dashboard: http://localhost:5001
2. Go to "Logs & AI" tab
3. Select "Centralized Logger" from the "Log Source" dropdown
4. Logs will appear immediately (no Docker required)

## Troubleshooting

### Permission Denied
```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### Docker Daemon Not Running
```bash
# Start Docker
sudo systemctl start docker
```

### Fluent Bit Container Fails to Start
```bash
# Check Docker logs
sudo docker logs fluent-bit

# Check if network exists
sudo docker network ls | grep healing-network
```

## Summary

**Fastest way:** Run `sudo ./scripts/start-fluent-bit.sh` in the project directory.

**Best long-term:** Add user to docker group so you don't need sudo every time.
