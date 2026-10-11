# arabic-roots

Enumerate triliteral (ف-ع-ل) Arabic roots constrained by phonotactic
co-occurrence matrices.

A **possible root** is a triliteral consonant sequence that is
*phonotactically legal* but *unattested* in the lexicon. The permissive
baseline is every `28³ = 21952` candidate over the 28-consonant inventory;
the co-occurrence matrices remove only pairs backed by a cited source. With
the shipped matrices there are **21168** legal roots; subtracting the **3957**
attested MSA roots that are also legal leaves **17211** possible roots. (Two
further attested roots are phonotactically illegal and are reported as a
warning.) The CLI emits possible roots.

## Requirements

- Python **3.14** only (`requires-python == "3.14.*"`); other versions are
  unsupported.
- [`uv`](https://docs.astral.sh/uv/) for the pinned virtualenv and locked
  dependency resolution.

## Install and run

Run everything from this directory (`Code/`) through `uv`:

```bash
uv sync --locked
uv run enumerate-roots --data-dir data --limit 10
```

The console script is `enumerate-roots`; the module path is equivalent:

```bash
uv run python -m arabic_roots --limit 10
```

### Options

| Flag         | Default       | Meaning                                              |
|--------------|---------------|------------------------------------------------------|
| `--data-dir` | `<repo>/data` | Data root holding `rules/` (`m_1-2.csv`, `m_2-3.csv`) |
| `--limit`    | `10`          | How many sample roots to print (`0` prints none)     |
| `--output`   | none          | Output path; format inferred from suffix (`.tsv`, `.csv`) |
| `--scheme`   | `arabic`      | Output scheme: `arabic`, `din31635`, `ijmes`, `ipa`  |
| `--delimiter`| `-`           | Separator between rendered consonants on stdout      |
| `--log-file` | none          | Append a timestamped UTF-8 run log to this path      |

`--output PATH` writes the full possible-roots set (ignoring `--limit`). The
format comes from the suffix:

- `.tsv` / `.csv` — delimited text, header `c1,c2,c3`.
- `.jsonl` — one JSON object per line (literal glyphs).
- `.parquet` — columnar; requires the optional extra (`uv sync --extra output`).
- `.sqlite` — a `roots` table with a primary key over the triple.

Text formats are UTF-8/NFC with LF endings; all preserve ORDER. An unknown
suffix is an error.

`--scheme` renders each consonant (`arabic` default, or `din31635`, `ijmes`,
`ipa`); it applies to stdout and to `--output` cells alike. `--delimiter`
joins the rendered consonants on stdout (default `-`; use `""` for
concatenation). Logs go to stderr; `--log-file PATH` appends the same
timestamped records (effective options, resolved inputs, counts, output) to a
file.

Sample stdout (hyphen-joined Arabic script; possible roots only):

```text
ء-ب-ء
ء-ب-ت
ء-ب-ث
```

Do not invoke `python enumerate-roots` — `enumerate-roots` is a generated
console script, not a file. See `docs/running.md` for failure modes.

## Data layout

```text
data/
  rules/m_1-2.csv              # C1–C2 gate, 28×28 bool
  rules/m_2-3.csv              # C2–C3 gate, 28×28 bool
  roots/attested.csv           # MSA attested roots: c1,c2,c3,variety,source
  transliterations/buckwalter.csv  # ingest-only encoding table
```

Rules live **only** in `data/rules/*.csv`. Each cell is `1` (pair may
co-occur) or `0` (forbidden). The `m_1-2` diagonal is `0` (`C1 ≠ C2`;
Greenberg 1950, *The Patterning of Root Morphemes in Semitic*, WORD 6:2,
p.162) while the `m_2-3` diagonal stays `1` (`C2 = C3` permitted); that
asymmetry is an evidence-based rule, not a default. Every `0` needs a page
citation plus a regression test.

## Architecture

Standard `src/` layout, package `arabic_roots`:

| Module | Responsibility |
|--------|----------------|
| `alphabet.py` | 28-glyph source of truth: `ORDER`, `LETTERS`, `LOOKUP`, place/manner |
| `phonotactics.py` | `load_matrices()` + `successors(matrix, order)` |
| `enumerator.py` | `iter_roots()` / `count_roots()` via matrix-successor walk (memoized) |
| `attestation.py` | `load_attested()` + `is_attested()` over `data/roots/attested.csv` |
| `possible.py` | `iter_possible()` / `count_possible()`: legal minus attested |
| `transliteration.py` | scheme encode/decode (Buckwalter now; DIN/IJMES/IPA later) |
| `arabic_chain_bank_provider.py` | build-time extraction/dedupe (pure, no I/O) |
| `statemachine.py` | `TriliteralMachine`: single-root guard prototype (tests only) |
| `writers.py` | suffix-driven output writers (`.tsv`, `.csv`, `.jsonl`, `.parquet`, `.sqlite`) |
| `render.py` | output schemes (`arabic`, `din31635`, `ijmes`, `ipa`) |
| `cli.py` | the `enumerate-roots` console script |

Enumeration walks the matrices' per-glyph successor lists, following only
`1` cells, and memoizes the materialized triples on matrix content.
`possible.py` subtracts the attested lexicon from that stream, so the CLI
emits only legal-but-unattested roots. Output is ORDER-lexicographic and
deterministic. Attestation is a separate axis: it is a lexicon, never a rule,
and does not feed enumeration.

## Build-time data

`data/roots/attested.csv` is derived from
[CAMeL-Lab/ArabicChainBank](https://github.com/CAMeL-Lab/ArabicChainBank) at a
pinned commit. Regenerate it only via the orchestrator (never edit by hand):

```bash
uv run python scripts/fetch_attested.py
```

Buckwalter appears **only** in `data/transliterations/buckwalter.csv`, an
external ingest-encoding table; no Buckwalter literal appears in `.py`.

## Development

Quality gates (all must pass):

```bash
uv sync --locked
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy src tests
uv run ty check
uv run pytest
uv run enumerate-roots --limit 5
```

Files are UTF-8, LF, NFC; Arabic glyphs are literal codepoints. `from
__future__ import annotations` is forbidden (Python 3.14 defers annotations
natively). See `AGENTS.md` for the full conventions and the knowledge-bank
policy, and `docs/` for `running.md`, `Future.md`, and `Completed.md`.

## License

Not stated.
