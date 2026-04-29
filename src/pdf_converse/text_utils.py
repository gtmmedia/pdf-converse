from __future__ import annotations

import re
from typing import Iterable, List, Sequence, Tuple


def normalize_whitespace(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_sentences(text: str) -> List[str]:
    text = text.replace("\n", " ")
    return re.split(r"(?<=[.!?])\s+", text)


def extract_keywords(text: str) -> List[str]:
    sanitized = re.sub(r"[^a-zA-Z0-9\s]", " ", text.lower())
    return [word for word in sanitized.split() if len(word) > 2]


def sentence_keyword_score(sentence: str, keywords: Sequence[str]) -> int:
    sentence_lower = sentence.lower()
    return sum(1 for keyword in keywords if keyword in sentence_lower)
