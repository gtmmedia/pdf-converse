# PDF-Constrained Conversational Agent

## Technical Note
This agent uses a two-stage, strictly grounded pipeline. It extracts text from the PDF with `pypdf`, chunks by sentence into page-bound segments, embeds chunks with TF-IDF, and retrieves the top matching chunks for each question. Answers are constructed extractively from the retrieved sentences only; if similarity is below a threshold, it refuses. This avoids model hallucination by never generating content not present in the PDF, at the cost of reduced fluency compared to a generative LLM.

Trade-offs:
- TF-IDF is lightweight and deterministic, but can miss semantic matches; the threshold helps enforce refusals.
- Extractive answers are faithful but may be less polished than abstractive summaries.
- Page-number-only citations are simple and robust but do not provide section anchors.

## Quick Start
1. Install dependencies:
   - `pip install -r requirements.txt`
2. Run the CLI:
   - PowerShell:
     - `$env:PYTHONPATH="src"`
   - `python -m pdf_converse.console --pdf sample_data/sample.pdf`
3. Ask questions. Type `exit` to quit.

## Simple Web UI
1. Install dependencies:
   - `pip install -r requirements.txt`
2. Run the app:
   - PowerShell:
     - `$env:PYTHONPATH="src"`
     - `streamlit run src/pdf_converse/web_app.py`
3. Upload a PDF and ask questions.

## Test Instructions (Evaluators)
1. Install dependencies:
   - `pip install -r requirements.txt`
2. Run tests:
   - PowerShell:
     - `$env:PYTHONPATH="src"`
     - `pytest`
3. Manual evaluation with the sample PDF:
   - Start the CLI with `python -m pdf_converse.console --pdf sample_data/sample.pdf`
   - Use the queries in [sample_data/sample_queries.md](sample_data/sample_queries.md)
   - Expected behavior:
     - Valid queries return extracted statements from the PDF with page citations.
     - Invalid queries are refused with an out-of-scope notice.

## Files
- Sample PDF: [sample_data/sample.pdf](sample_data/sample.pdf)
- Query list: [sample_data/sample_queries.md](sample_data/sample_queries.md)

## Notes on Grounding
Answers are constructed only from text retrieved from the PDF. If the similarity score is too low, the agent refuses. This enforces strict grounding and reduces hallucination risk.

## Observability and Testability
- The web UI shows index stats (page count, chunk count, cache hit) under "Index details."
- Tests are data-driven via JSON case files in [tests/cases](tests/cases).
- You can add external test suites via `PDF_CONVERSE_TEST_CASES_DIR` or `PDF_CONVERSE_TEST_CASES`.

## Deployment Notes
- Streamlit Cloud entry point: `streamlit_app.py`.
- Cached indexes are stored in the system temp directory to speed up re-runs.
