# Fluent Bit Docker Commands

## Quick Start Commands

### Option 1: Using Docker Compose (Recommended)

```bash
# Navigate to config directory
cd /home/kasun/Documents/Heal-X-Bot/config

# Create Docker network (if it doesn't exist)
sudo docker network create healing-network 2>/dev/null || true

# Start Fluent Bit
sudo docker compose -f docker-compose-fluent-bit.yml up -d

# OR if you have legacy docker-compose:
sudo docker-compose -f docker-compose-fluent-bit.yml up -d
```

### Option 2: Using Docker Run (Direct)

```bash
# Navigate to project root
cd /home/kasun/Documents/Heal-X-Bot

# Create network
sudo docker network create healing-network 2>/dev/null || true

# Create output directory
mkdir -p logs/fluent-bit

# Run Fluent Bit container
sudo docker run -d \
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

### Option 3: Using the Provided Script

```bash
# Make script executable (if not already)
chmod +x scripts/start-fluent-bit.sh

# Run the script (requires sudo for Docker)
sudo scripts/start-fluent-bit.sh
```

## Management Commands

### Check Status
```bash
# Check if container is running
sudo docker ps | grep fluent-bit

# Check container logs
sudo docker logs fluent-bit

# Follow logs in real-time
sudo docker logs -f fluent-bit
```

### Stop Fluent Bit
```bash
# Stop container
sudo docker stop fluent-bit

# OR using docker-compose
cd config
sudo docker compose -f docker-compose-fluent-bit.yml down
```

### Restart Fluent Bit
```bash
# Restart container
sudo docker restart fluent-bit

# OR using docker-compose
cd config
sudo docker compose -f docker-compose-fluent-bit.yml restart
```

### Remove Container
```bash
# Stop and remove container
sudo docker stop fluent-bit
sudo docker rm fluent-bit

# OR using docker-compose
cd config
sudo docker compose -f docker-compose-fluent-bit.yml down
```

## Fix Docker Permissions (Optional)

If you want to run Docker without sudo:

```bash
# Add your user to docker group
sudo usermod -aG docker $USER

# Apply changes (need to log out and log back in, or run):
newgrp docker

# Then you can run docker commands without sudo
docker ps
```

## Access Fluent Bit

- **HTTP API**: http://localhost:8888
- **Logs Output**: `logs/fluent-bit/fluent-bit-output.jsonl`

## Troubleshooting

### Check if Docker daemon is running
```bash
sudo systemctl status docker
```

### Start Docker daemon (if not running)
```bash
sudo systemctl start docker
```

### Check Fluent Bit configuration
```bash
# View config file
cat config/fluent-bit/fluent-bit.conf
```

### Check container health
```bash
sudo docker inspect fluent-bit | grep -A 10 Health
```

