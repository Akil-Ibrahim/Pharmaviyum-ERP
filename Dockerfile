# ===========================================================================
# Multi‑stage Dockerfile for Pharmaviyum CRM
# Updated for CI stability and best practices (2026)
# ===========================================================================

# ---------------------------------------------------------------------------
# Stage 1 – Builder (install build‑time dependencies)
# ---------------------------------------------------------------------------
FROM python:3.13-slim AS builder

# Make apt non‑interactive to avoid debconf dialogs in CI
ARG DEBIAN_FRONTEND=noninteractive

# Environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1

# Install system packages required to compile Python wheels
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        g++ \
        cmake && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Cache‑friendly copy of requirements
COPY requirements.txt .

# Install Python dependencies (cache layer for pip)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------------------
# Stage 2 – Production (minimal runtime image)
# ---------------------------------------------------------------------------
FROM python:3.13-slim AS production

LABEL maintainer="Pharmaviyum Team <dev@pharmaviyum.com>" \
      version="1.0.0" \
      description="AI‑powered CRM for pharmacy retail in SE Asia"

# Non‑interactive flag for the second stage as well
ARG DEBIAN_FRONTEND=noninteractive

# Runtime environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000 \
    ENVIRONMENT=production

# Install runtime tools required by the startup entrypoint and health checks.
# pg_isready is required for DB readiness, redis-cli for Redis readiness.
# `--no-log-init` avoids writing to /var/log/lastlog which can be problematic
# in slim images.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        postgresql-client \
        redis-tools \
        python3-setuptools && \
    rm -rf /var/lib/apt/lists/* && \
    useradd --create-home --shell /bin/bash --no-log-init app

WORKDIR /app

# Copy Python packages and binaries from the builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application source code, changing ownership to the non‑root user.
# The user already exists (created above), so `--chown` works reliably.
COPY --chown=app:app src/ ./src
COPY --chown=app:app alembic/ ./alembic
COPY --chown=app:app alembic.ini .
COPY --chown=app:app docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Run the container as the non‑root user
USER app

EXPOSE 8000

# Lightweight healthcheck using curl (silent, fail fast)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

# Entrypoint & default command
ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "src.pharmaviyum.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
