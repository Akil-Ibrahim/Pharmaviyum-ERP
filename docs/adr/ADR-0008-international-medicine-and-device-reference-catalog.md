# ADR-0008: Official International Medicine and Medical Device Reference Catalog

**Status:** Accepted — architecture and scope approved; implementation and source validation pending  
**Date:** 2026-11-16  
**Owners:** Pharmaviyum engineering

## Context

Pharmaviyum needs searchable medicine and medical-device reference data for the United States, EU/EEA, United Kingdom and Canada. Existing RxNorm, EMA Article 57 and Health Canada DPD importers cover only part of this scope and have restrictions that require review.

Reference data must not implicitly create pharmacy SKUs, sellable products, prices, batches, inventory, sales or dispensing authorization. Registration in one market does not establish authorization in another.

## Decision

### 1. Source policy and approved scope

Use official, publicly accessible, free regulatory or international sources only. Paid commercial databases, subscriptions and paid APIs are out of scope. Public availability does not automatically grant redistribution rights; document terms, attribution, rate limits and permitted reuse for each dataset before production ingestion.

| Domain / market | Official source candidates | Intended coverage |
|---|---|---|
| Medicine terminology | NLM RxNorm / RxNav | Normalized clinical and branded concepts, ingredients, strengths and dosage forms |
| US medicines | FDA openFDA, NDC Directory, Drugs@FDA, Orange Book | Product identifiers, labels, listings and approval data |
| EU/EEA medicines | EMA public PMS / Article 57 | Product, substance, strength, form, route and authorization data where exposed |
| Canada medicines | Health Canada DPD | DIN, product, ingredient, strength, form, route, company and status |
| UK medicines | Official MHRA public datasets/services | UK product and authorization data, subject to verified public access |
| US devices | FDA AccessGUDID | UDI-DI, device identity, brand/model and manufacturer |
| EU devices | EUDAMED public UDI/Devices data | Device and UDI information exposed through public modules |
| Canada devices | Health Canada MDALL | Licence, class, manufacturer and device information |
| UK devices | Official MHRA public device data, where available | Public device and registration information |

This is an implementation/discovery scope, not a claim of complete bulk access or identical field coverage. Before enabling an adapter, record the exact endpoint/dataset, access method, coverage, terms, attribution, update cadence, limitations and a reproducible sample validation. If no suitable free official interface exists, record a coverage gap; do not silently substitute a commercial aggregator.

No manufacturer or country-of-origin exclusion is allowed in reference-catalog ingestion, staging, review or search. This explicitly includes Teva and Israeli-origin records. Country and regulatory status remain visible source attributes, not hidden exclusion heuristics.

### 2. Separate domain models

Maintain two independent reference domains:

- **Medicine catalogue:** substances/ingredients, medicinal products and presentations, ingredient composition, strength/concentration, dosage form, route, release characteristics, brands, synonyms, manufacturers/authorization holders, national identifiers and market authorizations.
- **Medical-device catalogue:** device identity, brand/model, manufacturer, UDI-DI and national identifiers, classification/risk class, intended purpose and market-specific licences/registrations.

Shared source, provenance and import-run infrastructure is permitted. Do not combine medicines and devices into one polymorphic product table.

Keep reference entities separate from operational pharmacy Product/SKU, price, batch/lot, stock, sale and dispensing entities. Imports must never create sellable products or inventory implicitly. Local market authorization checks remain independent.

### 3. Provenance and source semantics

Preserve, where supplied: source ID, source record ID, dataset/release version, source URL, retrieval time, source-reported update/effective dates, market, regulatory status, raw source representation, content checksum and import-run ID.

Store source assertions separately from normalized canonical entities. Do not overwrite conflicting source facts without an explicit field-level precedence policy. Preserve each assertion and its provenance. Absence from a partial/delta response is not evidence of withdrawal. Apply withdrawal status only when source semantics explicitly support it.

Use stable external identifiers for idempotency. If identifiers do not establish identity, retain separate market-specific records or stage a candidate match for review; do not merge on similar names alone.

### 4. Import architecture

Implement source-specific adapters behind a common ingestion contract:

1. Fetch official APIs or bulk releases with timeouts, bounded retries and rate limits.
2. Persist import-run metadata and raw staging records.
3. Validate source schemas and required identifiers.
4. Normalize terminology, units, forms, routes and manufacturer names without losing original values.
5. Reconcile and deduplicate using stable source identifiers and conservative identity rules.
6. Idempotently upsert source assertions and canonical links.
7. Report rejected, changed and unresolved records with reasons.
8. Refresh search indexes and emit source-level reports.

One adapter failure must not block independent adapters. Imports must be restartable and safe to repeat. Full snapshots and incremental updates need separate source-aware handling. Refresh cadence follows each source's actual publication schedule.

### 5. Search

Use PostgreSQL normalized fields, Full Text Search and pg_trgm initially. Add a separate search service only if measured scale or relevance requirements justify it.

Medicine search: brand, INN/generic name, ingredient, synonym, strength/unit, dosage form, route, manufacturer, country and regulatory identifier. Device search: name, brand/model, manufacturer, UDI-DI, classification and national licence/registration identifier.

Rank exact identifier/name matches above structured ingredient/strength/form matches, then fuzzy matches. Return market, source, freshness and regulatory status. Do not label a result currently marketed or locally sellable unless the relevant source and local policy establish that fact.

### 6. Analogue semantics and safety

Expose two separate medicine result classes:

- **Exact generic equivalents:** require compatible active-ingredient composition, strength/concentration, dosage form, route and release characteristics. Account for clinically meaningful salt/base and combination distinctions. Missing or conflicting required attributes prohibit an exact-equivalent label.
- **Therapeutic alternatives:** different active ingredients potentially related by official therapeutic classification or indication. Display separately with evidence/source and a pharmacist/clinician assessment warning. ATC similarity alone does not prove clinical equivalence, interchangeability or suitability for a patient.

Do not automatically recommend, substitute, prescribe or dispense an analogue. This is reference information, not clinical decision support.

Device analogues require a separate policy based on intended purpose, device type, technical specifications, model, UDI and risk class. Similar names alone are insufficient.

### 7. Security and operations

Import public reference data only. Never place patient/customer data in source payloads, logs or import metadata. Apply least-privilege database access, bounded payload/error storage, source rate limits, timeouts and redacted diagnostics. Workers receive only the access required for their task.

Track import success/failure, source freshness, record counts, validation failures, duplicate candidates, unresolved matches and search quality. Provide dry-run, source-level disable switches, checkpoints and recovery procedures.

## Alternatives considered

- Commercial global catalogue/API — rejected because only official free sources are approved.
- One polymorphic table for medicines and devices — rejected because identity and regulatory models differ.
- Name-only deduplication/analogue matching — rejected due to false merges and unsafe equivalence claims.
- Automatic creation of pharmacy products/stock — rejected because reference data does not establish local saleability or physical inventory.
- Immediate separate search engine/vector database — deferred until PostgreSQL search is measured.

## Consequences

Benefits: auditable provenance, explicit national authorization semantics, independent medicine/device models, no paid data-provider dependency, and no implicit POS/inventory mutation.

Costs: source coverage and field completeness vary; adapters and normalization require maintenance; public access may still restrict bulk use or redistribution; analogue quality requires domain review and conservative abstention.

## Implementation and rollout

1. Audit current models, endpoints, importer scripts, exclusion policy, migrations and tests.
2. Define additive medicine/device schemas, source records, import runs, provenance and indexes.
3. Remove manufacturer/country exclusions from reference-catalog ingestion, listing, matching, review and search. Preserve unrelated POS saleability controls.
4. Reuse/extend RxNorm, EMA and Health Canada adapters; add FDA and device adapters; verify UK public sources before implementation.
5. Implement normalization, conservative deduplication, search and separately classified analogue results.
6. Add source-specific dry-runs, fixtures, contract, idempotency/replay, provenance and exclusion-regression tests.
7. Run QA migrations and dry-runs on the isolated QA database branch. Report coverage, counts, rejected records, duplicates, source terms and limitations.
8. Production migration/import requires separate explicit approval after dry-run review and backup/recovery checks. This ADR does not authorize production writes.

## Acceptance criteria

- No manufacturer/country-origin exclusion in medicine reference ingestion, review or search; regression tests include Teva and Israeli-origin examples.
- Medicine and device schemas are separate and provenance-backed.
- Every canonical record traces to one or more source assertions.
- Repeating the same source release creates no duplicates or repeated side effects.
- Source failures and malformed records are isolated and reported.
- Exact generic equivalents and therapeutic alternatives are distinct in API and UI.
- Missing evidence yields unknown/unmatched, not inferred equivalence.
- Reference imports never create pharmacy SKU, price, batch, stock or sale records.
- QA migration and dry-run evidence is reviewed before production writes.

### Initial implementation safeguards (2026-11-16)

The feature branch removes origin-based exclusions from reference-catalog API and
the existing RxNorm, EMA and Health Canada staging paths. The legacy local
pharmacy-product/POS eligibility policy remains isolated from reference data.

The former production-capable legacy staging workflow has been converted to
dry-run-only with no database credentials. The newer staging workflow requires the
separate `CATALOG_QA_DATABASE_URL` secret and an explicit `STAGE_QA` confirmation.
Deployment smoke checks validate API response shape rather than requiring a
pre-populated catalogue.

Historical revision `2026_11_05_000004` previously performed a destructive
origin-based purge. Its upgrade is now a no-op for databases that have not applied
it. Production had already recorded that revision; this source change does not
restore data removed by the former migration. The production reference catalogue
was empty at the 2026-11-16 audit.

These are code changes on the feature branch and remain subject to CI, QA migration,
and dry-run validation. Initial multi-ingredient composition schema, migration,
import payloads and search/review support have been added but are not yet validated.
Initial medical-device models, migration, Health Canada MDALL importer and authenticated
search API have also been added; MDALL response parsing tests are included. CI/QA
validation remains pending. FDA AccessGUDID bulk importer, EU/UK device adapters,
additional FDA/UK medicine adapters, and exact/therapeutic analogue classification
remain open implementation work.

## Status and implementation evidence

This ADR approves architecture and scope only. It does not claim that adapters, schema migrations, UI, source-terms review, catalogue imports or production rollout are complete. Update implementation status with code, test and QA evidence as phases are delivered.

## Related documentation

- [English source coverage and importer notes](../catalog/INTERNATIONAL_CATALOG_SOURCES.md)
- [Russian source coverage and importer notes](../catalog/INTERNATIONAL_CATALOG_SOURCES.ru.md)
