"""
i18n utilities — simple JSON-based translation system.

Translations stored in: app/static/locales/{lang}.json
Falls back to English if key missing in target language.
"""

import json
from functools import lru_cache
from pathlib import Path

from flask import request, session

LOCALES_DIR = Path(__file__).parent.parent / "static" / "locales"
SUPPORTED = ["en", "ta", "hi"]


@lru_cache(maxsize=10)
def _load_locale(lang: str) -> dict:
    path = LOCALES_DIR / f"{lang}.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def get_locale() -> str:
    """Determine active locale from session, query param, or Accept-Language."""
    if "lang" in session:
        lang = session["lang"]
    elif "lang" in request.args:
        lang = request.args["lang"]
        session["lang"] = lang
    else:
        lang = request.accept_languages.best_match(SUPPORTED) or "en"
    return lang if lang in SUPPORTED else "en"


def get_translations() -> "TranslationProxy":
    locale = get_locale()
    strings = _load_locale(locale)
    fallback = _load_locale("en")
    return TranslationProxy(strings, fallback)


class TranslationProxy:
    """Allows template usage: {{ t('key') }} or {{ t.key }}"""

    def __init__(self, strings: dict, fallback: dict) -> None:
        self._strings = strings
        self._fallback = fallback

    def __call__(self, key: str, **kwargs) -> str:
        text = self._strings.get(key) or self._fallback.get(key, key)
        if kwargs:
            try:
                return text.format(**kwargs)
            except KeyError:
                pass
        return text

    def __getattr__(self, key: str) -> str:
        return self(key)
