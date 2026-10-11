# arabic-roots

Enumerate triliteral (ف-ع-ل) Arabic roots constrained by phonotactic
co-occurrence matrices.

A **possible root** is a triliteral consonant sequence that is
*phonotactically legal* but *unattested* in the lexicon. The permissive
baseline is every `28³ = 21952` candidate over the 28-consonant inventory;
the co-occurrence matrices remove only pairs backed by a cited source. With
the shipped matrices the enumerator yields **21168** legal roots, of which
**3959** are attested MSA roots (so **17209** are possible roots).

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

`--output PATH` writes the full enumeration (ignoring `--limit`). The format
comes from the suffix: `.tsv` (tab-separated) or `.csv` (comma-separated),
both with the header `c1,c2,c3`, UTF-8/NFC and LF endings. An unknown suffix
is an error. See `docs/Future.md` for JSONL, Parquet, and SQLite plans.

Sample stdout (hyphen-joined Arabic script):

```text
ء-ب-ء
ء-ب-ب
ء-ب-ت
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
| `transliteration.py` | scheme encode/decode (Buckwalter now; DIN/IJMES/IPA later) |
| `arabic_chain_bank_provider.py` | build-time extraction/dedupe (pure, no I/O) |
| `statemachine.py` | `TriliteralMachine`: single-root guard prototype (tests only) |
| `cli.py` | the `enumerate-roots` console script |

Enumeration walks the matrices' per-glyph successor lists, following only
`1` cells, and memoizes the materialized triples on matrix content. Output is
ORDER-lexicographic and deterministic. Attestation is a separate axis: it is
a lexicon, never a rule, and does not feed enumeration.

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
