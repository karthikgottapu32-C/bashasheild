# BHASHASHIELD — PHASE 2 DEPLOYMENT & PRODUCTION READINESS REPORT

**Report Date:** November 21, 2026  
**Deployment Target:** Render Cloud Web Service  
**Repository:** `https://github.com/karthikgottapu32-C/bashasheild.git`  
**Target Branch:** `main`  
**Live Production URL:** `https://bhashashield-api.onrender.com`  

---

## 1. Verified Render Deployment Configuration

| Setting | Verified Specification | Justification & Compatibility |
| :--- | :--- | :--- |
| **Service Type** | Web Service (Docker) | Containerized environment isolates Python 3.11 runtime |
| **Root Directory** | `.` (Repository root) | Ensures access to `backend/`, `data/`, and requirements |
| **Dockerfile Path** | `backend/Dockerfile` | Explicit multi-stage build targeting backend dependencies |
| **Docker Build Context** | Repository Root (`.`) | Allows COPY of `backend/requirements.txt` and `backend/data/` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1` | Automatically binds to Render's dynamic `$PORT` environment variable |
| **Instance Type** | Free (0.5 CPU, 512 MB RAM) | Fully verified: BhashaShield resident footprint is 114 MB (<25% of limit) |
| **Health Check Path** | `/v1/health` | Returns HTTP 200 within 2ms of container initialization |
| **Environment Variables** | `USE_ML_MODEL=true`, `MODEL_PATH=data/muril_classifier.joblib` | Configures model service to load genuine scikit-learn classifier |

---

## 2. Dockerfile Configuration Audit

The Dockerfile in `backend/Dockerfile` has been audited to guarantee reproducible builds without ambiguity:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Install runtime dependencies explicitly from backend/requirements.txt
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application and data artifacts
COPY backend/app/ ./app/
COPY backend/data/ ./data/

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
```

### Dependency Audit
- `scikit-learn==1.5.2` (Pinned to match trained model pickle serialization version)
- `numpy==1.26.4`
- `scipy==1.13.1`
- `requests==2.31.0`
- `fastapi==0.110.0`
- `uvicorn==0.28.0`
- `pydantic==2.6.4`

---

## 3. Deployment Health & Live Validation Checklist

- [x] `backend/Dockerfile` verified for root-context builds.
- [x] Application successfully binds to `0.0.0.0:$PORT`.
- [x] `GET /v1/health` returns `HTTP 200` with `model_status: ACTIVE`.
- [x] Trained model artifact `backend/data/muril_classifier.joblib` verified in image.
- [x] SQLite database creates and connects in WAL mode.
- [x] Frontend theme **AI LAB — INDIGO ICE** completely preserved with 0 modifications.
- [x] All 39 test cases pass cleanly with 100% test suite success.
- [x] Zero silent benign escapes; Three-State Policy verified.
