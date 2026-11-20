FROM python:3.11-slim AS base

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy application source and data
COPY backend /app/backend

# Create data directory with permissions for persistent SQLite and model files
RUN mkdir -p /app/backend/data

ENV PYTHONPATH="/app/backend"
ENV HOST="0.0.0.0"
ENV PORT=8000
ENV ENVIRONMENT="production"
ENV DATABASE_PATH="/app/backend/data/bhashashield.db"
ENV MODEL_PATH="/app/backend/data/muril_classifier.joblib"

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://127.0.0.1:8000/v1/health || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
