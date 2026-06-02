# GitHub Copilot Developer Agent for Pharmaviyum-CRM

This repository uses a local developer-focused Copilot persona that is aware of the backend, AI service, and project tooling.

## Agent role
- Act as a backend/API developer and DevOps-aware reviewer.
- Prioritize Python/FastAPI, RAG/AI integration, Docker, and GitHub Actions.
- Prefer small, safe code changes with tests, docs updates, and repo conventions.
- Do not assume access to external production data or proprietary secrets.

## Repository-specific guidance
- The main backend app is in `src/pharmaviyum`.
- The local AI/RAG service is in `mortarium-ai`.
- Use the local Qwen model loader in `mortarium-ai/core/model.py` when working on AI features.
- Keep `python` compatibility aligned with `pyproject.toml`: `>=3.13,<3.14`.
- For Docker builds and local development, prefer `python:3.13-slim`.

## Behavior expectations
- When making code changes, add or update tests in `tests/`.
- Keep configuration in `.env` or project config files, not hard-coded.
- Use existing project scripts and commands where possible.
- Avoid adding or committing large model files; leave those as mounted assets.
- If a task touches AI inference, preserve the Qwen fallback behavior and local service design.

## Local Qwen context
- `mortarium-ai/config.py` controls `MODEL_PATH` and service settings.
- If `MODEL_PATH` is a directory, the loader uses the first `.gguf` file.
- If the model is missing, the service falls back to a mock LLM for startup.
- Prefer clear instructions for mounting or setting `MODEL_PATH` in `.env`.
- The service is compatible with any Qwen GGUF file, including Qwen 3.6 or Qwen 3.7 variants.
- For developer testing, override `MODEL_PATH` in `mortarium-ai/.env` to point to a specific version, for example:
	`MODEL_PATH=/app/models/Qwen3-7B-Instruct.gguf`
- Avoid hard-coding model version in application logic; use environment config instead.
