# Fluent Bit Format Fix

## Error Fixed
```
[error] [output:file:file.0] unknown format json_lines. abort.
```

## Solution
The file output plugin in Fluent Bit doesn't support `Format json_lines` parameter. I've removed it.

The file plugin will now write in its default format. To get proper JSON output, you have two options:

### Option 1: Use Default Format (Current)
The file plugin writes in a structured format by default. The configuration now is:

```ini
[OUTPUT]
    Name                file
    Match               *
    Path                /fluent-bit-output
    File                fluent-bit-output.jsonl
    json_date_key       timestamp
    json_date_format    %Y-%m-%dT%H:%M:%S
```

### Option 2: Use stdout with JSON Format (Alternative)
If you need pure JSON lines, you could redirect stdout:

```ini
[OUTPUT]
    Name                stdout
    Match               *
    Format              json
```

But this requires redirecting output in the docker run command.

## Current Configuration
The config file now:
- ✅ Removed invalid `Format json_lines` parameter
- ✅ Uses file plugin default format
- ✅ Added JSON date formatting options
- ✅ Simplified to just syslog and kern.log inputs

## Start Fluent Bit

```bash
cd /home/kasun/Documents/Heal-X-Bot

# Stop old container
docker stop fluent-bit 2>/dev/null
docker rm fluent-bit 2>/dev/null

# Start with fixed config
./scripts/start-fluent-bit-fixed.sh
```

Or manually:

```bash
docker run -d \
    --name fluent-bit \
    --restart unless-stopped \
    --network healing-network \
    -v $(pwd)/config/fluent-bit/fluent-bit.conf:/fluent-bit/etc/fluent-bit.conf:ro \
    -v /var/log:/var/log:ro \
    -v $(pwd)/logs/fluent-bit:/fluent-bit-output \
    fluent/fluent-bit:latest \
    /fluent-bit/bin/fluent-bit -c /fluent-bit/etc/fluent-bit.conf
```

## Verify

```bash
# Check container is running
docker ps | grep fluent-bit

# Check logs (should show no errors)
docker logs fluent-bit

# Check output file
ls -lh logs/fluent-bit/fluent-bit-output.jsonl
tail -f logs/fluent-bit/fluent-bit-output.jsonl
```

The file will contain log entries in Fluent Bit's default format, which should be readable by the reader.
