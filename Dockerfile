# ============================================================================
# PHARMAVIYUM AI - Production Dockerfile
# ============================================================================

FROM python:3.13-slim AS python-builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM oven/bun:1 AS frontend-builder

WORKDIR /frontend

COPY frontend/package.json ./
RUN bun install

COPY frontend/ ./
RUN bun run build

FROM python:3.13-slim AS production

LABEL maintainer="Pharmaviyum Team"
LABEL description="Enterprise AI/LLM layer for pharmaceutical CRM"

WORKDIR /app

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

COPY --from=python-builder /install /usr/local
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini .
COPY --from=frontend-builder /frontend/dist ./frontend/dist

RUN groupadd --system appgroup && \
    useradd --system --gid appgroup --uid 1000 --create-home appuser && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

# Database migrations are a release concern and should run as a separate deployment step.
CMD ["sh", "-c", "uvicorn src.pharmaviyum.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
