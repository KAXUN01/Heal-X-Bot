# Fluent Bit Log Management Setup

This guide explains how to use Fluent Bit for centralized log management in the Healing-Bot system.

## Overview

Fluent Bit is a lightweight log processor and forwarder that collects logs from multiple sources and outputs them in a structured format. The Healing-Bot dashboard can display these logs alongside the centralized logger.

## Quick Start

### 1. Start Fluent Bit Container

```bash
# Run the startup script
./scripts/start-fluent-bit.sh

# Or manually using docker-compose
cd config
docker-compose -f docker-compose-fluent-bit.yml up -d
```

### 2. Verify Fluent Bit is Running

```bash
# Check container status
docker ps | grep fluent-bit

# View Fluent Bit logs
docker logs -f fluent-bit

# Check output file
tail -f /var/log/fluent-bit/fluent-bit-output.jsonl
```

### 3. Access Logs in Dashboard

1. Open the dashboard: `http://localhost:5001`
2. Navigate to the **"Logs & AI Analysis"** tab
3. Use the **"Log Source"** dropdown at the top
4. Select **"Fluent Bit"** to view Fluent Bit logs
5. Use filters to search by service, level, or tag

## Configuration

### Fluent Bit Configuration

The Fluent Bit configuration is located at:
- `config/fluent-bit/fluent-bit.conf` - Main configuration
- `config/fluent-bit/parsers.conf` - Log parsers

### Log Sources

Fluent Bit is configured to collect from:
- `/var/log/syslog` - System logs
- `/var/log/kern.log` - Kernel logs
- `/var/log/auth.log` - Authentication logs
- `/var/log/messages` - General messages
- Systemd journal (Docker, Nginx, SSH services)

### Output

Fluent Bit outputs logs to:
- **File**: `/var/log/fluent-bit/fluent-bit-output.jsonl` (JSON Lines format)
- **HTTP**: `http://127.0.0.1:8888/fluent-bit/logs` (optional)

## API Endpoints

### Get Recent Fluent Bit Logs

```bash
# Get last 100 logs
curl http://localhost:5001/api/fluent-bit/recent?limit=100

# Filter by service
curl "http://localhost:5001/api/fluent-bit/recent?limit=100&service=syslog"

# Filter by level
curl "http://localhost:5001/api/fluent-bit/recent?limit=100&level=ERROR"

# Filter by tag
curl "http://localhost:5001/api/fluent-bit/recent?limit=100&tag=kernel"
```

### Get Statistics

```bash
curl http://localhost:5001/api/fluent-bit/statistics | jq '.'
```

### Get Available Sources/Tags

```bash
curl http://localhost:5001/api/fluent-bit/sources | jq '.'
```

## Log Format

Fluent Bit logs are structured as:

```json
{
  "timestamp": "2025-10-31T14:30:00.123456+05:30",
  "service": "syslog",
  "source": "fluent-bit",
  "source_file": "syslog",
  "tag": "syslog",
  "message": "Log message content",
  "level": "INFO",
  "raw": { /* Full Fluent Bit entry */ }
}
```

## Management

### Stop Fluent Bit

```bash
docker stop fluent-bit
```

### Restart Fluent Bit

```bash
docker restart fluent-bit
```

### View Container Logs

```bash
docker logs -f fluent-bit
```

### Update Configuration

1. Edit `config/fluent-bit/fluent-bit.conf`
2. Restart container: `docker restart fluent-bit`

### Check Log File Size

```bash
ls -lh /var/log/fluent-bit/
du -sh /var/log/fluent-bit/
```

## Integration with Dashboard

The dashboard automatically:
1. Detects when Fluent Bit is running
2. Reads logs from `/var/log/fluent-bit/fluent-bit-output.jsonl`
3. Displays logs with proper formatting and filtering
4. Supports AI analysis for error/warning logs

## Troubleshooting

### Fluent Bit Not Starting

```bash
# Check Docker logs
docker logs fluent-bit

# Check permissions
sudo ls -la /var/log/
sudo chmod 755 /var/log/fluent-bit

# Check network
docker network ls | grep healing-network
```

### No Logs Appearing

1. Verify Fluent Bit is running: `docker ps | grep fluent-bit`
2. Check output file exists: `ls -la /var/log/fluent-bit/`
3. Check file permissions: `sudo chmod 755 /var/log/fluent-bit`
4. View Fluent Bit logs: `docker logs fluent-bit`
5. Check API endpoint: `curl http://localhost:5001/api/fluent-bit/recent`

### Permission Errors

Fluent Bit needs read access to `/var/log/`:

```bash
# Add user to adm group (if running non-containerized)
sudo usermod -aG adm $USER

# Or ensure container has proper volumes mounted
# (Already configured in docker-compose-fluent-bit.yml)
```

## Advanced Configuration

### Custom Parsers

Add custom parsers to `config/fluent-bit/parsers.conf`:

```ini
[PARSER]
    Name        custom-parser
    Format      regex
    Regex       ^(?<timestamp>.*?) (?<level>.*?) (?<message>.*)$
    Time_Key    timestamp
    Time_Format %Y-%m-%d %H:%M:%S
```

### Additional Input Sources

Add more inputs to `config/fluent-bit/fluent-bit.conf`:

```ini
[INPUT]
    Name              tail
    Path              /var/log/custom.log
    Tag               custom
    Read_from_Head    true
    Parser            syslog-rfc5424
```

### Output Configuration

Modify output in `config/fluent-bit/fluent-bit.conf`:

```ini
[OUTPUT]
    Name                elasticsearch
    Match               *
    Host                127.0.0.1
    Port                9200
    Index               logs
    Type                _doc
```

## Performance

- **Memory Usage**: ~50-100MB
- **CPU Usage**: ~1-5%
- **Log Throughput**: Up to 100k logs/second
- **File Rotation**: Configured via logrotate or Fluent Bit's built-in rotation

## Security Notes

- Fluent Bit runs with read-only access to log files
- Output directory has restricted permissions
- HTTP output (if enabled) uses basic authentication
- Logs are stored locally by default (no external transmission)

## Support

For issues or questions:
1. Check Fluent Bit documentation: https://docs.fluentbit.io/
2. Review container logs: `docker logs fluent-bit`
3. Check dashboard API: `curl http://localhost:5001/api/fluent-bit/statistics`

