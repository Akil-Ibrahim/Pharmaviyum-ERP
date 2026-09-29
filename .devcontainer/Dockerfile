FROM mcr.microsoft.com/devcontainers/python:1-3.14-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
        postgresql-client \
        redis-tools \
    && rm -rf /var/lib/apt/lists/* \
    && corepack enable

WORKDIR /workspaces/Pharmaviyum-CRM

USER vscode
