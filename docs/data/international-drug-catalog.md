# International drug catalog import

Pharmaviyum has separate **Drug Reference**, **Medicinal Product**, and local **Product / inventory** entities. The international reference catalog is not pharmacy stock.

## Initial source: NLM RxNorm Current Prescribable Content

The importer downloads the current prescribable RxNorm archive from the U.S. National Library of Medicine and loads single-ingredient clinical and branded drug concepts into `drug_references`, `drug_reference_ingredients`, and `medicinal_products`.

- Source: https://www.nlm.nih.gov/research/umls/rxnorm/docs/rxnormfiles.html
- The NLM documents the Current Prescribable Content subset as available without a license.
- RxNorm is a useful normalized clinical-drug vocabulary, not a complete worldwide trade-name or regulatory-registration database. Country-specific brand names, approvals, package sizes, GTINs, and Rx/OTC status must be sourced and validated per market.
- Combination products are intentionally skipped until the data model supports linking one medicinal product to multiple active ingredients.
- Importing reference data does **not** create sellable products, prices, inventory, batches, expiry dates, or dispensing eligibility.

## Run

After the database has been migrated and the API environment has database access:

```bash
uv run python scripts/import_rxnorm_catalog.py
```

The importer is idempotent by canonical ingredient name and RxNorm concept identifier stored in `regulatory_id`. It prints the count of new reference and product rows. Review the logs and record counts before using the data operationally.
