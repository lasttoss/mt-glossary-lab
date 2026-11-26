"""The evaluation sets are data, so the rules about them are tested without a model."""
from pathlib import Path

import pytest

from mtgloss import glossary

ROOT = Path(__file__).resolve().parent.parent
SETS = ["dev.tsv", "holdout.tsv"]


def _cases(name: str):
    path = ROOT / "data" / "eval" / name
    rows = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        english, required = line.split("\t")
        rows.append((english, [t.strip() for t in required.split(",") if t.strip()]))
    return rows


@pytest.mark.parametrize("name", SETS)
def test_every_case_has_required_terms(name):
    cases = _cases(name)
    assert len(cases) >= 8
    assert all(required for _, required in cases)


@pytest.mark.parametrize("name", SETS)
def test_sources_are_unique(name):
    sources = [english for english, _ in _cases(name)]
    assert len(sources) == len(set(sources))


@pytest.mark.parametrize("name", SETS)
def test_required_terms_are_glossary_targets(name):
    targets = {r.right.lower() for r in glossary.load()}
    for english, required in _cases(name):
        for term in required:
            assert term.lower() in targets, f"{term!r} is required but no rule produces it ({english!r})"


def test_holdout_does_not_reuse_a_dev_sentence():
    dev = {english for english, _ in _cases("dev.tsv")}
    holdout = {english for english, _ in _cases("holdout.tsv")}
    assert not dev & holdout
