# Pharmaviyum CRM — Development Guide

## Requirements

- Python 3.14+
- Git
- PostgreSQL 16+
- Redis 7+
- Docker Desktop (optional)
- uv (recommended)

---

## Clone repository

git clone <repository_url>

cd Pharmaviyum-CRM

---

## Create virtual environment

uv venv

Activate:

Linux/macOS

source .venv/bin/activate

Windows

.venv\Scripts\activate

---

## Install dependencies

uv sync

If using pip:

pip install -r requirements.txt

---

## Configure environment

Copy:

.env.example

to

.env

Fill in:

DATABASE_URL

REDIS_URL

SECRET_KEY

MODEL_PATH

---

## Database

Create migrations

alembic revision --autogenerate -m "init"

Apply migrations

alembic upgrade head

---

## Run backend

uvicorn app.main:app --reload

Open:

http://127.0.0.1:8000

Swagger:

http://127.0.0.1:8000/docs

Redoc:

http://127.0.0.1:8000/redoc

---

## Tests

pytest

---

## Ruff

Check

ruff check .

Fix

ruff check . --fix

Format

ruff format .

---

## AI

Supported:

- LangGraph
- LangChain
- llama.cpp
- GGUF models
- Qwen
- Embeddings

---

## Docker

Build

docker compose build

Run

docker compose up -d

Stop

docker compose down

---

## Git

Create branch

git checkout -b feature/new-feature

Commit

git add .

git commit -m "Describe changes"

Push

git push origin feature/new-feature

---

## Project Structure

app/
api/
core/
db/
models/
schemas/
services/
repositories/
ai/
rag/
routers/
tests/
alembic/
docker/
scripts/

---

## Best Practices

- Python 3.14
- FastAPI
- SQLAlchemy 2.x
- Async only
- Pydantic v2
- Ruff
- Pytest
- Docker
- LangGraph
- PostgreSQL
- Redis

