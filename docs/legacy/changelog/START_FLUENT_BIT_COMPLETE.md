# Complete Guide to Start Fluent Bit

## Issue Found
The error "unknown shorthand flag: 'f' in -f" indicates that your Docker version doesn't support `docker compose` (it's an older version). The script has been updated to handle this.

## Step 1: Pull Fluent Bit Image

First, pull the Fluent Bit Docker image:

```bash
cd /home/kasun/Documents/Heal-X-Bot
docker pull fluent/fluent-bit:latest
```

Or use the helper script:

```bash
cd /home/kasun/Documents/Heal-X-Bot
./scripts/pull-fluent-bit-image.sh
```

## Step 2: Install docker-compose (Recommended)

Since your Docker version doesn't support `docker compose`, install the standalone docker-compose:

```bash
sudo apt update
sudo apt install docker-compose
```

Or install docker-compose-plugin (newer method):

```bash
sudo apt update
sudo apt install docker-compose-plugin
```

## Step 3: Start Fluent Bit

After pulling the image and installing docker-compose:

```bash
cd /home/kasun/Documents/Heal-X-Bot
./scripts/start-fluent-bit.sh
```

## Alternative: Manual Start (If docker-compose not available)

The updated script will automatically try to start Fluent Bit manually if docker-compose is not available. But you can also do it manually:

```bash
cd /home/kasun/Documents/Heal-X-Bot

# Create network if it doesn't exist
docker network create healing-network 2>/dev/null || true

# Create logs directory
mkdir -p logs/fluent-bit

# Start Fluent Bit container
docker run -d \
    --name fluent-bit \
    --restart unless-stopped \
    --network healing-network \
    -v $(pwd)/config/fluent-bit/fluent-bit.conf:/fluent-bit/etc/fluent-bit.conf:ro \
    -v $(pwd)/config/fluent-bit/parsers.conf:/fluent-bit/etc/parsers.conf:ro \
    -v /var/log:/var/log:ro \
    -v /var/lib/docker/containers:/var/lib/docker/containers:ro \
    -v $(pwd)/logs/fluent-bit:/fluent-bit-output \
    -v /run/journal:/run/journal:ro \
    -v /var/run/docker.sock:/var/run/docker.sock:ro \
    -p 8888:8888 \
    fluent/fluent-bit:latest \
    /fluent-bit/bin/fluent-bit -c /fluent-bit/etc/fluent-bit.conf
```

## Verify Fluent Bit is Running

```bash
# Check container status
docker ps | grep fluent-bit

# View Fluent Bit logs
docker logs fluent-bit

# Check if log file is being created
ls -lh logs/fluent-bit/fluent-bit-output.jsonl
tail -f logs/fluent-bit/fluent-bit-output.jsonl
```

## Wait for Logs

After starting:
1. Wait 10-30 seconds for logs to appear
2. Refresh the dashboard: http://localhost:5001
3. Go to "Logs & AI" tab
4. Select "Fluent Bit" as log source
5. Logs should appear!

## Quick Summary

```bash
# 1. Pull image
docker pull fluent/fluent-bit:latest

# 2. Install docker-compose (if not installed)
sudo apt install docker-compose

# 3. Start Fluent Bit
cd /home/kasun/Documents/Heal-X-Bot
./scripts/start-fluent-bit.sh
```

## Troubleshooting

### Image Pull Fails
```bash
# Check Docker is running
docker ps

# Try pulling again
docker pull fluent/fluent-bit:latest
```

### docker-compose Not Found
```bash
# Install docker-compose
sudo apt update
sudo apt install docker-compose

# Verify installation
docker-compose --version
```

### Container Fails to Start
```bash
# Check logs
docker logs fluent-bit

# Check if network exists
docker network ls | grep healing-network

# Remove and restart
docker stop fluent-bit
docker rm fluent-bit
./scripts/start-fluent-bit.sh
```

## Alternative: Use Centralized Logger

If you don't want to deal with Docker:
1. Open dashboard: http://localhost:5001
2. Go to "Logs & AI" tab  
3. Select "Centralized Logger" from dropdown
4. Logs appear immediately (no Docker needed)
