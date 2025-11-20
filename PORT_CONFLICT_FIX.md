# Port Conflict Fix - Database Port 5432

## Issue
Port 5432 was already in use by a local PostgreSQL installation, causing the cloud simulation database container to fail to start.

## Solution
Changed the host port mapping for the database from `5432:5432` to `15432:5432` in `docker-compose-cloud-sim.yml`.

## Changes Made

### Docker Compose Configuration
- **File**: `config/docker-compose-cloud-sim.yml`
- **Change**: Database port mapping updated from `"5432:5432"` to `"15432:5432"`
- **Impact**: 
  - Host port: 15432 (avoids conflict)
  - Container port: 5432 (unchanged - internal networking still works)

### Why This Works
- Containers communicate via Docker's internal network using container port 5432
- Only the host port mapping changed, so the API server connection string remains unchanged
- External access to the database now uses port 15432

## Usage

### Starting Services
```bash
# Clean up any existing containers first
docker compose -f config/docker-compose-cloud-sim.yml down

# Start services with new port mapping
docker compose -f config/docker-compose-cloud-sim.yml up -d
```

### Connecting to Database
- **From host machine**: `localhost:15432`
- **From other containers**: `database:5432` (internal Docker network)

### API Server Connection
The API server uses `DATABASE_URL=postgresql://postgres:postgres@database:5432/cloudsim` which works correctly because:
- `database` is the service name in Docker network
- `5432` is the container's internal port (unchanged)

## Verification
```bash
# Check if database is running
docker ps | grep cloud-sim-database

# Test connection from host
psql -h localhost -p 15432 -U postgres -d cloudsim

# Or use docker exec
docker exec -it cloud-sim-database psql -U postgres -d cloudsim
```

## Notes
- If you have a local PostgreSQL running on 5432, it will continue to work normally
- The cloud simulation database is now isolated on port 15432
- No changes needed to application code - internal networking is unchanged

