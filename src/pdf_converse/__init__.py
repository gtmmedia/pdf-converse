"""PDF-constrained conversational agent package."""

from importlib import import_module

__all__ = ["Answer", "PageChunk", "PdfConverseAgent", "PdfIndexer"]


def __getattr__(name: str):
    if name in {"Answer", "PdfConverseAgent"}:
        module = import_module(".agent", __name__)
        return getattr(module, name)
    if name in {"PageChunk", "PdfIndexer"}:
        module = import_module(".pdf_indexer", __name__)
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
