
"""
LLM model loading with graceful fallback.
Prevents container crash if model file is missing during startup.
"""
from pathlib import Path
from typing import Any, Type
from config import settings
from langchain_community.llms import LlamaCpp
import structlog

logger = structlog.get_logger()


class MockModelResponse:
    def __init__(self, content: str):
        self.content = content

    def __str__(self) -> str:
        return self.content


class MockLLM:
    def __init__(self):
        self._schema: Type[Any] | None = None

    def invoke(self, prompt: Any) -> Any:
        if self._schema is not None:
            if isinstance(prompt, dict):
                question = prompt.get("question", "")
            else:
                question = str(prompt)

            parsed = {}
            for field_name, field in self._schema.model_fields.items():
                if field_name == "rewritten_query":
                    parsed[field_name] = question or "mock query"
                elif field.annotation == bool:
                    parsed[field_name] = False
                elif field.annotation == int:
                    parsed[field_name] = 0
                else:
                    parsed[field_name] = ""

            return self._schema.parse_obj(parsed)

        return MockModelResponse(
            "Mock response: Model file not loaded. Please mount a .gguf file to /app/models/"
        )

    def with_structured_output(self, schema: Type[Any]) -> "MockLLM":
        self._schema = schema
        return self


def load_qwen_model() -> Any:
    """Load Qwen3 GGUF model. Falls back to mock if file missing."""
    model_path = Path(settings.MODEL_PATH).expanduser()

    if model_path.is_dir():
        gguf_files = sorted(model_path.glob("*.gguf"))
        if gguf_files:
            if len(gguf_files) > 1:
                logger.warning(
                    "Multiple .gguf files found; using first match.",
                    path=str(model_path),
                    selected=str(gguf_files[0]),
                )
            model_path = gguf_files[0]
            logger.info("MODEL_PATH directory provided; using model file.", path=str(model_path))
        else:
            logger.warning(
                "No .gguf files found in MODEL_PATH directory. Falling back to mock LLM.",
                path=str(model_path),
            )
            return MockLLM()

    if not model_path.exists():
        logger.warning(
            "Model file not found. Falling back to mock LLM.",
            path=str(model_path),
        )
        return MockLLM()

    logger.info("Loading model", model_path=str(model_path), model_name=model_path.name)
    return LlamaCpp(
        model_path=str(model_path),
        n_ctx=settings.MODEL_N_CTX,
        n_gpu_layers=settings.MODEL_N_GPU_LAYERS,
        temperature=settings.MODEL_TEMPERATURE,
        top_p=0.95,
        repeat_penalty=1.15,
        verbose=False,
        f16_kv=True,
        chat_format="qwen2",
        n_threads=4,
        n_batch=512,
    )
