# 🔍 Unused & Redundant Services Report

**Generated:** 2025-10-29  
**Status:** CRITICAL - Multiple unused services found + PORT CONFLICT detected

---

## 📊 Summary

| Service | Status | Action Required | Priority |
|---------|--------|-----------------|----------|
| **Grafana** | ❌ UNUSED | Remove | LOW |
| **Network Analyzer** | ⚠️ REDUNDANT + PORT CONFLICT | Fix or Remove | **HIGH** |
| **Incident Bot** | ⚠️ UNCLEAR | Review Usage | MEDIUM |

---

## 1. ❌ Grafana (Port 3000) - COMPLETELY UNUSED

### Issues:
- **Empty provisioning directory** - No dashboards configured
- **Not referenced anywhere** in the codebase
- **Redundant** with main dashboard (port 3001)
- **Wastes resources** (memory, CPU, port)

### Evidence:
```bash
# Empty provisioning directory
monitoring/grafana/provisioning/
... no children found ...

# Grafana config exists but not loaded
config/grafana.json (835 lines, never used)
```

### Recommendation:
**✅ SAFE TO REMOVE**

The main dashboard at port 3001 provides all visualization features.

---

## 2. ⚠️ Network Analyzer (Port 5001) - CRITICAL ISSUES

### Issues:

#### **A. PORT CONFLICT (CRITICAL)**
- Docker-compose maps network-analyzer to port **5001**:
  ```yaml
  network-analyzer:
    ports:
      - "5001:5000"
  ```
- Dashboard expects it on port **8000**:
  ```python
  self.network_analyzer_url = os.getenv("NETWORK_ANALYZER_URL", "http://localhost:8000")
  ```
- **Result:** Dashboard calls **incident-bot** instead of network-analyzer!
- **Impact:** IP blocking features may not work correctly

#### **B. REDUNDANT CODE**
- Network analyzer uses **same Dockerfile** as monitoring server:
  ```yaml
  network-analyzer:
    build:
      context: ./monitoring/server  # Same as monitoring server!
      dockerfile: Dockerfile
  ```
- Both services run the **same code**
- Monitoring server (port 5000) has the **same IP blocking** capabilities
- **Unnecessary duplication**

### Recommendation:
**Option 1:** Fix port configuration
- Change docker-compose to map network-analyzer to 8000
- Or update dashboard to use 5001

**Option 2:** Remove network-analyzer (RECOMMENDED)
- Use monitoring server (port 5000) for all API calls
- Update dashboard to call port 5000 for IP blocking
- Remove redundant service

---

## 3. ⚠️ Incident Bot (Port 8000) - UNCLEAR STATUS

### Current State:
- **Port:** 8000 (but dashboard might be calling it by mistake)
- **Features:** AWS S3 integration, Slack alerts, AI incident response
- **Referenced by:** Nothing in the dashboard code
- **Docker status:** Not running currently

### Questions:
1. Is this service actually needed?
2. Are AWS/Slack integrations actively used?
3. Should this be removed or documented?

### Recommendation:
**Review and decide:**
- If AWS/Slack integration is needed → **Keep and document**
- If not used → **Remove to simplify architecture**

---

## 📋 Recommended Actions

### Immediate (HIGH Priority):

#### 1. Fix Network Analyzer Port Conflict
**Option A - Update Docker Compose (Quickest):**
```yaml
# Change network-analyzer port from 5001 to 8000
network-analyzer:
  ports:
    - "8000:5000"  # Changed from 5001:5000
```

**Option B - Remove Network Analyzer (Recommended):**
1. Remove network-analyzer from docker-compose.yml
2. Update dashboard to use monitoring server (port 5000)
3. Test IP blocking functionality

### Short Term (MEDIUM Priority):

#### 2. Decide on Incident Bot
- Review if AWS/Slack integration is needed
- Document or remove

### Long Term (LOW Priority):

#### 3. Remove Grafana
```bash
# Remove from docker-compose.yml
# Delete unused files
rm -rf monitoring/grafana
rm config/grafana.json
```

---

## 🎯 Simplified Architecture (Recommended)

After cleanup, you would have:

```
┌─────────────────────────────────────────┐
│         Core Services                    │
├─────────────────────────────────────────┤
│ ✅ Model API (8080)                     │
│ ✅ Monitoring Server (5000) - API only  │
│ ✅ Dashboard (3001) - Main UI           │
│ ✅ Prometheus (9090) - Metrics          │
├─────────────────────────────────────────┤
│         Optional Services                │
├─────────────────────────────────────────┤
│ ⚠️  Incident Bot (8000) - TBD           │
└─────────────────────────────────────────┘

Removed:
❌ Grafana (port 3000) - Redundant
❌ Network Analyzer (port 5001) - Duplicate of monitoring server
```

---

## 💾 Current Resource Usage (Estimation)

| Service | Memory | CPU | Disk |
|---------|--------|-----|------|
| Grafana (unused) | ~200MB | ~5% | ~100MB |
| Network Analyzer (duplicate) | ~150MB | ~3% | ~50MB |
| **Total Savings** | **~350MB** | **~8%** | **~150MB** |

---

## 🔧 Implementation Steps

### Phase 1: Fix Critical Port Conflict (15 minutes)

**Option A - Quick Fix (Keep Network Analyzer):**
```bash
# Edit config/docker-compose.yml
# Change line 163 from:
      - "5001:5000"
# To:
      - "8000:5000"

# Restart services
docker-compose -f config/docker-compose.yml up -d network-analyzer
```

**Option B - Clean Fix (Remove Network Analyzer):**
```bash
# 1. Stop network-analyzer
docker-compose -f config/docker-compose.yml stop network-analyzer
docker-compose -f config/docker-compose.yml rm network-analyzer

# 2. Edit config/docker-compose.yml
# Remove network-analyzer service (lines 157-180)

# 3. Update dashboard environment in docker-compose.yml
# Change NETWORK_ANALYZER_HOST to monitoring server

# 4. Rebuild dashboard
docker-compose -f config/docker-compose.yml up -d --build dashboard
```

### Phase 2: Remove Grafana (10 minutes)
```bash
# 1. Stop Grafana
docker-compose -f config/docker-compose.yml stop grafana
docker-compose -f config/docker-compose.yml rm grafana

# 2. Remove from docker-compose.yml
# Delete grafana service (lines 131-155)

# 3. Clean up files
rm -rf monitoring/grafana
rm config/grafana.json

# 4. Update documentation
# Remove Grafana references from READMEs
```

### Phase 3: Review Incident Bot (30 minutes)
```bash
# 1. Test if incident-bot is needed
# Check AWS S3 integration
# Check Slack integration

# 2. Document or remove
# If keeping: Add to docs/guides/
# If removing: Delete from docker-compose.yml and incident-bot/
```

---

## ✅ Testing After Cleanup

### Test IP Blocking Feature:
```bash
# 1. Start dashboard
# 2. Go to IP Blocking tab
# 3. Try to block/unblock an IP
# 4. Verify it works correctly
```

### Test Metrics Collection:
```bash
# 1. Check Prometheus is scraping metrics
curl http://localhost:9090/targets

# 2. Verify dashboard shows metrics
# 3. Check system monitoring still works
```

---

## 📝 Notes

- All changes should be committed to git before making modifications
- Test each phase independently
- Keep backups of docker-compose.yml
- Document final architecture in main README

---

**Next Steps:**
1. Review this report
2. Decide on approach (Option A or B for network-analyzer)
3. Test changes in development
4. Update documentation
5. Commit to git

