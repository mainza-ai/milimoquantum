# ── Stage 1: Build Frontend (production) ─────────────
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ── Stage 1b: Dev Frontend (no tsc build) ────────────
FROM node:20-slim AS frontend-dev
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./

# ── Stage 2: Build Backend ───────────────────────────
FROM python:3.12-slim AS backend

# System deps (add curl for healthchecks)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./

# Copy frontend build output
COPY --from=frontend-build /app/frontend/dist /app/static

# Data directory
RUN mkdir -p /data/.milimoquantum

ENV HOST=0.0.0.0
ENV PORT=8000
ENV MILIMO_STORAGE_DIR=/data/.milimoquantum

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
