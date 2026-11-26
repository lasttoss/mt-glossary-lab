import pytest

from mtgloss import glossary
from mtgloss.glossary import Rule


def test_load_skips_comments_and_blank_lines():
    rules = glossary.load()
    assert rules
    assert all(isinstance(r, Rule) for r in rules)


def test_whole_word_only():
    rules = [Rule("server", "server")]
    out, fired = glossary.apply("a serverless function", rules)
    assert out == "a serverless function"
    assert fired == []


def test_rewrites_whole_word_case_insensitively():
    rules = [Rule("máy chủ", "server")]
    out, fired = glossary.apply("Máy chủ đã chết", rules)
    assert out == "server đã chết"
    assert fired == ["máy chủ -> server"]


def test_reports_every_fired_rule_in_file_order():
    rules = [Rule("triển khai", "deploy"), Rule("máy chủ", "server")]
    out, fired = glossary.apply("triển khai lên máy chủ", rules)
    assert out == "deploy lên server"
    assert fired == ["triển khai -> deploy", "máy chủ -> server"]


def test_apply_is_idempotent_when_target_is_not_a_source_word():
    rules = [Rule("triển khai", "deploy")]
    once, _ = glossary.apply("triển khai", rules)
    twice, fired = glossary.apply(once, rules)
    assert twice == once
    assert fired == []


def test_bad_line_raises(tmp_path):
    bad = tmp_path / "glossary.tsv"
    bad.write_text("only-one-column\n", encoding="utf-8")
    with pytest.raises(ValueError):
        glossary.load(bad)
