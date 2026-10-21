# arabic-possible-roots

Enumerate triliteral (ف-ع-ل) Arabic roots constrained by phonotactic
co-occurrence matrices.

A **possible root** is a triliteral consonant sequence that is
*phonotactically legal* but *unattested* in the lexicon. The permissive
baseline is every `28³ = 21952` candidate over the 28-consonant inventory;
the co-occurrence matrices remove only pairs backed by a cited source. With
the shipped matrices (the `self` and `homorganic` gates ANDed per position)
there are **13656** legal roots; subtracting the **3715** attested MSA roots
that are also legal leaves **9941** possible roots. (A further **244**
attested roots are phonotactically illegal and are reported as a warning.) The
CLI emits possible roots.

> [!WARNING]
> This is a work in progress; *244 attested roots are phonotactically illegal*
> including some very common ones like, ء-ه-ل, ر-ش-د.
> I'm still refining my codification of Arabic's phonotactical rules for triliteral roots.

## Requirements

- Python **3.14** only (`requires-python == "3.14.*"`); other versions are
  unsupported.
- [`uv`](https://docs.astral.sh/uv/) for the pinned virtualenv and locked
  dependency resolution.

## Install and run

Run everything from this directory (`arabic-possible-roots/`) through `uv`:

```bash
uv sync --locked
uv run enumerate-roots --data-dir data --limit 10
```

The console script is `enumerate-roots`; the module path is equivalent:

```bash
uv run python -m arabic_possible_roots --limit 10
```

### Options

| Flag         | Default       | Meaning                                              |
|--------------|---------------|------------------------------------------------------|
| `--data-dir` | `<repo>/data` | Data root holding `rules/` (per-type `m_1-2`/`m_2-3` matrices) |
| `--limit`    | `10`          | How many sample roots to print (`0` prints none)     |
| `--output`   | none          | Output path; format inferred from suffix (`.tsv`, `.csv`, `.jsonl`, `.parquet`, `.sqlite`) |
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
  rules/m_1-2_self.csv             # C1–C2 identity gate, 28×28 bool (diag 0)
  rules/m_1-2_homorganic.csv       # C1–C2 natural-class gate
  rules/m_2-3_self.csv             # C2–C3 identity gate, 28×28 bool (diag 1)
  rules/m_2-3_homorganic.csv       # C2–C3 natural-class gate
  roots/attested.csv           # MSA attested roots: c1,c2,c3,variety,source
  transliterations/buckwalter.csv  # ingest-only encoding table
  transliterations/ijmes.csv   # output scheme table: glyph,ijmes
```

Rules live **only** in `data/rules/*.csv`. Each position is assembled from one
or more *matrix types* (`m_{position}_{type}.csv`) combined by logical **AND**
— a pair is legal only if every selected matrix allows it. Each cell is `1`
(pair may co-occur) or `0` (forbidden). The `self` gate carries the identity
rule: the `m_1-2` diagonal is `0` (`C1 ≠ C2`; Greenberg 1950, *The Patterning
of Root Morphemes in Semitic*, WORD 6:2, p.162) while the `m_2-3` diagonal
stays `1` (`C2 = C3` permitted); that asymmetry is an evidence-based rule, not
a default. The `homorganic` gate forbids the two distinct members of a natural
class from being adjacent (McCarthy 1988, *Feature geometry and dependency*,
Phonetica 45:84-108). Every `0` needs a page citation plus a regression test.

## Architecture

Standard `src/` layout, package `arabic_possible_roots`:

| Module | Responsibility |
|--------|----------------|
| `__init__.py` | public API re-exports + `__version__` (single-sourced from `pyproject.toml`) |
| `alphabet.py` | 28-glyph source of truth: `ORDER`, `LETTERS`, `LOOKUP`, place/manner |
| `phonotactics.py` | `load_matrices()` / `load_matrix()` composition + `successors(matrix, order)` |
| `enumerator.py` | `iter_roots()` / `count_roots()` via matrix-successor walk (memoized) |
| `attestation.py` | `load_attested()` + `is_attested()` over `data/roots/attested.csv` |
| `possible.py` | `iter_possible()` / `count_possible()`: legal minus attested |
| `transliteration.py` | scheme encode/decode primitives (Buckwalter ingest, IJMES output) |
| `arabic_chain_bank_provider.py` | build-time extraction/dedupe (pure, no I/O) |
| `writers.py` | suffix-driven output writers (`.tsv`, `.csv`, `.jsonl`, `.parquet`, `.sqlite`) |
| `render.py` | output transliteration schemes (`arabic`, `din31635`, `ijmes`, `ipa`) |
| `cli.py` | the `enumerate-roots` console script |

Enumeration walks the matrices' per-glyph successor lists, following only
`1` cells, and memoizes the materialized triples on matrix content.
`possible.py` subtracts the attested lexicon from that stream, so the CLI
emits only legal-but-unattested roots. Output is ORDER-lexicographic and
deterministic. Attestation is a separate axis: it is a lexicon, never a rule,
and does not feed enumeration.

## Using as a library

The package exposes a small public API (re-exported from `arabic_possible_roots`) so
other programs can reuse it without wiring into the CLI:

```python
from arabic_possible_roots import (
    count_possible,
    is_attested,
    iter_possible,
    load_attested,
    load_matrices,
)

m_1_2, m_2_3 = load_matrices()          # 28×28 boolean co-occurrence gates
attested = load_attested()              # {"msa": frozenset[(c1, c2, c3), ...]}

count_possible(m_1_2, m_2_3, attested)  # 9941
is_attested("ك", "ت", "ب", attested)    # True
next(iter_possible(m_1_2, m_2_3, attested))  # ("ء", "ب", "ء")
```

The distribution ships inline type annotations plus a `py.typed` marker
(PEP 561), so downstream `mypy` / `ty` users get types without extra setup.

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

## Releasing

Releases use [commitizen](https://commitizen-tools.github.io/commitizen/) to
infer the next version from Conventional Commits, update `CHANGELOG.md` and
`uv.lock`, commit, and tag:

```bash
uv run cz bump                        # e.g. 0.6.0 -> 0.7.0; commits + tags v0.7.0
git push origin --follow-tags         # push the tag after creating the repo
uv run cz bump 1.0.0                  # override the inferred version
```

Tags are annotated (`vX.Y.Z`). See `docs/releasing.md` for the full workflow.

## Contributing

This is an academic project with strict reproducibility and evidence rules:
every phonotactic `0` in a matrix needs a page citation plus a regression test,
and Arabic glyphs are literal NFC codepoints. Read `AGENTS.md` before changing
`data/` or adding rules, and run the quality gates above before any commit.
The human engineer owns all `git commit`/`git tag` operations.

## License

[MIT](LICENSE) © 2026 Michael Gatto.
