"""Command line entry point.

    python -m mtgloss translate --text "We deploy on Friday"
    python -m mtgloss eval --model-dir ~/models/envit5-ct2
    python -m mtgloss terms

`eval` needs the model; `terms` and the unit tests do not.
"""
from __future__ import annotations

import argparse
import statistics
import sys
import time
from pathlib import Path

from . import glossary, translator

ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = ROOT / "data" / "eval"


def _load_eval(name: str) -> list[tuple[str, list[str]]]:
    cases: list[tuple[str, list[str]]] = []
    for raw in (EVAL_DIR / f"{name}.tsv").read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        english, required = line.split("\t")
        cases.append((english, [t.strip().lower() for t in required.split(",") if t.strip()]))
    return cases


def cmd_terms(_args: argparse.Namespace) -> int:
    rules = glossary.load()
    print(f"{len(rules)} rules from data/glossary.tsv")
    for rule in rules[:5]:
        print(f"  {rule.wrong} -> {rule.right}")
    return 0


def cmd_translate(args: argparse.Namespace) -> int:
    rules = glossary.load()
    engine = translator.Translator(args.model_dir, threads=args.threads)
    result = translator.to_vi(args.text, engine, rules, live=args.live)
    print(f"source : {result['source']}")
    print(f"model  : {result['raw']}")
    print(f"final  : {result['text']}")
    if result["fired"]:
        print(f"patched: {', '.join(result['fired'])}")
    return 0


def _run_set(name: str, engine, rules, verbose: bool) -> tuple[int, int, int]:
    cases = _load_eval(name)
    raw_hits = final_hits = 0
    latencies: list[float] = []
    for english, required in cases:
        started = time.perf_counter()
        result = translator.to_vi(english, engine, rules)
        latencies.append((time.perf_counter() - started) * 1000)

        raw = result["raw"].lower()
        final = result["text"].lower()
        raw_ok = all(term in raw for term in required)
        final_ok = all(term in final for term in required)
        raw_hits += raw_ok
        final_hits += final_ok

        if verbose:
            mark = "ok  " if final_ok else "MISS"
            print(f"  [{mark}] {'+'.join(required):24s} | {result['text']}")
            if not raw_ok:
                print(f"          model alone missed it: {english!r}")

    latencies.sort()
    print(f"{name:8s} cases {len(cases):2d} · model alone {raw_hits:2d}/{len(cases)} · "
          f"+ term table {final_hits:2d}/{len(cases)} · "
          f"p50 {statistics.median(latencies):.0f} ms · p95 {latencies[int(len(latencies) * 0.95) - 1]:.0f} ms")
    return raw_hits, final_hits, len(cases)


def cmd_eval(args: argparse.Namespace) -> int:
    rules = glossary.load()
    engine = translator.Translator(args.model_dir, threads=args.threads)
    names = ["dev", "holdout"] if args.set == "all" else [args.set]

    total_ok = total = 0
    for name in names:
        _, final_hits, count = _run_set(name, engine, rules, args.verbose)
        total_ok += final_hits
        total += count

    print(f"misses: {total - total_ok}/{total}"
          + ("  (a term table cannot restore words the model dropped — see docs/measurements.md)" if total_ok < total else ""))
    if args.strict and total_ok < total:
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mtgloss", description="EN->VI translation with a term table")
    sub = parser.add_subparsers(dest="command", required=True)

    p_tr = sub.add_parser("translate", help="translate one sentence and show what the term table patched")
    p_tr.add_argument("--model-dir", required=True, help="CTranslate2 model dir containing spiece.model")
    p_tr.add_argument("--text", required=True)
    p_tr.add_argument("--threads", type=int, default=8)
    p_tr.add_argument("--live", action="store_true", help="treat input as an in-progress subtitle line")
    p_tr.set_defaults(func=cmd_translate)

    p_ev = sub.add_parser("eval", help="run the fixed evaluation set and print pass rates")
    p_ev.add_argument("--model-dir", required=True)
    p_ev.add_argument("--threads", type=int, default=8)
    p_ev.add_argument("--set", default="dev", choices=["dev", "holdout", "all"],
                      help="dev = rules were written against it; holdout = untouched while tuning")
    p_ev.add_argument("--verbose", action="store_true")
    p_ev.add_argument("--strict", action="store_true", help="exit non-zero when a case still misses a term")
    p_ev.set_defaults(func=cmd_eval)

    sub.add_parser("terms", help="print the term table without loading a model").set_defaults(func=cmd_terms)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
