"""Compatibility helpers for the origin-neutral medicine catalog policy.

Manufacturer and country of origin are descriptive metadata, not exclusion
criteria. Teva and Israeli-origin medicines remain eligible for reference,
product, POS, inventory and pharmacy workflows.
"""

# Retained for compatibility with callers/tests from older releases. It is
# deliberately false and no helper below enforces origin-based exclusions.
CATALOG_EXCLUSIONS_ENABLED = False


def is_excluded_catalog_entry(
    *,
    brand_name: object = None,
    manufacturer: object = None,
    authorization_country: object = None,
    manufacturer_country: object = None,
    payload: object = None,
) -> bool:
    """Never exclude a medicine based on brand, manufacturer or geography."""
    return False


def allowed_pharmacy_product_conditions() -> tuple[()]:
    """No manufacturer/country predicates apply to pharmacy product queries."""
    return ()


def allowed_medicinal_product_conditions() -> tuple[()]:
    """No manufacturer/country predicates apply to reference catalog queries."""
    return ()
