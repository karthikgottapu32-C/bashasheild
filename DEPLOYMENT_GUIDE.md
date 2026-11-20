# BhashaShield Deployment & Production Operations Guide

## 1. System Requirements

- **Python**: Version 3.10+ (tested on Python 3.11)
- **Node.js**: Version 18+ (tested on Node.js 20+)
- **Operating System**: Linux (Debian, Ubuntu, Alpine), macOS, or Windows Server
- **Hardware Profile**: 2 CPU cores, 4 GB RAM minimum for high-throughput rule & n-gram inference (sub-15ms P95 latency).
- **Persistent Storage**: Minimum 1 GB persistent volume for SQLite audit logs and ML model artifacts.

---

## 2. Docker & Containerized Deployment (Recommended)

BhashaShield includes production Dockerfiles and a `docker-compose.yml` configuration with persistent storage and health probes.

### Quick Start with Docker Compose:
```bash
# 1. Clone repository and navigate to root
cd bhashashield

# 2. Configure environment
cp .env.example .env

# 3. Build and launch services
docker compose up -d --build

# 4. Verify running services
docker compose ps
```

### Container Architecture:
- `bhashashield-backend`: FastAPI application on port 8000 with Python 3.11-slim, persistent volume mount at `/app/backend/data`.
- `bhashashield-frontend`: High-performance Nginx Alpine container on port 80 serving compiled React SPA assets and reverse-proxying API calls to backend.
- `bhashashield_sqlite_data`: Named Docker volume ensuring SQLite audit database persists across container restarts and updates.

### Model Loading Verification:
The deployment container requires access to `muril_classifier.joblib` located at `/app/backend/data/muril_classifier.joblib`. If missing, the backend automatically initializes in deterministic rule-only fallback mode and can retrain via:
```bash
docker compose exec backend python -m app.ml.train
```

---

## 3. Manual Bare-Metal Production Deployment

### Backend Service (Uvicorn / Systemd)
```powershell
# Windows
$env:PYTHONPATH="$PWD\backend"
python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --workers 4
```

```bash
# Linux with Gunicorn + Uvicorn Workers
export PYTHONPATH="$PWD/backend"
gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:8000
```

### Frontend Build & Hosting
```bash
cd frontend
npm ci
npm run build
```
Deploy the generated `frontend/dist/` assets to Nginx, AWS S3 / CloudFront, or Cloudflare Pages.

---

## 4. Production Health Monitoring & Alerts

| Endpoint | Method | Purpose | SLA / Target |
| :--- | :---: | :--- | :--- |
| `/v1/health` | GET | Liveness & Readiness probe | 200 OK (`{"status":"healthy"}`) |
| `/v1/decision` | POST | High-throughput AI guardrail | Sub-50ms latency |
| `/stats` | GET | SOC dashboard metrics | Aggregated threat distribution |
| `/evaluation/report` | GET | Held-out benchmark metrics | F1 > 0.95, FPR < 0.05 |

---

## 5. Security & Secret Management

- Store sensitive environment variables in secure secret managers (e.g., AWS Secrets Manager, GCP Secret Manager, or HashiCorp Vault).
- Never commit `.env` files containing production secrets to version control.
- In production, set `CORS_ORIGINS` to explicit authorized domains rather than wildcards.
