import 'dart:convert';
import 'package:flutter/services.dart';

class I18nService {
  static String _currentLang = 'pt';
  static Map<String, Map<String, String>> _translations = {};

  static const languages = {
    'pt': {'flag': '\u{1F1E7}\u{1F1F7}', 'name': 'Portugu\u00EAs'},
    'en': {'flag': '\u{1F1FA}\u{1F1F8}', 'name': 'English'},
    'es': {'flag': '\u{1F1EA}\u{1F1F8}', 'name': 'Espa\u00F1ol'},
    'fr': {'flag': '\u{1F1EB}\u{1F1F7}', 'name': 'Fran\u00E7ais'},
  };

  static Future<void> init() async {
    for (final lang in languages.keys) {
      final jsonStr = await rootBundle.loadString('assets/i18n/$lang.json');
      final Map<String, dynamic> data = json.decode(jsonStr);
      _translations[lang] = data.map((k, v) => MapEntry(k, v.toString()));
    }
  }

  static String get currentLanguage => _currentLang;

  static void setLanguage(String lang) {
    if (languages.containsKey(lang)) {
      _currentLang = lang;
    }
  }

  static String t(String key) {
    return _translations[_currentLang]?[key]
        ?? _translations['pt']?[key]
        ?? key;
  }
}
