"""Output guards for a small translation model.

Two failure modes showed up with a 266M-parameter model on real meeting text, so both are
handled here rather than in the model:

1. Repetition. When the input is a partial sentence (streaming subtitles), the model emits
   the same phrase five or six times. `cut_loop` keeps the first pass.
2. Length blow-up. Vietnamese runs about 1.1-1.4x the English word count; past 1.8x the model
   is repeating, not translating. `cap_len` truncates only the in-progress line.

Both functions are pure so they can be tested without a model.
"""
from __future__ import annotations

import re

_NON_LATIN = re.compile(r"[\u3000-\u303f\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uff00-\uffef]+")


def clean(text: str) -> str:
    """Collapse whitespace and drop CJK characters a small model sometimes mixes in."""
    return re.sub(r"\s{2,}", " ", _NON_LATIN.sub(" ", text or "")).strip()


def cut_loop(text: str, min_words: int = 3) -> str:
    """Truncate at the first repeat of the longest repeated n-gram of `min_words` or more."""
    words = (text or "").split()
    n = len(words)
    if n < 2 * min_words:
        return text
    low = [w.lower() for w in words]
    for k in range(n // 2, min_words - 1, -1):
        seen: dict[tuple[str, ...], int] = {}
        for i in range(n - k + 1):
            gram = tuple(low[i : i + k])
            if gram in seen:
                return " ".join(words[: seen[gram] + k])
            seen[gram] = i
    return text


def cap_len(out: str, src: str, ratio: float = 1.8, pad: int = 6) -> str:
    """Cut an in-progress translation that grew past `ratio` times the source word count."""
    cap = max(12, int(ratio * len((src or "").split())) + pad)
    words = (out or "").split()
    return " ".join(words[:cap]) if len(words) > cap else out
