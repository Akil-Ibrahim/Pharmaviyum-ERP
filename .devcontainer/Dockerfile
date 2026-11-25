FROM python:3.15.0-bookworm

ENV UV_VERSION=0.13.8 \
    UV_LINK_MODE=copy

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
        libffi-dev \
        libjpeg-dev \
        libpq-dev \
        postgresql-client \
        redis-tools \
        tesseract-ocr \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --no-cache-dir "uv==${UV_VERSION}"

RUN useradd --create-home --shell /bin/bash vscode

WORKDIR /workspaces/Pharmaviyum-ERP

USER vscode
