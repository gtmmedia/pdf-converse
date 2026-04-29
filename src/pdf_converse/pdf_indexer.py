from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Callable, List, Sequence, Tuple

from pypdf import PdfReader
import joblib
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
        cache_dir: str | Path | None = None,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_chars = min_chunk_chars
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self._chunks: List[PageChunk] = []
        self._matrix = None

    def load_pdf(
        self,
        pdf_path: str,
        progress_cb: Callable[[int, int], None] | None = None,
    ) -> List[Tuple[int, str]]:
        reader = PdfReader(pdf_path)
        pages: List[Tuple[int, str]] = []
        total = len(reader.pages)
        for idx, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            pages.append((idx, normalize_whitespace(text)))
            if progress_cb:
                progress_cb(idx, total)
        return pages

    def index_pdf(
        self,
        pdf_path: str,
        progress_cb: Callable[[int, int], None] | None = None,
    ) -> None:
        cache_key = self._cache_key(pdf_path)
        if cache_key and self._load_cache(cache_key):
            return

        pages = self.load_pdf(pdf_path, progress_cb=progress_cb)
        self.index_from_texts(pages)
        if progress_cb and pages:
            progress_cb(len(pages), len(pages))
        if cache_key:
            self._save_cache(cache_key)

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

    def _cache_key(self, pdf_path: str) -> str | None:
        if self.cache_dir is None:
            return None
        path = Path(pdf_path)
        if not path.exists():
            return None

        hasher = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(chunk)
        settings = {
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "min_chunk_chars": self.min_chunk_chars,
        }
        digest = hasher.hexdigest()
        settings_hash = hashlib.sha256(json.dumps(settings, sort_keys=True).encode("utf-8")).hexdigest()
        return f"pdf_index_{digest}_{settings_hash}"

    def _cache_path(self, cache_key: str) -> Path:
        assert self.cache_dir is not None
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        return self.cache_dir / f"{cache_key}.joblib"

    def _load_cache(self, cache_key: str) -> bool:
        if self.cache_dir is None:
            return False
        cache_path = self._cache_path(cache_key)
        if not cache_path.exists():
            return False
        payload = joblib.load(cache_path)
        self.vectorizer = payload["vectorizer"]
        self._matrix = payload["matrix"]
        self._chunks = payload["chunks"]
        return True

    def _save_cache(self, cache_key: str) -> None:
        if self.cache_dir is None:
            return
        cache_path = self._cache_path(cache_key)
        payload = {
            "vectorizer": self.vectorizer,
            "matrix": self._matrix,
            "chunks": self._chunks,
        }
        joblib.dump(payload, cache_path)
