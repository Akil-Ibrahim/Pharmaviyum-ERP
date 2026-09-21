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
from typing import Any, AsyncGenerator, cast

from fastapi import HTTPException, Request, status
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from redis.asyncio import Redis

from src.pharmaviyum.ai.agents.checkpointer import AgentCheckpointer
from src.pharmaviyum.ai.agents.pharmacist_agent import PharmacistAgent
from src.pharmaviyum.ai.config import settings
from src.pharmaviyum.ai.evaluation.evaluator import AgentEvaluator
from src.pharmaviyum.ai.harness.agent_harness import AgentHarness
from src.pharmaviyum.ai.harness.cache import PromptCache
from src.pharmaviyum.ai.harness.guardrails import MedicalGuardrails
from src.pharmaviyum.ai.harness.memory import DialogueMemory
from src.pharmaviyum.ai.harness.model_router import ModelRouter
from src.pharmaviyum.ai.mcp.client import MCPClient
from src.pharmaviyum.ai.mortarium_rag.embeddings import EmbeddingsFactory
from src.pharmaviyum.ai.mortarium_rag.graph import LangGraphRAG
from src.pharmaviyum.ai.mortarium_rag.ports import LLMPort, RetrieverPort
from src.pharmaviyum.ai.mortarium_rag.ingestion.orchestrator import (
    IngestionOrchestrator,
)
from src.pharmaviyum.ai.mortarium_rag.vector_store import PgVectorStore
from src.pharmaviyum.ai.observability.tracer import ObservabilityTracer, tracer
from src.pharmaviyum.core.logging import logger

mcp_client = MCPClient()


def get_redis(request: Request) -> Redis:
    redis = getattr(request.app.state, "redis_client", None)
    if redis is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis service unavailable",
        )
    return redis


async def get_db_session(request: Request) -> AsyncGenerator[Any, None]:
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

    if settings.cloud_llm_provider == "gemini":
        api_key = settings.gemini.api_key
        if api_key is None:
            raise RuntimeError(
                "USE_CLOUD_LLM=true with GEMINI provider requires GEMINI_API_KEY"
            )
        return ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key.get_secret_value(),
            temperature=settings.gemini.temperature,
            timeout=settings.gemini.timeout_seconds,
        )

    api_key = settings.groq.api_key
    if api_key is None:
        raise RuntimeError(
            "USE_CLOUD_LLM=true with GROQ provider requires GROQ_API_KEY"
        )
    return ChatGroq(
        model=model,
        api_key=api_key,
        temperature=settings.groq.temperature,
        timeout=settings.groq.timeout_seconds,
    )


def _build_embeddings_provider() -> str:
    """Select the embedding backend for the active AI provider."""
    if not settings.use_cloud_llm:
        return "ollama"
    return "gemini" if settings.cloud_llm_provider == "gemini" else "openai"


@lru_cache(maxsize=1)
def get_llm_fast() -> BaseChatModel:
    model = (
        (
            settings.gemini.fast_model
            if settings.cloud_llm_provider == "gemini"
            else settings.groq.fast_model
        )
        if settings.use_cloud_llm
        else settings.ollama.fast_model
    )
    return _build_llm(model)


@lru_cache(maxsize=1)
def get_llm_main() -> BaseChatModel:
    model = (
        (
            settings.gemini.model
            if settings.cloud_llm_provider == "gemini"
            else settings.groq.model
        )
        if settings.use_cloud_llm
        else settings.ollama.main_model
    )
    return _build_llm(model)


@lru_cache(maxsize=1)
def get_llm_complex() -> BaseChatModel:
    model = (
        (
            settings.gemini.complex_model
            if settings.cloud_llm_provider == "gemini"
            else settings.groq.model
        )
        if settings.use_cloud_llm
        else settings.ollama.complex_model
    )
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

            embeddings_provider = _build_embeddings_provider()
            embeddings_api_key = (
                settings.gemini.api_key.get_secret_value()
                if settings.use_cloud_llm
                and settings.cloud_llm_provider == "gemini"
                and settings.gemini.api_key
                else (
                    settings.openai.api_key.get_secret_value()
                    if settings.use_cloud_llm and settings.openai.api_key
                    else None
                )
            )
            embedding_model = (
                settings.gemini.embedding_model
                if settings.use_cloud_llm and settings.cloud_llm_provider == "gemini"
                else (
                    settings.openai.embedding_model if settings.use_cloud_llm else None
                )
            )
            embedding_dimensions = settings.pgvector.vector_dimensions

            embeddings = EmbeddingsFactory.create(
                provider=embeddings_provider,
                use_cache=True,
                redis_client=redis,
                api_key=embeddings_api_key,
                model=embedding_model or settings.ollama.embedding_model,
                endpoint=settings.ollama.base_url,
                dimensions=embedding_dimensions,
            )
            self.ingestion_orchestrator = IngestionOrchestrator(
                session_factory=db_session_factory,
                redis_client=redis,
                embeddings_provider=embeddings_provider,
                embeddings_api_key=embeddings_api_key,
                embeddings_model=embedding_model,
                embeddings_dimensions=embedding_dimensions,
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
                vector_store=cast(RetrieverPort, vector_store),
                embeddings=embeddings,
                llm=cast(LLMPort, get_llm_main()),
                fast_llm=cast(LLMPort, get_llm_fast()),
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
                    (
                        settings.gemini.complex_model
                        if settings.cloud_llm_provider == "gemini"
                        else settings.groq.model
                    )
                    if settings.use_cloud_llm
                    else settings.ollama.complex_model
                ),
            )
            self._initialized = True


ai_components = AIComponents()

# Backwards-compatible dependency names used by the application layer.
ai_container = ai_components


def get_agent_harness() -> AgentHarness:
    if ai_components.agent_harness is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI components are not initialized",
        )
    return ai_components.agent_harness


def get_redis_client(request: Request) -> Redis:
    return get_redis(request)
