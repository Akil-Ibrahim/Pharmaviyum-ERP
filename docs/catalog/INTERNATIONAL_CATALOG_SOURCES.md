# International medicine and medical-device reference catalogue

**Architecture decision:** [ADR-0008](../adr/ADR-0008-international-medicine-and-device-reference-catalog.md) · [Русская версия](./INTERNATIONAL_CATALOG_SOURCES.ru.md)

## Approved scope

Build separate medicine and medical-device reference catalogues from official, publicly accessible, free sources for the United States, EU/EEA, United Kingdom and Canada. Commercial databases and paid APIs are out of scope.

Source candidates: NLM RxNorm/RxNav; FDA openFDA, NDC Directory, Drugs@FDA and Orange Book; EMA public PMS/Article 57; Health Canada DPD; official MHRA medicine data; FDA AccessGUDID; public EUDAMED UDI/Devices data; Health Canada MDALL; and official MHRA device data where publicly available.

This is a discovery and implementation scope, not a guarantee of complete bulk access, identical fields or unrestricted redistribution. Before enabling a source, document its exact dataset/API, coverage, terms, attribution, rate limits, update cadence and limitations. A missing free official interface is a documented coverage gap; do not substitute a commercial aggregator.

## Domain boundaries

- **Medicine reference data:** substances/ingredients, products and presentations, composition, strength/concentration, dosage form, route, release characteristics, brands, synonyms, manufacturers/authorization holders, national identifiers and market authorizations.
- **Medical-device reference data:** device identity, brand/model, manufacturer, UDI-DI and national identifiers, classification/risk class, intended purpose and market-specific licences/registrations.

Use separate domain models. Shared source/provenance/import-run infrastructure is acceptable. Reference records are not pharmacy Products/SKUs, prices, batches, inventory, sales or dispensing authorization.

No manufacturer or country-of-origin exclusions are allowed in reference-catalog ingestion, staging, review or search. Teva and Israeli-origin records must be retained when present in an approved source. Country and regulatory status are visible source attributes, not hidden exclusion rules.

## Source coverage and current implementation

| Source | Market | Data represented | Current-state note |
|---|---|---|---|
| NLM RxNorm/RxNav | US-centric terminology | Normalized clinical/branded concepts, ingredients, strengths and dose forms | Existing importer requires audit and expansion; not a global authorization catalogue |
| FDA openFDA/NDC/Drugs@FDA/Orange Book | United States | Product identifiers, labels, listings and approval data | Adapter and dataset-specific terms/semantics require validation |
| EMA PMS/Article 57 | EU/EEA | Public product, substance and authorization data | Existing importer requires audit; public API coverage is limited to exposed fields/modules |
| Health Canada DPD | Canada | DIN, product, ingredient, strength, form, route, company and status | Existing importer requires audit; preserve market/status semantics |
| Official MHRA medicine data | United Kingdom | Public product and authorization information | Exact public dataset/interface and reuse terms must be verified |
| FDA AccessGUDID | US devices | UDI-DI, device identity, brand/model and manufacturer | Official v3 lookup and full-release/pipe-delimited downloads confirmed; importer not yet implemented |
| Public EUDAMED UDI/Devices | EU devices | Publicly exposed UDI/device and actor information | Public module availability and export scope require verification |
| Health Canada MDALL | Canada devices | Licence, class, manufacturer and device information | Initial adapter, models, migration and authenticated search API implemented on feature branch; CI/QA pending |
| Official MHRA device data | UK devices | Public device/registration information | Exact public dataset/interface and reuse terms must be verified |

## Provenance and import contract

Preserve source ID, source record ID, dataset/release version, source URL, retrieval time, source-reported update/effective dates, market, regulatory status, raw source representation, content checksum and import-run ID.

Adapter lifecycle:

1. Fetch official API/bulk release with timeouts, bounded retries and rate limits.
2. Persist import-run metadata and raw staging records.
3. Validate source schema and identifiers.
4. Normalize names, units, ingredients, forms and routes without discarding original values.
5. Reconcile using stable identifiers and conservative matching.
6. Idempotently upsert source assertions and canonical links.
7. Report rejected, changed and unresolved records.
8. Refresh search indexes and emit source-level reports.

Full snapshots and incremental feeds need separate source-aware processing. Absence from a partial response is not proof of withdrawal. One adapter failure must not block independent sources.

## Search and analogue semantics

Initially use PostgreSQL normalized columns, Full Text Search and pg_trgm. Medicine search covers brand, INN/generic, ingredient, synonyms, strength/unit, dosage form, route, manufacturer, country and regulatory ID. Device search covers name, brand/model, manufacturer, UDI-DI, classification and national licence/registration ID.

Medicine analogues are distinct:

- **Exact generic equivalents:** compatible active-ingredient composition, strength/concentration, dosage form, route and release profile, including clinically relevant salt/base and combination distinctions.
- **Therapeutic alternatives:** potentially related medicines with different active ingredients. Display separately with evidence/source and a pharmacist/clinician assessment warning. ATC similarity alone does not establish equivalence or interchangeability.

Do not automatically recommend or substitute medicines. Device analogues require a separate policy based on intended purpose, type, technical specifications, model, UDI and risk class.

## ERP boundary

A reference record is not a local sellable product. Import must not create local SKU, retail price, batch/lot, stock, sale or dispensing authorization. Source-market authorization does not establish authorization in Ukraine or another local market.

### Health Canada MDALL implementation

The first medical-device adapter is Health Canada's official MDALL API:

- API guide: https://health-products.canada.ca/api/documentation/mdall-documentation-en.html
- Licence, device, company and device-identifier endpoints are consumed separately and
  joined using the official licence/device/company identifiers.
- Active and archived licence/device/identifier records are retained with source status.
- Manufacturer country, risk class, licence type, licence dates and device identifiers
  are preserved when published.
- MDALL covers licensed Class II, III and IV devices; it does not represent all Class I
  devices. The catalogue must show this source-coverage limitation.

The implementation is in `scripts/import_health_canada_mdall.py`, with the
`medical_devices`, `medical_device_identifiers` and
`medical_device_authorizations` tables and the authenticated
`/medical-devices/search` API. It is reference data only.

AccessGUDID implementation note: the public v3 lookup API resolves one device when
provided a DI, UDI or public record key; it is not a general catalogue search endpoint.
For a searchable local reference catalogue, use the official full-release pipe-delimited
ZIP, which is designed for relational imports, and process daily/weekly deltas with
source-aware upsert/delete semantics. The current full delimited release is approximately
406 MB, so ingestion must stream/extract and batch-write rather than load the archive
into application memory. Official docs:
https://accessgudid.nlm.nih.gov/resources/developers/v3/device_lookup_api
https://accessgudid.nlm.nih.gov/download/delimited
https://accessgudid.nlm.nih.gov/help/download

### Next medical-device adapters

- US FDA/NLM AccessGUDID: public device lookup APIs and full release downloads.
  Official resources: https://accessgudid.nlm.nih.gov/resources/home and
  https://accessgudid.nlm.nih.gov/
- EU EUDAMED: implement only against the public modules/data actually available and
  retain module/version provenance.
- UK MHRA: confirm the current public register/export and reuse terms before coding.

## Implementation progress (feature branch)

The first implementation pass is being developed on
`feat/international-medicine-device-catalog`:

- Manufacturer/country exclusion checks have been removed from reference-catalog
  source creation, source listing, matching, review and search.
- RxNorm, EMA and Health Canada staging no longer applies the legacy Teva/Israel
  exclusion predicate. EMA/DPD no longer require manufacturer-origin metadata
  merely to retain a source record.
- The legacy predicate remains isolated to local pharmacy-product/POS eligibility;
  it is not a reference-catalog filter.
- Deployment smoke checks validate the search API response contract and do not
  require a particular medicine to have been imported.
- The manual import workflow is restricted to an explicitly configured
  `CATALOG_QA_DATABASE_URL`; it has no production database target.

**Known scope gaps:** an initial `medicinal_product_ingredients` composition table,
backfill migration, importer payload support and search/review support for combination
products have been added on this branch. They still require CI and QA migration
validation. The initial medical-device models, Health Canada MDALL adapter and search API have
also been added, but are not yet validated by CI/QA. FDA AccessGUDID and EU/UK device
adapters, FDA/UK medicine adapters, analogue classification, and source-by-source
licensing validation remain open.

**Historical migration caveat:** revision
`2026_11_05_000004_purge_excluded_catalog_entries` previously deleted matching
reference rows and deactivated matching local products. Its upgrade has been made a
no-op for databases that have not applied it, to prevent future destructive purges.
A database that already applied the former revision is not automatically restored;
recovery of deleted records would require a suitable pre-migration backup. The
production catalog was reported empty during the 2026-11-16 audit.

## Existing importer notes — audit required

The repository currently contains:
- scripts/import_rxnorm_catalog.py
- scripts/import_ema_catalog.py
- scripts/import_health_canada_dpd.py

Current implementations have scope limitations requiring code audit. In particular, the legacy exclusion policy and importer restrictions must be removed from the reference-catalog path. This documentation change does not alter runtime behavior.

The legacy workflow .github/workflows/stage-medicine-reference-catalog.yml and its database target must be audited before reuse. Any write-capable workflow must target an explicitly approved environment and must not write production by default.

## Rollout and safety gates

1. Audit current models, endpoints, scripts, migrations, exclusion checks and tests.
2. Define additive medicine/device schemas and provenance.
3. Remove country/manufacturer exclusions from medicine reference ingestion, listing, matching, review and search; preserve independent POS saleability rules.
4. Extend existing medicine adapters and validate additional official sources.
5. Add device adapters and separate search.
6. Add analogue classification, fixtures, contract, idempotency, replay and regression tests.
7. Run migrations and dry-runs on the isolated QA database branch; report counts, coverage, failures, duplicates and source terms.
8. Obtain explicit approval before production migration or catalogue writes; verify backup/recovery first.

No production catalogue import is authorized by this document. Implementation, source terms, coverage and runtime behavior remain unverified until supported by code and test evidence.
