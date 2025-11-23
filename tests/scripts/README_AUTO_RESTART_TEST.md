# Auto-Restart Feature Test

These test scripts verify that the system automatically restarts stopped services.

## ⚠️ WARNING

**These scripts will STOP services!** Only run them in a test environment or when you're prepared for services to be temporarily unavailable.

## Prerequisites

1. The healing dashboard API must be running:
   ```bash
   python monitoring/server/healing_dashboard_api.py
   # OR
   uvicorn monitoring.server.healing_dashboard_api:app --host 0.0.0.0 --port 5001
   ```

2. Auto-restart must be enabled in the configuration

3. Sudo access (required to stop/start services)

## Test Scripts

### 1. Simple Bash Test (`test_auto_restart_simple.sh`)

**Quick test for a single service**

```bash
# Test nginx (default)
./tests/scripts/test_auto_restart_simple.sh

# Test a specific service
./tests/scripts/test_auto_restart_simple.sh mysql

# Test with custom wait time (default is 30 seconds)
./tests/scripts/test_auto_restart_simple.sh nginx 60
```

**What it does:**
1. Checks if service is running
2. Stops the service
3. Waits and monitors for automatic restart
4. Reports success or failure

### 2. Comprehensive Python Test (`test_auto_restart_feature.py`)

**Full-featured test with multiple options**

```bash
# Run the test (interactive menu)
python tests/scripts/test_auto_restart_feature.py
```

**Test Options:**
1. **Single Service Test** - Tests auto-restart for nginx
2. **Two Services Test** - Tests auto-restart for nginx and mysql simultaneously
3. **All Services Test** - Tests all monitored services
4. **Custom Selection** - Choose specific services to test

**What it does:**
- Checks API connection
- Verifies auto-restart configuration
- Stops service(s)
- Monitors for automatic restart
- Provides detailed results and timing

## Example Usage

### Quick Test (Bash)
```bash
$ ./tests/scripts/test_auto_restart_simple.sh nginx

==========================================
  Auto-Restart Feature Test
==========================================

Service to test: nginx
Wait time: 30s

Step 1: Checking initial status...
✅ Service nginx is running

Step 2: Stopping service nginx...
✅ Service nginx stopped successfully

Step 3: Waiting for automatic restart (checking every 2s)...
-----------------------------------

==========================================
✅ SUCCESS: Service nginx was automatically restarted!
   Restart time: 4 seconds
==========================================
```

### Comprehensive Test (Python)
```bash
$ python tests/scripts/test_auto_restart_feature.py

======================================================================
        Auto-Restart Feature Test Suite
======================================================================

ℹ️  This script tests that the system automatically restarts stopped services
ℹ️  Testing against: http://localhost:5001
ℹ️  Services to test: nginx, mysql, ssh, docker, postgresql
⚠️  This script will STOP services. Make sure you're in a test environment!

➜ Checking API connection...
✅ API is accessible
➜ Checking auto-restart configuration...
✅ Auto-restart is ENABLED

======================================================================
Select test mode:
  1. Test single service (nginx)
  2. Test two services (nginx, mysql)
  3. Test all services
  4. Custom service selection
======================================================================

Enter choice (1-4) [default: 1]: 2

======================================================================
        Testing Auto-Restart: Multiple Services (nginx, mysql)
======================================================================

➜ Step 1: Ensuring all services are running
ℹ️  Starting nginx...
✅ Service nginx started successfully
ℹ️  Starting mysql...
✅ Service mysql started successfully

➜ Step 2: Stopping all services
➜ Stopping service: nginx
✅ Service nginx stopped successfully
➜ Stopping service: mysql
✅ Service mysql stopped successfully
✅ Stopped 2 service(s)

➜ Step 3: Monitoring for automatic restart
ℹ️  Monitoring 2 service(s) for up to 30 seconds...
✅ nginx was automatically restarted after 3.2s
✅ mysql was automatically restarted after 4.1s

======================================================================
                        Test Results
======================================================================

✅ Successfully auto-restarted: 2/2

Restarted services:
  ✅ nginx
  ✅ mysql

======================================================================
                        Test Summary
======================================================================

✅ Two Services Test (nginx, mysql): PASSED

Results: 1/1 tests passed
✅ All tests passed! ✅
```

## How It Works

1. **Initial Check**: Verifies the service is running
2. **Stop Service**: Uses `systemctl stop` to stop the service
3. **Monitor**: Checks service status every 2 seconds
4. **Verify**: Confirms the service was automatically restarted
5. **Report**: Shows success/failure with timing information

## Expected Behavior

When a service is stopped:
- The monitoring loop should detect it within 2-5 seconds
- The auto-restart mechanism should restart it automatically
- The service should be running again within 5-10 seconds

## Troubleshooting

### Service Not Auto-Restarting

1. **Check Auto-Restart Configuration**:
   ```bash
   curl http://localhost:5001/api/config | jq .auto_restart
   ```
   Should return `true`

2. **Check Monitoring Loop**:
   - Verify the monitoring loop is running
   - Check logs for monitoring activity

3. **Check Service List**:
   - Ensure the service is in the monitored services list
   - Default: `["nginx", "mysql", "ssh", "docker", "postgresql"]`

4. **Check Service Status**:
   ```bash
   systemctl status nginx
   ```

### API Not Accessible

```bash
# Check if API is running
curl http://localhost:5001/api/health

# Start API if not running
python monitoring/server/healing_dashboard_api.py
```

### Permission Issues

Make sure you have sudo access:
```bash
sudo systemctl status nginx
```

## Integration with CI/CD

```yaml
# Example GitHub Actions
- name: Test Auto-Restart Feature
  run: |
    # Start API in background
    python monitoring/server/healing_dashboard_api.py &
    sleep 5
    
    # Run test
    python tests/scripts/test_auto_restart_feature.py
```

## Notes

- The test waits up to 30 seconds by default for auto-restart
- Services are stopped temporarily during testing
- The test verifies both single and multiple service scenarios
- All services are restored to running state after testing (if auto-restart works)

