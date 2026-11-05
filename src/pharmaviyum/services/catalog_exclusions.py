"""Central policy for excluding disallowed manufacturers and country origins."""

import re
from collections.abc import Mapping

_ISRAEL_COUNTRY_VALUES = {
    "il", "isr", "israel", "state of israel", "израиль", "ізраїль",
}
_COUNTRY_KEYS = {
    "country", "authorizationcountry", "authorizationcountryname",
    "manufacturercountry", "countryoforigin", "countryofmanufacture",
    "countryofproduction", "origincountry", "madein",
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
    """Reject Teva and products explicitly identified as Israeli by country metadata."""
    if any(
        value is not None and re.search(r"\bteva\b", str(value), re.IGNORECASE)
        for value in (brand_name, manufacturer)
    ):
        return True

    countries = [authorization_country, manufacturer_country, *_country_values(payload)]
    return any(
        value is not None
        and str(value).strip().casefold() in _ISRAEL_COUNTRY_VALUES
        for value in countries
    )



def allowed_pharmacy_product_conditions():
    """SQL predicates that prevent excluded catalog items from being sold or listed."""
    from sqlalchemy import func, not_, or_, select

    from src.pharmaviyum.models.drug_catalog import MedicinalProduct
    from src.pharmaviyum.models.product import Product

    israel_codes = ("il", "isr", "israel", "state of israel", "израиль", "ізраїль")
    linked_to_excluded_catalog_product = (
        select(MedicinalProduct.id)
        .where(
            MedicinalProduct.id == Product.medicinal_product_id,
            or_(
                func.coalesce(MedicinalProduct.brand_name, "").ilike("%teva%"),
                func.coalesce(MedicinalProduct.manufacturer, "").ilike("%teva%"),
                func.lower(func.trim(MedicinalProduct.authorization_country)).in_(
                    israel_codes
                ),
                func.lower(func.trim(MedicinalProduct.manufacturer_country)).in_(
                    israel_codes
                ),
            ),
        )
        .exists()
    )
    return (
        not_(Product.name.ilike("%teva%")),
        not_(func.coalesce(Product.manufacturer, "").ilike("%teva%")),
        not_(func.lower(func.trim(func.coalesce(Product.manufacturer_country, ""))).in_(israel_codes)),
        not_(linked_to_excluded_catalog_product),
    )
