"""BioScale i18n — English only."""

from i18n import en

_strings = en.strings

LANGUAGES = {'en': {'flag': '🇺🇸', 'name': 'English'}}


def t(key):
    """Return English string for key."""
    return _strings.get(key, key)


def set_language(lang_code):
    pass


def get_language():
    return 'en'
