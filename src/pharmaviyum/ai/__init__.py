"""
Pharmaviyum AI Layer — Public API.

This module exposes the complete AI/LLM stack for the Pharmaviyum pharmaceutical CRM:
- RAG Pipeline (ingestion, chunking, embeddings, hybrid search, generation)
- MCP Server (JSON-RPC 2.0 with tools, resources, prompts)
- LangGraph Agent (Router → Planner → Executor → Reviewer)
- Agent Harness (memory, guardrails, cache, model routing, HITL)
- Evaluation (LLM-as-judge, benchmark runner, golden dataset)
- Observability (OpenTelemetry + LangSmith + Prometheus)

Usage:
    from src.pharmaviyum.ai import (
        RAGPipeline, AgentHarness, MCPServer,
        settings, tracer, mcp_client,
    )
"""

# LangGraph Agent
from .agents import (
    AgentCheckpointer,
    AgentState,
    AgentStreamManager,
    PharmacistAgent,
    create_callback_manager,
    create_safety_check_subgraph,
    node_retry,
    require_pharmacist_approval_node,
)
from .config import AISettings, settings

# Evaluation
from .evaluation import (
    GOLDEN_DATASET,
    AgentEvaluator,
    BenchmarkResult,
    BenchmarkRunner,
    EvaluationResult,
)

# Agent Harness
from .harness import (
    AgentHarness,
    AgentResponse,
    ContextWindowManager,
    DialogueMemory,
    GracefulDegradation,
    HumanReviewQueue,
    MedicalGuardrails,
    ModelRouter,
    PromptCache,
    ToolCallingLayer,
)

# MCP Server & Client
from .mcp import (
    MCPClient,
    MCPServer,
    analytics_tracker,
    get_mcp_health_status,
    health_checker,
    mcp_client,
    mcp_server,
    prompt_registry,
    resource_registry,
    tool_registry,
)

# RAG Pipeline
from .mortarium_rag import (
    Chunk,
    Document,
    DocumentPreprocessor,
    DriftDetector,
    EmbeddingQualityEvaluator,
    IngestionOrchestrator,
    MedicalChunker,
    MultiLanguageEmbeddingRouter,
    PgVectorStore,
    QueryContext,
    RAGPipeline,
    RAGResponse,
    RetrievalResult,
)

# Observability
from .observability import (
    ObservabilityTracer,
    ai_registry,
    calculate_llm_cost,
    record_evaluation_scores,
    record_llm_usage,
    record_tool_call,
    tracer,
)

__version__ = "1.0.0"

__all__ = [
    # Config
    "settings",
    "AISettings",
    # RAG
    "RAGPipeline",
    "IngestionOrchestrator",
    "MedicalChunker",
    "PgVectorStore",
    "MultiLanguageEmbeddingRouter",
    "EmbeddingQualityEvaluator",
    "DriftDetector",
    "DocumentPreprocessor",
    "Document",
    "Chunk",
    "RetrievalResult",
    "RAGResponse",
    "QueryContext",
    # MCP
    "MCPServer",
    "mcp_server",
    "MCPClient",
    "mcp_client",
    "tool_registry",
    "resource_registry",
    "prompt_registry",
    "analytics_tracker",
    "health_checker",
    "get_mcp_health_status",
    # Agents
    "PharmacistAgent",
    "AgentState",
    "AgentCheckpointer",
    "AgentStreamManager",
    "create_callback_manager",
    "create_safety_check_subgraph",
    "require_pharmacist_approval_node",
    "node_retry",
    # Harness
    "AgentHarness",
    "DialogueMemory",
    "MedicalGuardrails",
    "PromptCache",
    "ModelRouter",
    "AgentResponse",
    "ToolCallingLayer",
    "ContextWindowManager",
    "GracefulDegradation",
    "HumanReviewQueue",
    # Evaluation
    "AgentEvaluator",
    "EvaluationResult",
    "BenchmarkRunner",
    "BenchmarkResult",
    "GOLDEN_DATASET",
    # Observability
    "ObservabilityTracer",
    "tracer",
    "ai_registry",
    "record_tool_call",
    "record_llm_usage",
    "record_evaluation_scores",
    "calculate_llm_cost",
]
