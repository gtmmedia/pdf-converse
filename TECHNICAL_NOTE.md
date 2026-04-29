# Technical Note

## Architecture
- PDF text extraction with `pypdf`, preserving page boundaries.
- Sentence-based chunking with overlap to keep context while enabling retrieval.
- TF-IDF vectorization for lightweight, deterministic retrieval.
- Extractive answer assembly from top-ranked sentences only.
- Explicit refusal when similarity is below a threshold to enforce grounding.

## Key Decisions
- **TF-IDF over embeddings/LLMs:** deterministic, low-resource, and easy to deploy.
- **Extractive answers only:** prevents hallucinations and enforces PDF-grounded responses.
- **Page-level citations:** robust and simple to compute across arbitrary PDFs.
- **On-disk caching:** avoids re-indexing and keeps response time consistent.
- **Multilingual support:** language detection + stopword-based keyword scoring.

## Trade-offs
- TF-IDF can miss semantic matches; a refusal threshold mitigates false positives.
- Extractive answers are faithful but may be less fluent than generative summaries.
- Page-only citations are less precise than section anchors.
- Large PDFs may increase indexing time and memory usage; max features and float32 reduce this.
