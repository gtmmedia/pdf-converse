from __future__ import annotations

import tempfile
from typing import List, Tuple

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
    return PdfIndexer()


if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "agent" not in st.session_state:
    st.session_state.agent = None


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
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded.read())
        tmp_path = tmp.name

    with st.spinner("Indexing PDF..."):
        indexer = build_indexer()
        indexer.index_pdf(tmp_path)
        st.session_state.agent = PdfConverseAgent(indexer=indexer, min_score=min_score, top_k=top_k, language=language)

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
