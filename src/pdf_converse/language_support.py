from __future__ import annotations

import re
from typing import Dict, List, Set

try:
    from langdetect import detect, LangDetectException
except ImportError:
    detect = None
    LangDetectException = Exception


SUPPORTED_LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "zh-cn": "Chinese (Simplified)",
    "ja": "Japanese",
    "pt": "Portuguese",
    "ru": "Russian",
}

STOPWORDS_BY_LANGUAGE: Dict[str, Set[str]] = {
    "en": {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
        "do", "does", "did", "will", "would", "should", "could", "may", "might",
        "can", "must", "shall", "of", "as", "by", "with", "from", "it", "this",
        "that", "these", "those", "i", "you", "he", "she", "we", "they", "what",
        "which", "who", "when", "where", "why", "how",
    },
    "es": {
        "el", "la", "de", "que", "y", "a", "en", "un", "ser", "se", "no", "haber",
        "por", "con", "su", "para", "está", "están", "estoy", "eres", "somos", "sois",
        "me", "te", "le", "nos", "os", "les", "mío", "tuyo", "suyo", "nuestro", "vuestro",
    },
    "fr": {
        "le", "la", "de", "et", "à", "en", "un", "être", "se", "ne", "pas",
        "avoir", "pour", "avec", "par", "ce", "il", "qui", "que", "est", "sont",
        "je", "tu", "il", "nous", "vous", "elles", "mon", "ton", "son", "notre", "votre",
    },
    "de": {
        "der", "die", "das", "und", "in", "den", "von", "zu", "das", "mit", "sich",
        "des", "auf", "für", "ist", "im", "dem", "nicht", "ein", "eine", "als",
        "auch", "es", "an", "werden", "aus", "er", "hat", "dass", "sie", "nach",
    },
}


def detect_language(text: str) -> str:
    if detect is None:
        return "en"
    try:
        lang = detect(text)
        return lang if lang in SUPPORTED_LANGUAGES else "en"
    except (LangDetectException, Exception):
        return "en"


def get_stopwords(language: str) -> Set[str]:
    return STOPWORDS_BY_LANGUAGE.get(language, STOPWORDS_BY_LANGUAGE["en"])


def multilingual_keywords(text: str, language: str | None = None) -> List[str]:
    if language is None:
        language = detect_language(text)
    
    sanitized = re.sub(r"[^a-zA-Z0-9\s\u4e00-\u9fff\u3040-\u309f]", " ", text.lower())
    words = sanitized.split()
    stopwords = get_stopwords(language)
    return [w for w in words if len(w) > 2 and w not in stopwords]


def format_multilingual_response(
    answer_text: str,
    citations: List[int],
    language: str,
    refused: bool = False,
) -> str:
    if refused:
        messages = {
            "en": "Answer: {text}\nCitations: none (out of scope)",
            "es": "Respuesta: {text}\nCitas: ninguna (fuera de alcance)",
            "fr": "Réponse: {text}\nCitations: aucune (hors de portée)",
            "de": "Antwort: {text}\nZitate: keine (außerhalb des Umfangs)",
            "pt": "Resposta: {text}\nCitações: nenhuma (fora do escopo)",
            "zh-cn": "答案: {text}\n引用: 无 (超出范围)",
            "ja": "回答: {text}\n引用: なし (スコープ外)",
            "ru": "Ответ: {text}\nЦитаты: нет (вне области)",
        }
        template = messages.get(language, messages["en"])
        return template.format(text=answer_text)
    
    citation_label = {
        "en": "Citations",
        "es": "Citas",
        "fr": "Citations",
        "de": "Zitate",
        "pt": "Citações",
        "zh-cn": "引用",
        "ja": "引用",
        "ru": "Цитаты",
    }.get(language, "Citations")
    
    citation_text = ", ".join(f"p.{page}" for page in citations)
    return f"Answer: {answer_text}\n{citation_label}: {citation_text}"
