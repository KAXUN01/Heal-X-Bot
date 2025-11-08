# Fix Fluent Bit Container Restarting Issue

## Problem
The Fluent Bit container is restarting with exit code 255, indicating a configuration or startup error.

## Quick Fix

Run the diagnostic script first to see what's wrong:

```bash
cd /home/kasun/Documents/Heal-X-Bot
./scripts/diagnose-fluent-bit.sh
```

Then run the fix script:

```bash
cd /home/kasun/Documents/Heal-X-Bot
./scripts/fix-fluent-bit.sh
```

## Manual Fix Steps

### 1. Stop and Remove the Failing Container

```bash
docker stop fluent-bit
docker rm fluent-bit
```

### 2. Check Container Logs

```bash
docker logs fluent-bit --tail 50
```

This will show you the exact error.

### 3. Common Issues and Fixes

#### Issue 1: Network Doesn't Exist
```bash
docker network create healing-network
```

#### Issue 2: Configuration Error
```bash
# Test configuration
docker run --rm -v "$(pwd)/config/fluent-bit:/fluent-bit/etc:ro" \
  fluent/fluent-bit:latest \
  /fluent-bit/bin/fluent-bit -c /fluent-bit/etc/fluent-bit.conf --dry-run
```

#### Issue 3: Output Directory Permissions
```bash
mkdir -p logs/fluent-bit
chmod 755 logs/fluent-bit
```

#### Issue 4: Systemd Journal Access
The systemd input might fail if journald is not accessible. You can temporarily disable it by commenting out the systemd input in `config/fluent-bit/fluent-bit.conf`.

### 4. Start with Minimal Configuration

Create a minimal config to test:

```bash
cat > config/fluent-bit/fluent-bit-minimal.conf << 'EOF'
[SERVICE]
    Flush         1
    Daemon        off
    Log_Level     info

[INPUT]
    Name              tail
    Path              /var/log/syslog
    Tag               syslog
    Read_from_Head    false
    Refresh_Interval  2

[OUTPUT]
    Name                file
    Match               *
    Path                /fluent-bit-output
    File                fluent-bit-output.jsonl
    Format              json_lines
EOF

# Test with minimal config
docker run -d \
    --name fluent-bit-test \
    --network healing-network \
    -v "$(pwd)/config/fluent-bit/fluent-bit-minimal.conf:/fluent-bit/etc/fluent-bit.conf:ro" \
    -v "$(pwd)/logs/fluent-bit:/fluent-bit-output" \
    -v /var/log:/var/log:ro \
    fluent/fluent-bit:latest \
    /fluent-bit/bin/fluent-bit -c /fluent-bit/etc/fluent-bit.conf

# Check if it works
sleep 3
docker ps | grep fluent-bit-test
docker logs fluent-bit-test
```

### 5. Full Restart with Fix Script

The fix script handles all these issues:

```bash
cd /home/kasun/Documents/Heal-X-Bot
./scripts/fix-fluent-bit.sh
```

## Verify It's Working

After fixing:

```bash
# Check container status
docker ps | grep fluent-bit

# Check logs
docker logs fluent-bit --tail 20

# Check if log file is being created
ls -lh logs/fluent-bit/fluent-bit-output.jsonl
tail -f logs/fluent-bit/fluent-bit-output.jsonl
```

## Common Error Messages and Solutions

### "Error: cannot open file"
- **Solution**: Check file paths and permissions

### "Error: network not found"
- **Solution**: Create network: `docker network create healing-network`

### "Error: permission denied"
- **Solution**: Check volume mount permissions, ensure directories exist

### "Error: systemd journal not accessible"
- **Solution**: Remove systemd input or ensure `/run/journal` is mounted

### "Error: configuration file not found"
- **Solution**: Check file paths in docker run command

## Alternative: Simplified Configuration

If systemd input is causing issues, use this simplified config:

```bash
# Edit config/fluent-bit/fluent-bit.conf
# Comment out the [INPUT] systemd section (lines 43-49)
```

Or create a new simplified config file and use that instead.

## Still Not Working?

1. Check Docker daemon is running: `docker ps`
2. Check disk space: `df -h`
3. Check Docker logs: `journalctl -u docker.service`
4. Try running Fluent Bit manually to see exact error:
   ```bash
   docker run --rm -it \
     -v "$(pwd)/config/fluent-bit:/fluent-bit/etc:ro" \
     -v "$(pwd)/logs/fluent-bit:/fluent-bit-output" \
     -v /var/log:/var/log:ro \
     fluent/fluent-bit:latest \
     /fluent-bit/bin/fluent-bit -c /fluent-bit/etc/fluent-bit.conf
   ```

## Summary

**Quick fix**: Run `./scripts/fix-fluent-bit.sh`

**Manual fix**: 
1. Stop container: `docker stop fluent-bit && docker rm fluent-bit`
2. Check logs: `docker logs fluent-bit`
3. Create network: `docker network create healing-network`
4. Fix permissions: `chmod 755 logs/fluent-bit`
5. Restart with fix script or manually
