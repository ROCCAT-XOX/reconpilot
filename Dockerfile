# ============================================
# ReconForge Multi-Stage Build
# Backend (Python/FastAPI) + Frontend (React) + Nginx
# ============================================

# --- Stage 1: Frontend Build ---
FROM node:22-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --ignore-scripts
COPY frontend/ ./
RUN npm run build

# --- Stage 2: Backend Dependencies ---
FROM python:3.12-slim AS backend-deps
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*
COPY backend/ ./
RUN pip install --no-cache-dir --prefix=/install .

# --- Stage 3: Production Image ---
FROM python:3.12-slim AS production
WORKDIR /app

# Install nginx + runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies
COPY --from=backend-deps /install /usr/local

# Copy backend code
COPY backend/ /app/backend/
ENV PYTHONPATH=/app/backend

# Copy frontend build
COPY --from=frontend-build /app/frontend/dist /usr/share/nginx/html

# Nginx config
RUN rm /etc/nginx/sites-enabled/default
COPY nginx/nginx-docker.conf /etc/nginx/conf.d/default.conf

# Scripts (entrypoint, seed, backup)
COPY scripts/ /app/scripts/
COPY scripts/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh /app/scripts/*.sh

# Data directories
RUN mkdir -p /app/data/reports /app/data/scans /app/data/uploads

EXPOSE 80

ENTRYPOINT ["/docker-entrypoint.sh"]
