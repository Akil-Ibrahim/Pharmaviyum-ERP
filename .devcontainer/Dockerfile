FROM python:3.15.2-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
        postgresql-client \
        redis-tools \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --upgrade pip

RUN useradd --create-home --shell /bin/bash vscode

WORKDIR /workspaces/Pharmaviyum-CRM

USER vscode
