from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path

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


def rerun_app() -> None:
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()


with st.sidebar:
    if st.button("Reset app"):
        st.cache_resource.clear()
        st.session_state.clear()
        rerun_app()


@st.cache_resource(show_spinner=False)
def build_indexer() -> PdfIndexer:
    cache_dir = Path(tempfile.gettempdir()) / "pdf_converse_cache"
    return PdfIndexer(cache_dir=cache_dir, max_features=50000)


def save_upload(uploaded) -> tuple[str, str]:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        hasher = hashlib.sha256()
        uploaded.seek(0)
        while True:
            chunk = uploaded.read(1024 * 1024)
            if not chunk:
                break
            tmp.write(chunk)
            hasher.update(chunk)
        uploaded.seek(0)
        return tmp.name, hasher.hexdigest()


def index_pdf_with_progress(indexer: PdfIndexer, pdf_path: str) -> None:
    progress = st.progress(0, text="Extracting PDF pages...")

    def progress_cb(current: int, total: int) -> None:
        if total <= 0:
            return
        progress.progress(current / total, text=f"Extracting pages {current}/{total}...")

    indexer.index_pdf(pdf_path, progress_cb=progress_cb)
    progress.progress(1.0, text="Indexing complete.")


def init_session_state() -> None:
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "agent" not in st.session_state:
        st.session_state.agent = None
    if "pdf_hash" not in st.session_state:
        st.session_state.pdf_hash = None
    if "upload_hash" not in st.session_state:
        st.session_state.upload_hash = None
    if "upload_sig" not in st.session_state:
        st.session_state.upload_sig = None
    if "pdf_path" not in st.session_state:
        st.session_state.pdf_path = None


MAX_UPLOAD_MB = 50


def get_upload_info(uploaded) -> tuple[str, str]:
    signature = (uploaded.name, uploaded.size)

    if st.session_state.upload_sig == signature and st.session_state.pdf_path:
        return st.session_state.pdf_path, st.session_state.upload_hash

    if uploaded.size and uploaded.size > MAX_UPLOAD_MB * 1024 * 1024:
        st.error(f"PDF is too large ({uploaded.size / 1024 / 1024:.1f} MB). Max is {MAX_UPLOAD_MB} MB.")
        st.stop()

    tmp_path, file_hash = save_upload(uploaded)
    st.session_state.upload_sig = signature
    st.session_state.upload_hash = file_hash
    st.session_state.pdf_path = tmp_path
    return tmp_path, file_hash


def ensure_indexed(indexer: PdfIndexer, pdf_path: str, file_hash: str) -> None:
    if st.session_state.pdf_hash == file_hash:
        return

    with st.spinner("Indexing PDF..."):
        try:
            index_pdf_with_progress(indexer, pdf_path)
        except Exception as exc:
            st.error(f"Indexing failed: {exc}")
            st.stop()

    st.session_state.pdf_hash = file_hash
    st.session_state.chat_history = []


init_session_state()


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
    indexer = build_indexer()
    pdf_path, file_hash = get_upload_info(uploaded)
    ensure_indexed(indexer, pdf_path, file_hash)

    st.session_state.agent = PdfConverseAgent(
        indexer=indexer,
        min_score=min_score,
        top_k=top_k,
        language=language,
    )

    if hasattr(indexer, "stats"):
        stats = indexer.stats()
    else:
        stats = {"pages": "n/a", "chunks": "n/a", "cache_hit": "n/a"}
    with st.expander("Index details", expanded=False):
        st.write(f"Pages: {stats['pages']}")
        st.write(f"Chunks: {stats['chunks']}")
        st.write(f"Cache: {'hit' if stats['cache_hit'] else 'miss'}")

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
