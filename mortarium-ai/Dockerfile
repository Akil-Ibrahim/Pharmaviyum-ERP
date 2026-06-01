# Stage 1: Build environment
FROM python:3.13-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    cmake \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/* && apt-get clean

ENV PIP_NO_CACHE_DIR=1 PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime environment
FROM python:3.13-slim AS runtime

LABEL maintainer="Mortarium AI Team"
LABEL version="1.0.0"

# Install runtime dependencies INCLUDING curl for health checks
RUN groupadd --gid 1000 mortarium && \
    useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash mortarium && \
    apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/* && apt-get clean

WORKDIR /app

# Copy packages from builder
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=mortarium:mortarium . .

# Create directories
RUN mkdir -p /app/models /app/data/vector_store /app/logs && \
    chown -R mortarium:mortarium /app && \
    chmod -R 750 /app

ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    MODEL_PATH=/app/models \
    VECTOR_STORE_PATH=/app/data/vector_store

USER mortarium
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
