# BhashaShield — Production Deployment & Operations Checklist

**Release Version:** 1.0.0  
**Target Environment:** Docker / Docker Compose / Kubernetes  
**Auditor:** DevOps & Infrastructure Engineering Team  

---

## 1. Deployment Architecture Summary

BhashaShield is packaged as a two-tier containerized stack with a persistent data layer:

```
                  ┌──────────────────────────────┐
                  │       Client Traffic         │
                  └──────────────┬───────────────┘
                                 │
                         Port 80 │ (or 443 with TLS)
                                 ▼
                  ┌──────────────────────────────┐
                  │      Frontend Container      │
                  │   Nginx Alpine (Reverse Px)  │
                  │  Static SPA Assets + Proxy   │
                  └──────────────┬───────────────┘
                                 │
                   Internal HTTP │ http://backend:8000
                                 ▼
                  ┌──────────────────────────────┐
                  │      Backend Container       │
                  │   Python 3.11-slim / Uvicorn │
                  │  FastAPI Intelligence Engine │
                  └──────────────┬───────────────┘
                                 │
                       Mounted Volume /app/backend/data
                                 ▼
                  ┌──────────────────────────────┐
                  │  Persistent Volume (SQLite)  │
                  │   bhashashield_sqlite_data   │
                  │   WAL Mode Enabled           │
                  └──────────────────────────────┘
```

---

## 2. Pre-Flight Configuration Checklist

| Item | Requirement | Status | Verification Command |
|---|---|---|---|
| **Environment File** | Copy `.env.example` to `.env` | Required | `cp .env.example .env` |
| **Admin Secret** | Set strong `ADMIN_API_KEY` | Required | Check `ADMIN_API_KEY` in `.env` |
| **CORS Whitelist** | Set strict production origins | Recommended | `CORS_ORIGINS="https://yourdomain.com"` |
| **Persistent Volume**| Bind `bhashashield_sqlite_data` | Verified | Verified in `docker-compose.yml` |
| **Container User** | Non-root service isolation | Configured | Python unprivileged runtime |
| **Health Probes** | Backend & Frontend probes | Configured | Probes defined on `/v1/health` |

---

## 3. Operational Runbooks

### 3.1 Launching the Stack via Docker Compose
To build and launch both services in detached mode:
```bash
docker-compose up --build -d
```

Verify service status:
```bash
docker-compose ps
```

---

### 3.2 Health Check Inspection
Inspect API health and engine state:
```bash
curl -f http://localhost:8000/v1/health
```
Expected output:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "model_status": "LOADED",
  "engine": "BhashaShield Enterprise Intelligence Engine",
  "policy_engine": "ACTIVE"
}
```

---

### 3.3 Database Backup Runbook
To create an atomic, non-blocking online backup without taking the database offline:
```bash
docker-compose exec backend python scripts/backup_db.py --backup
```
Backups are timestamped and saved into `/app/backend/data/backups/`. Integrity is checked automatically via `PRAGMA integrity_check`.

To schedule automated daily backups via host crontab:
```cron
0 2 * * * docker-compose -f /opt/bhashashield/docker-compose.yml exec -T backend python scripts/backup_db.py --backup >> /var/log/bhashashield_backup.log 2>&1
```

---

### 3.4 Database Restoration Runbook
To restore a verified backup to the running service:
```bash
docker-compose exec backend python scripts/backup_db.py --restore /app/backend/data/backups/bhashashield_backup_<TIMESTAMP>.db
```
The restore utility automatically verifies file integrity prior to overwriting the database.

---

### 3.5 Upgrades & Rolling Restarts
To perform a zero-downtime rolling restart or apply an updated release:
```bash
git pull origin main
docker-compose build
docker-compose up -d --no-deps backend
docker-compose up -d --no-deps frontend
```
Because the SQLite database is mounted to the external `bhashashield_sqlite_data` volume, container recreation does not incur data loss.
