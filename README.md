# mt-glossary-lab

EN→VI machine translation on CPU, plus the part that actually decides whether the output is
usable: a **term table** for developer vocabulary, measured on a fixed set of sentences.

The model is a 266M-parameter T5 fine-tuned for English–Vietnamese, converted to CTranslate2 int8.
Small models translate domain words literally, so a team ends up reading "máy chủ" where they say
"server". The table pins those words; the evaluation says how much that is worth.

## Numbers on my machine

Ryzen 7 8845HS, CPU only, int8, 8 threads, beam 2. Every number below is printed by
`python -m mtgloss eval --set all`; the raw output is in [docs/measurements.md](docs/measurements.md).

| Set | Sentences | Model alone | + term table |
|---|---|---|---|
| `dev` (rules were written against it) | 14 | 0/14 | **13/14** |
| `holdout` (never opened while tuning) | 8 | 0/8 | **7/8** |

Latency per sentence: **p50 ≈ 120-130 ms**, p95 ≈ 140-190 ms.

The two remaining misses are the interesting part: the model *dropped* the word instead of
mistranslating it — "we migrated the database last weekend" came back as "chúng tôi đã migrate vào
rồi", with no noun at all. **A term table cannot restore a word that is not there.** That is a job
for a bigger model or an LLM check over the output, and it is out of scope here on purpose.

## What this does not prove

- Not a translation-quality benchmark. 22 sentences written from real meeting lines, not a corpus.
- No BLEU/chrF++. Term hits are counted exactly; fluency is not graded at all.
- Vietnamese only, one direction. No other language pair.
- The `dev` number is optimistic by construction: the last five rules were added *after* reading
  those failures. `holdout` exists so that number cannot be the only one quoted.
- One pair of CPU threads settings, one machine. No GPU path.

## Run

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev,model]"

# Download a CTranslate2 EN->VI model (any directory containing model.bin + spiece.model),
# for example a VietAI envit5 conversion. Then:
python -m mtgloss translate --model-dir /path/to/envit5-ct2 --text "We deploy on Friday"
python -m mtgloss eval --model-dir /path/to/envit5-ct2 --set all
python -m mtgloss terms            # table only, no model needed
```

```
$ python -m mtgloss translate --model-dir ~/models/envit5-ct2 --text "Please open a pull request and ask for a review"
source : Please open a pull request and ask for a review
model  : Vui lòng mở yêu cầu kéo và yêu cầu đánh giá
final  : Vui lòng mở pull request và yêu cầu review
patched: yêu cầu kéo -> pull request, đánh giá -> review
```

`patched` is the point: the tool never hides what the model produced.

## Layout

```
mtgloss/glossary.py     term table: whole-word rewrite, reports every rule that fired
mtgloss/postprocess.py  repetition guard + length cap for in-progress subtitle lines
mtgloss/translator.py   CTranslate2 wrapper (lazy), full path model -> guards -> table
mtgloss/cli.py          translate / eval / terms
data/glossary.tsv       the table (25 rules)
data/eval/dev.tsv       sentences + required terms
data/eval/holdout.tsv   same shape, untouched while writing rules
docs/measurements.md    raw command output behind the table above
```

## Testing

`python -m pytest -q` — 25 tests, none of them need a model: the guards are pure functions, the
table is data, and `StubTranslator` stands in for the model. The model-backed numbers are produced
locally by `eval`, not in CI.

MIT licensed.
