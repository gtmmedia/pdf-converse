from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple

from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .text_utils import normalize_whitespace, split_sentences


@dataclass(frozen=True)
class PageChunk:
    page_num: int
    text: str


class PdfIndexer:
    def __init__(
        self,
        chunk_size: int = 800,
        chunk_overlap: int = 200,
        min_chunk_chars: int = 200,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_chars = min_chunk_chars
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self._chunks: List[PageChunk] = []
        self._matrix = None

    def load_pdf(self, pdf_path: str) -> List[Tuple[int, str]]:
        reader = PdfReader(pdf_path)
        pages: List[Tuple[int, str]] = []
        for idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            pages.append((idx + 1, normalize_whitespace(text)))
        return pages

    def index_pdf(self, pdf_path: str) -> None:
        self.index_from_texts(self.load_pdf(pdf_path))

    def index_from_texts(self, pages: Sequence[Tuple[int, str]]) -> None:
        chunks = self._chunk_pages(pages)
        self._chunks = chunks
        if not chunks:
            self._matrix = None
            return
        self._matrix = self.vectorizer.fit_transform([chunk.text for chunk in chunks])

    def query(self, question: str, top_k: int = 3) -> List[Tuple[PageChunk, float]]:
        if not self._chunks or self._matrix is None:
            return []
        q_vec = self.vectorizer.transform([question])
        scores = cosine_similarity(q_vec, self._matrix).flatten()
        best_indices = scores.argsort()[::-1][:top_k]
        return [(self._chunks[i], float(scores[i])) for i in best_indices]

    def _chunk_pages(self, pages: Sequence[Tuple[int, str]]) -> List[PageChunk]:
        chunks: List[PageChunk] = []
        for page_num, text in pages:
            if not text:
                continue
            sentences = split_sentences(text)
            buffer: List[str] = []
            current_len = 0
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                sentence_len = len(sentence)
                if current_len + sentence_len > self.chunk_size and buffer:
                    chunk_text = " ".join(buffer).strip()
                    if len(chunk_text) >= self.min_chunk_chars:
                        chunks.append(PageChunk(page_num=page_num, text=chunk_text))
                    buffer = buffer[-self._overlap_sentence_count(buffer):]
                    current_len = sum(len(s) for s in buffer)
                buffer.append(sentence)
                current_len += sentence_len
            if buffer:
                chunk_text = " ".join(buffer).strip()
                if len(chunk_text) >= self.min_chunk_chars or not chunks:
                    chunks.append(PageChunk(page_num=page_num, text=chunk_text))
        return chunks

    def _overlap_sentence_count(self, buffer: Sequence[str]) -> int:
        if self.chunk_overlap <= 0:
            return 0
        count = 0
        total = 0
        for sentence in reversed(buffer):
            total += len(sentence)
            count += 1
            if total >= self.chunk_overlap:
                break
        return count
