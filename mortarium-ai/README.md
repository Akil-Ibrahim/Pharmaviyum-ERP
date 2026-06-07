# Mortarium AI Qwen Setup

This folder contains the local Mortarium AI service used for RAG and agent workflows.

## Best practice
- Keep model configuration in environment variables, not hard-coded in application logic.
- Use `MODEL_PATH` to point to a specific `.gguf` file or a directory containing one. To force a specific Qwen version, set `MODEL_PATH` to the exact `.gguf` filename (for example `MODEL_PATH=/app/models/qwen2.5-7b-instruct-q4_k_m.gguf`).
- Mount model files into the container as read-only when using Docker.
- Do not commit `.env` or model binaries to source control.
- If the model is missing, the service falls back to a mock LLM to avoid startup failure, but this is not suitable for real inference.

## Recommended local setup
1. Copy example environment variables:
   ```bash
   cp mortarium-ai/.env.example mortarium-ai/.env
   ```
2. Set a strong secret and confirm service URLs:
   - `API_SECRET_KEY`
   - `DATABASE_URL`
   - `REDIS_URL`
   - `MODEL_PATH=/app/models/qwen2.5-7b-instruct-q4_k_m.gguf`
3. Place the Qwen model file into `mortarium-ai/models/`.
4. Keep `mortarium-ai/models/` in Git with a `.gitkeep` file if the directory is otherwise empty.

## Running locally
With Docker:
```bash
cd mortarium-ai
docker compose up --build
```

Without Docker:
```bash
cd mortarium-ai
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn api.server:app --reload --host 0.0.0.0 --port 8000
```

## Validation
- `http://localhost:8000/health` should return a healthy response.
- The local AI service will log a warning if Qwen is not found.

## Key files
- `config.py` — environment-driven settings, including `MODEL_PATH`.
- `core/model.py` — Qwen loader with fallback behavior.
- `core/nodes.py` — places the loaded LLM into the application.
- `api/server.py` — FastAPI endpoints and health checks.
