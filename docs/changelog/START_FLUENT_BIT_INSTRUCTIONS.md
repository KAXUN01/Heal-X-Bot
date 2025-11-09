# How to Start Fluent Bit

## Current Status
- ✅ Docker is installed at `/usr/bin/docker`
- ❌ User is NOT in the docker group (requires sudo)
- ❌ Docker daemon may not be running

## Option 1: Add User to Docker Group (Recommended - No sudo needed)

Run these commands in your terminal:

```bash
# Add your user to the docker group
sudo usermod -aG docker $USER

# Apply the changes (logout and login again, or use newgrp)
newgrp docker

# Verify you're in the docker group
groups

# Start Fluent Bit
cd /home/kasun/Documents/Heal-X-Bot
./scripts/start-fluent-bit.sh
```

**After adding to docker group, you'll need to logout and login again for the change to take full effect.**

## Option 2: Start Docker Daemon and Use Sudo

Run these commands in your terminal:

```bash
# Start Docker daemon (if not running)
sudo systemctl start docker

# Start Fluent Bit with sudo
cd /home/kasun/Documents/Heal-X-Bot
sudo ./scripts/start-fluent-bit.sh
```

## Option 3: Use the Helper Script

There's a helper script that uses sudo:

```bash
cd /home/kasun/Documents/Heal-X-Bot
./start-fluent-bit-with-sudo.sh
```

## Quick Start (After Docker is Accessible)

Once Docker is accessible (either via docker group or sudo), run:

```bash
cd /home/kasun/Documents/Heal-X-Bot
./scripts/start-fluent-bit.sh
```

The script will:
1. ✅ Check if Docker is running
2. ✅ Verify Fluent Bit configuration exists
3. ✅ Create the logs directory
4. ✅ Create the Docker network if needed
5. ✅ Start the Fluent Bit container
6. ✅ Show container status

## Verify Fluent Bit is Running

After starting, check the status:

```bash
# Check if container is running
docker ps | grep fluent-bit

# View Fluent Bit logs
docker logs fluent-bit

# Check if log file is being created
ls -lh /home/kasun/Documents/Heal-X-Bot/logs/fluent-bit/fluent-bit-output.jsonl
tail -f /home/kasun/Documents/Heal-X-Bot/logs/fluent-bit/fluent-bit-output.jsonl
```

## Troubleshooting

### Docker Permission Denied
If you see "permission denied" errors:
- Add user to docker group: `sudo usermod -aG docker $USER`
- Logout and login again
- Or use sudo: `sudo docker ps`

### Docker Daemon Not Running
If Docker daemon is not running:
```bash
sudo systemctl start docker
sudo systemctl enable docker  # Enable auto-start on boot
```

### Fluent Bit Container Fails to Start
Check the logs:
```bash
docker logs fluent-bit
```

### No Logs Appearing
- Wait 10-30 seconds after starting (Fluent Bit needs time to process logs)
- Check if log file exists: `ls -la logs/fluent-bit/`
- Check container logs: `docker logs fluent-bit`
- Verify Fluent Bit is reading from system logs: `docker exec fluent-bit ls -la /var/log/`

## Next Steps

1. **Add user to docker group** (Option 1 - recommended)
2. **Logout and login again** (or use `newgrp docker`)
3. **Start Fluent Bit**: `./scripts/start-fluent-bit.sh`
4. **Check dashboard**: Open `http://localhost:5001` → Logs & AI tab
5. **Switch to Fluent Bit**: Use the "Log Source" dropdown to select "Fluent Bit"

## Note

Fluent Bit is **optional**. The system works perfectly with the centralized logger, which doesn't require Docker. Fluent Bit provides additional log collection capabilities but is not required for basic functionality.
