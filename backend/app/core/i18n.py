import gettext
import struct
import threading
from contextvars import ContextVar
from typing import LiteralString, Self

from app.core.paths import APP_DIR

_lock = threading.Lock()

LOCALES_DIR = APP_DIR / "locales"

# Context variable to store current locale per request
current_locale: ContextVar[str] = ContextVar("current_locale", default="en")

# Cache for translation objects
_translations = {}


class TranslatableMessage:
    def __init__(
        self,
        singular: LiteralString,
        plural: LiteralString | None = None,
        n: int | None = None,
        n_key: str | None = None,
        **kwargs,
    ) -> None:
        self.singular = singular
        self.plural = plural
        self.n = n
        self.n_key = n_key
        self.kwargs = kwargs

    def is_plural_type(self) -> bool:
        return self.plural is not None and self.n is not None

    def is_valid(self) -> bool:
        if self.plural is not None and self.n is None and self.n_key is None:
            return False

        str_to_check: str = self.singular
        if self.is_plural_type() and self.n != 1:
            assert self.plural is not None
            str_to_check = self.plural

        try:
            str_to_check.format(**self.kwargs)
            return True
        except KeyError:
            return False

    def set_n(self, n: int) -> Self:
        self.n = n
        return self

    def set_kwargs(self, **kwargs) -> Self:
        self.kwargs = kwargs
        return self

    def to_dict(self):
        return {
            "singular": self.singular,
            "plural": self.plural,
            "n": self.n,
            "n_key": self.n_key,
            "kwargs": self.kwargs,
            "is_plural_type": self.is_plural_type(),
            "is_valid": self.is_valid(),
        }


def _(message: LiteralString) -> TranslatableMessage:
    """
    Dummy function for Babel extraction only (single message template).
    NEVER used at runtime.
    """
    return TranslatableMessage(message)


def n_(
    singular: LiteralString, plural: LiteralString, n_key: str | None = None
) -> TranslatableMessage:
    """
    Dummy function for Babel extraction only (singular and plural message template).
    NEVER used at runtime.
    """
    return TranslatableMessage(singular, plural, n_key=n_key)


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


def translate(tm: TranslatableMessage) -> str:
    """
    Translate a message in the current locale with interpolation of placeholders.
    """
    locale = current_locale.get()
    translation = get_translation(locale)

    translated: str = ""

    if tm.is_plural_type():
        assert tm.plural is not None and tm.n is not None
        translated = translation.ngettext(tm.singular, tm.plural, tm.n)
    else:
        translated = translation.gettext(tm.singular)

    try:
        translated = translated.format(**tm.kwargs)
    except KeyError:
        # TODO: Returns a string with {placeholders} - might be an issue
        pass

    return translated


def set_locale(locale: str):
    """Set the current locale for the request"""
    current_locale.set(locale)


def get_locale() -> str:
    """Get the current locale"""
    return current_locale.get()
