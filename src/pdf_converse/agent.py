from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple

from .pdf_indexer import PageChunk, PdfIndexer
from .text_utils import extract_keywords, sentence_keyword_score, split_sentences

try:
    from .language_support import detect_language, format_multilingual_response
except ImportError:
    detect_language = None
    format_multilingual_response = None


@dataclass(frozen=True)
class Answer:
    text: str
    citations: List[int]
    refused: bool


class PdfConverseAgent:
    def __init__(
        self,
        indexer: PdfIndexer,
        min_score: float = 0.15,
        top_k: int = 3,
        language: str | None = None,
    ) -> None:
        self.indexer = indexer
        self.min_score = min_score
        self.top_k = top_k
        self.language = language or "en"

    def answer(self, question: str, language: str | None = None) -> Answer:
        self._update_language(question, language)

        matches = self.indexer.query(question, top_k=self.top_k)
        if not matches or matches[0][1] < self.min_score:
            return self._refusal()

        selected = self._select_sentences(question, matches, self.language)
        if not selected:
            best_chunk = matches[0][0]
            excerpt = best_chunk.text[:500].rstrip()
            return Answer(text=excerpt, citations=[best_chunk.page_num], refused=False)

        ordered = self._dedupe_sentences(selected)
        answer_text = "\n".join(f"- {sentence}" for sentence, _page in ordered)
        citations = sorted({page for _sentence, page in ordered})
        return Answer(text=answer_text, citations=citations, refused=False)

    def format_response(self, answer: Answer) -> str:
        if format_multilingual_response:
            return format_multilingual_response(
                answer.text,
                answer.citations,
                self.language,
                answer.refused,
            )
        if answer.refused:
            return f"Answer: {answer.text}\nCitations: none (out of scope)"
        citation_text = ", ".join(f"p.{page}" for page in answer.citations)
        return f"Answer: {answer.text}\nCitations: {citation_text}"

    def _refusal(self) -> Answer:
        return Answer(
            text=(
                "I can only answer using the provided PDF. "
                "I do not have that information."
            ),
            citations=[],
            refused=True,
        )

    def _update_language(self, question: str, language: str | None) -> None:
        if language:
            self.language = language
        elif detect_language:
            self.language = detect_language(question)

    def _select_sentences(
        self,
        question: str,
        matches: Sequence[Tuple[PageChunk, float]],
        language: str = "en",
    ) -> List[Tuple[str, int]]:
        keywords = extract_keywords(question, language)
        candidates: List[Tuple[str, int, int]] = []
        for chunk, _score in matches:
            for sentence in split_sentences(chunk.text):
                cleaned = sentence.strip()
                if not cleaned:
                    continue
                score = sentence_keyword_score(cleaned, keywords)
                if score <= 0:
                    continue
                candidates.append((cleaned, chunk.page_num, score))
        candidates.sort(key=lambda item: item[2], reverse=True)
        return [(sentence, page) for sentence, page, _score in candidates[:3]]

    @staticmethod
    def _dedupe_sentences(items: List[Tuple[str, int]]) -> List[Tuple[str, int]]:
        seen = set()
        deduped = []
        for sentence, page in items:
            normalized = sentence.strip().lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            deduped.append((sentence.strip(), page))
        return deduped
