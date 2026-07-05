# ============================================================================
# Multi-stage Dockerfile for Pharmaviyum CRM
# Best practice 2026: Security, size optimization, layer caching
# ============================================================================

# ----------------------------------------------------------------------------
# Stage 1: Builder - Install dependencies
# ----------------------------------------------------------------------------
FROM python:3.14.6-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ----------------------------------------------------------------------------
# Stage 2: Production - Minimal runtime image
# ----------------------------------------------------------------------------
FROM python:3.14.6-slim as production

# Metadata
LABEL maintainer="Pharmaviyum Team <dev@pharmaviyum.com>" \
      version="1.0.0" \
      description="AI-powered CRM for pharmacy retail in Southeast Asia"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000 \
    ENVIRONMENT=production

# Install runtime system dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash app

# Set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=app:app src/ ./src
COPY --chown=app:app alembic/ ./alembic
COPY --chown=app:app alembic.ini .

# Copy entrypoint script
COPY --chown=app:app docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Switch to non-root user
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "src.pharmaviyum.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
