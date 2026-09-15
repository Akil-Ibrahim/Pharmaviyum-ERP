"""
Main RAG Pipeline orchestrator.

Best practice 2026:
- End-to-end pipeline (ingest → chunk → embed → store → retrieve → generate)
- Streaming support for long responses
- Structured outputs with Pydantic validation
- Medical guardrails for safety
- Multi-language support (vi/en/th/id)
"""

from __future__ import annotations

import time
from typing import AsyncIterator

from src.pharmaviyum.core.logging import logger

from .chunking import MedicalChunker
from .embeddings import EmbeddingsProvider
from .schemas import Document, QueryContext, RAGResponse, RetrievalResult
from .vector_store import PgVectorStore


class RAGPipeline:
    """
    End-to-end RAG pipeline for pharmaceutical knowledge.

    Usage:
        pipeline = RAGPipeline(vector_store, embeddings, llm)

        # Ingest documents
        await pipeline.ingest([document])

        # Query
        response = await pipeline.query("What is the dosage of Paracetamol?", context)
    """

    def __init__(
        self,
        vector_store: PgVectorStore,
        embeddings: EmbeddingsProvider,
        llm,
        chunker: MedicalChunker | None = None,
        guardrails=None,
    ):
        self.vector_store = vector_store
        self.embeddings = embeddings
        self.llm = llm
        self.chunker = chunker or MedicalChunker()
        self.guardrails = guardrails

    async def ingest(
        self,
        documents: list[Document],
        chunking_strategy: str = "medical",
    ) -> dict[str, int]:
        """
        Ingest documents into vector store.

        Pipeline:
        1. Chunk documents (medical-aware)
        2. Generate embeddings (batched)
        3. Upsert to pgvector

        Returns:
            Statistics about ingestion
        """
        start_time = time.perf_counter()
        total_chunks = 0

        for document in documents:
            # Step 1: Chunk
            chunks = self.chunker.chunk(document, strategy=chunking_strategy)
            if not chunks:
                logger.warning(f"No chunks generated for document {document.id}")
                continue

            # Step 2: Embed (batched for throughput)
            embeddings = await self.embeddings.embed_batch(
                [c.content for c in chunks],
                batch_size=32,
            )

            # Step 3: Upsert to vector store
            await self.vector_store.upsert(chunks, embeddings)
            total_chunks += len(chunks)

            logger.info(
                f"Ingested document {document.id}: {len(chunks)} chunks",
                extra={"doc_type": document.doc_type, "country": document.country},
            )

        latency_ms = (time.perf_counter() - start_time) * 1000
        logger.info(f"Ingestion complete: {total_chunks} chunks in {latency_ms:.2f}ms")

        return {
            "documents_processed": len(documents),
            "chunks_created": total_chunks,
            "latency_ms": latency_ms,
        }

    async def query(
        self,
        question: str,
        context: QueryContext,
    ) -> RAGResponse:
        """
        Query the RAG pipeline.

        Pipeline:
        1. Embed query
        2. Hybrid search (vector + BM25 + RRF)
        3. Construct prompt with retrieved context
        4. Generate answer with LLM
        5. Apply medical guardrails
        6. Return structured response
        """
        start_time = time.perf_counter()

        # Step 1: Embed query
        query_embedding = await self.embeddings.embed(question)

        # Step 2: Hybrid search
        retrieved = await self.vector_store.hybrid_search(
            query=question,
            query_embedding=query_embedding,
            top_k=10,
            filters=self._build_filters(context),
            reranker="bge-reranker-v2-m3",
        )

        if not retrieved:
            logger.warning(f"No results found for query: {question[:50]}")
            return RAGResponse(
                answer="I couldn't find relevant information for your question.",
                sources=[],
                confidence=0.0,
                warnings=["no_results"],
                model_used="none",
                latency_ms=(time.perf_counter() - start_time) * 1000,
            )

        # Step 3: Construct prompt
        prompt = self._build_prompt(question, retrieved, context)

        # Step 4: Generate answer
        generation_start = time.perf_counter()
        llm_response = await self.llm.generate(
            prompt=prompt,
            temperature=context.temperature,
            max_tokens=context.max_tokens,
        )
        _generation_latency = time.perf_counter() - generation_start

        # Step 5: Apply guardrails
        answer = llm_response.content
        warnings: list[str] = []

        if self.guardrails:
            validated = await self.guardrails.validate(
                answer=answer,
                question=question,
                sources=retrieved,
            )
            answer = validated.answer
            warnings = validated.warnings

        # Step 6: Compute confidence (average retrieval score)
        confidence = sum(r.score for r in retrieved) / len(retrieved)

        total_latency = (time.perf_counter() - start_time) * 1000

        logger.info(
            f"RAG query complete: {question[:50]}...",
            extra={
                "sources": len(retrieved),
                "confidence": confidence,
                "latency_ms": total_latency,
                "country": context.country,
            },
        )

        return RAGResponse(
            answer=answer,
            sources=retrieved,
            confidence=confidence,
            warnings=warnings,
            model_used=self.llm.model_name,
            latency_ms=total_latency,
            tokens_used=getattr(llm_response, "tokens_used", 0),
        )

    async def query_stream(
        self,
        question: str,
        context: QueryContext,
    ) -> AsyncIterator[str]:
        """
        Streaming query for long responses.

        Yields tokens as they're generated.
        Use for real-time UI updates.
        """
        # Embed + retrieve (same as query)
        query_embedding = await self.embeddings.embed(question)
        retrieved = await self.vector_store.hybrid_search(
            query=question,
            query_embedding=query_embedding,
            top_k=10,
            filters=self._build_filters(context),
        )

        if not retrieved:
            yield "I couldn't find relevant information for your question."
            return

        prompt = self._build_prompt(question, retrieved, context)

        # Stream from LLM
        async for token in self.llm.generate_stream(
            prompt=prompt,
            temperature=context.temperature,
            max_tokens=context.max_tokens,
        ):
            yield token

    def _build_filters(self, context: QueryContext) -> dict:
        """Build metadata filters from query context."""
        filters = {}

        if context.country:
            filters["country"] = context.country
        if context.category:
            filters["category"] = context.category
        if context.halal_filter:
            filters["halal_certified"] = True

        return filters

    def _build_prompt(
        self,
        question: str,
        sources: list[RetrievalResult],
        context: QueryContext,
    ) -> str:
        """
        Construct prompt with retrieved context.

        Best practice 2026:
        - Clear instruction
        - Numbered sources for citation
        - Language-specific instructions (SEA multi-language)
        - Safety constraints for medical advice
        """
        # Format sources with numbering
        sources_text = ""
        for i, source in enumerate(sources, 1):
            sources_text += f"\n[{i}] {source.chunk.content}\n"
            sources_text += (
                f"    (Source: {source.chunk.metadata.get('source', 'unknown')}, "
            )
            sources_text += f"Type: {source.chunk.chunk_type})\n"

        # Language-specific instruction
        lang_instructions = {
            "vi": "Trả lời bằng tiếng Việt.",
            "en": "Answer in English.",
            "th": "ตอบเป็นภาษาไทย.",
            "id": "Jawab dalam bahasa Indonesia.",
        }

        prompt = f"""You are a pharmaceutical AI assistant for Southeast Asian pharmacies.

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

        return prompt
