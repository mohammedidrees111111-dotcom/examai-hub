import re

_RE_SCRIPT = re.compile(r'[\u0600-\u06FF]')
_RE_LATIN = re.compile(r'[a-zA-Z]')
_RE_CYRILLIC = re.compile(r'[\u0400-\u04FF]')
_RE_HAN = re.compile(r'[\u4E00-\u9FFF]')
_RE_HANGUL = re.compile(r'[\uAC00-\uD7AF]')
_RE_JAPANESE = re.compile(r'[\u3040-\u309F\u30A0-\u30FF]')
_RE_DEVANAGARI = re.compile(r'[\u0900-\u097F]')

LANG_DATA = None


def _load_lang_data():
    global LANG_DATA
    if LANG_DATA is None:
        from app.services.language_data import LANGUAGE_DATA
        LANG_DATA = LANGUAGE_DATA


def detect_language(text: str) -> str:
    _load_lang_data()
    sample = text[:3000]
    scripts = {
        "ar": len(_RE_SCRIPT.findall(sample)),
        "latn": len(_RE_LATIN.findall(sample)),
        "cyrl": len(_RE_CYRILLIC.findall(sample)),
        "han": len(_RE_HAN.findall(sample)),
        "hang": len(_RE_HANGUL.findall(sample)),
        "jpan": len(_RE_JAPANESE.findall(sample)),
        "deva": len(_RE_DEVANAGARI.findall(sample)),
    }
    dominant = max(scripts, key=scripts.get)
    if scripts[dominant] == 0:
        return "en"

    if dominant == "latn":
        return _detect_latin_language(sample)
    script_to_lang = {"ar": "ar", "cyrl": "ru", "han": "zh", "hang": "ko", "jpan": "ja", "deva": "hi"}
    return script_to_lang.get(dominant, "en")


def _detect_latin_language(text: str) -> str:
    samples = {
        "en": {"the", "and", "for", "are", "that", "with", "have", "this", "from", "they"},
        "es": {"que", "los", "las", "por", "con", "para", "como", "una", "del", "muy"},
        "fr": {"que", "les", "pas", "dans", "pour", "sur", "avec", "tout", "plus", "bien"},
        "de": {"und", "die", "der", "das", "ist", "mit", "auf", "von", "sich", "auch"},
        "pt": {"que", "com", "uma", "para", "dos", "muito", "mais", "pelo", "isso", "este"},
        "it": {"che", "una", "sono", "con", "come", "per", "nel", "piu", "dal", "degli"},
        "tr": {"bir", "ve", "bu", "icin", "gibi", "daha", "olarak", "kadar", "sonra", "cok"},
    }
    words = set(re.findall(r'\b\w{2,}\b', text.lower()))
    best_lang, best_score = "en", 0
    for lang, common in samples.items():
        score = len(words & common)
        if score > best_score:
            best_score = score
            best_lang = lang
    return best_lang


def get_lang_data(lang: str) -> dict:
    _load_lang_data()
    return LANG_DATA.get(lang, LANG_DATA.get("en", {}))


def lang_format(lang: str, key: str, **kwargs) -> str:
    data = get_lang_data(lang)
    ui = data.get("ui_strings", {})
    template = ui.get(key, LANG_DATA.get("en", {}).get("ui_strings", {}).get(key, str(kwargs)))
    if isinstance(template, str):
        return template.format(**kwargs)
    return str(kwargs)


def get_stop_words(lang: str) -> frozenset:
    data = get_lang_data(lang)
    return data.get("stop_words", frozenset())


def get_definition_pattern(lang: str) -> str:
    data = get_lang_data(lang)
    triggers = data.get("definition_triggers", [])
    en_data = LANG_DATA.get("en", {})
    en_triggers = en_data.get("definition_triggers", [])
    all_triggers = list(dict.fromkeys(triggers + en_triggers))
    return "|".join(re.escape(t) for t in all_triggers[:10])


def get_emphasis_signals(lang: str) -> list:
    data = get_lang_data(lang)
    return data.get("emphasis_signals", [])


def get_comparison_triggers(lang: str) -> str:
    data = get_lang_data(lang)
    triggers = data.get("comparison_triggers", [])
    return "|".join(re.escape(t) for t in triggers)


def get_exception_triggers(lang: str) -> str:
    data = get_lang_data(lang)
    triggers = data.get("exception_triggers", [])
    return "|".join(re.escape(t) for t in triggers)


def get_sentence_separator(lang: str) -> str:
    data = get_lang_data(lang)
    return data.get("sentence_separator", ". ")


def get_min_word_length(lang: str) -> int:
    data = get_lang_data(lang)
    return data.get("min_word_length", 4)
