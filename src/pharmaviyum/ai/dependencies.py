"""FastAPI Dependency Injection for AI Layer.

Best practice 2026:
- Lazy initialization of heavy components (LLMs, Vector Stores)
- Request-scoped dependencies for DB sessions
- Singleton pattern for stateless services and shared infrastructure
- Durable PostgreSQL persistence for LangGraph workflows
"""

from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import Any, AsyncGenerator

from fastapi import Depends, HTTPException, Request, status
from langchain_core.language_models import BaseChatModel
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.pharmaviyum.ai.agents import AgentCheckpointer, PharmacistAgent
from src.pharmaviyum.ai.config import settings
from src.pharmaviyum.ai.evaluation import AgentEvaluator
from src.pharmaviyum.ai.harness import (
    AgentHarness,
    DialogueMemory,
    MedicalGuardrails,
    ModelRouter,
    PromptCache,
)
from src.pharmaviyum.ai.mcp import MCPClient, mcp_client
from src.pharmaviyum.ai.observability import ObservabilityTracer, tracer
from src.pharmaviyum.ai.rag import (
    EmbeddingsFactory,
    IngestionOrchestrator,
    LangGraphRAG,
    PgVectorStore,
)
from src.pharmaviyum.core.logging import logger


async def get_redis_client(request: Request) -> AsyncGenerator[Redis, None]:
    redis = getattr(request.app.state, "redis_client", None)
    if redis is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis service unavailable",
        )
    yield redis


async def get_db_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    factory = getattr(request.app.state, "db_session_factory", None)
    if factory is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable",
        )
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def _build_llm(model: str) -> BaseChatModel:
    """Build the configured LLM backend without changing the local default."""
    if not settings.use_cloud_llm:
        return ChatOllama(
            model=model,
            base_url=settings.ollama.base_url,
            temperature=settings.ollama.temperature,
        )

    api_key = settings.groq.api_key
    if api_key is None:
        raise RuntimeError(
            "USE_CLOUD_LLM=true requires GROQ_API_KEY to be configured"
        )
    return ChatGroq(
        model=model,
        api_key=api_key,
        temperature=settings.groq.temperature,
        timeout=settings.groq.timeout_seconds,
    )


@lru_cache(maxsize=1)
def get_llm_fast() -> BaseChatModel:
    model = settings.groq.fast_model if settings.use_cloud_llm else settings.ollama.fast_model
    return _build_llm(model)


@lru_cache(maxsize=1)
def get_llm_main() -> BaseChatModel:
    model = settings.groq.model if settings.use_cloud_llm else settings.ollama.main_model
    return _build_llm(model)


@lru_cache(maxsize=1)
def get_llm_complex() -> BaseChatModel:
    model = settings.groq.model if settings.use_cloud_llm else settings.ollama.complex_model
    return _build_llm(model)


class AIComponents:
    def __init__(self):
        self._initialized = False
        self._lock = asyncio.Lock()
        self.rag_pipeline: LangGraphRAG | None = None
        self.ingestion_orchestrator: IngestionOrchestrator | None = None
        self.agent_harness: AgentHarness | None = None
        self.mcp_client: MCPClient = mcp_client
        self.evaluator: AgentEvaluator | None = None
        self.tracer: ObservabilityTracer = tracer
        self.checkpointer: AgentCheckpointer | None = None
        self.checkpoint_saver: Any | None = None

    async def initialize(self, redis: Redis, db_session_factory: Any):
        if self._initialized:
            return
        async with self._lock:
            if self._initialized:
                return
            logger.info("Initializing AI components...")
            vector_store = PgVectorStore(
                session_factory=db_session_factory,
                table_name=settings.pgvector.table_name,
                dimensions=settings.pgvector.vector_dimensions,
            )
            try:
                await vector_store.initialize()
            except Exception as exc:
                logger.warning("PgVectorStore initialize deferred: %s", exc)

            embeddings_provider = "ollama"
            embeddings = EmbeddingsFactory.create(
                provider=embeddings_provider, use_cache=True, redis_client=redis
            )
            self.ingestion_orchestrator = IngestionOrchestrator(
                session_factory=db_session_factory,
                redis_client=redis,
                embeddings_provider=embeddings_provider,
            )
            memory = DialogueMemory(
                redis_client=redis,
                max_short_term_messages=settings.agent.max_history_messages,
                summarization_threshold=settings.agent.summarization_threshold,
            )
            guardrails = MedicalGuardrails(country_code=settings.halal.default_country)

            self.checkpointer = AgentCheckpointer(
                database_url=settings.pgvector.database_url.get_secret_value().replace(
                    "postgresql+asyncpg", "postgresql"
                )
            )
            self.checkpoint_saver = await self.checkpointer.initialize()
            self.rag_pipeline = LangGraphRAG(
                vector_store=vector_store,
                embeddings=embeddings,
                llm=get_llm_main(),
                fast_llm=get_llm_fast(),
                guardrails=guardrails,
                checkpointer=self.checkpoint_saver,
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
                    "fallback": get_llm_main(),
                }
            )
            agent = PharmacistAgent(
                router_llm=get_llm_fast(),
                main_llm=get_llm_main(),
                mcp_client=self.mcp_client,
                rag_pipeline=self.rag_pipeline,
                checkpointer=self.checkpoint_saver,
            )
            self.agent_harness = AgentHarness(
                agent=agent,
                memory=memory,
                guardrails=guardrails,
                cache=cache,
                model_router=model_router,
            )
            self.evaluator = AgentEvaluator(
                eval_llm=get_llm_complex(),
                evaluator_model_name=(
                    settings.groq.model
                    if settings.use_cloud_llm
                    else settings.ollama.complex_model
                ),
            )
            self._initialized = True
            logger.info(
                "AI components initialized successfully (llm_backend=%s)",
                "groq" if settings.use_cloud_llm else "ollama",
            )


ai_container = AIComponents()


async def get_ai_container(
    redis: Redis = Depends(get_redis_client), request: Request = None
) -> AIComponents:
    db_factory = (
        getattr(request.app.state, "db_session_factory", None) if request else None
    )
    if db_factory is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable",
        )
    await ai_container.initialize(redis=redis, db_session_factory=db_factory)
    return ai_container


async def get_rag_pipeline(
    container: AIComponents = Depends(get_ai_container),
) -> LangGraphRAG:
    if not container.rag_pipeline:
        raise HTTPException(status_code=500, detail="LangGraph RAG not initialized")
    return container.rag_pipeline


async def get_ingestion_orchestrator(
    container: AIComponents = Depends(get_ai_container),
) -> IngestionOrchestrator:
    if not container.ingestion_orchestrator:
        raise HTTPException(
            status_code=500, detail="Ingestion Orchestrator not initialized"
        )
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
    return ai_container.tracer
