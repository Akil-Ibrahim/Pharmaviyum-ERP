# ============================================================================
# PHARMAVIYUM AI - Production Dockerfile
# ============================================================================

FROM python:3.14.7-slim AS python-builder

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

RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel uv

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project --no-editable

COPY README.md ./README.md
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY scripts/ ./scripts/
RUN chmod +x scripts/start.sh
COPY alembic.ini .
COPY README.md .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

FROM oven/bun:1 AS frontend-builder

WORKDIR /frontend

COPY frontend/shadcn-admin/package.json ./
RUN bun install

COPY frontend/shadcn-admin/ ./
RUN bun run build

FROM python:3.14.7-slim AS production

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

COPY --from=python-builder /app/.venv /app/.venv
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY scripts/ ./scripts/
COPY alembic.ini .
ENV PATH="/app/.venv/bin:$PATH"
COPY --from=frontend-builder /frontend/dist ./static

RUN groupadd --system appgroup && \
    useradd --system --gid appgroup --uid 1000 --create-home appuser && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -fsS "http://localhost:\${PORT:-8000}/health" || exit 1

# Migrations and demo seeding are deployment concerns, not application startup.
# Production release pipelines must run migrations exactly once before traffic.
CMD ["sh", "scripts/start.sh"]
