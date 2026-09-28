# AGENTS.md — Arabic FakeRoot Enumerator

## 1. Goal

Enumerate every possible triliteral (ف-ع-ل) root over the Arabic consonant
inventory, filtered by phonotactic co-occurrence. A *fake root* is
phonotactically legal but unattested. Permissive baseline is
`28³ = 21952` candidates; matrices only remove pairs with a cited source.

## 2. Architecture

Standard `src/` layout, package `arabic_roots`:

```text
src/arabic_roots/
  alphabet.py       # 28-glyph source of truth: ORDER, LETTERS, LOOKUP, CATEGORIES
  phonotactics.py   # load_matrices() + is_allowed(c1,c2,c3,m_1_2,m_2_3)
  enumerator.py     # iter_roots() / count_roots() via itertools.product
  statemachine.py   # TriliteralMachine: single-root guard prototype (tests only)
  cli.py            # `enumerate-roots` console script
  __main__.py       # `python -m arabic_roots` delegate to cli.main
data/m_1-2.csv      # C1–C2 gate, 28×28 bool, all-1 init, diag=1
data/m_2-3.csv      # C2–C3 gate, same shape/init
docs/running.md     # how to run (commands, failure table, options)
docs/Future.md      # unimplemented micro-PRDs (attestation, oracle, rendering)
tests/              # alphabet, matrices, golden-count, cli
../Notes/           # Obsidian knowledge bank (outside git, read-only ref)
../Media/           # PDFs, IPA scans (outside git)
```

Rules live **only** in `data/*.csv`. `statemachine.py` carries literals and
queries matrices in `pair12_allowed` / `pair23_allowed`; never add rule logic
there. `enumerator.py` (`itertools.product` + `is_allowed`) is the batch path
and the only production enumeration route. `TriliteralMachine` is a
single-root guard prototype — it validates one triple at a time and is
exercised by tests only; it is **not** on the enumeration path.

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
- Ignore `Master FF Internals.md` (unrelated Firefox note).
- `Misc.md` complete-graph idea is rejected: `28²` transitions per position is
  unmaintainable; matrices + guards replace it.

## 4. Unicode exclusively (strict)

- Files: UTF-8, LF, NFC. Enforced by `.editorconfig` (`charset=utf-8`),
  `.gitattributes` (`working-tree-encoding=UTF-8`), `PYTHONUTF8=1`.
- Arabic glyphs are literal codepoints (`"ح"`, never `"H"`, `"7"`, `"\\u062D"`).
  Normalize ingest with `unicodedata.normalize("NFC", s)`.
- Scope: 28 consonants in `ORDER`, hamza = single `ء U+0621`. No carriers
  (`أ إ آ ؤ ئ`), no bare alif (`ا U+0627`). Validate via
  `alphabet.normalize_glyph` / `is_valid_glyph`.
- Romanization only at I/O: IPA (`[ħ ʕ q tˤ]`, Thelwall) for reasoning,
  DIN 31635 (`ḥ ṯ ǧ š ṣ ḍ ṭ ẓ ʿ ʾ ġ`) for reversible display, IJMES as output
  variant. Forbid Buckwalter/Arabizi/`sh|kh|gh|th|dh` keys in code/tests.
- CSVs: UTF-8, first column + header = glyphs in `ORDER`, cells `0`/`1`.

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
- `mypy --strict` (+ `pandas-stubs`; `statemachine.*` is `ignore_missing_imports`).
- `ty check` is also the opencode LSP backend (see §6); keep it clean.
- `pytest --cov=arabic_roots`; target 100% on `alphabet`/`phonotactics`.
- No `print()` in `src/` (logging only; `cli.py` stdout for roots is the one
  exception). Immutability: `frozendict`, `tuple`, `NamedTuple`. No new deps
  without justification.
- Reproducibility: commit `uv.lock`; fixed `ORDER`; `itertools.product`
  order is the output order; `LC_ALL=C.UTF-8`.

## 6. opencode config (`opencode.jsonc`, project root)

- `instructions: ["AGENTS.md"]` so agents load this file.
- `formatter: true` (ruff is the Python formatter).
- `lsp.ty: { command: ["ty","server"], extensions: [".py",".pyi"] }` — `ty`
  is not built-in, so it is declared as a custom server per `/docs/lsp`.
  Requires the `ty` dev dependency. If LSP desyncs, fall back to the CLI:
  `uv run ty check`. Verify with `opencode debug config`.
- `watcher.ignore`: `.venv`, `__pycache__`, `.pytest_cache`.

## 7. Conventions

- Imports: `from arabic_roots.alphabet import ORDER, normalize_glyph` (never
  `sys.path` hacks; package resolves via `[tool.setuptools.packages.find]`).
- Data access: `load_matrices()` defaults to `<repo>/data`; pass `data_dir`
  explicitly in tests via `tmp_path`.
- Matrix edits: change CSV + add pinning test + cite source in the same commit.
- CLI: `uv run enumerate-roots --data-dir data --limit 10 [--output roots.tsv]`
  (alt: `uv run python -m arabic_roots …`); never `python enumerate-roots`
  (not a file — it is a console script). See `docs/running.md`.
- Git: Agent should not commit to Git and must leave that to the human engineer.
- Keep `.idea/` and `.venv/` out of review diffs.
