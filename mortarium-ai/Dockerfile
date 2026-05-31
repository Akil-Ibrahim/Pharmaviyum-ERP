FROM python:3.14.5-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake git libpq-dev curl python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

WORKDIR /build
COPY requirements.txt .

# Install build dependencies first
RUN uv pip install --no-cache scikit-build-core pybind11

# Then install main requirements
RUN uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv pip install --no-cache --upgrade pip && \
    uv pip install --no-cache -r requirements.txt

FROM python:3.14.5-slim AS runtime

RUN groupadd --gid 1000 mortarium && \
    useradd --uid 1000 --gid 1000 --create-home mortarium

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY --chown=mortarium:mortarium . .
RUN mkdir -p models data/vector_store logs && chown -R mortarium:mortarium /app

USER mortarium
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000
CMD ["python", "main.py"]
