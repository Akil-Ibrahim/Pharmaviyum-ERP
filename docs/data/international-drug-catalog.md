# International and European drug catalog

Pharmaviyum separates **Drug Reference**, **Medicinal Product**, and local **Product / inventory** entities. Regulatory reference rows are not pharmacy stock.

## European source: EMA Article 57

The EMA publishes an official XLSX dataset of medicines with valid marketing authorisations in the European Economic Area (EEA). It includes product name, active substance, route of administration, country of authorisation, and marketing authorisation holder. Source: https://www.ema.europa.eu/en/human-regulatory-overview/post-authorisation/data-medicines-iso-idmp-standards-post-authorisation/public-data-article-57-database

This is European regulatory reference data, not a complete retail pack/barcode catalogue. It does not itself provide pharmacy prices, batches, expiry dates, stock availability, or a reliable Rx/OTC classification. The importer stores authorisation country separately and skips rows with multiple active substances until the schema supports multiple ingredients.

Validate the downloaded file without database writes:

```bash
uv run python scripts/import_ema_catalog.py --dry-run
```

After the migration has been applied in a test environment, import:

```bash
uv run python scripts/import_ema_catalog.py
```

## US source: NLM RxNorm Current Prescribable Content

The importer `scripts/import_rxnorm_catalog.py` loads single-ingredient clinical and branded drug concepts from the U.S. National Library of Medicine.

- Source: https://www.nlm.nih.gov/research/umls/rxnorm/docs/rxnormfiles.html
- Required attribution: “This product uses publicly available data courtesy of the U.S. National Library of Medicine (NLM), National Institutes of Health, Department of Health and Human Services; NLM is not responsible for the product and does not endorse or recommend this or any other product.”
- RxNorm is US-centric and excludes drugs exclusively marketed outside the US. It is not a complete global medicine list.

## Safety and data boundaries

Neither import creates sellable products, prices, pharmacy inventory, batches, expiry dates, or dispensing eligibility. Do not infer local market authorisation, Rx/OTC status, or availability from a reference match alone.
