# 🏗️ Pharmaviyum AI Layer Architecture

## Overview
This document describes the enterprise-grade AI/LLM layer built for the Pharmaviyum pharmaceutical CRM. It provides end-to-end RAG, agentic tool orchestration, and strict medical safety guardrails.

## High-Level Diagram

```text
┌─────────────────────────────────────────────────────────────────────┐
│                         FastAPI Application                         │
│  Endpoints: /api/v1/ai/query, /stream, /ingest, /health, /metrics   │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│                    Dependency Injection Layer                       │
│  (Lazy initialization, Singleton LLM clients, Redis/DB sessions)    │
└──────┬────────────────────┬─────────────────────┬──────────────────┘
       │                    │                     │
┌──────▼──────┐      ┌──────▼──────┐      ┌──────▼──────┐
│  RAG Pipeline│      │ LangGraph   │      │ MCP Server  │
│  (Hybrid Search)│   │ Agent       │      │ (JSON-RPC)  │
└──────┬──────┘      └──────┬──────┘      └──────┬──────┘
       │                    │                     │
┌──────▼────────────────────▼─────────────────────▼──────┐
│              Agent Harness (Orchestrator)              │
│  Memory │ Guardrails │ Cache │ Model Router │ HITL    │
└────────────────────────┬───────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    ┌─────────┐    ┌──────────┐    ┌──────────┐
    │PostgreSQL│    │  Redis   │    │  Ollama  │
    │+ pgvector│    │(Cache+MQ)│    │  (LLM)   │
    └─────────┘    └──────────┘    └──────────┘
```

## Key Components

### 1. RAG Pipeline
- **Ingestion**: Async Celery workers process PDF/HTML/DOCX with OCR and table extraction.
- **Preprocessing**: PII redaction, text normalization, and content hashing for deduplication.
- **Retrieval**: Hybrid search (Vector + BM25) with Reciprocal Rank Fusion (RRF) and cross-encoder reranking.
- **Optimizations**: HyDE (Hypothetical Document Embeddings), multi-query retrieval, and contextual compression.

### 2. MCP (Model Context Protocol) Server
- **Protocol**: JSON-RPC 2.0 compliant (`tools/list`, `tools/call`, `resources/read`, `prompts/get`).
- **Clinical Tools**: Drug interaction checker, patient history retrieval.
- **Regulatory Tools**: Global Halal Compliance Engine (Sunni + Shia fiqh, Istihalah, Darurah), Prescription verification (SEA limits).
- **Management**: RBAC, usage analytics, health checks, and semantic versioning.

### 3. LangGraph Agent
- **Architecture**: 4-node state machine (Router → Planner → Executor → Reviewer).
- **Resilience**: PostgreSQL checkpointer for state persistence, `@node_retry` decorators, and circuit breakers.
- **Safety**: Interrupt nodes for Human-in-the-Loop (HITL) pharmacist approval on critical decisions.

### 4. Observability & Evaluation
- **Tracing**: OpenTelemetry (OTLP) + LangSmith for end-to-end request tracing.
- **Metrics**: Prometheus metrics for latency, tool success rates, and LLM token costs.
- **Evaluation**: LLM-as-a-judge benchmark runner with Golden Dataset (Recall@k, MRR, NDCG, safety scoring).

## Unique Differentiators
1. **Global Halal AI Engine**: The only CRM with native support for both Sunni (4 madhhabs) and Shia (Sistani, Khamenei) jurisprudence, including Istihalah (chemical transformation) logic.
2. **SEA/MENA Regulatory Awareness**: Built-in country-specific limits for controlled substances (Vietnam, Indonesia, Thailand, Saudi Arabia, Iran, Iraq).
3. **Production-Ready**: Full Kubernetes support with liveness/readiness probes, graceful degradation, and structured error handling.

## Getting Started

1. **Install Dependencies**:
```bash
   pip install -r requirements-ai.txt
```

2. **Configure Environment**:
```bash
   cp .env.example .env
   # Edit .env with your Redis, PostgreSQL, and Ollama URLs
```

3. **Run Ollama Models**:
```bash
   ollama pull qwen2.5:7b
   ollama pull mxbai-embed-large
```

4. **Start the Application**:
```bash
   uvicorn src.pharmaviyum.main:app --reload --port 8000
```

5. **Run Examples**:
```bash
   python docs/ai_examples.py
```

6. **View Documentation**:
   - Swagger UI: http://localhost:8000/docs
   - Metrics: http://localhost:8000/metrics
