# Production Dockerfile for Pharmaviyum-CRM
# Security-hardened multi-stage build following best practices

# ========== BUILD STAGE ==========
FROM python:3.14-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/* \
    && apt-get clean

# Upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn \
    && rm -rf ~/.cache/pip

# ========== RUNTIME STAGE ==========
FROM python:3.14-slim AS runtime

# Labels for image metadata
LABEL maintainer="Akil Ibrahim <akil.ibrahim@example.com>" \
      version="1.0.0" \
      description="Pharmaviyum CRM - Pharmacy Management System" \
      security.contact="security@example.com"

# Create non-root user with minimal privileges
RUN groupadd --gid 1000 --system appgroup \
    && useradd --uid 1000 --gid 1000 --system --create-home --shell /bin/bash appuser \
    && apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    tini \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/* \
    && apt-get clean \
    && rm -rf /tmp/* /var/tmp/*

WORKDIR /app

# Copy Python packages from builder (only necessary binaries)
COPY --from=builder /usr/local/lib/python3.14/site-packages/ /usr/local/lib/python3.14/site-packages/
COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn
COPY --from=builder /usr/local/bin/gunicorn /usr/local/bin/gunicorn
COPY --from=builder /usr/local/bin/pip /usr/local/bin/pip

# Clean Python cache in site-packages
RUN find /usr/local/lib/python3.14/site-packages/ -type d -name "__pycache__" -exec rm -rf {} + \
    && find /usr/local/lib/python3.14/site-packages/ -name "*.pyc" -delete \
    && find /usr/local/lib/python3.14/site-packages/ -name "*.pyo" -delete

# Copy application code with proper ownership
COPY --chown=appuser:appgroup . .

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/models \
    && chown appuser:appgroup /app \
    && chown -R appuser:appgroup /app/data /app/logs /app/models \
    && chmod 750 /app \
    && chmod -R 750 /app/data /app/logs /app/models

# Set secure environment variables
ENV PYTHONPATH=/app/src \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Security: Disable Python's interactive features
ENV PYTHONNOUSERSITE=1

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use tini as init system for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Start application with gunicorn (production server)
CMD ["gunicorn", "pharmaviyum.main:app", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--capture-output", \
     "--enable-stdio-inheritance"]
