# International medicine reference catalogue

## Source coverage

The reference catalogue is built from multiple regulator/reference datasets. No single public source is a complete, globally authoritative list of every medicine, presentation, strength, and country authorization.

| Source | Geographic scope | Data represented | Important limitation |
|---|---|---|---|
| NLM RxNorm Current Prescribable Content | United States-centric clinical terminology | Ingredient concepts and clinical/branded drug concepts, strengths, and dosage forms | Not a complete global brand/authorization catalogue; current importer excludes combination products |
| EMA Article 57 product data | European Economic Area | Product names, active substances, strength, form, route, country, and authorization holder | Not every medicine in every country; current importer excludes multi-ingredient records |
| Health Canada Drug Product Database (DPD) | Canada | Drug Identification Number, brand, company, active ingredient and strength, dosage form, route, package information, and product status | Canadian regulatory data only; current importer stages single-active-ingredient products with Approved or Marketed status |

Official source documentation:
- NLM RxNorm: https://www.nlm.nih.gov/research/umls/rxnorm/
- EMA Article 57: https://www.ema.europa.eu/en/human-regulatory-overview/research-development/data-medicines-iso-idmp-standards/substance-product-organisation-referential-spor-master-data
- Health Canada DPD API: https://health-products.canada.ca/api/documentation/dpd-documentation-en.html

Health Canada describes the DPD as product-specific information for drugs approved for use in Canada and exposes the data through a JSON/XML API. Its active-ingredient endpoint includes ingredient name and strength; related endpoints provide dosage form, route, package information, and product status. The DPD contains approximately 47,000 product records across current and historical statuses. The importer deliberately retains only current Approved or Marketed single-ingredient records.

## Importing

Run from the repository root after applying database migrations. First run the three dry-run commands:

    uv run python scripts/import_rxnorm_catalog.py --dry-run
    uv run python scripts/import_ema_catalog.py --dry-run
    uv run python scripts/import_health_canada_dpd.py --dry-run

After reviewing the dry-run counts and confirming source reuse terms, run the importers:

    uv run python scripts/import_rxnorm_catalog.py
    uv run python scripts/import_ema_catalog.py
    uv run python scripts/import_health_canada_dpd.py

Each importer records source identity, source version, extraction time, source URL, a conservative licensing note, and a normalized payload. The Health Canada source version is a SHA-256 checksum over the fetched source resources. Re-running the same source version is idempotent.

## Review and saleability boundaries

- Imported records are staged with pending_review status.
- A superuser can approve a source record by linking it to an existing canonical reference or explicitly creating a global DrugReference and MedicinalProduct. The source record retains its provenance link.
- POS reference search can show these records as **Pending review · reference only**, including INN/ingredient, brand/product name, strength, dosage form, route, manufacturer, country, and source-market status when supplied.
- A staged record is not a local pharmacy Product. It has no local SKU, retail price, pharmacy inventory, batch, expiry, or sellable quantity.
- Source-market approval is not authorization to sell in Ukraine or any other market. Local regulatory status and pharmacy policy must be checked independently.
- The current canonical product model represents one active ingredient per medicinal product. Combination products are excluded by the current importers rather than silently misrepresented.
- Data source licenses and redistribution terms must be checked before redistributing any imported dataset.

## Expanding coverage

Additional regulator-specific adapters can be added without changing the POS product/stock model. Candidate sources should be assessed individually for data completeness, API stability, licensing, refresh cadence, authorization-status semantics, and ingredient/strength normalization. Examples include the FDA NDC Directory (United States) and other national regulator product databases. Their records must remain explicitly country-scoped and provenance-backed.
