"""Central policy for excluding disallowed manufacturers and country origins."""

import re
from collections.abc import Mapping

_ISRAEL_COUNTRY_VALUES = {
    "il", "isr", "israel", "state of israel", "израиль", "ізраїль",
}
_COUNTRY_KEYS = {
    "country", "authorizationcountry", "authorizationcountryname",
    "manufacturercountry", "countryoforigin", "countryofmanufacture",
    "countryofproduction", "origin_country", "madein",
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
    payload: object = None,
) -> bool:
    """Reject Teva and products explicitly identified as Israeli by country metadata."""
    if any(
        value is not None and re.search(r"\bteva\b", str(value), re.IGNORECASE)
        for value in (brand_name, manufacturer)
    ):
        return True

    countries = [authorization_country, *_country_values(payload)]
    return any(
        value is not None
        and str(value).strip().casefold() in _ISRAEL_COUNTRY_VALUES
        for value in countries
    )
