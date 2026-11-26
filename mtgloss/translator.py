"""EN -> VI translation on CPU with CTranslate2.

The default model is a 266M-parameter T5 fine-tuned for English-Vietnamese (VietAI envit5,
converted to CTranslate2 int8). It is a separate download, so the class is imported lazily and
the rest of the package works without it — CI runs the guards and the term table with a stub.
"""
from __future__ import annotations

import re
import threading
from pathlib import Path

from . import glossary, postprocess


class Translator:
    """Wraps a CTranslate2 model directory containing `spiece.model`."""

    def __init__(self, model_dir: Path | str, threads: int = 8) -> None:
        import ctranslate2  # imported here so the package imports without the runtime
        import sentencepiece as spm

        self.dir = Path(model_dir)
        self._tr = ctranslate2.Translator(
            str(self.dir), device="cpu", compute_type="int8", intra_threads=threads
        )
        self._sp = spm.SentencePieceProcessor(model_file=str(self.dir / "spiece.model"))
        self._lock = threading.RLock()

    def _pieces(self, text: str) -> list[str]:
        return [self._sp.id_to_piece(i) for i in self._sp.encode(text)]

    def raw(self, text: str, src: str = "en") -> str:
        """Translate without the term table, so the caller can see what the model alone produced."""
        tag = "en: " if src == "en" else "vi: "
        # The model loops when the input is a partial sentence, so bound the output length.
        max_len = min(200, max(48, int(len(text) * 1.2) + 24))
        with self._lock:
            result = self._tr.translate_batch(
                [self._pieces(tag + text)],
                beam_size=2,
                max_decoding_length=max_len,
                end_token="</s>",
            )
        out = self._sp.decode_pieces(result[0].hypotheses[0])
        return re.sub(r"^\s*(vi|en)\s*:\s*", "", out).strip()


class StubTranslator:
    """Deterministic stand-in for tests: repeats the source, so guards can be exercised."""

    def raw(self, text: str, src: str = "en") -> str:
        return text


def to_vi(text: str, translator, rules: list[glossary.Rule], *, live: bool = False) -> dict:
    """Full path: model -> repetition guard -> term table.

    `live=True` is for an in-progress subtitle line; the final line is not truncated.
    """
    text = (text or "").strip()
    if not text:
        return {"source": text, "raw": "", "text": "", "fired": []}

    raw = translator.raw(text, "en")
    out = postprocess.clean(postprocess.cut_loop(raw))
    if live:
        out = postprocess.cap_len(out, text)
    final, fired = glossary.apply(out, rules)
    return {"source": text, "raw": raw, "text": final, "fired": fired}
