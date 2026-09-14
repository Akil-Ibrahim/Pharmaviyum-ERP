"""
FastAPI Dependency Injection for AI Layer.

Best practice 2026:
- Lazy initialization of heavy components (LLMs, Vector Stores)
- Request-scoped dependencies for DB sessions
- Singleton pattern for stateless services (Guardrails, Routers)
- Graceful degradation if dependencies fail to initialize
"""
from __future__ import annotations
import asyncio
from typing import AsyncGenerator, Any
from functools import lru_cache
from fastapi import Depends, HTTPException, status, Request
from langchain_ollama import ChatOllama
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.pharmaviyum.ai.config import settings
from src.pharmaviyum.ai.rag import RAGPipeline, IngestionOrchestrator
from src.pharmaviyum.ai.mcp import MCPClient, mcp_client
from src.pharmaviyum.ai.agents import (
    PharmacistAgent,
    AgentCheckpointer,
    AgentStreamManager,
    create_callback_manager,
)
from src.pharmaviyum.ai.harness import (
    AgentHarness,
    DialogueMemory,
    MedicalGuardrails,
    PromptCache,
    ModelRouter,
    ToolCallingLayer,
    ContextWindowManager,
    GracefulDegradation,
    HumanReviewQueue,
)
from src.pharmaviyum.ai.evaluation import AgentEvaluator
from src.pharmaviyum.ai.observability import ObservabilityTracer, tracer
from src.pharmaviyum.core.logging import logger

# ============================================================================
# CORE INFRASTRUCTURE DEPENDENCIES
# ============================================================================

async def get_redis_client() -> AsyncGenerator[Redis, None]:
    """Get async Redis client for caching and memory."""
    try:
        redis = Redis.from_url(
            settings.redis.url,
            decode_responses=True,
            health_check_interval=30,
        )
        # Test connection
        await redis.ping()
        yield redis
        await redis.aclose()
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis service unavailable",
        )


async def get_db_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """
    Get async SQLAlchemy session from the main app's state.
    Assumes main.py sets up `request.state.db_session_factory`.
    """
    # Fallback to a mock or the actual factory if configured
    factory = getattr(request.app.state, "db_session_factory", None)
    if not factory:
        # Mock for standalone AI module testing
        logger.warning("DB session factory not found in app.state, using mock")
        yield None
        return
    
    async with factory() as session:
        yield session


# ============================================================================
# LLM PROVIDER DEPENDENCIES
# ============================================================================

@lru_cache(maxsize=1)
def get_llm_fast():
    """Cached fast LLM for routing and simple tasks."""
    return ChatOllama(
        model=settings.ollama.fast_model,
        base_url=settings.ollama.base_url,
        temperature=settings.ollama.temperature,
    )


@lru_cache(maxsize=1)
def get_llm_main():
    """Cached main LLM for general reasoning."""
    return ChatOllama(
        model=settings.ollama.main_model,
        base_url=settings.ollama.base_url,
        temperature=settings.ollama.temperature,
    )


@lru_cache(maxsize=1)
def get_llm_complex():
    """Cached complex LLM for deep medical reasoning."""
    return ChatOllama(
        model=settings.ollama.complex_model,
        base_url=settings.ollama.base_url,
        temperature=settings.ollama.temperature,
    )


# ============================================================================
# AI COMPONENT DEPENDENCIES
# ============================================================================

class AIComponents:
    """Container for all initialized AI components."""
    def __init__(self):
        self._initialized = False
        self._lock = asyncio.Lock()
        
        # Components
        self.rag_pipeline: RAGPipeline | None = None
        self.ingestion_orchestrator: IngestionOrchestrator | None = None
        self.agent_harness: AgentHarness | None = None
        self.mcp_client: MCPClient = mcp_client
        self.evaluator: AgentEvaluator | None = None
        self.tracer: ObservabilityTracer = tracer

    async def initialize(
        self,
        redis: Redis,
        db_session_factory: Any,
    ):
        """Lazy initialization of heavy AI components."""
        if self._initialized:
            return
            
        async with self._lock:
            if self._initialized:  # Double-check locking
                return
            
            logger.info("Initializing AI components...")
            
            # 1. RAG Pipeline
            self.rag_pipeline = RAGPipeline(
                redis_client=redis,
                session_factory=db_session_factory,
            )
            
            # 2. Ingestion Orchestrator
            self.ingestion_orchestrator = IngestionOrchestrator(
                session_factory=db_session_factory,
                redis_client=redis,
                embeddings_provider="ollama",
            )
            
            # 3. Harness Components
            memory = DialogueMemory(
                redis_client=redis,
                max_short_term_messages=settings.agent.max_history_messages,
                summarization_threshold=settings.agent.summarization_threshold,
            )
            
            guardrails = MedicalGuardrails(
                country_code=settings.halal.default_country,
            )
            
            cache = PromptCache(
                redis_client=redis,
                similarity_threshold=settings.rag.similarity_threshold,
            )
            
            model_router = ModelRouter(
                models={
                    "fast": get_llm_fast(),
                    "main": get_llm_main(),
                    "complex": get_llm_complex(),
                    "fallback": get_llm_main(),  # Fallback to main if complex fails
                }
            )
            
            # 4. LangGraph Agent
            checkpointer = AgentCheckpointer(
                database_url=settings.pgvector.database_url.get_secret_value().replace("postgresql+asyncpg", "postgresql"),
            )
            saver = await checkpointer.initialize()
            
            agent = PharmacistAgent(
                router_llm=get_llm_fast(),
                main_llm=get_llm_main(),
                mcp_client=self.mcp_client,
                rag_pipeline=self.rag_pipeline,
            )
            
            # Inject checkpointer into agent graph (if supported by your graph setup)
            # agent.graph.checkpointer = saver
            
            # 5. Agent Harness
            self.agent_harness = AgentHarness(
                agent=agent,
                memory=memory,
                guardrails=guardrails,
                cache=cache,
                model_router=model_router,
            )
            
            # 6. Evaluator
            self.evaluator = AgentEvaluator(
                eval_llm=get_llm_complex(),
                evaluator_model_name=settings.ollama.complex_model,
            )
            
            self._initialized = True
            logger.info("✅ AI components initialized successfully")


# Global singleton instance
ai_container = AIComponents()


async def get_ai_container(
    redis: Redis = Depends(get_redis_client),
    request: Request = None,
) -> AIComponents:
    """
    Main dependency that ensures all AI components are initialized.
    Returns the singleton container.
    """
    # Extract DB factory from app state if available
    db_factory = getattr(request.app.state, "db_session_factory", None) if request else None
    
    await ai_container.initialize(redis=redis, db_session_factory=db_factory)
    return ai_container


# ============================================================================
# CONVENIENCE DEPENDENCIES (for specific endpoints)
# ============================================================================

async def get_rag_pipeline(
    container: AIComponents = Depends(get_ai_container),
) -> RAGPipeline:
    if not container.rag_pipeline:
        raise HTTPException(status_code=500, detail="RAG Pipeline not initialized")
    return container.rag_pipeline


async def get_ingestion_orchestrator(
    container: AIComponents = Depends(get_ai_container),
) -> IngestionOrchestrator:
    if not container.ingestion_orchestrator:
        raise HTTPException(status_code=500, detail="Ingestion Orchestrator not initialized")
    return container.ingestion_orchestrator


async def get_agent_harness(
    container: AIComponents = Depends(get_ai_container),
) -> AgentHarness:
    if not container.agent_harness:
        raise HTTPException(status_code=500, detail="Agent Harness not initialized")
    return container.agent_harness


async def get_evaluator(
    container: AIComponents = Depends(get_ai_container),
) -> AgentEvaluator:
    if not container.evaluator:
        raise HTTPException(status_code=500, detail="Evaluator not initialized")
    return container.evaluator


async def get_tracer() -> ObservabilityTracer:
    """Get the global observability tracer."""
    return ai_container.tracer
