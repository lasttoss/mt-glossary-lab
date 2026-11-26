"""Term table applied after machine translation.

A small CPU translation model translates developer vocabulary literally: "deploy" becomes
"triển khai", "server" becomes "máy chủ". A term table pins the words a team actually says.
This module only owns the table and the rewrite; it never calls a model.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "glossary.tsv"


@dataclass(frozen=True)
class Rule:
    wrong: str
    right: str

    def pattern(self) -> re.Pattern[str]:
        # Whole word only: "server" must not fire inside "serverless".
        return re.compile(rf"(?<!\w){re.escape(self.wrong)}(?!\w)", re.IGNORECASE)


def load(path: Path | str = DEFAULT_PATH) -> list[Rule]:
    """Read `wrong<TAB>right` lines. Blank lines and `#` comments are ignored."""
    rules: list[Rule] = []
    text = Path(path).read_text(encoding="utf-8")
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split("\t") if p.strip()]
        if len(parts) != 2:
            raise ValueError(f"expected two tab-separated columns: {raw!r}")
        rules.append(Rule(parts[0], parts[1]))
    return rules


def apply(text: str, rules: list[Rule]) -> tuple[str, list[str]]:
    """Apply every rule once, in file order.

    Returns the rewritten text and the rules that actually fired, so a caller can report
    which term the model got wrong instead of silently patching the output.
    """
    fired: list[str] = []
    out = text
    for rule in rules:
        new, n = rule.pattern().subn(rule.right, out)
        if n:
            fired.append(f"{rule.wrong} -> {rule.right}")
            out = new
    return out, fired
