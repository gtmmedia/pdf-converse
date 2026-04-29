# Evaluator Test Instructions

## Setup
1. Install dependencies:
   - `pip install -r requirements.txt`
2. Set `PYTHONPATH` (PowerShell):
   - `$env:PYTHONPATH="src"`

## Automated Tests
Run:
- `pytest`

Expected:
- All tests pass.

## Manual Evaluation (Sample PDF)
1. Start the CLI:
   - `python -m pdf_converse.console --pdf sample_data/sample.pdf`
2. Use the prompts in [sample_data/sample_queries.md](sample_data/sample_queries.md).

Expected behavior:
- In-scope questions return extractive answers with page citations.
- Out-of-scope questions are refused with an out-of-scope message.

## Manual Evaluation (Web UI)
1. Run Streamlit:
   - `streamlit run streamlit_app.py`
2. Upload `sample_data/sample.pdf`.
3. Ask questions from [sample_data/sample_queries.md](sample_data/sample_queries.md).

Expected behavior:
- Same as CLI: grounded answers with page citations and refusals for out-of-scope queries.
