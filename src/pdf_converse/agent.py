from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple

from .pdf_indexer import PageChunk, PdfIndexer
from .text_utils import extract_keywords, sentence_keyword_score, split_sentences


@dataclass(frozen=True)
class Answer:
    text: str
    citations: List[int]
    refused: bool


class PdfConverseAgent:
    def __init__(self, indexer: PdfIndexer, min_score: float = 0.15, top_k: int = 3) -> None:
        self.indexer = indexer
        self.min_score = min_score
        self.top_k = top_k
        self.history: List[Tuple[str, str]] = []

    def answer(self, question: str) -> Answer:
        matches = self.indexer.query(question, top_k=self.top_k)
        if not matches or matches[0][1] < self.min_score:
            return self._refusal()

        selected = self._select_sentences(question, matches)
        if not selected:
            best_chunk = matches[0][0]
            excerpt = best_chunk.text[:500].rstrip()
            return Answer(text=excerpt, citations=[best_chunk.page_num], refused=False)

        answer_text = " ".join(item[0] for item in selected)
        citations = sorted({item[1] for item in selected})
        return Answer(text=answer_text, citations=citations, refused=False)

    def format_response(self, answer: Answer) -> str:
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

    def _select_sentences(
        self, question: str, matches: Sequence[Tuple[PageChunk, float]]
    ) -> List[Tuple[str, int]]:
        keywords = extract_keywords(question)
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
