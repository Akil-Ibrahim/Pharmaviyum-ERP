"""Core i18n functionality."""
import json
from pathlib import Path
from typing import Optional
from functools import lru_cache
from fastapi import Request


class I18n:
    def __init__(self, default_locale: str = "vi"):
        self.default_locale = default_locale
        self.translations: dict[str, dict[str, str]] = {}
        self._load_translations()
    
    def _load_translations(self):
        locales_dir = Path(__file__).parent / "locales"
        if not locales_dir.exists():
            return
        for locale_file in locales_dir.glob("*.json"):
            locale = locale_file.stem
            try:
                with open(locale_file, encoding="utf-8") as f:
                    self.translations[locale] = json.load(f)
            except Exception as e:
                print(f"Failed to load {locale_file}: {e}")
    
    def t(self, key: str, locale: Optional[str] = None, **kwargs) -> str:
        locale = locale or self.default_locale
        translation = self.translations.get(locale, {}).get(key)
        if not translation:
            translation = self.translations.get(self.default_locale, {}).get(key)
        if not translation:
            translation = self.translations.get("en", {}).get(key)
        if not translation:
            return key
        try:
            return translation.format(**kwargs)
        except (KeyError, IndexError):
            return translation
    
    def get_locale_from_request(self, request: Request) -> str:
        locale = request.headers.get("X-Locale")
        if locale and locale in self.translations:
            return locale
        accept_lang = request.headers.get("Accept-Language", "")
        if accept_lang:
            for lang in accept_lang.split(","):
                base = lang.split(";")[0].strip().lower().split("-")[0]
                if base in self.translations:
                    return base
        return self.default_locale


i18n = I18n(default_locale="vi")


@lru_cache(maxsize=1000)
def translate(key: str, locale: str, **kwargs) -> str:
    return i18n.t(key, locale, **kwargs)
