# Technology Stack & Glossary

[English](./technology-stack.md) · [Русский](./technology-stack.ru.md)

This section explains not only which technologies are present, but why Pharmaviyum uses them and which part of the system they serve. The version numbers are repository declarations; they do not, by themselves, prove that a dependency is active in every production environment.

### 1. Backend and API

| Technology | Definition | Why Pharmaviyum uses it |
|---|---|---|
| **Python 3.15** | High-level, general-purpose programming language. | Implements the backend, pharmacy domain rules, integrations, background jobs and Mortarium AI services. The application runtime is pinned exactly to CPython `==3.15.0` in `pyproject.toml` and `.python-version`; CI and Docker use the same patch. The Demo FastAPI Cloud runtime must independently report the exact target `3.15.0` and expected build SHA before a Demo rollout is considered successful. Production runtime verification is performed on the pharmacy server after the Ansible release and is recorded as site acceptance evidence. |
| **FastAPI 0.164.0** | Python framework for building APIs using type hints and ASGI. | Exposes the ERP/CRM and AI endpoints, validates requests, applies dependency-based authorization and publishes the OpenAPI contract. |
| **Uvicorn 0.54.0** | ASGI web server. | Runs the FastAPI application and handles asynchronous HTTP connections. FastAPI is the application framework; Uvicorn is the server process. |
| **Pydantic 2.14.3** | Data validation and serialization library. | Defines and validates request/response schemas and structured configuration data, including medication-related fields. |
| **Pydantic Settings 2.16.2** | Settings management built on Pydantic. | Loads typed application configuration from environment variables and supported settings sources. Secrets belong in the deployment secret store, not in source control. |
| **SQLAlchemy 2.1.8** | Python SQL toolkit and object-relational mapper (ORM). | Maps pharmacy domain objects to relational tables and provides controlled SQL queries and transactions. |
| **Alembic 1.20.1** | Database schema migration tool for SQLAlchemy. | Versions schema changes and applies reviewed database migrations. It does not automatically upgrade production just because code is deployed. |
| **asyncpg 0.32.0** | Asynchronous PostgreSQL driver for Python. | Provides async database connectivity for application paths that use the native async PostgreSQL driver. |
| **psycopg 3.3.9** | PostgreSQL adapter for Python. | Provides PostgreSQL connectivity for synchronous or supported async database/tooling paths. |
| **OpenAPI** | Machine-readable API description standard. | Documents FastAPI endpoints and supports generated frontend API clients and integration tooling. |

### 2. Data layer and persistence

| Technology | Definition | Why Pharmaviyum uses it |
|---|---|---|
| **PostgreSQL** | Open-source relational database management system (RDBMS). | Primary structured data store and source of truth for pharmacy operations: users, pharmacies, products, prescriptions, orders, inventory, batches, suppliers and audit records. Relational constraints and transactions protect consistency. |
| **pgvector 0.8.7** | PostgreSQL extension that adds vector data types and similarity-search operations. | Stores and searches embedding vectors alongside authorized document/chunk metadata for semantic retrieval in Mortarium RAG. It extends PostgreSQL; it is not a separate database. |
| **Redis** | In-memory data structure server used for low-latency data access and coordination. | Supports cache, short-lived state and infrastructure coordination where configured. It is not the authoritative store for pharmacy transactions. |
| **Valkey** | Open-source, Redis-compatible in-memory data store. | Used by the separate Pharmacy Edge Ansible deployment profile. It is intentionally documented separately from the local Redis service. |
| **Redis Python client 8.1.0** | Python client library for Redis-compatible servers. | Lets backend services and workers communicate with configured Redis-compatible infrastructure. |
| **PostgreSQL full-text search** | Database-native lexical search over textual documents. | Complements vector similarity in hybrid RAG retrieval, helping exact medication terms, identifiers and phrases remain searchable. |

**Environment boundary:** FastAPI Cloud is the public Demo host only; Demo uses isolated data services and synthetic data. Production is deployed to the pharmacy server through Ansible, using the approved Pharmacy Edge Compose/service profile and local operational data services. Local development/CI Compose is disposable and must not be treated as a Production deployment. The legacy `docker-compose.prod.yml` still contains PostgreSQL 16/Redis 7 and is not an approved deployment path for either environment. Verify actual runtime versions from the deployed image and host; do not copy Demo provider assumptions into the pharmacy-server profile. See [version policy](#version-policy-and-dependency-management) and [the canonical deployment boundary](deployment/PRODUCTION_DEMO_INFRASTRUCTURE_BASELINE.md).

### 3. Background jobs and asynchronous processing

| Technology | Definition | Why Pharmaviyum uses it |
|---|---|---|
| **Celery 5.6.3** | Distributed task queue for executing work outside the HTTP request lifecycle. | Runs bounded background jobs such as document ingestion and processing, embedding/indexing tasks and other work that should not block an API response. |
| **Celery worker** | A process that consumes and executes queued Celery tasks. | Separates long-running or retryable work from the FastAPI web process and allows worker capacity to be scaled independently. |
| **Redis broker/backend (when configured)** | Redis-compatible transport/state service used by Celery deployments. | Carries queued task messages and/or task results according to the configured Celery topology. The exact broker and result-backend URLs are deployment configuration, not hard-coded assumptions. |

### 4. Frontend and user interface

| Technology | Definition | Why Pharmaviyum uses it |
|---|---|---|
| **React 19.3** | JavaScript library for building component-based user interfaces. | Builds the pharmacy ERP/CRM screens, dashboards, POS and operational workflows. |
| **TypeScript 6.0.x** | JavaScript superset with static type checking. | Detects many interface and data-contract errors during development and makes frontend code easier to maintain. |
| **Vite 8.x** | Frontend development server and build tool. | Provides fast local development, asset processing and optimized production bundles. |
| **Tailwind CSS 4.x** | Utility-first CSS framework. | Implements the responsive design system, layout, spacing, typography, colors and themes. |
| **shadcn/ui approach + Radix UI** | Composable UI component pattern built with accessible primitives; shadcn components are maintained in the application rather than treated as a remote component runtime. | Provides consistent, accessible forms, dialogs, menus, tables and dashboard components while allowing Pharmaviyum-specific customization. |
| **TanStack Query 5.x** | Server-state fetching, caching and synchronization library for React. | Manages API data, loading/error states, cache invalidation and refetching for screens backed by FastAPI. |
| **TanStack Router 1.x** | Type-safe routing library for React. | Defines frontend routes, route parameters, nested layouts and navigation. |
| **Axios 1.x** | Promise-based HTTP client. | Sends frontend requests to the FastAPI API and centralizes request/response handling. |
| **Zod 4.x** | TypeScript-first schema validation library. | Validates frontend data and form payloads at runtime and can share validation intent with TypeScript types. |
| **React Hook Form 7.x** | React form-state and validation library. | Manages complex forms with less unnecessary rendering, including operational and catalog forms. |
| **Zustand 5.x** | Lightweight state-management library. | Holds client-side UI state that does not belong in server-state caching. |
| **Recharts 3.x** | React charting library. | Renders operational dashboards, inventory trends and business metrics. |
| **Vitest 4.x** | Test runner designed for modern Vite projects. | Runs frontend unit/component tests. |
| **Playwright 1.59.1** | Browser automation and end-to-end testing framework. | Exercises real browser workflows such as navigation, forms and critical user journeys. |

### 5. Mortarium AI, LLM and agent architecture

**Mortarium** is the pharmacist-facing AI decision-support layer inside Pharmaviyum. It uses authorized application context and evidence retrieval to help pharmacy professionals find, summarize and interpret relevant information. It is advisory: deterministic application services retain control over permissions, calculations, inventory, payments and dispensing decisions.

| Technology / concept | Definition | Why Pharmaviyum uses it |
|---|---|---|
| **AI layer** | The application subsystem that combines models, retrieval, orchestration, tools, policy checks and evaluation. | Gives pharmacists a controlled AI assistant integrated with ERP workflows rather than an isolated general-purpose chatbot. |
| **LLM (Large Language Model)** | A model trained to understand and generate natural language. | Interprets pharmacist questions, summarizes retrieved evidence and produces structured, source-aware responses. Model/provider selection is configuration-driven; a model name must be taken from the active deployment configuration, not inferred from a library list. |
| **QwenCloud** | Configured model-provider profile used by the current demo setup. | Supplies language-model inference for the demo profile. The demo provider setting must not be confused with proof of the production provider/model or its availability. |
| **LangChain 1.4.0** | Framework and abstractions for composing model, prompt, retriever and tool integrations. | Provides integration building blocks used by the AI layer. It is not itself the agent workflow engine or the database. |
| **LangGraph 1.2.21** | Graph-based orchestration framework for stateful, multi-step LLM workflows. | Coordinates Mortarium agent and RAG stages, conditional routing, tool decisions, bounded retries and checkpointed workflow state. |
| **Agent** | A controlled software workflow in which a model can select among permitted next steps or tools. | Lets Mortarium decide whether a question needs retrieval, a response from supplied context or an authorized read-only tool. Server-side policy—not the model—decides what is permitted. |
| **Agent Harness** | The application control layer around model/agent execution: input validation, authorization context, bounded memory, prompt/cache policy, model routing, output validation and telemetry. | Provides consistent safety and operational controls around LangGraph and LLM calls. In this project it is an architectural/application layer, not a claim that a separate product named “Harness AI” has been installed. |
| **RAG (Retrieval-Augmented Generation)** | A pattern that retrieves relevant source material and supplies it to an LLM before it generates an answer. | Grounds pharmacy answers in approved documents and indexed knowledge instead of relying only on model parameters. The intended response preserves source IDs/citations and authorization scope. |
| **Embeddings** | Numeric vector representations of text that capture semantic relationships. | Represent document chunks and queries so semantically related pharmacy information can be found even when wording differs. The exact embedding model must be read from active runtime configuration. |
| **Vector search** | Similarity search over embedding vectors. | Finds semantically related chunks for RAG. |
| **Hybrid search** | Combination of lexical/full-text retrieval and vector similarity retrieval. | Balances exact medication names, strengths and identifiers with semantically related text. |
| **Chunking** | Splitting source documents into smaller, retrievable passages while retaining useful context and metadata. | Keeps retrieved context within model limits and improves relevance. The current MedicalChunker supports medical-heading heuristics, sentence grouping and recursive fallback; its token estimate is approximate, not a tokenizer-exact count. |
| **Metadata filtering** | Restricting retrieval using trusted attributes such as pharmacy, access level, language and document source. | Prevents cross-pharmacy retrieval and excludes patient-level material unless the authenticated request has the matching patient scope. Missing or invalid scope must fail closed. |
| **MCP (Model Context Protocol)** | A protocol for exposing tools and resources to AI applications through a defined client/server contract; this project documents a JSON-RPC-based MCP layer. | Gives Mortarium a controlled way to discover and invoke approved pharmacy operations. Tool availability is role-filtered and server-authorized; model-generated arguments never establish identity or permission. |
| **Prompt/context engineering** | Designing instructions and selecting trusted context supplied to a model. | Keeps the assistant focused on the pharmacist's task, jurisdiction, language, selected patient scope and evidence budget. |
| **Guardrails** | Input/output checks and policy constraints around model behavior. | Rejects invalid scope, limits unsafe tool use, checks response structure and supports safe abstention when evidence is missing or conflicting. |
| **Ragas 0.4.3** | Framework for evaluating RAG quality using reference data and evaluator models. | Measures offline signals such as faithfulness, answer relevancy, context precision and context recall. It is declared in the `eval` dependency group and used by CI/evaluation jobs; it is not installed in the production runtime or imported by the production request path. |
| **Pharmaceutical quality metrics** | Domain-specific checks beyond generic LLM scores. | Tests citation support, medication name/strength/form, negation preservation, unsupported clinical claims, patient isolation and English/Russian retrieval. These are regression checks, not clinical certification. |

**Important AI boundary:** RAG and agent workflows do not make an answer clinically authoritative. Patient and pharmacy authorization is enforced by application code and retrieval filters. The pharmacist remains responsible for professional decisions. See [Mortarium AI system design](./ai/AI_LLM_SYSTEM_DESIGN.md), [chunking pipeline](./ai/chunking-pipeline.md) and [Ragas evaluation](./ai/ragas-pharmaceutical-evaluation.md).

### 6. Observability and operations

| Technology | Definition | Why Pharmaviyum uses it |
|---|---|---|
| **OpenTelemetry 1.45.2** | Vendor-neutral APIs, SDKs and conventions for telemetry, especially distributed traces. | Tracks bounded spans across API and Mortarium workflows so latency and failures can be investigated. Sensitive prompts, patient data, tokens and retrieved clinical text must not be attached to spans. |
| **OTLP** | OpenTelemetry Protocol for exporting telemetry to a collector/backend. | Transports traces from the application to a configured telemetry collector. SDK presence alone does not prove that production traces are being delivered. |
| **Prometheus** | Metrics collection and time-series monitoring system. | Collects numeric service metrics such as request counts, error rates, queue depth and latency histograms. Labels must remain low-cardinality and must not contain patient/user identifiers. |
| **Grafana** | Dashboard and visualization platform for metrics and other telemetry sources. | Displays operational dashboards and supports investigation of service health and performance. |
| **Jaeger** | Distributed tracing backend and trace UI. | Provides a local trace viewer for inspecting spans and request relationships in the development Compose stack. |
| **OpenTelemetry Collector** | Vendor-neutral service that receives, processes and exports telemetry. | Separates application instrumentation from the final trace backend and provides a controlled telemetry pipeline. |
| **Structured application logs** | Machine-readable event records with consistent fields. | Helps correlate failures and operational events without logging secrets, patient details or full clinical payloads. |
| **Health/readiness checks** | Endpoints that report process health and dependency readiness. | Distinguish a running web process from an application whose required dependencies are ready. |

The repository includes local observability infrastructure. Production trace delivery, alert routing and end-to-end coverage require a configured collector/backend and live verification; they must not be inferred from local Compose files.

### 7. Infrastructure, delivery and developer tooling

| Technology | Definition | Why Pharmaviyum uses it |
|---|---|---|
| **Docker** | Platform for packaging applications and dependencies into containers. | Produces repeatable runtime images for the API and supporting processes. |
| **Docker Compose** | Tool for defining and running multi-container applications. | Starts disposable local development/test dependencies such as PostgreSQL, Redis, workers and local observability services. |
| **FastAPI Cloud** | Managed hosting/deployment platform for the FastAPI application. | Hosts the public Demo backend only. It is not a Production deployment target. |
| **Ansible** | Agentless infrastructure automation tool. | Provisions and deploys reviewed application releases to pharmacy servers under the Pharmacy Edge profile; real host inventory and credentials remain private. |
| **GitHub** | Source-control and collaboration platform. | Hosts the repository, branches, pull requests, code review and release history. |
| **GitHub Actions** | CI/CD automation service integrated with GitHub. | Runs lint, formatting, type checks, tests, security scans and build validation. Passing CI is a quality signal; it does not itself prove production health. |
| **uv 0.13.8** | Fast Python package manager and project/environment tool. | Installs Python dependencies, runs commands and keeps the resolved dependency set reproducible using `pyproject.toml` and `uv.lock`. |
| **Bun 1.4.4** | JavaScript runtime, package manager and frontend toolchain. | Installs frontend dependencies and runs frontend scripts for development, builds and tests. |
| **Ansible** | Agentless infrastructure automation tool. | Provisions pharmacy servers and deploys reviewed Production application releases under the Pharmacy Edge profile. It is infrastructure automation, not the ERP's application business logic. |
| **Mailpit 1.33.1** | Local SMTP capture and email testing tool. | Captures development emails so password recovery and notification flows can be tested without sending real messages. Production SMTP is configured separately. |

### 8. Testing, quality and security tooling

| Technology | Definition | Why Pharmaviyum uses it |
|---|---|---|
| **Pytest 9.2.0** | Python testing framework. | Tests backend business logic, API behavior, database integration, AI/RAG behavior and security invariants. |
| **pytest-asyncio** | Pytest plugin for asynchronous tests. | Exercises async FastAPI, database and service code. |
| **pytest-cov** | Pytest coverage plugin. | Measures which code paths are exercised by the test suite. Coverage is a measurement, not proof that behavior is correct. |
| **Ruff** | Fast Python linter and code-quality tool. | Detects common defects and enforces selected lint rules. |
| **Black** | Opinionated Python code formatter. | Keeps Python formatting consistent. |
| **isort** | Python import sorter. | Keeps imports ordered consistently. |
| **mypy** | Static type checker for Python. | Finds type inconsistencies before runtime. |
| **Bandit** | Static security analysis tool for Python. | Flags selected risky code patterns for review. |
| **pip-audit** | Python dependency vulnerability checker. | Checks installed/declarative Python dependencies against known vulnerability advisories. |
| **ESLint** | JavaScript/TypeScript linter. | Finds frontend code-quality and common correctness issues. |
| **Prettier** | Code formatter for frontend and supported text/config files. | Keeps frontend formatting consistent. |
| **Playwright** | Browser-based end-to-end testing tool. | Validates complete user journeys in a real browser rather than testing isolated functions only. |

### Dependency source of truth

Python dependency definitions are maintained in:

- `pyproject.toml` — direct dependencies, optional groups and tool configuration.
- `uv.lock` — resolved, reproducible Python dependency versions.
- `[dependency-groups].eval` in `pyproject.toml` — isolated Ragas evaluation dependencies, installed explicitly for evaluation with `uv sync --group eval`; the group is excluded from the production runtime installation.

Frontend dependency definitions are maintained in:

- `frontend/shadcn-admin/package.json` — frontend dependencies and scripts.
- `frontend/shadcn-admin/bun.lock` — resolved frontend dependency versions.

Do not maintain a second authoritative Python dependency list. Change dependencies in their source manifests, regenerate the relevant lockfile and run the corresponding CI checks.

For exact declared versions, environment boundaries and the upgrade procedure, see the version policy below.

---

## Version policy and dependency management

This page records the versions declared by the repository configuration. It is not a claim that every dependency has been independently tested against every newer release.

## Runtime and framework versions

| Area | Version declared in repository | Source of truth |
|---|---|---|
| Python | Application runtime pinned exactly to `==3.15.0` in `pyproject.toml` and `.python-version`; CI, Docker and the deployment gate require CPython 3.15.0. The temporary 3.15.0 pin matches the last known FastAPI Cloud `/version` result (2026-11-15); a new rollout still requires live confirmation of the expected build SHA, CPython 3.15.0, health and readiness. Ansible controller CI separately uses Python 3.14.10 for ansible-core 2.21. | `pyproject.toml`, `.python-version`, `.github/workflows/ci.yml`, `.github/workflows/deploy-fastapi-cloud.yml`, `.github/workflows/ansible-quality.yml`, `Dockerfile` |
| FastAPI | `0.164.0` | `pyproject.toml` (lockfile regeneration pending) |
| Uvicorn | `0.54.0` | `pyproject.toml` |
| Pydantic | `2.14.3` | `pyproject.toml` |
| Pydantic Settings | `2.16.2` | `pyproject.toml` |
| SQLAlchemy | `2.1.8` | `pyproject.toml` |
| Alembic | `1.20.1` | `pyproject.toml` |
| asyncpg / psycopg | `0.32.0` / `3.3.9` | `pyproject.toml` |
| PostgreSQL | Local PostgreSQL on the pharmacy server for Production; separate isolated PostgreSQL for Demo; disposable PostgreSQL for development/CI | Ansible/Compose pharmacy-server profile, Demo provider metadata, Docker Compose and CI service definitions |
| Redis server | Managed Redis for hosted Production and isolated managed Redis for Demo; Redis 8.8.4 compatibility target, exact hosted server version provider-reported and must be verified; local development/CI uses Redis 8.8.4 | FastAPI Cloud integration/provider metadata; Docker Compose and CI service definitions |
| pgvector container extension | `0.8.7` | `pgvector/pgvector:0.8.7-pg18` image tag |
| pgvector Python client | `0.4.1` | `pyproject.toml` |
| LangGraph | `1.2.21` | `pyproject.toml` |
| LangChain | `1.4.0` | `pyproject.toml` |
| Redis Python client | `8.1.0` | `pyproject.toml` |
| Celery | `5.6.3` | `pyproject.toml` |
| OpenTelemetry API / SDK / OTLP exporter | `1.45.2` | `pyproject.toml` |
| OpenTelemetry instrumentation packages | `0.66b2` | `pyproject.toml` |
| Ansible Community Package | `14.6.0` | `ansible/requirements.txt` |
| ansible-core | `2.21.6` | `ansible/requirements.txt` |
| Ansible controller Python | `3.14.10` | `.github/workflows/ansible-quality.yml` |
| uv | `0.13.8` | Dockerfile and GitHub Actions workflows |
| React / React DOM | `^19.3.1` | `frontend/shadcn-admin/package.json` |
| TypeScript | `~6.0.3` | `frontend/shadcn-admin/package.json` |
| Vite | `^8.3.8` | `frontend/shadcn-admin/package.json` |
| Tailwind CSS | `^4.3.5` | `frontend/shadcn-admin/package.json` |
| Bun | `1.4.4` | Dockerfile and GitHub Actions workflows |
| TanStack Query | `^5.103.1` | `frontend/shadcn-admin/package.json` |
| TanStack Router | `^1.170.36` | `frontend/shadcn-admin/package.json` |
| Vitest | `^4.1.11` | `frontend/shadcn-admin/package.json` |
| Mailpit | `1.33.1` local SMTP sink for development; production SMTP is configured separately | `docker-compose.yml` |

Exact resolved Python package versions are recorded in `uv.lock`. The application interpreter is pinned to CPython 3.15.0 in `pyproject.toml` and `.python-version`. FastAPI 0.164.0 was released on 2026-11-15 and includes an upstream OpenAPI fix for response models with nested computed fields ([FastAPI release notes](https://fastapi.tiangolo.com/release-notes/)). The last known hosted `/version` result was CPython 3.15.0 on 2026-11-15; do not describe production as running the new build until `/version` confirms the expected SHA and CPython 3.15.0. Frontend dependency ranges are declared in `frontend/shadcn-admin/package.json`; do not assume a version range means a particular patch release is installed.

## Tooling

- Python dependency and command workflow: `uv`
- Python lint and quality checks: Ruff, Black, isort, mypy, pytest
- Frontend package manager and scripts: Bun
- Frontend quality gates: ESLint, Prettier, TypeScript build, Vitest, Playwright E2E
- Container build: Docker multi-stage build
- CI: GitHub Actions

Monitoring images: Prometheus `3.16.0`, Grafana `13.3.1`, OpenTelemetry Collector Contrib `0.165.1`, Jaeger `1.76.0` in local Compose. Bun is pinned consistently to `1.4.4` across Docker and CI workflows.

## Dependency update procedure

1. Change Python direct dependencies and optional dependency groups (such as `eval`) in `pyproject.toml`.
2. Regenerate and commit `uv.lock`; CI uses frozen synchronization, and the RAG evaluation job installs its group with `uv sync --frozen --group eval`.
3. Change frontend dependencies in `frontend/shadcn-admin/package.json` and regenerate the committed `frontend/shadcn-admin/bun.lock`.
4. Run backend lint, formatting, typing, unit and integration checks; run frontend lint, formatting, production build and tests.
5. Check compatibility notes and security advisories for major-version upgrades.
6. Update this document and the README only after the repository configuration has been updated. Do not describe a planned upgrade as already installed.
7. Open a pull request and review GitHub Actions results before merging.

## Runtime infrastructure notes

- Production PostgreSQL runs locally on the pharmacy server under the approved Ansible/Pharmacy Edge profile; Demo uses a separate isolated database. Disposable development/CI Compose targets PostgreSQL 18 with pgvector 0.8.7.
- The application uses the pgvector Python client and PostgreSQL extension for vector search where enabled; these are separately versioned components.
- Production cache/queue services run according to the approved pharmacy-server Ansible profile; Demo uses isolated supporting services. Verify actual Production runtime versions on the pharmacy server. Disposable development/CI Compose targets Redis 8.8.4.
- The pharmacy-edge Ansible template uses Valkey; that server profile is intentionally kept separate from the local Redis service.
- Local Compose captures outgoing application emails in Mailpit (`http://localhost:8025`, SMTP `localhost:1025`). See [email delivery and local testing](./development/email.md) for setup. Demo delivery requires explicit SMTP host, port, sender, TLS mode, and credentials in the Demo hosting environment; Production SMTP is configured on the pharmacy server through its protected Ansible-managed environment.
- Mortarium's LLM provider/model selection is environment-configured. See [AI architecture](./ai_architecture.md) and [FastAPI Cloud deployment](./deployment/FASTAPI_CLOUD.md) for the current deployment profile.

## Documentation rule

When versions change, update the dependency manifests and lockfiles first. Keep README badges, architecture diagrams, setup guides and this page consistent with the actual configuration. Never put secrets, patient information or production credentials in documentation.