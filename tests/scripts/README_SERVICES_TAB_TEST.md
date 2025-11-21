# Services Tab Feature Test

This test script verifies that the services tab correctly filters out running services and only displays stopped/failed services.

## Prerequisites

1. The healing dashboard API must be running on port 5001 (default)
   ```bash
   # Start the healing dashboard API
   python monitoring/server/healing_dashboard_api.py
   # OR
   uvicorn monitoring.server.healing_dashboard_api:app --host 0.0.0.0 --port 5001
   ```

2. Python 3.6+ with required packages:
   ```bash
   pip install requests
   ```

3. Sudo access (for service management tests)

## Running the Test

### Basic Test
```bash
python tests/scripts/test_services_tab_feature.py
```

### With Custom API URL
```bash
BASE_URL=http://localhost:5001 python tests/scripts/test_services_tab_feature.py
```

## What the Test Does

1. **API Endpoint Test**: Verifies `/api/services` endpoint exists and returns correct data
2. **Response Format Test**: Checks that API response has correct structure
3. **Filtering Logic Test**: Ensures only non-running services are returned
4. **Service Restart Test**: Tests restarting a stopped service (if available)

## Test Scenarios

### Scenario 1: All Services Running
When all services are running, the API should return an empty list or show "All Services Running" message.

### Scenario 2: Some Services Stopped
When some services are stopped, the API should only return those stopped services, not the running ones.

### Scenario 3: Service Restart
The test can verify that restarting a service works correctly.

## Manual Testing

To manually test the feature:

1. **Stop a service**:
   ```bash
   sudo systemctl stop nginx
   ```

2. **Check the API**:
   ```bash
   curl http://localhost:5001/api/services | jq .
   ```

3. **Verify only stopped services are returned**:
   - The response should only include `nginx` (stopped)
   - Running services like `mysql`, `ssh`, `docker` should NOT appear

4. **Start the service again**:
   ```bash
   sudo systemctl start nginx
   ```

5. **Verify it's removed from the API response**:
   ```bash
   curl http://localhost:5001/api/services | jq .
   ```
   - `nginx` should no longer appear in the response

## Expected Output

```
============================================================
        Services Tab Feature Test Suite
============================================================

ℹ️  This script tests that the services tab only shows non-running services
ℹ️  Testing against: http://localhost:5001
ℹ️  Services to test: nginx, mysql, ssh, docker, postgresql

============================================================
        Testing API Endpoint: /api/services
============================================================

ℹ️  Fetching services from: http://localhost:5001/api/services
✅ API returned 2 services
ℹ️  Actual running services: 3
ℹ️  Actual stopped services: 2
✅ API correctly filters out running services

API Response:
  🔴 nginx: stopped
  🔴 postgresql: stopped

Actual Service Statuses:
  🟢 nginx: Running
  🟢 mysql: Running
  🟢 ssh: Running
  🔴 docker: Stopped
  🔴 postgresql: Stopped

============================================================
                Test Summary
============================================================

✅ API Endpoint Test: PASSED
✅ Response Format Test: PASSED
✅ Filtering Logic Test: PASSED
✅ Service Restart Test: PASSED

Results: 4/4 tests passed
✅ All tests passed! ✅
```

## Troubleshooting

### Connection Error
If you see "Could not connect to http://localhost:5001":
- Make sure the healing dashboard API is running
- Check the port number (default is 5001)
- Verify firewall settings

### Permission Denied
If service status checks fail:
- Ensure you have sudo access
- Some services may require root privileges to check status

### No Stopped Services
If all services are running:
- The test will still verify that the API returns an empty list
- To test restart functionality, manually stop a service first

## Integration with CI/CD

You can integrate this test into your CI/CD pipeline:

```yaml
# Example GitHub Actions
- name: Test Services Tab Feature
  run: |
    python tests/scripts/test_services_tab_feature.py
```

