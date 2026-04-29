from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import pytest

from pdf_converse.agent import PdfConverseAgent
from pdf_converse.pdf_indexer import PdfIndexer


CASES_DIR = Path(__file__).parent / "cases"


def _collect_case_files() -> List[Path]:
    files = list(CASES_DIR.glob("*.json"))

    extra_dir = os.environ.get("PDF_CONVERSE_TEST_CASES_DIR")
    if extra_dir:
        files.extend(Path(extra_dir).glob("*.json"))

    extra_files = os.environ.get("PDF_CONVERSE_TEST_CASES")
    if extra_files:
        for item in extra_files.split(os.pathsep):
            item = item.strip()
            if item:
                files.append(Path(item))

    unique: List[Path] = []
    seen = set()
    for file_path in files:
        if not file_path.exists():
            continue
        resolved = file_path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(file_path)
    return sorted(unique)


def _load_datasets() -> List[Dict[str, Any]]:
    datasets: List[Dict[str, Any]] = []
    for file_path in _collect_case_files():
        raw = json.loads(file_path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            raw = [raw]
        for dataset in raw:
            dataset = dict(dataset)
            dataset["_case_file"] = file_path
            datasets.append(dataset)
    return datasets


_DATASETS = _load_datasets()
if not _DATASETS:
    pytest.skip("No external case files found.", allow_module_level=True)

_INDEXER_CACHE: Dict[Tuple[str, str], PdfIndexer] = {}


def _build_indexer(dataset: Dict[str, Any]) -> PdfIndexer:
    case_file = Path(dataset["_case_file"])
    indexer_config = dataset.get("indexer", {})
    cache_key = (str(case_file.resolve()), json.dumps(indexer_config, sort_keys=True))
    if cache_key in _INDEXER_CACHE:
        return _INDEXER_CACHE[cache_key]

    indexer = PdfIndexer(**indexer_config)
    if "pdf_path" in dataset:
        pdf_path = (case_file.parent / dataset["pdf_path"]).resolve()
        indexer.index_pdf(str(pdf_path))
    else:
        pages = dataset.get("pages", [])
        indexer.index_from_texts(pages)

    _INDEXER_CACHE[cache_key] = indexer
    return indexer


def _iter_cases() -> Iterable[Tuple[Dict[str, Any], Dict[str, Any]]]:
    for dataset in _DATASETS:
        for case in dataset.get("cases", []):
            yield dataset, case


def _case_id(dataset: Dict[str, Any], case: Dict[str, Any]) -> str:
    name = dataset.get("name", "dataset")
    case_id = case.get("id") or case.get("question", "case")
    return f"{name}::{case_id}"


_PARAM_CASES = [
    pytest.param(dataset, case, id=_case_id(dataset, case))
    for dataset, case in _iter_cases()
]


@pytest.mark.parametrize("dataset,case", _PARAM_CASES)
def test_case_from_file(dataset: Dict[str, Any], case: Dict[str, Any]) -> None:
    indexer = _build_indexer(dataset)
    min_score = case.get("min_score", dataset.get("min_score", 0.1))
    top_k = case.get("top_k", dataset.get("top_k", 3))
    agent = PdfConverseAgent(indexer=indexer, min_score=min_score, top_k=top_k)

    question = case["question"]
    answer = agent.answer(question)

    expect_refusal = case.get("expect_refusal")
    assert expect_refusal is not None
    assert answer.refused is expect_refusal

    if expect_refusal:
        assert answer.citations == []
        return

    for page in case.get("must_cite", []):
        assert page in answer.citations
    for snippet in case.get("must_include", []):
        assert snippet.lower() in answer.text.lower()
