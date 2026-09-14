# ============================================================================
# PHARMAVIYUM AI - Multi-stage Dockerfile
# Python 3.14 + Tesseract OCR + pgvector support
# ============================================================================

# ----------------------------------------------------------------------------
# Stage 1: Builder — install heavy dependencies
# ----------------------------------------------------------------------------
FROM python:3.14-slim AS builder

WORKDIR /app

# Install build tools (needed for packages without Python 3.14 wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements
COPY requirements-ai.txt .

# Install Python dependencies
# Using --no-cache-dir to keep image small
RUN pip install --no-cache-dir -r requirements-ai.txt

# ----------------------------------------------------------------------------
# Stage 2: Production — minimal runtime image
# ----------------------------------------------------------------------------
FROM python:3.14-slim AS production

LABEL maintainer="Pharmaviyum Team"
LABEL description="Enterprise AI/LLM layer for pharmaceutical CRM"
LABEL version="1.0.0"

WORKDIR /app

# Install runtime dependencies only
# Tesseract with multi-language support (vi, ar, th, id, en)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libjpeg62-turbo \
    zlib1g \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-vie \
    tesseract-ocr-ara \
    tesseract-ocr-tha \
    tesseract-ocr-ind \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY requirements-ai.txt .

# Create non-root user for security
RUN groupadd -r appgroup && \
    useradd -r -g appgroup -u 1000 -m appuser && \
    chown -R appuser:appgroup /app

USER appuser

# Expose port
EXPOSE 8000

# Health check — lightweight curl-based probe
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command: run migrations + start API
CMD ["sh", "-c", "alembic upgrade head && uvicorn src.pharmaviyum.main:app --host 0.0.0.0 --port 8000"]
