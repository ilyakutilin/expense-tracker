import gettext
from contextvars import ContextVar
from pathlib import Path

# Context variable to store current locale per request
current_locale: ContextVar[str] = ContextVar("current_locale", default="en")

# Path to translations
LOCALES_DIR = Path(__file__).parent / "locales"

# Cache for translation objects
_translations = {}


def get_translation(locale: str):
    """Get or create translation object for a locale"""
    if locale not in _translations:
        try:
            translation = gettext.translation(
                domain="messages",
                localedir=str(LOCALES_DIR),
                languages=[locale],
                fallback=True,
            )
            _translations[locale] = translation
        except FileNotFoundError:
            # Fallback to English if translation not found
            _translations[locale] = gettext.NullTranslations()

    return _translations[locale]


def _(message: str, **kwargs) -> str:
    """
    Translate a message in the current locale with placeholder support.

    Usage:
        _("User with email {email} already exists", email="user@example.com")
    """
    locale = current_locale.get()
    translation = get_translation(locale)
    translated = translation.gettext(message)

    # Handle placeholders
    if kwargs:
        translated = translated.format(**kwargs)

    return translated


def set_locale(locale: str):
    """Set the current locale for the request"""
    current_locale.set(locale)


def get_locale() -> str:
    """Get the current locale"""
    return current_locale.get()
