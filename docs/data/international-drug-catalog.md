# International drug catalog import

Pharmaviyum has separate **Drug Reference**, **Medicinal Product**, and local **Product / inventory** entities. The international reference catalog is not pharmacy stock.

## Initial source: NLM RxNorm Current Prescribable Content

The importer downloads the current prescribable RxNorm archive from the U.S. National Library of Medicine and loads single-ingredient clinical and branded drug concepts into `drug_references`, `drug_reference_ingredients`, and `medicinal_products`.

- Source: https://www.nlm.nih.gov/research/umls/rxnorm/docs/rxnormfiles.html
- The NLM provides the Current Prescribable Content subset without licensing restrictions. NLM requests this attribution in products that use RxNorm: “This product uses publicly available data courtesy of the U.S. National Library of Medicine (NLM), National Institutes of Health, Department of Health and Human Services; NLM is not responsible for the product and does not endorse or recommend this or any other product.”
- RxNorm Current Prescribable Content is US-centric: NLM describes it as an approximation of prescription drugs marketed in the United States, with some frequently prescribed OTC drugs, and says it excludes drugs exclusively marketed outside the US. Treat it as a country-neutral data model's initial reference seed, not a complete global medicine list. Country-specific brand names, approvals, package sizes, GTINs, and Rx/OTC status must be sourced and validated per market.
- Combination products are intentionally skipped until the data model supports linking one medicinal product to multiple active ingredients.
- Importing reference data does **not** create sellable products, prices, inventory, batches, expiry dates, or dispensing eligibility.

## Run

First validate the downloaded archive without changing the database:

```bash
uv run python scripts/import_rxnorm_catalog.py --dry-run
```

After the database has been migrated and the API environment has database access, run the import:

```bash
uv run python scripts/import_rxnorm_catalog.py
```

The importer streams the archive to a temporary file, checks the archive structure, and is idempotent by canonical ingredient name and RxNorm concept identifier stored in `regulatory_id`. It prints the count of new reference and product rows. Review the logs and record counts before using the data operationally. The dry run reports parsed counts and never writes to the database.
