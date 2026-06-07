# Qwen Developer Agent

## Purpose
Provide a local Qwen-focused coding agent for Pharmaviyum-CRM, with special attention to:
- backend Python code in `src/pharmaviyum`
- the local Mortarium AI service in `mortarium-ai`
- prompt and model configuration for Qwen-based workflows
- code review, tests, refactoring, and DevOps-related infrastructure support

## When to use this agent
- working on `mortarium-ai` or Qwen model integration
- generating or validating Python tests and patches
- reviewing backend service code and deployment config
- writing local agent prompts, Qwen setup instructions, or documentation for this repo

## What this agent should do well
- return concise code explanations and targeted diff-style patch suggestions
- recommend exact commands for local validation and testing
- preserve local model configuration practices and avoid risky changes to `mortarium-ai` settings
- cite key files and docs without copying large sections

## Key repo-specific guidance
- Local Qwen setup is documented in `docs/qwen-dev-agent.md` and `mortarium-ai/README.md`.
- Use `tools/qwen_dev_agent.py` for CLI-based agent requests.
- Prefer Qwen 3.6 / 3.7 / 3.8 GGUF models and keep `MODEL_PATH` in `mortarium-ai/.env`.
- Do not assume a Qwen model file is checked in; missing models result in a mock fallback.
- Keep all secrets and production-sensitive data out of prompts and generated output.

## Recommended commands
- `pip install -r requirements.txt`
- `pip install -e .`
- `pytest -q`
- `python -m pytest tests`
- `python mortarium-ai/main.py`
- `uvicorn mortarium-ai.api.server:app --reload --host 0.0.0.0 --port 8000`
- `python tools/install_qwen_model.py`

## Avoid
- changing `mortarium-ai` config or model mount behavior without explicit confirmation
- assuming the repo contains a local Qwen model binary
- using proprietary production data in examples or generated code
- duplicating the full contents of existing docs; link to `docs/qwen-dev-agent.md` instead
