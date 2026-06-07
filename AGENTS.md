# AI Agent Instructions for Pharmaviyum-CRM

## Purpose
This file helps AI coding agents work effectively in the Pharmaviyum demo repository. It highlights the main services, AI model conventions, and recommended commands.

## Repository overview
- Backend Python app lives under `src/pharmaviyum` and is packaged via `pyproject.toml`.
- AI/RAG service lives under `mortarium-ai`.
- Frontend app lives under `frontend/shadcn-admin`.

## Qwen / AI model guidance
- The repository uses a local Qwen model loader in `mortarium-ai/core/model.py`.
- Default model path is `mortarium-ai/models/qwen2.5-7b-instruct-q4_k_m.gguf` via `mortarium-ai/config.py`.
- If the model file is missing, the service falls back to a mock LLM implementation to keep startup working.
- The loader uses `langchain_community.llms.LlamaCpp` with `chat_format="qwen2"`.
- Configuration defaults are controlled by environment variables and the `.env` file in `mortarium-ai`.
- Best practice: keep `MODEL_PATH` in `mortarium-ai/.env` and mount model files read-only into `mortarium-ai/models/`.
 - Developer agent: there is a lightweight Qwen-based developer agent documented in `docs/qwen-dev-agent.md` and a CLI client at `tools/qwen_dev_agent.py`.
 - Use Qwen 3.6/3.7/3.8 GGUF models for best code-understanding results.

## Important files
- `mortarium-ai/core/model.py` — Qwen model loading and fallback behavior.
- `mortarium-ai/config.py` — local AI service settings, model path, database, Redis, and runtime config.
- `mortarium-ai/api/server.py` — local Mortarium AI FastAPI app endpoints.
- `mortarium-ai/main.py` — entrypoint for running the Mortarium AI service.
- `src/pharmaviyum` — main backend application code.
- `tests` — Python test suite.

## Build and test commands
- Install project dependencies using `pip install -r requirements.txt` or `pip install -e .` in a virtual environment.
- Run Python tests with `pytest -q` from the repository root.
- Use `python -m pytest tests` for explicit test invocation.
- Run the local AI service with `python mortarium-ai/main.py` or `uvicorn mortarium-ai.api.server:app --reload --port 8000`.

## Behavior expectations
- Avoid exposing or referencing proprietary production data; this repository is a demo branch with synthetic data.
- If editing AI integration, confirm that local Qwen model config and container mounts are preserved.
- Do not assume the Qwen model is present in the repo; model files are external assets and may be mounted at runtime.

## Notes
- This repository includes `AGENTS.md` and `.github/copilot-instructions.md` for AI guidance.
- The frontend workflow at `frontend/shadcn-admin/.github/workflows/claude-review.yml` references `CLAUDE.md`, but this repo does not currently include that file.
- Use documentation links rather than duplicating full content from existing docs.
