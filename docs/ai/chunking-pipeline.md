# Mortarium Pharmaceutical Chunking Pipeline

**Status:** Architecture documentation of the current implementation and a staged target design. This document distinguishes shipped behavior from capabilities that still require implementation and tests.

## 1. Purpose and safety properties

Chunking converts source documents into bounded, retrievable evidence units for Mortarium's LangGraph RAG workflow. In a pharmacy system, a chunk must preserve the clinical meaning and the context needed to interpret it: medicine identity, strength, dosage form, route, population, conditions, warnings, negation, jurisdiction, source and version.

A chunk is an indexing unit, not an independent clinical authority. The original source remains authoritative. Retrieval and generation must remain tenant- and patient-scoped, evidence-bounded and citation-aware.

## 2. Current repository implementation

The current implementation is in `src/pharmaviyum/ai/mortarium_rag/chunking.py`:

- `MedicalChunker` exposes `medical`, `semantic` and `recursive` strategies.
- The medical strategy detects a limited set of headings (indications, dosage, contraindications, interactions and side effects) and splits section text.
- The semantic strategy groups sentence-like spans up to a configured token budget.
- The recursive strategy falls back through paragraph, newline, sentence and whitespace separators.
- Defaults are 512 estimated tokens and 50 overlap units.
- Chunks retain document ID, sequential chunk index, chunk type, token count and copied document metadata (including source, document type, country and language).
- The compatibility `RAGPipeline.ingest` calls the chunker, embeds chunk content and upserts chunks into the vector store.

**Important implementation caveats:**

1. The current token counter is `len(text) // 4`, a rough character heuristic, not the tokenizer used by the embedding model. Token budgets are therefore approximate.
2. The current `semantic` strategy is sentence-boundary grouping; it is not embedding-based semantic boundary detection.
3. Heading detection is heuristic and currently has limited language coverage. Do not claim complete Russian/English SmPC section parsing.
4. The current chunk schema does not define a first-class parent/child relationship, page/character spans, table structure, heading path or chunking/index revision.
5. The splitter does not provide a dedicated table-aware parser. Tables may be flattened or split by generic separators depending on loader output.
6. The current `Chunk` metadata is flexible, but flexible metadata alone does not prove that every source location or medicine entity is extracted correctly.
7. The documented active API ingestion path is Celery-backed. Verify the API task path and the compatibility facade independently; do not assume they have identical authorization, idempotency or metadata behavior.

These are known limits of the current code, not evidence that every ingestion run is defective.

## 3. Target pipeline

The recommended target is a versioned, structure-aware hybrid pipeline:

```text
Original file / source
  -> format-aware loader and layout extraction
  -> normalization (preserve headings, tables, lists and page anchors)
  -> document identity, jurisdiction and version validation
  -> structure-aware section segmentation
  -> semantic refinement within a section (optional, measured)
  -> bounded child chunks + parent section context
  -> metadata/entity enrichment
  -> embedding and lexical indexing
  -> versioned index publication
  -> tenant-scoped hybrid retrieval and reranking
  -> LangGraph grading, evidence compression and cited generation
```

### Strategy responsibilities

| Strategy | Intended responsibility | Guardrail |
|---|---|---|
| Structure-aware | Split at document/section/subsection boundaries | Never detach a section from its heading path |
| Semantic refinement | Improve boundaries inside long sections | Keep sentences and clinical propositions intact |
| Parent-child | Retrieve precise child evidence and return bounded parent context | Parent and child must share document, version and access scope |
| Table-aware | Preserve row/column/header relationships | Never turn a dose/value into an unlabeled free-floating number |
| Recursive fallback | Bound malformed or unstructured text | Mark fallback use in metadata and quality telemetry |
| Multilingual | Support language-specific parsing and retrieval | Preserve original text; do not silently translate evidence |

A generic recursive splitter remains a safe fallback, not the preferred primary strategy for structured medicine information.

## 4. Chunk content and metadata contract

Each chunk should preserve the original evidence text and carry, where available:

- Identity: `document_id`, `chunk_id`, `chunk_index`, `parent_chunk_id`.
- Provenance: source URI or stable source key, document type, publisher, version, content hash, publication/effective dates, page and source offsets.
- Structure: section ID, heading path, section type, table ID/row identifiers and chunk type.
- Scope: pharmacy/tenant ID, access level, patient ID only for patient-scoped documents, jurisdiction/country.
- Language: detected and declared language, with the original language retained.
- Pharmaceutical entities: canonical drug/ingredient identifiers, product name, strength, dosage form, route and population only when reliably extracted and validated.
- Processing: chunking strategy/version, parser version, tokenizer/model identifier, estimated or measured token count, fallback flags and ingestion/index revision.

Example shape (illustrative contract, not a claim that every field is currently persisted):

```json
{
  "document_id": "smPC_001",
  "chunk_id": "smPC_001_v3_child_014",
  "parent_chunk_id": "smPC_001_v3_section_04",
  "section": "Contraindications",
  "heading_path": ["4. Clinical particulars", "4.3 Contraindications"],
  "language": "en",
  "country": "GB",
  "drug_name": "Omeprazole",
  "active_ingredient": "omeprazole",
  "strength": "20 mg",
  "dosage_form": "capsule",
  "source_page": 4,
  "document_version": "3",
  "chunking_version": "medical-v2",
  "chunk_type": "contraindications"
}
```

Do not fabricate missing metadata. Unknown values remain null/absent and should not be inferred by the model during ingestion.

## 5. Pharmaceutical preservation rules

- Keep a medicine name attached to the passage it qualifies.
- Keep strength, units, dosage form and route together; never detach a numeric dose from its unit or population.
- Preserve negation, uncertainty, conditional language, exceptions and temporal qualifiers (for example, "not recommended", "only if", "unless", "in patients with").
- Keep contraindications, warnings, interactions, dosage instructions and adverse effects distinguishable.
- Keep table headers with every retained row; represent merged cells and footnotes explicitly where the source parser supports them.
- Do not merge contradictory statements from different documents or versions into one chunk.
- Keep jurisdiction, effective dates and source version available to retrieval filters and citations.
- Preserve source text; any normalized or translated representation must be separately labeled and traceable to the original.

## 6. Initial tuning profile

The following are experimental starting ranges, not clinical standards or fixed production defaults:

| Setting | Initial experiment |
|---|---:|
| Child chunk size | 200–400 tokenizer tokens |
| General chunk size | 400–700 tokenizer tokens |
| Parent section context | 1,000–1,500 tokenizer tokens, bounded |
| Overlap | 50–100 tokenizer tokens, only where it does not duplicate or distort a table/list |
| Retrieval candidates | Tune against a labeled corpus and latency budget |
| Tokenizer | Match the embedding model/tokenizer where available |

The current implementation's 512/50 values are approximate because it counts characters divided by four. Do not compare those estimates directly with model-tokenizer measurements. Tune by document type, language and section; evaluate retrieval quality and cost together.

## 7. Versioning, re-ingestion and publication

Treat source documents, chunking configuration and embeddings as versioned artifacts.

- Compute a stable content hash for the normalized source and record parser/chunker configuration versions.
- Make ingestion idempotent for the same source version and processing configuration.
- Build a new index revision alongside the currently active revision; do not overwrite the only usable index in place.
- Validate chunk counts, provenance, metadata completeness and retrieval regression before switching the active revision.
- Retain the previous revision for rollback according to the approved retention policy.
- A changed chunker, parser, embedding model or critical metadata mapping requires re-indexing and benchmark evidence.
- Never mix chunks from incompatible document versions without explicit freshness and jurisdiction handling.

## 8. Retrieval and LangGraph integration

Chunking is upstream of the existing LangGraph RAG graph. The graph remains responsible for query transformation, scoped retrieval, document grading, bounded rewriting, evidence compression, generation and output guardrails.

Retrieval must apply the authenticated pharmacy scope and, for patient-level evidence, the explicit patient scope. Parent expansion must reapply the same authorization filters; it must not be possible to retrieve a child safely and then load an unauthorized parent.

Citations must resolve to the original document and its exact version/page/section where available. Compression must preserve source IDs and must not remove negation, units, conditions or warnings. A query rewrite or HyDE candidate is a retrieval aid, never evidence.

## 9. Evaluation and acceptance gates

Use offline Ragas evaluation together with deterministic pharmaceutical regression tests. Compare chunking revisions on the same frozen, synthetic or de-identified corpus and query set.

| Quality dimension | What to measure |
|---|---|
| Context precision / recall | Whether relevant evidence is retrieved and required evidence is not missed |
| Faithfulness | Whether answer claims are supported by retrieved evidence |
| Citation correctness | Claim-to-source entailment and exact source/version resolution |
| Medication entity accuracy | Drug, ingredient, strength, unit, form and route preservation |
| Negation preservation | Polarity and conditional qualifiers survive parsing, chunking, retrieval and compression |
| Table integrity | Header/value/row relationships survive extraction and retrieval |
| Multilingual retrieval | Recall and answer quality reported separately for English and Russian (and each additional supported language) |
| Patient/pharmacy isolation | No cross-tenant or cross-patient evidence, parent expansion, cache or checkpoint leakage |
| Freshness | Correct document version and jurisdiction selected |
| Operational cost | Ingestion time, embedding volume, index size, retrieval latency and failure rate |

A release candidate should pass deterministic integrity and isolation tests before any aggregate Ragas score is considered. Set thresholds from a reviewed baseline; do not invent universal thresholds. LLM-judge results are regression signals, not clinical validation, regulatory approval or proof of clinical safety.

## 10. Required test scenarios

At minimum, maintain regression fixtures for:

1. A contraindication section whose heading must remain attached to its content.
2. A dosage table with headers, multiple strengths, units and footnotes.
3. A negative statement and a conditional exception.
4. A long section that requires multiple child chunks and parent expansion.
5. English and Russian versions of equivalent source material.
6. Two document versions with different effective dates.
7. Two pharmacies and two patients with overlapping medicine names.
8. Malformed text that triggers recursive fallback.
9. Duplicate source ingestion and retry after partial failure.
10. Citation resolution from child chunk to original source page and version.

## 11. Security and privacy

Chunk metadata is part of the authorization boundary. Enforce tenant and patient filters in trusted server-side code, not model-generated arguments or user-supplied metadata. Do not place PHI in chunk IDs, metric labels, trace attributes or ordinary logs. Use synthetic/de-identified evaluation fixtures. Apply retention and deletion policies to source files, chunks, embeddings, parent records, checkpoints and backups.

## 12. Code map

- Chunker: `src/pharmaviyum/ai/mortarium_rag/chunking.py`
- RAG schemas: `src/pharmaviyum/ai/mortarium_rag/schemas.py`
- Compatibility ingestion/retrieval facade: `src/pharmaviyum/ai/mortarium_rag/pipeline.py`
- Document preprocessing: `src/pharmaviyum/ai/mortarium_rag/ingestion/preprocessing.py`
- Ingestion orchestration: `src/pharmaviyum/ai/mortarium_rag/ingestion/`
- LangGraph RAG architecture: [langgraph-rag-architecture.md](./langgraph-rag-architecture.md)
- Pharmaceutical Ragas evaluation: [ragas-pharmaceutical-evaluation.md](./ragas-pharmaceutical-evaluation.md)
- AI system design: [AI_LLM_SYSTEM_DESIGN.md](./AI_LLM_SYSTEM_DESIGN.md)

## 13. Implementation status

This document records the target architecture and the observed current code boundaries. It does **not** assert that parent-child retrieval, table-aware parsing, tokenizer-accurate budgets, complete Russian/English section parsing, index blue/green publication or all listed regression fixtures are already implemented. Those capabilities require code changes, tests and evidence before being marked complete.
