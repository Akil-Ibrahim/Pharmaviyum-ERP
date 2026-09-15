"""
Internationalization (i18n) support for multi-language applications.

Critical for SEA region:
- Vietnamese (vi) - primary market
- Thai (th) - Thailand market
- Indonesian (id) - Indonesia market
- English (en) - fallback
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

from fastapi import Request


class I18n:
    """Internationalization manager."""

    def __init__(self, default_locale: str = "vi"):
        self.default_locale = default_locale
        self.translations: dict[str, dict[str, str]] = {}
        self._load_translations()

    def _load_translations(self):
        """Load all translation files from locales directory."""
        locales_dir = Path(__file__).parent.parent.parent.parent / "locales"

        if not locales_dir.exists():
            return

        for locale_file in locales_dir.glob("*.json"):
            locale = locale_file.stem
            try:
                with open(locale_file, encoding="utf-8") as f:
                    self.translations[locale] = json.load(f)
            except Exception:
                pass

    def t(self, key: str, locale: Optional[str] = None, **kwargs) -> str:
        """
        Translate a key with variable interpolation.

        Examples:
            i18n.t("patient.created", name="John")
            i18n.t("patient.created", locale="vi", name="Nguyen")
        """
        locale = locale or self.default_locale

        # Try requested locale
        translation = self.translations.get(locale, {}).get(key)

        # Fallback to default locale
        if not translation:
            translation = self.translations.get(self.default_locale, {}).get(key)

        # Fallback to English
        if not translation:
            translation = self.translations.get("en", {}).get(key)

        # Fallback to key itself
        if not translation:
            return key

        # Interpolate variables
        try:
            return translation.format(**kwargs)
        except (KeyError, IndexError):
            return translation

    def get_locale_from_request(self, request: Request) -> str:
        """
        Detect locale from request headers.

        Priority:
        1. X-Locale header (explicit)
        2. Accept-Language header (browser preference)
        3. Default locale
        """
        locale = request.headers.get("X-Locale")
        if locale and locale in self.translations:
            return locale

        accept_language = request.headers.get("Accept-Language", "")
        if accept_language:
            for lang in accept_language.split(","):
                lang = lang.split(";")[0].strip().lower()
                base_locale = lang.split("-")[0]
                if base_locale in self.translations:
                    return base_locale

        return self.default_locale


# Singleton instance
i18n = I18n(default_locale="vi")


@lru_cache(maxsize=1000)
def translate(key: str, locale: str, **kwargs) -> str:
    """Cached translation function for performance."""
    return i18n.t(key, locale, **kwargs)
