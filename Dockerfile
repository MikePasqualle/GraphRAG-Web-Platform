# Root Dockerfile: builds a single container running Backend (FastAPI) + Frontend (Next.js) + Nginx via Supervisor

# ----------------------
# Backend build stage
# ----------------------
FROM python:3.11-slim AS backend-build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    pkg-config \
    libhdf5-dev \
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libjpeg-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend

# Copy and install backend dependencies
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ ./

# ----------------------
# Frontend deps stage
# ----------------------
FROM node:18-alpine AS frontend-deps
WORKDIR /app/frontend
COPY frontend/package*.json ./
# Robust install: prefer lockfile, fallback to install
RUN npm install --frozen-lockfile || npm install

# ----------------------
# Frontend build stage
# ----------------------
FROM node:18-alpine AS frontend-build
WORKDIR /app/frontend
# Bring node_modules from deps to keep cache
COPY --from=frontend-deps /app/frontend/node_modules ./node_modules
# Copy full frontend source (ensures tsconfig.json, next.config.js, src/** exist)
COPY frontend/ ./
# Early sanity checks to fail fast if files missing
RUN test -f tsconfig.json && test -f next.config.js && test -f src/lib/utils.ts
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# ----------------------
# Final runtime image
# ----------------------
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NEXT_TELEMETRY_DISABLED=1 \
    APP_HOME=/app

# Install system packages: Node.js 18, Nginx, Supervisor
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gnupg ca-certificates nginx supervisor \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get update && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR ${APP_HOME}

# Create directories
RUN mkdir -p ${APP_HOME}/backend ${APP_HOME}/frontend ${APP_HOME}/logs ${APP_HOME}/data/uploads ${APP_HOME}/data/output ${APP_HOME}/data/metadata ${APP_HOME}/data/cache

# Copy backend (with installed site-packages)
COPY --from=backend-build /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=backend-build /usr/local/bin /usr/local/bin
COPY --from=backend-build /app/backend ${APP_HOME}/backend

# Copy frontend standalone build
COPY --from=frontend-build /app/frontend/.next/standalone ${APP_HOME}/frontend
COPY --from=frontend-build /app/frontend/.next/static ${APP_HOME}/frontend/.next/static
COPY --from=frontend-build /app/frontend/public ${APP_HOME}/frontend/public

# Nginx config
COPY nginx/nginx.conf /etc/nginx/nginx.conf

# Supervisor config and entrypoint
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Permissions
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser \
    && chown -R appuser:appgroup ${APP_HOME}

EXPOSE 80

USER appuser

# Start services via Supervisor: 
# - uvicorn (FastAPI backend) at 127.0.0.1:8000
# - node (Next.js server) at 127.0.0.1:3000
# - nginx reverse-proxy on :80
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]


