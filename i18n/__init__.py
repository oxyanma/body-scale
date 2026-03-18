"""BioScale i18n — Internacionalização com 4 idiomas."""

from i18n import pt, en, es, fr

_current_lang = 'pt'

_translations = {
    'pt': pt.strings,
    'en': en.strings,
    'es': es.strings,
    'fr': fr.strings,
}

LANGUAGES = {
    'pt': {'flag': '🇧🇷', 'name': 'Português'},
    'en': {'flag': '🇺🇸', 'name': 'English'},
    'es': {'flag': '🇪🇸', 'name': 'Español'},
    'fr': {'flag': '🇫🇷', 'name': 'Français'},
}


def t(key):
    """Return translated string for current language, fallback to PT."""
    lang_dict = _translations.get(_current_lang, _translations['pt'])
    return lang_dict.get(key, _translations['pt'].get(key, key))


def set_language(lang_code):
    """Set active language."""
    global _current_lang
    if lang_code in _translations:
        _current_lang = lang_code


def get_language():
    """Get current language code."""
    return _current_lang
