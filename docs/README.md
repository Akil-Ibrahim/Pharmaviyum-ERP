# Documentation

This directory contains the current engineering documentation for Pharmaviyum ERP/CRM.

## Start here

| Area | Document | Purpose |
|---|---|---|
| Architecture | [`ai_architecture.md`](./ai_architecture.md) | Current AI/RAG, MCP, memory, guardrail, and observability architecture. |
| RAG | [`rag_architecture_audit.md`](./rag_architecture_audit.md) | Dated RAG security/quality audit and remaining work. |
| Development | [`guides/ENVIRONMENT_SETUP.md`](./guides/ENVIRONMENT_SETUP.md) | Canonical local environment and deployment prerequisites. |
| Testing | [`guides/TESTING.md`](./guides/TESTING.md) | Test layout, quality gates, and validation commands. |
| Codespaces | [`guides/CODESPACES_GUIDE.md`](./guides/CODESPACES_GUIDE.md) | GitHub Codespaces workflow. |
| Operations | [`operations/INCIDENT_RUNBOOK.md`](./operations/INCIDENT_RUNBOOK.md) | Incident triage and rollback guidance. |
| Release | [`operations/RELEASE_RUNBOOK.md`](./operations/RELEASE_RUNBOOK.md) | Staging release and rollback procedure. |
| Production engineering | [`operations/PRODUCTION_ENGINEERING.md`](./operations/PRODUCTION_ENGINEERING.md) | Operational contract and production engineering standards. |
| DevOps roadmap | [`devops/README.md`](./devops/README.md) | Capacity, observability, reliability, security, and recovery roadmap. |
| ADRs | [`adr/`](./adr/) | Architecture decisions and their implementation status. |
| WebSocket | [`websocket-protocol.md`](./websocket-protocol.md) | Current v1 WebSocket design/contract status. |
| Interview | [`interview/README.md`](./interview/README.md) | Senior Python / AI / LLM interview preparation. |
| Internal | [`internal/AGENTS.md`](./internal/AGENTS.md) | Repository-specific AI coding-agent guidance. |

## Documentation ownership rules

- Document the implemented repository, not historical or hypothetical infrastructure.
- Keep one canonical procedure for each workflow; remove duplicate command guides.
- Architectural decisions belong in `docs/adr/`.
- Operational procedures belong in `docs/operations/`.
- Development procedures belong in `docs/guides/`.
- Large roadmap documents belong in `docs/devops/`.
- Interview material is intentionally separate from operational/project documentation.
- When a command, service, path, or architectural invariant changes, update the canonical document in the same change.
- Never place credentials, real customer/patient data, or provider secrets in documentation.
