"""Legacy policy for local pharmacy-product workflows.

International reference-catalog ingestion, review, matching and search must not
apply manufacturer or country exclusions. Pharmacy-product predicates remain
isolated for legacy local POS/product eligibility behavior.
"""

import re
from collections.abc import Mapping

# Legacy local pharmacy-product eligibility policy; never use for reference-catalog ingestion/search.
CATALOG_EXCLUSIONS_ENABLED = True

_ISRAEL_COUNTRY_VALUES = {
    "il",
    "isr",
    "israel",
    "state of israel",
    "израиль",
    "ізраїль",
}
_COUNTRY_KEYS = {
    "country",
    "countryname",
    "holdercountry",
    "holdercountryname",
    "marketingauthorizationholdercountry",
    "marketingauthorisationholdercountry",
    "countryofholder",
    "countryofmanufacturer",
    "countryofmanufacturing",
    "manufacturingcountry",
    "countrywhereproduced",
    "productioncountry",
    "countryofregistration",
    "registrationcountry",
    "authorizationterritory",
    "authorisationterritory",
    "territoryofauthorization",
    "territoryofauthorisation",
    "authorizationcountry",
    "authorizationcountryname",
    "countryofauthorization",
    "countrywhereauthorised",
    "countrywhereauthorized",
    "countryofmarketingauthorisation",
    "countryofmarketingauthorization",
    "marketingauthorisationcountry",
    "marketingauthorizationcountry",
    "manufacturercountry",
    "countryoforigin",
    "countryofmanufacture",
    "countryofproduction",
    "origincountry",
    "madein",
}


def _normalise_key(value: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).casefold())


def _country_values(payload: object):
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            if _normalise_key(key) in _COUNTRY_KEYS and value is not None:
                if isinstance(value, (list, tuple, set)):
                    yield from value
                else:
                    yield value
            yield from _country_values(value)
    elif isinstance(payload, (list, tuple, set)):
        for value in payload:
            yield from _country_values(value)


def is_excluded_catalog_entry(
    *,
    brand_name: object = None,
    manufacturer: object = None,
    authorization_country: object = None,
    manufacturer_country: object = None,
    payload: object = None,
) -> bool:
    """Return whether a local pharmacy-product entry matches the legacy policy."""
    if not CATALOG_EXCLUSIONS_ENABLED:
        return False

    if any(
        value is not None and re.search(r"teva", str(value), re.IGNORECASE)
        for value in (brand_name, manufacturer)
    ):
        return True

    countries = [authorization_country, manufacturer_country, *_country_values(payload)]

    def is_israeli_country(value: object) -> bool:
        country = str(value).strip().casefold()
        if country in _ISRAEL_COUNTRY_VALUES or "israel" in country:
            return True
        return bool(re.search(r"(?<![a-z])(?:il|isr)(?![a-z])", country))

    return any(value is not None and is_israeli_country(value) for value in countries)


def allowed_pharmacy_product_conditions():
    """SQL predicates that prevent excluded medicines from entering pharmacy workflows."""
    if not CATALOG_EXCLUSIONS_ENABLED:
        return ()

    from sqlalchemy import func, not_, or_, select

    from src.pharmaviyum.models.drug_catalog import MedicinalProduct
    from src.pharmaviyum.models.product import Product

    israel_codes = ("il", "isr", "israel", "state of israel", "израиль", "ізраїль")

    def israeli_country_clause(column):
        normalized = func.lower(func.trim(func.coalesce(column, "")))
        return or_(
            normalized.in_(israel_codes),
            normalized.ilike("%israel%"),
            normalized.op("~*")(r"(^|[^a-z])(il|isr)([^a-z]|$)"),
        )

    linked_to_excluded_catalog_product = (
        select(MedicinalProduct.id)
        .where(
            MedicinalProduct.id == Product.medicinal_product_id,
            or_(
                func.coalesce(MedicinalProduct.brand_name, "").ilike("%teva%"),
                func.coalesce(MedicinalProduct.manufacturer, "").ilike("%teva%"),
                israeli_country_clause(MedicinalProduct.authorization_country),
                israeli_country_clause(MedicinalProduct.manufacturer_country),
            ),
        )
        .exists()
    )
    return (
        not_(Product.name.ilike("%teva%")),
        not_(func.coalesce(Product.manufacturer, "").ilike("%teva%")),
        not_(israeli_country_clause(Product.manufacturer_country)),
        not_(linked_to_excluded_catalog_product),
    )


def allowed_medicinal_product_conditions():
    """Deprecated compatibility helper: reference catalog has no origin exclusions."""
    return ()
