# Fluent Bit Setup and Troubleshooting Guide

## Overview
Fluent Bit is configured to collect system logs from `/var/log/syslog`, `/var/log/kern.log`, `/var/log/auth.log`, `/var/log/messages`, and systemd services (Docker, Nginx, SSH). Logs are written to `logs/fluent-bit/fluent-bit-output.jsonl` and displayed in the dashboard's System-Wide Logs section.

## Prerequisites

1. **Docker must be running**
   - Check Docker status: `docker ps`
   - Start Docker on Linux: `sudo systemctl start docker`
   - Start Docker Desktop on macOS/Windows

2. **Docker network must exist**
   - The `healing-network` network will be created automatically by the start script

## Starting Fluent Bit

### Using the Start Script (Recommended)
```bash
./scripts/start-fluent-bit.sh
```

The script will:
- Check if Docker is running
- Verify Fluent Bit configuration exists
- Create the output directory (`logs/fluent-bit/`)
- Create the Docker network if needed
- Start the Fluent Bit container

### Manual Start
```bash
cd config
docker-compose -f docker-compose-fluent-bit.yml up -d
```

## Checking Fluent Bit Status

### Container Status
```bash
docker ps | grep fluent-bit
```

### View Container Logs
```bash
docker logs fluent-bit
docker logs fluent-bit --tail 50  # Last 50 lines
docker logs -f fluent-bit          # Follow logs
```

### Check Output File
```bash
ls -lh logs/fluent-bit/fluent-bit-output.jsonl
tail -f logs/fluent-bit/fluent-bit-output.jsonl
```

## Dashboard Integration

### Switching Log Sources
In the dashboard, you can switch between:
- **Fluent Bit**: Logs collected by Fluent Bit Docker container
- **Centralized Logger**: Logs collected by the Python centralized logger

Use the "Log Source" dropdown in the System-Wide Logs section.

### Troubleshooting Dashboard Issues

#### Issue: "Fluent Bit not available"
**Solution**: 
1. Check if Docker is running: `docker ps`
2. Check if Fluent Bit container is running: `docker ps | grep fluent-bit`
3. Start Fluent Bit: `./scripts/start-fluent-bit.sh`
4. Refresh the dashboard

#### Issue: "Fluent Bit is running but no logs yet"
**Possible Causes**:
- Fluent Bit just started and hasn't processed logs yet (wait 10-30 seconds)
- No new logs are being generated
- Fluent Bit is reading from tail (only new logs, not historical)

**Solution**:
1. Wait a moment for logs to appear
2. Generate some logs to test (e.g., `sudo tail -f /var/log/syslog`)
3. Check Fluent Bit container logs for errors: `docker logs fluent-bit`
4. Verify the output file is being created: `ls -lh logs/fluent-bit/fluent-bit-output.jsonl`

#### Issue: "Fluent Bit connection failed"
**Solution**:
1. Verify Docker is running: `docker ps`
2. Check Fluent Bit container status: `docker ps -a | grep fluent-bit`
3. Restart Fluent Bit: `docker restart fluent-bit` or `./scripts/start-fluent-bit.sh`
4. Check container logs for errors: `docker logs fluent-bit`

## Configuration Files

### Fluent Bit Configuration
- **Location**: `config/fluent-bit/fluent-bit.conf`
- **Key Settings**:
  - `Flush 1`: Flush logs every 1 second
  - `Read_from_Head false`: Only read new logs (not historical)
  - `Refresh_Interval 2`: Check for new logs every 2 seconds
  - Output: `logs/fluent-bit/fluent-bit-output.jsonl`

### Docker Compose Configuration
- **Location**: `config/docker-compose-fluent-bit.yml`
- **Volume Mounts**:
  - `/var/log:/var/log:ro`: System logs (read-only)
  - `../logs/fluent-bit:/fluent-bit-output`: Output directory
  - `/run/journal:/run/journal:ro`: Systemd journal (read-only)

## Log Sources

Fluent Bit collects logs from:

1. **Tail Inputs**:
   - `/var/log/syslog` → Tag: `syslog`
   - `/var/log/kern.log` → Tag: `kernel`
   - `/var/log/auth.log` → Tag: `auth`
   - `/var/log/messages` → Tag: `messages`

2. **Systemd Input**:
   - `docker.service` → Tag: `systemd`
   - `nginx.service` → Tag: `systemd`
   - `ssh.service` → Tag: `systemd`

## Common Issues and Solutions

### Issue: Fluent Bit container keeps restarting
**Check**:
1. Container logs: `docker logs fluent-bit`
2. Configuration syntax errors
3. File permissions on output directory

**Solution**:
- Verify `config/fluent-bit/fluent-bit.conf` syntax is correct
- Ensure output directory is writable: `chmod 755 logs/fluent-bit/`
- Check Docker has permission to mount volumes

### Issue: Output file not created
**Check**:
1. Container is running: `docker ps | grep fluent-bit`
2. Volume mount is correct: `docker inspect fluent-bit | grep -A 5 Mounts`
3. Container logs for errors: `docker logs fluent-bit`

**Solution**:
- Verify volume mount path in `docker-compose-fluent-bit.yml`
- Check if directory exists and is writable
- Restart container: `docker restart fluent-bit`

### Issue: No logs in dashboard
**Check**:
1. Output file exists: `ls -lh logs/fluent-bit/fluent-bit-output.jsonl`
2. File has content: `wc -l logs/fluent-bit/fluent-bit-output.jsonl`
3. File format is correct: `head -1 logs/fluent-bit/fluent-bit-output.jsonl | jq .`

**Solution**:
- Ensure file exists and has JSON lines format
- Check API endpoint: `curl http://localhost:5001/api/fluent-bit/recent?limit=10`
- Verify `fluent_bit_reader` is initialized in `healing_dashboard_api.py`

## API Endpoints

- `GET /api/fluent-bit/recent?limit=100&service=...&level=...`: Get recent logs
- `GET /api/fluent-bit/statistics`: Get log statistics
- `GET /api/fluent-bit/sources`: Get available log sources/tags

## Stopping Fluent Bit

```bash
docker stop fluent-bit
# Or using docker-compose
cd config
docker-compose -f docker-compose-fluent-bit.yml down
```

## Notes

- Fluent Bit reads logs from tail by default (only new logs after container starts)
- To see historical logs, you can temporarily set `Read_from_Head true` in `fluent-bit.conf` (restart container after change)
- The output file format is JSON Lines (one JSON object per line)
- Logs are cached in memory by the Python reader for fast access
- The cache size is limited to 10,000 logs to manage memory usage

