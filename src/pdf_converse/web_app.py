from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import tempfile
from pathlib import Path
from threading import Lock
from typing import Dict

import streamlit as st

try:
    from .agent import PdfConverseAgent
    from .pdf_indexer import PdfIndexer
    from .language_support import SUPPORTED_LANGUAGES, detect_language
except ImportError:
    from pdf_converse.agent import PdfConverseAgent
    from pdf_converse.pdf_indexer import PdfIndexer
    from pdf_converse.language_support import SUPPORTED_LANGUAGES, detect_language


st.set_page_config(page_title="PDF Converse", page_icon="📄", layout="wide")

st.title("PDF-Constrained Conversational Agent")
st.caption("Upload a PDF and ask questions grounded in its contents.")


@st.cache_resource(show_spinner=False)
def build_indexer() -> PdfIndexer:
    cache_dir = Path(tempfile.gettempdir()) / "pdf_converse_cache"
    return PdfIndexer(cache_dir=cache_dir)


@st.cache_resource(show_spinner=False)
def build_executor() -> ThreadPoolExecutor:
    return ThreadPoolExecutor(max_workers=1)


@st.cache_resource(show_spinner=False)
def build_progress_state() -> Dict[str, object]:
    return {"current": 0, "total": 0, "lock": Lock()}


def _index_pdf_task(indexer: PdfIndexer, pdf_path: str, progress_state: Dict[str, object]) -> None:
    def progress_cb(current: int, total: int) -> None:
        lock = progress_state["lock"]
        with lock:
            progress_state["current"] = current
            progress_state["total"] = total

    indexer.index_pdf(pdf_path, progress_cb=progress_cb)


if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "agent" not in st.session_state:
    st.session_state.agent = None
if "pdf_hash" not in st.session_state:
    st.session_state.pdf_hash = None
if "index_future" not in st.session_state:
    st.session_state.index_future = None
if "index_error" not in st.session_state:
    st.session_state.index_error = None
if "indexing_hash" not in st.session_state:
    st.session_state.indexing_hash = None


uploaded = st.file_uploader("Upload a PDF", type=["pdf"])

col1, col2, col3 = st.columns(3)
with col1:
    language = st.selectbox(
        "Language",
        options=list(SUPPORTED_LANGUAGES.keys()),
        format_func=lambda x: SUPPORTED_LANGUAGES[x],
        index=0,
    )
with col2:
    min_score = st.slider("Refusal threshold", min_value=0.05, max_value=0.6, value=0.15, step=0.05)
with col3:
    top_k = st.slider("Top matches", min_value=1, max_value=5, value=3)

if uploaded is not None:
    file_bytes = uploaded.getvalue()
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    indexer = build_indexer()
    executor = build_executor()
    progress_state = build_progress_state()

    if st.session_state.pdf_hash != file_hash:
        if st.session_state.index_future is None and st.session_state.indexing_hash != file_hash:
            st.session_state.index_error = None
            st.session_state.indexing_hash = file_hash
            with progress_state["lock"]:
                progress_state["current"] = 0
                progress_state["total"] = 0
            st.session_state.index_future = executor.submit(
                _index_pdf_task, indexer, tmp_path, progress_state
            )

        if st.session_state.index_future and st.session_state.index_future.done():
            try:
                st.session_state.index_future.result()
                st.session_state.pdf_hash = st.session_state.indexing_hash
            except Exception as exc:
                st.session_state.index_error = str(exc)
            finally:
                st.session_state.index_future = None

        if st.session_state.index_error:
            st.error(f"Indexing failed: {st.session_state.index_error}")
            st.stop()

        if st.session_state.pdf_hash != file_hash:
            with progress_state["lock"]:
                current = int(progress_state["current"])
                total = int(progress_state["total"])
            if total > 0:
                st.progress(current / total, text=f"Indexing pages {current}/{total}...")
            else:
                st.info("Indexing PDF in background. Click 'Check status' to refresh.")
            st.button("Check status")
            st.stop()

    st.session_state.agent = PdfConverseAgent(
        indexer=indexer,
        min_score=min_score,
        top_k=top_k,
        language=language,
    )

    st.success("PDF indexed. Ask a question below.")

    question = st.text_input("Your question")
    if st.button("Ask") and question.strip():
        agent = st.session_state.agent
        detected_lang = detect_language(question)
        answer = agent.answer(question, language=detected_lang)
        st.session_state.chat_history.append((question, agent.format_response(answer)))

    for user_q, response in reversed(st.session_state.chat_history):
        st.markdown(f"**You:** {user_q}")
        st.markdown(f"**Agent:** {response}")
else:
    st.info("Upload a PDF to get started.")
