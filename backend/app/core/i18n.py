import gettext
import struct
import threading
from contextvars import ContextVar

from app.core.paths import APP_DIR

_lock = threading.Lock()

LOCALES_DIR = APP_DIR / "locales"

# Context variable to store current locale per request
current_locale: ContextVar[str] = ContextVar("current_locale", default="en")

# Cache for translation objects
_translations = {}


def _(message: str) -> str:
    """
    Dummy function for Babel extraction only.
    NEVER used at runtime.
    """
    return message


def get_translation(locale: str) -> gettext.NullTranslations:
    """Get or create translation object for a locale"""
    with _lock:
        if locale not in _translations:
            try:
                translation = gettext.translation(
                    domain="messages",
                    localedir=str(LOCALES_DIR),
                    languages=[locale],
                    fallback=True,
                )
                _translations[locale] = translation
            except (FileNotFoundError, OSError, struct.error):
                # Fallback to English if translation not found
                _translations[locale] = gettext.NullTranslations()

    return _translations[locale]


def translate(message: str, **kwargs) -> str:
    """
    Translate a message in the current locale with interpolation of placeholders.

    Usage:
        translate("User with email {email} already exists", email="user@example.com")
    """
    locale = current_locale.get()
    translation = get_translation(locale)
    translated = translation.gettext(message)

    if kwargs:
        try:
            translated = translated.format(**kwargs)
        except KeyError:
            pass

    return translated


def translate_plural(singular: str, plural: str, n: int, **kwargs) -> str:
    """
    Translate a pluralizable message based on count.

    Usage:
        translate_plural("{n} object found", "{n} objects found", count, n=count)
    """
    locale = current_locale.get()
    translation = get_translation(locale)
    translated = translation.ngettext(singular, plural, n)

    if kwargs:
        try:
            translated = translated.format(**kwargs)
        except KeyError:
            pass

    return translated


def set_locale(locale: str):
    """Set the current locale for the request"""
    current_locale.set(locale)


def get_locale() -> str:
    """Get the current locale"""
    return current_locale.get()
