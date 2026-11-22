FROM python:3.11-slim AS base

# Install curl for container healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source and data
COPY . ./

# Normalize layout: if copied from repo root, flatten backend/* to /app
RUN if [ -d backend/app ]; then \
        cp -rn backend/* ./ && rm -rf backend; \
    fi

# Ensure data directory exists with write permissions for SQLite runtime
RUN mkdir -p /app/data

# Maintain backwards-compatibility alias for /app/backend and its submodules
RUN mkdir -p /app/backend && \
    (ln -s /app/data /app/backend/data 2>/dev/null || true) && \
    (ln -s /app/app /app/backend/app 2>/dev/null || true)

ENV PYTHONPATH="/app:/app/backend"
ENV HOST="0.0.0.0"
ENV PORT=10000
ENV ENVIRONMENT="production"
ENV DATABASE_PATH="/app/data/bhashashield.db"
ENV MODEL_PATH="/app/data/muril_classifier.joblib"

EXPOSE 10000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://127.0.0.1:${PORT:-10000}/v1/health || exit 1

# Render dynamically injects $PORT (e.g. 10000). Using sh -c expands ${PORT:-10000} properly.
# 1 worker process consumes ~135MB RAM, safely below Render's 512MB free/starter tier limit.
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000} --workers 1"]
