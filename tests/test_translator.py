"""Full path with a stub translator, so no model or network is needed."""
from mtgloss import glossary, postprocess, translator


def _path(text, live=False):
    rules = glossary.load()
    return translator.to_vi(text, translator.StubTranslator(), rules, live=live)


def test_empty_input_short_circuits():
    out = _path("")
    assert out == {"source": "", "raw": "", "text": "", "fired": []}


def test_repetition_is_cut_before_the_term_table(monkeypatch):
    repeated = "deploy xong thi bao toi " * 3
    out = _path(repeated)
    # The guard keeps everything up to the end of the first repeated n-gram, then stops.
    assert len(out["text"].split()) < len(repeated.split())
    assert out["text"].startswith("deploy xong thi bao toi")


class LoopingTranslator:
    """A short source line that the model answers with a wall of repeated words."""

    def raw(self, text, src="en"):
        return "một " * 60


def test_live_line_is_capped_and_final_line_is_not():
    rules = glossary.load()
    source = "we deploy on friday"  # 4 words, so the cap is 1.8 * 4 + 6 = 13
    live = translator.to_vi(source, LoopingTranslator(), rules, live=True)["text"]
    final = translator.to_vi(source, LoopingTranslator(), rules, live=False)["text"]
    assert len(live.split()) == 13
    assert len(final.split()) > len(live.split())


def test_term_table_patches_and_reports():
    rules = [glossary.Rule("máy chủ", "server")]
    out = translator.to_vi("máy chủ chết", translator.StubTranslator(), rules)
    assert out["text"] == "server chết"
    assert out["fired"] == ["máy chủ -> server"]
    assert out["raw"] == "máy chủ chết"


def test_stub_keeps_source_visible_as_raw():
    out = _path("Please open a pull request")
    assert out["raw"] == "Please open a pull request"


def test_cjk_is_removed_end_to_end():
    out = _path("máy chủ 世界 chết")
    assert "世界" not in out["text"]
