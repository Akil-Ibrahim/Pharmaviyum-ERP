"""
Medical RAG pipeline orchestrated by LangGraph.

Replaces the linear RAGPipeline.query() path with an explicit state machine:

  transform_query -> retrieve -> grade_documents
    -> (rewrite_query -> retrieve)*  [max 2 rewrites]
    -> compress -> generate -> guardrails -> END

Ingestion (chunk -> embed -> upsert) stays outside the graph as a batch job.

Integrates with existing project components:
  - QueryTransformer.generate_multi_query / transform_with_hyde
  - ContextualCompressor.compress (returns CompressedContext)
  - PgVectorStore.hybrid_search
  - EmbeddingsProvider.embed
"""
from __future__ import annotations

import time
from typing import Any, Literal

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .contextual_compression import ContextualCompressor
from .embeddings import EmbeddingsProvider
from .query_transformer import QueryTransformer
from .schemas import QueryContext, RAGResponse, RetrievalResult
from .state import RAGState
from .vector_store import PgVectorStore
from src.pharmaviyum.core.logging import logger


class LangGraphRAG:
    """
    End-to-end medical RAG driven by LangGraph StateGraph.

    Public API mirrors RAGPipeline.query so callers need minimal changes:
      response = await rag.query(question, context)
      async for event in rag.astream(question, context): ...
    """

    # Hard limit on rewrite loops to avoid infinite retrieve cycles
    MAX_REWRITES = 2

    def __init__(
        self,
        vector_store: PgVectorStore,
        embeddings: EmbeddingsProvider,
        llm: Any,
        fast_llm: Any | None = None,
        guardrails: Any | None = None,
        checkpointer: Any | None = None,
    ) -> None:
        """
        Args:
            vector_store: pgvector hybrid search backend.
            embeddings: Embedding provider (supports embed / embed_batch).
            llm: Main reasoning model used for final answer generation.
            fast_llm: Cheap/fast model for grading and query rewrite.
                      Falls back to llm if not provided.
            guardrails: Optional medical safety layer with post_process().
            checkpointer: LangGraph checkpointer (MemorySaver by default).
        """
        self.vector_store = vector_store
        self.embeddings = embeddings
        self.llm = llm
        self.fast_llm = fast_llm or llm
        self.guardrails = guardrails

        # Existing project helpers (real APIs)
        self.transformer = QueryTransformer(llm=self.fast_llm)
        self.compressor = ContextualCompressor(llm=self.fast_llm)

        self.graph = self._build_graph(checkpointer)

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------

    def _build_graph(self, checkpointer: Any | None):
        """Wire nodes and conditional edges, then compile."""
        workflow = StateGraph(RAGState)

        # Register nodes
        workflow.add_node("transform_query", self.transform_query_node)
        workflow.add_node("retrieve", self.retrieve_node)
        workflow.add_node("grade_documents", self.grade_documents_node)
        workflow.add_node("rewrite_query", self.rewrite_query_node)
        workflow.add_node("compress", self.compress_node)
        workflow.add_node("generate", self.generate_node)
        workflow.add_node("guardrails", self.guardrails_node)

        # Linear + conditional topology
        workflow.set_entry_point("transform_query")
        workflow.add_edge("transform_query", "retrieve")
        workflow.add_edge("retrieve", "grade_documents")

        workflow.add_conditional_edges(
            "grade_documents",
            self._route_after_grade,
            {
                "sufficient": "compress",
                "rewrite": "rewrite_query",
                "give_up": "generate",  # answer with whatever we have / refuse
            },
        )
        workflow.add_edge("rewrite_query", "retrieve")
        workflow.add_edge("compress", "generate")
        workflow.add_edge("generate", "guardrails")
        workflow.add_edge("guardrails", END)

        return workflow.compile(checkpointer=checkpointer or MemorySaver())

    # ------------------------------------------------------------------
    # Nodes
    # ------------------------------------------------------------------

    async def transform_query_node(self, state: RAGState) -> dict[str, Any]:
        """
        Expand the user question into retrieval variants.

        Uses multi-query + HyDE via the existing QueryTransformer to improve
        recall on medical terminology and multi-language inputs.
        """
        question = state["question"]
        ctx = state["context"]
        ctx_dict = {
            "language": ctx.language,
            "country": ctx.country,
        }

        # Multi-query variations (includes original as first item)
        variations = await self.transformer.generate_multi_query(
            query=question,
            num_variations=2,
            context=ctx_dict,
        )
        queries = [v.transformed_query for v in variations if v.transformed_query]

        # Optional HyDE document as an extra retrieval query
        try:
            hyde = await self.transformer.transform_with_hyde(
                query=question,
                context=ctx_dict,
            )
            if hyde.transformed_query and hyde.transformed_query not in queries:
                queries.append(hyde.transformed_query)
        except Exception as e:
            logger.warning("HyDE skipped: %s", e)

        if not queries:
            queries = [question]

        logger.debug("Query transformed into %d variants", len(queries))

        return {
            "transformed_queries": queries,
            "rewrite_count": 0,
            "warnings": [],
        }

    async def retrieve_node(self, state: RAGState) -> dict[str, Any]:
        """
        Run hybrid search (vector + BM25 + RRF) for every query variant.

        Results are deduplicated by chunk id, keeping the highest score,
        then truncated to a fixed top-k for the grader.
        """
        ctx = state["context"]
        filters = self._build_filters(ctx)
        all_hits: list[RetrievalResult] = []

        for q in state["transformed_queries"]:
            query_embedding = await self.embeddings.embed(q)
            hits = await self.vector_store.hybrid_search(
                query=q,
                query_embedding=query_embedding,
                top_k=10,
                filters=filters,
            )
            all_hits.extend(hits)

        # Deduplicate: keep best score per chunk
        best: dict[str, RetrievalResult] = {}
        for hit in all_hits:
            key = str(hit.chunk.id)
            if key not in best or hit.score > best[key].score:
                best[key] = hit

        ranked = sorted(best.values(), key=lambda h: h.score, reverse=True)[:12]
        logger.info(
            "Retrieved %d unique chunks (from %d raw hits)",
            len(ranked),
            len(all_hits),
        )

        return {"retrieved": ranked}

    async def grade_documents_node(self, state: RAGState) -> dict[str, Any]:
        """
        LLM-as-judge: keep only chunks that are actually relevant.

        Critical for medical RAG — prevents the generator from hallucinating
        on loosely related drug leaflets or guidelines.
        """
        question = state["question"]
        graded: list[RetrievalResult] = []

        for hit in state["retrieved"]:
            prompt = (
                f"Question: {question}\n\n"
                f"Document chunk:\n{hit.chunk.content[:800]}\n\n"
                "Is this chunk relevant to answer the question? "
                "Reply with only YES or NO."
            )
            resp = await self.fast_llm.ainvoke(prompt)
            text = (
                resp.content if hasattr(resp, "content") else str(resp)
            ).strip().upper()
            if text.startswith("YES"):
                graded.append(hit)

        decision: Literal["sufficient", "insufficient"] = (
            "sufficient" if len(graded) >= 2 else "insufficient"
        )
        logger.info(
            "Graded documents: %d/%d relevant -> %s",
            len(graded),
            len(state["retrieved"]),
            decision,
        )

        return {"graded": graded, "grade_decision": decision}

    async def rewrite_query_node(self, state: RAGState) -> dict[str, Any]:
        """
        Rewrite the question when retrieval quality is too low.

        Increments rewrite_count so the router can eventually give up.
        """
        original = state["question"]
        prompt = (
            "Rewrite the following pharmaceutical question to improve "
            "document retrieval. Keep medical terms precise and concise.\n"
            f"Original: {original}\n"
            "Rewritten:"
        )
        resp = await self.fast_llm.ainvoke(prompt)
        rewritten = (
            resp.content if hasattr(resp, "content") else str(resp)
        ).strip()

        logger.info(
            "Query rewritten (attempt %d): %s",
            state.get("rewrite_count", 0) + 1,
            rewritten[:80],
        )

        return {
            "transformed_queries": [rewritten],
            "rewrite_count": state.get("rewrite_count", 0) + 1,
            "warnings": [f"query_rewritten:{rewritten[:80]}"],
        }

    async def compress_node(self, state: RAGState) -> dict[str, Any]:
        """
        Contextual compression + Lost-in-the-Middle reordering.

        Uses the existing ContextualCompressor API:
          compress(query=..., retrieved=..., context=...) -> CompressedContext
        """
        sources = state["graded"] or state["retrieved"]
        ctx = state["context"]

        compressed = await self.compressor.compress(
            query=state["question"],
            retrieved=sources,
            context={
                "language": ctx.language,
                "country": ctx.country,
            },
        )
        text = compressed.compressed_text if compressed else ""
        logger.debug("Compressed context length: %d chars", len(text))
        return {"compressed_context": text}

    async def generate_node(self, state: RAGState) -> dict[str, Any]:
        """
        Produce the final answer grounded in retrieved (or empty) context.

        If no relevant documents exist, returns a safe refusal instead of
        letting the model invent medical advice.
        """
        ctx = state["context"]
        sources = state["graded"] or state["retrieved"]
        context_text = state.get("compressed_context") or self._fallback_context(sources)

        model_name = getattr(self.llm, "model_name", None) or getattr(
            self.llm, "model", "unknown"
        )

        if not sources:
            return {
                "answer": (
                    "I don't have enough information in the knowledge base "
                    "to answer safely. Please consult a licensed pharmacist."
                ),
                "confidence": 0.0,
                "model_used": str(model_name),
                "tokens_used": 0,
                "warnings": ["no_relevant_documents"],
            }

        prompt = self._build_prompt(state["question"], context_text, ctx)
        resp = await self.llm.ainvoke(prompt)
        answer = resp.content if hasattr(resp, "content") else str(resp)

        tokens = 0
        if hasattr(resp, "usage_metadata") and isinstance(resp.usage_metadata, dict):
            tokens = int(resp.usage_metadata.get("total_tokens", 0) or 0)

        # Simple confidence heuristic based on number of supporting sources
        confidence = min(0.95, 0.4 + 0.1 * len(sources))

        return {
            "answer": answer,
            "confidence": confidence,
            "model_used": str(model_name),
            "tokens_used": tokens,
        }

    async def guardrails_node(self, state: RAGState) -> dict[str, Any]:
        """
        Post-generation medical safety checks.

        Applies external guardrails (if configured) and enforces a minimum
        disclaimer when dosage-like language appears without a consult note.
        """
        answer = state.get("answer") or ""
        warnings = list(state.get("warnings") or [])

        if self.guardrails is not None:
            # Support both async post_process and simple callable shapes
            post = getattr(self.guardrails, "post_process", None)
            if post is not None:
                result = await post(answer, state["context"])
                answer = getattr(result, "sanitized_output", None) or answer
                extra = getattr(result, "warnings", None) or []
                warnings.extend(extra)

        # Hard rule: dosage language must be accompanied by a disclaimer
        lower = answer.lower()
        dosage_markers = ("take ", "dosage", "mg/kg", "mg per", "tablet")
        has_dosage_language = any(m in lower for m in dosage_markers)
        has_disclaimer = "consult" in lower and "pharmacist" in lower

        if has_dosage_language and not has_disclaimer:
            warnings.append("missing_pharmacist_disclaimer")
            answer = (
                answer.rstrip()
                + "\n\nConsult a licensed pharmacist for personalized advice."
            )

        return {"answer": answer, "warnings": warnings}

    # ------------------------------------------------------------------
    # Conditional routing
    # ------------------------------------------------------------------

    def _route_after_grade(
        self, state: RAGState
    ) -> Literal["sufficient", "rewrite", "give_up"]:
        """
        Decide next step after document grading.

        - sufficient  -> compress -> generate
        - rewrite     -> rewrite_query -> retrieve (if budget left)
        - give_up     -> generate with whatever we have (or refuse)
        """
        if state["grade_decision"] == "sufficient":
            return "sufficient"
        if state.get("rewrite_count", 0) < self.MAX_REWRITES:
            return "rewrite"
        return "give_up"

    # ------------------------------------------------------------------
    # Public API (drop-in replacement for RAGPipeline.query / stream)
    # ------------------------------------------------------------------

    async def query(
        self,
        question: str,
        context: QueryContext,
        thread_id: str | None = None,
    ) -> RAGResponse:
        """
        Run the full RAG graph and return a structured RAGResponse.

        Compatible with the previous RAGPipeline.query signature.
        """
        start = time.perf_counter()
        initial = self._initial_state(question, context)
        config = {"configurable": {"thread_id": thread_id or "rag-default"}}

        final: RAGState = await self.graph.ainvoke(initial, config=config)

        return RAGResponse(
            answer=final.get("answer") or "",
            sources=final.get("graded") or final.get("retrieved") or [],
            confidence=float(final.get("confidence") or 0.0),
            warnings=list(final.get("warnings") or []),
            model_used=final.get("model_used") or "",
            latency_ms=(time.perf_counter() - start) * 1000,
            tokens_used=int(final.get("tokens_used") or 0),
        )

    async def astream(self, question: str, context: QueryContext):
        """
        Stream node-level updates for UI status messages.

        Yields dicts: {"node": "<node_name>", "data": <partial state update>}
        """
        initial = self._initial_state(question, context)
        async for event in self.graph.astream(initial, stream_mode="updates"):
            for node_name, node_data in event.items():
                yield {"node": node_name, "data": node_data}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _initial_state(self, question: str, context: QueryContext) -> RAGState:
        """Build a clean initial state for a new graph run."""
        return {
            "question": question,
            "context": context,
            "transformed_queries": [],
            "retrieved": [],
            "graded": [],
            "compressed_context": "",
            "grade_decision": "insufficient",
            "rewrite_count": 0,
            "answer": None,
            "warnings": [],
            "confidence": 0.0,
            "model_used": "",
            "latency_ms": 0.0,
            "tokens_used": 0,
        }

    def _build_filters(self, context: QueryContext) -> dict[str, Any]:
        """Map QueryContext fields to vector-store metadata filters."""
        filters: dict[str, Any] = {"country": context.country}
        if context.category:
            filters["category"] = context.category
        if context.halal_filter:
            filters["halal"] = True
        return filters

    def _fallback_context(self, sources: list[RetrievalResult]) -> str:
        """Simple numbered context when compression was skipped."""
        parts: list[str] = []
        for i, src in enumerate(sources, 1):
            parts.append(f"[{i}] {src.chunk.content}")
        return "\n\n".join(parts)

    def _build_prompt(
        self,
        question: str,
        sources_text: str,
        context: QueryContext,
    ) -> str:
        """
        Build the grounded generation prompt with language + safety rules.

        Kept close to the original RAGPipeline prompt for behaviour parity.
        """
        lang_instructions = {
            "vi": "Trả lời bằng tiếng Việt.",
            "en": "Answer in English.",
            "th": "ตอบเป็นภาษาไทย.",
            "id": "Jawab dalam bahasa Indonesia.",
        }

        return f"""You are a pharmaceutical AI assistant for Southeast Asian pharmacies.

{lang_instructions.get(context.language, "Answer in English.")}

Answer the question based ONLY on the provided sources. If the answer is not in the sources, say "I don't have enough information."

IMPORTANT SAFETY RULES:
- Never recommend dosages not explicitly stated in sources
- Always mention contraindications if relevant
- Flag potential drug interactions
- For controlled substances, mention regulatory requirements
- End with: "Consult a licensed pharmacist for personalized advice."

SOURCES:
{sources_text}

QUESTION: {question}

ANSWER:"""
