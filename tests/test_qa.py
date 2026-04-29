from pdf_converse.agent import PdfConverseAgent
from pdf_converse.pdf_indexer import PdfIndexer


def build_indexer():
    indexer = PdfIndexer(min_chunk_chars=20)
    indexer.index_from_texts(
        [
            (1, "Rule A: Wear insulated gloves. Rule B: Keep device dry."),
            (2, "Inspect monthly; replace filter every 6 months."),
        ]
    )
    return indexer


def test_refuses_when_out_of_scope():
    indexer = build_indexer()
    agent = PdfConverseAgent(indexer=indexer, min_score=0.6)
    answer = agent.answer("What is the company stock price?")
    assert answer.refused is True
    assert answer.citations == []


def test_answers_with_citation():
    indexer = build_indexer()
    agent = PdfConverseAgent(indexer=indexer, min_score=0.1)
    answer = agent.answer("What should I wear?")
    assert answer.refused is False
    assert 1 in answer.citations
    assert "gloves" in answer.text.lower()
