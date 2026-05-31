"""
LLM model loading with graceful fallback.
Prevents container crash if model file is missing during startup.
"""
from pathlib import Path
from config import settings
from langchain_community.llms import LlamaCpp
import structlog

logger = structlog.get_logger()

def load_qwen_model() -> LlamaCpp:
    """Load Qwen3 GGUF model. Falls back to mock if file missing."""
    model_path = Path(settings.MODEL_PATH)
    
    if not model_path.exists():
        logger.warning(f"Model not found at {model_path}. Using mock LLM for startup.")
        # Return a lightweight mock that satisfies the interface
        class MockLLM:
            def invoke(self, prompt: str) -> str:
                return "Mock response: Model file not loaded. Please mount .gguf to /app/models/"
            def with_structured_output(self, schema):
                return self
        return MockLLM()  # type: ignore

    logger.info(f"Loading model: {model_path}")
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
        n_batch=512
    )
