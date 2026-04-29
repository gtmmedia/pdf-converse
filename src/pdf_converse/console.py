from __future__ import annotations

import argparse

from .agent import PdfConverseAgent
from .pdf_indexer import PdfIndexer


def main() -> None:
    parser = argparse.ArgumentParser(description="PDF-constrained conversational agent")
    parser.add_argument("--pdf", required=True, help="Path to the PDF file")
    parser.add_argument("--top-k", type=int, default=3, help="Top matches to consider")
    parser.add_argument(
        "--min-score", type=float, default=0.15, help="Minimum similarity to answer"
    )
    args = parser.parse_args()

    indexer = PdfIndexer()
    indexer.index_pdf(args.pdf)

    agent = PdfConverseAgent(indexer=indexer, min_score=args.min_score, top_k=args.top_k)
    print("PDF loaded. Ask a question, or type 'exit' to quit.")

    while True:
        try:
            question = input("You: ").strip()
        except EOFError:
            break
        if not question:
            continue
        if question.lower() in {"exit", "quit"}:
            break
        answer = agent.answer(question)
        print(agent.format_response(answer))


if __name__ == "__main__":
    main()
