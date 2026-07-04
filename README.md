<p align="center">
  <img src="assets/pharmaviyum.png" alt="Pharmaviyum CRM Banner" width="100%">
</p>

[![Demo](https://img.shields.io/badge/Demo‑Safe‑green)](#demo)
[![NDA](https://img.shields.io/badge/NDA‑Yes‑blue)](#legal-notice)
[![DB](https://img.shields.io/badge/DB‑PostgreSQL‑blue)](#database)
[![Python](https://img.shields.io/badge/Python‑3.14%2B‑blue?logo=python)](#technical-stack)
[![FastAPI](https://img.shields.io/badge/FastAPI‑0.139.0‑black?logo=fastapi)](#technical-stack)
[![React](https://img.shields.io/badge/React‑19.2.1‑61DAFB?logo=react)](#technical-stack)
[![Next.js](https://img.shields.io/badge/Next.js‑16.2.2‑000000?logo=nextdotjs)](#technical-stack)
[![Docker](https://img.shields.io/badge/Docker‑✓‑2496ED?logo=docker)](#cicd--docker)

# Pharmaviyum CRM

**Pharmaviyum** is a pharmacy‑focused CRM platform with ERP integration, powered by the **Mortarium AI** RAG module. It:

* Centralises client interactions for pharmacy staff.
* Automates routine workflows (orders, inventory, analytics).
* Improves service quality while keeping the existing ERP system untouched.

---

## Table of Contents

1. [Project Overview](#project-overview)  
2. [Technical Stack](#technical-stack)  
3. [Installation & Local Development](#installation--local-development)  
4. [Configuration](#configuration)  
5. [Testing](#testing)  
6. [CI/CD & Docker](#cicd--docker)  
7. [Repository Versions](#repository-versions)  
8. [Contributing](#contributing)  
9. [License & Legal Notice](#license--legal-notice)  
10. [Contact](#contact)

---

## Project Overview

Pharmaviyum CRM is built for **pharmacists** and **pharmacy operators**. The system is divided into three logical layers:

| Layer | Technology | Purpose |
|------|------------|---------|
| **Backend** | FastAPI 0.139.0, SQLAlchemy 2.0, asyncpg 0.30.0 | REST API, business logic, ERP integration, Mortarium AI RAG service |
| **AI Subsystem** | Mortarium AI → LlamaCPP 0.3.16 (model `qwen2.5‑7b‑instruct‑q4_k_m.gguf`) | Vector‑store search, answer generation, form auto‑completion |
| **Frontend** | Next.js 16.2.2, React 19.2.1, Tailwind 4.2.2, shadcn‑admin (Radix UI) | Pharmacist‑facing UI, order tables, analytics dashboards |
| **Database** | PostgreSQL (docker‑compose) | Persistent storage for clients, orders, logs, etc. |

---

## Technical Stack

| Category | Packages (exact versions) |
|----------|---------------------------|
| **Python runtime** | `python>=3.14` |
| **Web framework** | `fastapi==0.139.0`, `uvicorn[standard]==0.35.0` |
| **Data validation** | `pydantic==2.11.7`, `pydantic-settings==2.10.1` |
| **Database** | `sqlalchemy==2.0.41`, `asyncpg==0.30.0`, `alembic==1.16.2`, `pgvector==0.4.1` |
| **Cache** | `redis==6.2.0` |
| **Security** | `python-jose[cryptography]==3.5.0`, `passlib[bcrypt]==1.7.4`, `python-multipart==0.0.20` |
| **AI / RAG** | `langchain==0.3.27`, `langgraph==0.6.5`, `llama-cpp-python==0.3.16`, `sentence-transformers==5.0.0` |
| **HTTP clients** | `httpx==0.28.1`, `aiohttp==3.12.14` |
| **Utilities** | `python-dotenv==1.1.1`, `email-validator==2.2.0` |
| **Dev tools (backend)** | `pytest>=8.4.0`, `pytest-asyncio>=1.1.0`, `ruff>=0.12.0`, `mypy>=1.17.0`, `pre-commit>=4.3.0` |
| **Frontend** | `next==16.2.2`, `react==19.2.1`, `react-dom==19.2.1`, `typescript==5.9.3`, `tailwindcss==4.2.2` |
| **UI / components** | `@radix-ui/*` (v1‑2), `shadcn-admin` (based on Radix), `zod==4.3.6`, `zustand==5.0.12`, `recharts==2.15.4`, `@ai-sdk/*` (v2) |
| **Frontend dev tools** | `eslint==9.39.4`, `prettier==3.8.1`, `husky==9.1.7`, `lint-staged==16.4.0`, `drizzle-kit==0.31.10`, `tsx==4.21.0` |

---

## Installation & Local Development

> **Prerequisites**: Docker ≥ 24, Python ≥ 3.14, Node ≥ 18

```bash
# 1️⃣ Clone the repo
git clone https://github.com/Akil-Ibrahim/Pharmaviyum-CRM
cd Pharmaviyum-CRM

# 2️⃣ Python virtual environment
python -m venv .venv
source .venv/bin/activate
pip install -e .   # editable install of the package

# 3️⃣ Front‑end dependencies
cd frontend/shadcn-admin
npm ci            # or `yarn install`
cd ../../

# 4️⃣ Environment variables
cp .env.example .env
# Edit .env → set a strong SECRET_KEY, adjust DB URL, etc.

# 5️⃣ Start the Docker stack (Postgres, Redis, OTEL collector, etc.)
docker compose up -d

# 6️⃣ Apply DB migrations
alembic upgrade head

# 7️⃣ Run the backend
uvicorn mortarium-ai.api.server:app --reload --port 8000

# 8️⃣ Run the frontend
cd frontend/shadcn-admin
npm run dev
```

- UI: <http://localhost:3000>
- OpenAPI docs: <http://localhost:8000/docs>

---

## Configuration

| Variable | Description | Example |
|----------|-------------|---------|
| `APP_NAME` | Human‑readable name | `Pharmaviyum CRM` |
| `DEBUG` | FastAPI debug flag | `True` |
| `DATABASE_URL` | PostgreSQL DSN | `postgresql+asyncpg://postgres:pass@localhost:5432/pharmaviyum` |
| `REDIS_URL` | Redis cache URL | `redis://localhost:6379/0` |
| `SECRET_KEY` | JWT signing secret (32‑byte hex) | `change‑this‑in‑production‑use‑openssl‑rand‑hex‑32` |
| `MORTARIUM_MODEL_PATH` | Path to the Qwen model file | `./models/qwen2.5-7b-instruct-q4_k_m.gguf` |
| `MORTARIUM_EMBEDDING_MODEL` | Embedding model for vector store | `BAAI/bge-m3` |
| `RATE_LIMIT_PER_MINUTE` | AI request throttling | `20` |
| `MODEL_N_GPU_LAYERS` | GPU layers (`-1` = CPU‑only) | `20` |

> **Security tip:** Never commit real secrets. In production supply them via a secret manager (GitHub Secrets, HashiCorp Vault, AWS SSM, etc.).

---

## Testing

```bash
# Backend
pytest -q

# Frontend
cd frontend/shadcn-admin
npm run test
```

Tests cover API contracts, business rules, mock LLM responses, and UI component behaviour.

---

## CI/CD & Docker

**GitHub Actions** (`.github/workflows/ci.yml` – to be added)

1. **Lint** – `ruff`, `black`, `eslint`, `prettier`.  
2. **Test** – run both Pytest and Vitest.  
3. **Build** – multi‑stage Docker image (backend + frontend).  
4. **Push** – to Docker Hub or a private registry.

**Dockerfile** (multi‑stage):

- **builder** – installs dev deps, compiles TypeScript, builds the Python wheels.
- **runtime** – minimal image, runs as non‑root user, copies only required artifacts.

---

## Repository Versions

| Branch | Purpose | Accessibility |
|--------|---------|----------------|
| `main` / `production` | Full internal codebase with real ERP integrations and production data | **Restricted – NDA required** |
| `dev` / `demo` | Safe demonstration version with synthetic data and abstracted business logic | Public (this repository) |

Both branches currently use the **Qwen 2.5 7 B Instruct** model (`qwen2.5‑7b‑instruct‑q4_k_m.gguf`). If a larger model (e.g., Qwen 3‑32B) is desired for production, simply update `MORTARIUM_MODEL_PATH` and adjust `MODEL_N_GPU_LAYERS` accordingly.

---

## Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/<name>`).
3. Run `pre-commit run --all-files` to ensure linting passes.
4. Open a Pull Request with a concise description of the change.

**Code style**

- Python – PEP 8, `ruff`, `black`.
- TypeScript – `eslint`, `prettier`.

All new dependencies must be added to `pyproject.toml` (backend) or `package.json` (frontend) with exact version numbers.

---

## License & Legal Notice

- This repository is **protected under a Non‑Disclosure Agreement (NDA)**.
- No part of the code may be copied, distributed, or used beyond evaluation without **explicit written permission** from the author.
- The **demo** branch contains only **synthetic data** and is intended solely for architectural review and discussion.

---

## Contact

**[Your Name]**
✉️ `your.email@example.com`

Feel free to reach out for architectural walkthroughs, deployment assistance, or access requests.

---

*© 2026 Pharmaviyum. All rights reserved.*
