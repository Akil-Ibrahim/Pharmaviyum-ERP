"""Evaluate real tenant-scoped retrieval on a synthetic pharmacy SOP golden set.

Requires PostgreSQL with pgvector and either local FastEmbed or a configured
embedding provider. A disposable PostgreSQL schema is created and dropped.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import subprocess
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Sequence
from uuid import UUID, uuid5

import numpy as np
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.pharmaviyum.ai.config import settings
from src.pharmaviyum.ai.mortarium_rag.embeddings import EmbeddingsFactory
from src.pharmaviyum.ai.mortarium_rag.quality_metrics import (
    EmbeddingQualityEvaluator,
)
from src.pharmaviyum.ai.mortarium_rag.schemas import Chunk
from src.pharmaviyum.ai.mortarium_rag.vector_store import PgVectorStore

DATASET_NAMESPACE = UUID("44384428-4c71-4acd-8657-08a934cb38aa")
FASTEMBED_MODEL = "BAAI/bge-small-en-v1.5"
FASTEMBED_DIMENSIONS = 384


@dataclass(frozen=True)
class CorpusChunk:
    key: str
    content: str
    source: str
    tenant: str = "primary"


@dataclass(frozen=True)
class GoldenQuery:
    query: str
    relevant_chunk_keys: tuple[str, ...]


CORPUS: tuple[CorpusChunk, ...] = (
    CorpusChunk(
        "receiving",
        "Receiving deliveries: compare each delivered item and quantity with the purchase order. Record damaged or missing items on the delivery discrepancy form before signing.",
        "receiving-sop",
    ),
    CorpusChunk(
        "cold_chain",
        "Refrigerated stock: record refrigerator temperature at opening and closing each day. Quarantine stock if the reading is outside the range printed on its product label and notify the responsible pharmacist.",
        "cold-chain-sop",
    ),
    CorpusChunk(
        "returns",
        "Customer returns: returned medicines must not be placed back into saleable inventory. Store them in the designated returns container and record the return in the returns log.",
        "returns-sop",
    ),
    CorpusChunk(
        "recall",
        "Product recall: identify affected batch numbers, stop dispensing affected stock, move it to the marked quarantine area, and document quantities in the recall register.",
        "recall-sop",
    ),
    CorpusChunk(
        "expiry",
        "Expiry checks: inspect stock shelves monthly, remove expired products from sale, and record the product name, batch number, quantity, and disposal route in the expiry log.",
        "expiry-sop",
    ),
    CorpusChunk(
        "access",
        "Closing procedure: lock the dispensary, secure controlled inventory according to local policy, set the alarm, and record the closing checklist with the duty manager.",
        "closing-sop",
    ),
    CorpusChunk(
        "cleaning",
        "Cleaning schedule: clean and sign the workbench checklist at opening and after any spill. Report damaged equipment to the duty manager.",
        "cleaning-sop",
    ),
    CorpusChunk(
        "supplier",
        "Supplier invoices: match the invoice number and line items against the purchase order and delivery note. Escalate price or quantity differences to the inventory manager.",
        "invoice-sop",
    ),
    CorpusChunk(
        "stock_count",
        "Cycle counts: count the listed shelf quantities, compare them with the inventory system, and submit unexplained differences to the inventory manager for review.",
        "stock-count-sop",
    ),
    CorpusChunk(
        "privacy",
        "Customer privacy: keep printed customer records out of public view, return documents to locked storage after use, and report suspected exposure to the privacy lead.",
        "privacy-sop",
    ),
    CorpusChunk(
        "other_tenant_cold_chain",
        "Refrigerated stock: record refrigerator temperature at opening and closing each day. Quarantine stock if readings are outside the product label range.",
        "other-tenant-cold-chain-sop",
        "other",
    ),
    CorpusChunk(
        "other_tenant_returns",
        "Customer returns must be logged and placed in the designated returns container, not returned to saleable inventory.",
        "other-tenant-returns-sop",
        "other",
    ),
)

GOLDEN_SET: tuple[GoldenQuery, ...] = (
    GoldenQuery(
        "What should staff verify and document when a delivery arrives?",
        ("receiving",),
    ),
    GoldenQuery(
        "Which records are checked before signing for a supplier shipment?",
        ("receiving",),
    ),
    GoldenQuery(
        "Where should damaged or missing delivery items be noted?",
        ("receiving",),
    ),
    GoldenQuery(
        "How often should fridge temperatures be recorded, and what if they are out of range?",
        ("cold_chain",),
    ),
    GoldenQuery(
        "What should staff do with refrigerated stock after an out-of-range reading?",
        ("cold_chain",),
    ),
    GoldenQuery(
        "At what times is the refrigerator temperature log completed?",
        ("cold_chain",),
    ),
    GoldenQuery(
        "Can a customer's returned medicine go back on the shelf?",
        ("returns",),
    ),
    GoldenQuery(
        "Where are medicines placed after a customer brings them back?",
        ("returns",),
    ),
    GoldenQuery(
        "What information is entered in the returns log?",
        ("returns",),
    ),
    GoldenQuery(
        "What steps should staff take when a product batch is recalled?",
        ("recall",),
    ),
    GoldenQuery(
        "Where should recalled inventory be moved after dispensing is stopped?",
        ("recall",),
    ),
    GoldenQuery(
        "Which batch details and quantities are recorded during a recall?",
        ("recall",),
    ),
    GoldenQuery(
        "How do staff identify and record expired stock?",
        ("expiry",),
    ),
    GoldenQuery(
        "How frequently are shelves checked for expired products?",
        ("expiry",),
    ),
    GoldenQuery(
        "What details belong in the expiry log?",
        ("expiry",),
    ),
    GoldenQuery(
        "What must be secured and recorded at the end of the day?",
        ("access",),
    ),
    GoldenQuery(
        "Which checklist is completed when the pharmacy closes?",
        ("access",),
    ),
    GoldenQuery(
        "What security steps are taken before leaving the dispensary?",
        ("access",),
    ),
    GoldenQuery(
        "When is the workbench cleaned and where are spills recorded?",
        ("cleaning",),
    ),
    GoldenQuery(
        "Who is told about damaged cleaning or workbench equipment?",
        ("cleaning",),
    ),
    GoldenQuery(
        "When should staff sign the workbench cleaning checklist?",
        ("cleaning",),
    ),
    GoldenQuery(
        "How should invoice quantities be checked against received goods?",
        ("supplier", "receiving"),
    ),
    GoldenQuery(
        "What documents are compared when checking a supplier invoice?",
        ("supplier",),
    ),
    GoldenQuery(
        "Who reviews price differences on an invoice?",
        ("supplier",),
    ),
    GoldenQuery(
        "How are shelf counts compared with inventory records?",
        ("stock_count",),
    ),
    GoldenQuery(
        "What happens when a cycle count does not match the system?",
        ("stock_count",),
    ),
    GoldenQuery(
        "Who reviews unexplained differences found during a shelf count?",
        ("stock_count",),
    ),
    GoldenQuery(
        "How should printed customer records be protected?",
        ("privacy",),
    ),
    GoldenQuery(
        "Where do staff return customer paperwork after using it?",
        ("privacy",),
    ),
    GoldenQuery(
        "Who should be notified about a possible exposure of customer records?",
        ("privacy",),
    ),
)


def _chunk_id(key: str) -> UUID:
    return uuid5(DATASET_NAMESPACE, key)


def _validate_dataset() -> None:
    keys = {chunk.key for chunk in CORPUS if chunk.tenant == "primary"}
    if len(keys) != len([chunk for chunk in CORPUS if chunk.tenant == "primary"]):
        raise ValueError("Primary corpus chunk keys must be unique")
    for case in GOLDEN_SET:
        if not case.relevant_chunk_keys:
            raise ValueError(
                "Every golden query must label at least one relevant chunk"
            )
        missing = set(case.relevant_chunk_keys) - keys
        if missing:
            raise ValueError(
                f"Golden query references unknown primary chunks: {missing}"
            )


def _percentiles(values: Sequence[float]) -> dict[str, float]:
    if not values:
        return {}
    return {
        f"p{percentile}": round(float(np.percentile(values, percentile)), 3)
        for percentile in (50, 95, 99)
    }


def _provider_config() -> tuple[str, str, str | None, str]:
    if not settings.use_cloud_llm:
        return (
            "ollama",
            settings.ollama.embedding_model,
            None,
            settings.ollama.base_url,
        )
    if settings.cloud_llm_provider == "gemini":
        api_key = settings.gemini.api_key
        if api_key is None:
            raise RuntimeError("Set GEMINI_API_KEY in the local environment")
        return (
            "gemini",
            settings.gemini.embedding_model,
            api_key.get_secret_value(),
            "",
        )
    api_key = settings.openai.api_key
    if api_key is None:
        raise RuntimeError(
            "Groq chat uses OpenAI embeddings in this project; set OPENAI_API_KEY locally"
        )
    return "openai", settings.openai.embedding_model, api_key.get_secret_value(), ""


class FastEmbedAdapter:
    """Async adapter for the optional local FastEmbed evaluation model."""

    def __init__(self) -> None:
        from fastembed import TextEmbedding

        self.model = TextEmbedding(model_name=FASTEMBED_MODEL, threads=2)

    async def embed(self, text: str) -> list[float]:
        return await asyncio.to_thread(
            lambda: next(self.model.query_embed(text)).tolist()
        )

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        vectors = await asyncio.to_thread(
            lambda: list(self.model.embed(texts, batch_size=16, parallel=1))
        )
        return [vector.tolist() for vector in vectors]


async def run_benchmark(
    pharmacy_id: int, top_k: int, concurrency: int, embedding_provider: str
) -> dict[str, object]:
    _validate_dataset()
    if pharmacy_id <= 0:
        raise ValueError("pharmacy_id must be a positive integer")
    if top_k <= 0:
        raise ValueError("top_k must be a positive integer")
    if concurrency <= 0:
        raise ValueError("concurrency must be a positive integer")

    provider_initialization_start = time.perf_counter()
    if embedding_provider == "fastembed":
        provider_name = "fastembed"
        model_name = FASTEMBED_MODEL
        embeddings = FastEmbedAdapter()
        embedding_dimensions = FASTEMBED_DIMENSIONS
    else:
        provider_name, model_name, api_key, endpoint = _provider_config()
        embeddings = EmbeddingsFactory.create(
            provider=provider_name,
            use_cache=False,
            api_key=api_key,
            model=model_name,
            endpoint=endpoint,
            dimensions=settings.pgvector.vector_dimensions,
        )
        embedding_dimensions = settings.pgvector.vector_dimensions
    provider_initialization_seconds = (
        time.perf_counter() - provider_initialization_start
    )

    database_url = settings.pgvector.database_url.get_secret_value()
    schema = f"rag_eval_{uuid5(DATASET_NAMESPACE, str(time.time_ns())).hex[:20]}"
    admin_engine = create_async_engine(database_url, pool_pre_ping=True)
    async with admin_engine.begin() as connection:
        await connection.execute(text(f'CREATE SCHEMA "{schema}"'))

    engine = create_async_engine(
        database_url,
        pool_pre_ping=True,
        connect_args={"server_settings": {"search_path": f"{schema},public"}},
    )
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    table_name = "evaluation_chunks"
    vector_store = PgVectorStore(
        session_factory,
        table_name=table_name,
        dimensions=embedding_dimensions,
    )
    tenant_ids = {
        "primary": pharmacy_id,
        "other": pharmacy_id + 1,
    }
    chunks = [
        Chunk(
            id=_chunk_id(item.key),
            document_id=uuid5(DATASET_NAMESPACE, f"document:{item.key}"),
            content=item.content,
            chunk_index=0,
            chunk_type="general",
            token_count=len(item.content.split()),
            metadata={
                "pharmacy_id": tenant_ids[item.tenant],
                "source": item.source,
                "access_level": "pharmacy",
                "language": "en",
            },
        )
        for item in CORPUS
    ]
    embedding_times: list[float] = []
    search_times: list[float] = []
    total_times: list[float] = []
    retrieved_ids: list[list[UUID]] = []
    query_vectors: list[list[float]] = []
    relevant_ids = [
        [_chunk_id(key) for key in case.relevant_chunk_keys] for case in GOLDEN_SET
    ]
    cross_tenant_hits = 0
    per_query_results: list[dict[str, object]] = []
    key_by_id = {chunk.id: item.key for chunk, item in zip(chunks, CORPUS)}

    try:
        await vector_store.initialize()
        corpus_start = time.perf_counter()
        corpus_vectors = await embeddings.embed_batch(
            [chunk.content for chunk in chunks]
        )
        corpus_embedding_seconds = time.perf_counter() - corpus_start
        corpus_upsert_start = time.perf_counter()
        await vector_store.upsert(chunks, corpus_vectors)
        corpus_upsert_seconds = time.perf_counter() - corpus_upsert_start

        semaphore = asyncio.Semaphore(concurrency)

        async def evaluate_case(
            case: GoldenQuery,
        ) -> tuple[
            list[UUID], list[float], float, float, float, int, dict[str, object]
        ]:
            async with semaphore:
                total_start = time.perf_counter()
                embedding_start = time.perf_counter()
                query_vector = await embeddings.embed(case.query)
                embedding_latency = (time.perf_counter() - embedding_start) * 1000
                search_start = time.perf_counter()
                results = await vector_store.hybrid_search(
                    query=case.query,
                    query_embedding=query_vector,
                    top_k=top_k,
                    filters={
                        "pharmacy_id": pharmacy_id,
                        "access_level": "pharmacy",
                    },
                )
                search_latency = (time.perf_counter() - search_start) * 1000
                total_latency = (time.perf_counter() - total_start) * 1000
                result_ids = [result.chunk.id for result in results]
                cross_tenant_count = sum(
                    result.chunk.metadata.get("pharmacy_id") != pharmacy_id
                    for result in results
                )
                detail = {
                    "query": case.query,
                    "relevant_chunk_keys": list(case.relevant_chunk_keys),
                    "retrieved_chunk_keys": [
                        key_by_id[result_id] for result_id in result_ids
                    ],
                    "embedding_latency_ms": round(embedding_latency, 3),
                    "pgvector_hybrid_search_latency_ms": round(search_latency, 3),
                    "embedding_plus_retrieval_latency_ms": round(total_latency, 3),
                }
                return (
                    result_ids,
                    query_vector,
                    embedding_latency,
                    search_latency,
                    total_latency,
                    cross_tenant_count,
                    detail,
                )

        workload_start = time.perf_counter()
        case_results = await asyncio.gather(
            *(evaluate_case(case) for case in GOLDEN_SET)
        )
        workload_seconds = time.perf_counter() - workload_start
        for (
            result_ids,
            query_vector,
            embedding_latency,
            search_latency,
            total_latency,
            cross_tenant_count,
            detail,
        ) in case_results:
            retrieved_ids.append(result_ids)
            query_vectors.append(query_vector)
            embedding_times.append(embedding_latency)
            search_times.append(search_latency)
            total_times.append(total_latency)
            cross_tenant_hits += cross_tenant_count
            per_query_results.append(detail)

        retrieval_metrics = EmbeddingQualityEvaluator.evaluate_retrieval(
            query_embeddings=query_vectors,
            relevant_doc_ids=relevant_ids,
            retrieved_doc_ids=retrieved_ids,
            k_values=sorted({1, min(3, top_k), top_k}),
            latency_ms=total_times,
        )
        dataset_manifest = {
            "corpus": [
                {"key": item.key, "content": item.content, "tenant": item.tenant}
                for item in CORPUS
            ],
            "queries": [
                {
                    "query": case.query,
                    "relevant_chunk_keys": case.relevant_chunk_keys,
                }
                for case in GOLDEN_SET
            ],
        }
        revision = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        runner_digest = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        dirty_worktree = bool(
            subprocess.run(
                ["git", "status", "--porcelain"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
        return {
            "benchmark": "synthetic-pharmacy-sop-retrieval",
            "generated_at": datetime.now(UTC).isoformat(),
            "code_revision": revision,
            "runner_sha256": runner_digest,
            "worktree_dirty": dirty_worktree,
            "dataset_sha256": hashlib.sha256(
                json.dumps(dataset_manifest, sort_keys=True).encode()
            ).hexdigest(),
            "provider": provider_name,
            "embedding_model": model_name,
            "vector_store": "PostgreSQL/pgvector hybrid search",
            "query_count": len(GOLDEN_SET),
            "corpus_chunk_count": len(chunks),
            "top_k": top_k,
            "query_concurrency": concurrency,
            "provider_initialization_seconds": round(
                provider_initialization_seconds, 3
            ),
            "retrieval_workload_seconds": round(workload_seconds, 3),
            "retrieval_queries_per_second": round(
                len(GOLDEN_SET) / workload_seconds, 3
            ),
            "tenant_isolation": {
                "primary_tenant_id": pharmacy_id,
                "other_tenant_fixture_count": sum(
                    item.tenant == "other" for item in CORPUS
                ),
                "cross_tenant_hits": cross_tenant_hits,
            },
            "per_query_results": per_query_results,
            "retrieval_quality": {
                "samples_evaluated": retrieval_metrics.samples_evaluated,
                "recall_at_k": retrieval_metrics.recall_at_k,
                "precision_at_k": retrieval_metrics.precision_at_k,
                "mrr": retrieval_metrics.mrr,
                "ndcg_at_k": retrieval_metrics.ndcg_at_k,
            },
            "latency_ms": {
                "embedding": _percentiles(embedding_times),
                "pgvector_hybrid_search": _percentiles(search_times),
                "embedding_plus_retrieval": {
                    **_percentiles(total_times),
                    "mean": round(retrieval_metrics.avg_latency_ms, 3),
                },
                "corpus_embedding_total_seconds": round(corpus_embedding_seconds, 3),
                "corpus_pgvector_upsert_seconds": round(corpus_upsert_seconds, 3),
            },
            "not_measured": [
                "LLM generation",
                "answer groundedness",
                "citation precision and recall",
                "provider token usage and cost",
                "production-scale throughput",
            ],
        }
    finally:
        await engine.dispose()
        async with admin_engine.begin() as connection:
            await connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        await admin_engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pharmacy-id",
        type=int,
        default=900001,
        help="Synthetic tenant ID isolated in the disposable schema (default: 900001).",
    )
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument(
        "--concurrency",
        type=int,
        default=1,
        help="Concurrent synthetic queries; start at 1 and increase cautiously.",
    )
    parser.add_argument(
        "--embedding-provider",
        choices=("configured", "fastembed"),
        default="fastembed",
        help=(
            "Use local FastEmbed by default, or the provider configured in AI settings."
        ),
    )
    parser.add_argument("--output", help="Optional path for a JSON report.")
    args = parser.parse_args()
    result = asyncio.run(
        run_benchmark(
            args.pharmacy_id,
            args.top_k,
            args.concurrency,
            args.embedding_provider,
        )
    )
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as report:
            report.write(rendered + "\n")
    print(rendered)


if __name__ == "__main__":
    main()
