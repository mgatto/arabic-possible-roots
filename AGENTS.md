# AGENTS.md — Arabic PossibleRoot Enumerator

## 1. Goal

Enumerate triliteral (ف-ع-ل) roots over the Arabic consonant
inventory, filtered by phonotactic co-occurrence. A *possible root* is
phonotactically legal but unattested. Permissive baseline is
`28³ = 21952` candidates; matrices only remove pairs with a cited source.

Code Python modules for maximum exportability for reuse in other parts of this library and for other projects, too.
For example, a Transliteration choice for output should be structured to be reusable by other programs since it has a
utility beyond this specific project we're working in now.

## 2. Architecture

Standard `src/` layout, package `arabic_possible_roots`:

```text
src/arabic_possible_roots/
  __init__.py       # public API re-exports + __version__ (single-sourced via importlib.metadata)
  py.typed          # PEP 561 marker (shipped via [tool.setuptools.package-data])
  alphabet.py       # 28-glyph source of truth: ORDER, LETTERS, LOOKUP, Place/Manner
  phonotactics.py   # load_matrices()/load_matrix() composition + successors(matrix, order)
  enumerator.py     # iter_roots() / count_roots() via matrix-successor walk (memoized)
  arabic_chain_bank_provider.py # ArabicChainBank build-time extraction/dedupe (pure, no I/O)
  transliteration.py# scheme encode/decode primitives (Buckwalter ingest, IJMES output)
  attestation.py    # load_attested() + is_attested() over data/roots/attested.csv
  possible.py       # iter_possible()/count_possible(): legal minus attested
  writers.py        # suffix-driven output writers (tsv/csv/jsonl/parquet/sqlite)
  render.py         # output transliteration schemes (arabic/din31635/ijmes/ipa)
  cli.py            # `enumerate-roots` console script
  __main__.py       # `python -m arabic_possible_roots` delegate to cli.main
data/rules/m_1-2_self.csv       # C1–C2 identity gate, 28×28 bool, diag=0 (C1≠C2, Greenberg 1950 p.162)
data/rules/m_1-2_homorganic.csv # C1–C2 natural-class gate (McCarthy 1988)
data/rules/m_2-3_self.csv       # C2–C3 identity gate, 28×28 bool, diag=1 (C2=C3 permitted)
data/rules/m_2-3_homorganic.csv # C2–C3 natural-class gate (McCarthy 1988)
data/roots/attested.csv         # MSA attested roots: c1,c2,c3,variety,source (NFC)
data/transliterations/buckwalter.csv # ingest-only encoding table: glyph,buckwalter (28 rows)
data/transliterations/ijmes.csv      # output scheme table: glyph,ijmes (28 rows)
scripts/            # build-time orchestrators (fetch_attested.py)
docs/running.md     # how to run (commands, failure table, options)
docs/releasing.md   # commitizen release workflow (cz bump / tag / push)
docs/Future.md      # open micro-PRDs (natural classes, branded glyph)
docs/Completed.md   # shipped micro-PRDs ledger (date, SHA, evidence)
tests/              # alphabet, matrices, golden-count, chain-bank, attestation, cli
../Notes/           # Obsidian knowledge bank (outside git, read-only ref)
../Media/           # PDFs, IPA scans (outside git)
```

Rules live **only** in `data/rules/*.csv`. Each position is assembled from
per-type matrices (`m_{position}_{type}.csv`, types `self` and `homorganic`)
combined by logical AND in `phonotactics.load_matrices()` — a pair is legal
only if every selected type allows it; `load_matrix(position, types)` composes
one position explicitly. `phonotactics.successors()` turns each matrix into
per-glyph successor lists, and `enumerator.py` walks those lists (never
generating a forbidden pair), memoizing the materialized triples on matrix
content — it is the batch path and the only production enumeration route.
(The former single-root guard prototype `statemachine.py` was archived to
`_Archive/`; its oracle idea is dropped — see `docs/Future.md`.)

Attestation is a separate axis from phonotactics. `attestation.py` reads
`data/roots/attested.csv` (MSA triliteral roots: `c1,c2,c3,variety,source`) and
answers `is_attested(...)`; `arabic_chain_bank_provider.py` holds the pure
root extraction/dedupe used only at build time by `scripts/fetch_attested.py`,
with scheme encode/decode in `transliteration.py`. Attested data is a lexicon,
not a rule: it never feeds `successors`, and `enumerator.py` stays rule-only.
`possible.py` is the composition layer — it subtracts a variety's attested
`frozenset` from `iter_roots(...)` to yield the possible roots the CLI emits.

Legacy top-level `Alphabet.py` / `main.py` are superseded and deleted;
do not reintroduce them. `main.py` had a missing `pandas` import and ASCII
stub alphabet — ported and fixed under `src/`.

### Runtime: Python 3.14 only

- `pyproject.toml` pins `requires-python == 3.14.*`, `.python-version` pins
  the interpreter, `.venv` runs 3.14.7 via `uv`. The system Python 3.11 is
  unsupported; always run through `uv run` / `uv sync`.
- `ruff` uses `target-version = "py314"`, `mypy` uses `python_version = "3.14"`
  with `--strict`, `ty` uses `[tool.ty.environment] python-version = "3.14"`.
- Python 3.14 implements PEP 649 (via PEP 749): annotations are lazily
  deferred natively, stored as the lightweight `__annotate__` function and
  evaluated only when explicitly requested at runtime — not at import time.
- Consequence: `from __future__ import annotations` is **forbidden** in this
  repo. It was a pre-3.14 shim for forward references and import-time cost
  and is now dead weight. Never add it to new files; remove it on sight.
  All modules and tests must pass `ruff`, `mypy --strict`, and `ty check`
  without it.

## 3. Knowledge bank (`../Notes/`, incomplete — treat gaps explicitly)

- Priority: `Sources.md` > `IPA Chart for Arabic.md` > `alphabet.py` docstring
  > `Transliteration Schemes.md` comparison table.
- Owned: Thelwall & Sa'adeddin 1999 pp. 51–54 (alphabet/IPA);
  Ryder *Arabic: A Linguistic Introduction* (phonotactics ruleset).
- Empty stubs: `Architecture.md`, `Phonotactic Rules for Arabic.md`, `Why.md`.
  Never invent a prohibition: each `0` in a matrix needs `TODO(Ryder:p.X)` or a
  page citation plus a regression test pinning the pair.
- The `m_1-2_self` diagonal is `0` (`C1 ≠ C2`; Greenberg 1950, *The Patterning of
  Root Morphemes in Semitic*, WORD 6:2, p.162) while the `m_2-3_self` diagonal
  stays `1` (`C2 = C3` permitted). This asymmetry is an evidence-based rule,
  pinned in `tests/test_enumeration.py`.
- The `homorganic` matrices forbid the two *distinct* members of one natural
  class from being adjacent (McCarthy 1988, *Feature geometry and dependency*,
  Phonetica 45:84-108); their diagonals stay `1`. Both homorganic CSVs are
  byte-identical, pinned in `tests/test_matrices.py`.
- Ignore `Master FF Internals.md` (unrelated Firefox note).
- `Misc.md` complete-graph idea is rejected: `28²` transitions per position is
  unmaintainable; matrices + guards replace it.

## 4. Unicode exclusively (strict)

- Files: UTF-8, LF, NFC. Enforced by `.editorconfig` (`charset=utf-8`),
  `.gitattributes` (`working-tree-encoding=UTF-8`), `PYTHONUTF8=1`.
- Arabic glyphs are literal codepoints (`"ح"`, never `"H"`, `"7"`, `"\\u062D"`).
  Normalize via `alphabet.nfc`; raw `unicodedata.normalize` appears **only**
  inside `nfc` (enforced by `tests/test_unicode_policy.py`).
- Scope: 28 consonants in `ORDER`, hamza = single `ء U+0621`. No carriers
  (`أ إ آ ؤ ئ`), no bare alif (`ا U+0627`). Validate via
  `alphabet.normalize_glyph` / `is_valid_glyph`.
- Romanization only at I/O: IPA (`[ħ ʕ q tˤ]`, Thelwall) for reasoning,
  DIN 31635 (`ḥ ṯ ǧ š ṣ ḍ ṭ ẓ ʿ ʾ ġ`) for reversible display, IJMES as output
  variant. Forbid Buckwalter/Arabizi/`sh|kh|gh|th|dh` literals in `src/`;
  scheme tables are data, stored in `data/transliterations/*.csv`
  (`buckwalter.csv` ingest-only; `ijmes.csv` output) and loaded at runtime by
  `transliteration.py` / `render.py`, so no Buckwalter or IJMES symbol appears
  in `.py`. Tests may use IJMES literals (see §7).
- CSVs: UTF-8/NFC, LF. Matrices (`data/rules/`): one file per
  `m_{position}_{type}.csv` (`position` ∈ `1-2`/`2-3`, `type` ∈ `self`/
  `homorganic`), first column + header = glyphs in `ORDER`, cells `0`/`1`.
  `data/roots/attested.csv`: header
  `c1,c2,c3,variety,source`, glyph cells in `ORDER`.
  `data/transliterations/*.csv`: header `glyph,<scheme>`, glyph column exactly
  `ORDER` (`buckwalter.csv`, `ijmes.csv`).

## 5. Quality gates (must pass before commit)

```bash
uv sync --locked
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy src tests
uv run ty check
uv run pytest
uv run enumerate-roots --limit 5
```

- `ruff`: `py314`, line-length 88, `E,F,I,UP,B,W,N,C90`.
- `mypy --strict` (+ `pandas-stubs`).
- `ty check` is also the opencode LSP backend (see §6); keep it clean.
- `pytest --cov=arabic_possible_roots`; target 100% on `alphabet`/`phonotactics`.
- No `print()` in `src/` (logging only; `cli.py` stdout for roots is the one
  exception). Immutability: `frozendict`, `tuple`, `NamedTuple`. No new deps
  without justification; the Parquet writer's `pyarrow` is an opt-in extra
  (`uv sync --extra output`), never a core dependency.
- Reproducibility: commit `uv.lock`; fixed `ORDER`; the successor walk emits
  ORDER-lexicographic order (identical to the old `itertools.product` order);
  `LC_ALL=C.UTF-8`.

## 6. opencode config (`opencode.jsonc`, project root)

- `instructions: ["AGENTS.md"]` so agents load this file.
- `formatter: true` (ruff is the Python formatter).
- `lsp.ty: { command: ["ty","server"], extensions: [".py",".pyi"] }` — `ty`
  is not built-in, so it is declared as a custom server per `/docs/lsp`.
  Requires the `ty` dev dependency. If LSP desyncs, fall back to the CLI:
  `uv run ty check`. Verify with `opencode debug config`.
- `watcher.ignore`: `.venv`, `__pycache__`, `.pytest_cache`.

## 7. Conventions

- Imports: `from arabic_possible_roots.alphabet import ORDER, normalize_glyph` (never
  `sys.path` hacks; package resolves via `[tool.setuptools.packages.find]`).
- Data access: `load_matrices()` defaults to `<repo>/data`, reads its `rules/`
  sub-directory, and ANDs the `self`+`homorganic` types per position by
  default; `load_matrix(position, types)` composes one position. Pass the data
  root explicitly in tests via `tmp_path`.
- Matrix edits: change CSV + add pinning test + cite source in the same commit.
- Attested data: `load_attested()` likewise defaults to `<repo>/data` and reads
  its `roots/` sub-directory.
  Regenerate `data/roots/attested.csv` only via
  `uv run python scripts/fetch_attested.py` (pinned upstream SHA); never edit
  it by hand. Re-pin the golden count in `tests/test_attestation.py` when the
  source SHA changes.
- CLI: `uv run enumerate-roots --data-dir data --limit 10 [--output roots.tsv]`
  (alt: `uv run python -m arabic_possible_roots …`); never `python enumerate-roots`
  (not a file — it is a console script). The CLI emits possible roots (legal
  minus attested), logs both counts, and warns on attested-but-illegal roots.
  `--output` format is inferred from the suffix (`.tsv`/`.csv` headed
  `c1,c2,c3`, plus `.jsonl`, `.sqlite`, and `.parquet`); an unknown suffix exits
  `2`. `.parquet` needs the optional `output` extra (`pyarrow`). Rendering is
  controlled by `--scheme {arabic,din31635,ijmes,ipa}` (default `arabic`) and
  `--delimiter` (default `-`); rendering lives in `render.py` at the CLI
  boundary. `--log-file PATH` appends timestamped run records (options,
  embedded choices, counts, output) to a file, mirrored to stderr. See
  `docs/running.md`.
- Git: Agent should not commit to Git and must leave that to the human engineer.
- Versioning: `__version__` is single-sourced — `arabic_possible_roots.__version__`
  reads `[project] version` from `pyproject.toml` via `importlib.metadata`
  (never hand-edit a duplicate literal); `py.typed` is shipped via
  `[tool.setuptools.package-data]`.
- Releasing: `uv run cz bump` (commitizen) infers the next version from
  Conventional Commits, rewrites `CHANGELOG.md` and `uv.lock`, commits, and tags
  `vX.Y.Z`; the human then pushes (`git push origin --follow-tags`). The agent
  never bumps/tags. See `docs/releasing.md`.
- Keep `.idea/` and `.venv/` out of review diffs.
