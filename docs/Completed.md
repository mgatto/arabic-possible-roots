# Completed work — micro-PRD ledger

Append-only record of shipped micro-PRDs. `docs/Future.md` remains the
backlog; when a PRD ships it gets an "Implemented — see Completed.md" marker
there and a full entry here.

## Entry template

```markdown
## PRD N — <title>

- **Completed:** YYYY-MM-DD
- **Commit:** <sha>
- **Summary:** <one paragraph>
- **Deliverables:** <files added/changed>
- **Acceptance evidence:** <tests, commands, pinned counts>
- **Deviations:** <what differed from the original PRD and why>
- **Resolved open questions:** <decisions taken>
- **Follow-ups:** <new work spun out>
```

---

## PRD 1 — Attested-roots data source (MSA; Classical/dialects later)

- **Completed:** 2026-09-29
- **Commit:** TBD (agent does not commit; fill in after merge)
- **Summary:** Added an MSA attested-roots dataset derived from
  [CAMeL-Lab/ArabicChainBank](https://github.com/CAMeL-Lab/ArabicChainBank)
  (CamelMorph v1.0), pinned to commit
  `ec88574fde176e453cfa5715135a42b7a02cef98`. The committed artifact is
  `data/attested.csv` with **3,959** triliteral roots; a build-time
  orchestrator regenerates it and a runtime loader/predicate
  (`load_attested`, `is_attested`) exposes it alongside `is_allowed`.
- **Deliverables:**
  - `data/attested.csv` — `c1,c2,c3,variety,source`, UTF-8/NFC/LF, `variety=msa`,
    `source=arabicchainbank@<sha>`.
  - `data/buckwalter.csv` — ingest-only encoding table (`glyph,buckwalter`),
    glyph column exactly `ORDER`; the single sanctioned Buckwalter location.
  - `src/arabic_roots/transliteration.py` — scheme encode/decode
    (`build_decoder` / `build_encoder`, `decode_root` / `encode_root`).
  - `src/arabic_roots/ingest.py` — pure root extraction/dedupe (no I/O).
  - `src/arabic_roots/attestation.py` — `load_attested()` / `is_attested()`.
  - `scripts/fetch_attested.py` — stdlib-only build-time orchestrator.
  - `tests/test_transliteration.py`, `tests/test_ingest.py`,
    `tests/test_attestation.py`.
  - Docs: `Sources.md` citation + BibTeX, `docs/running.md` regeneration
    section, `AGENTS.md` tree/§2/§4/§7 updates.
- **Acceptance evidence:**
  - `uv run pytest` — 40 passed; `ingest.py` and `attestation.py` at 100%.
  - Golden count pinned: `GOLDEN_MSA_COUNT = 3959` in `tests/test_attestation.py`.
  - `uv run ruff check src tests`, `ruff format --check`, `mypy src tests`,
    `uv run ty check` all clean; `scripts/` also clean.
  - Spot checks: `ك-ت-ب` attested; `ض-ض-ض` (legal, unattested) reported possible.
- **Deviations:**
  - The approved extraction path (`POS == ROOT` Arabic `LEMMA_ARA` rows) exists
    only in `lemmas_sample.csv` (13 roots), **not** in the full `lemmas.csv`
    (34,451 rows; no `POS == ROOT` rows; root only in the Buckwalter `ROOT`
    column). Switched to decoding that column.
  - Because Buckwalter is otherwise forbidden (AGENTS.md §4), the 28-entry map
    was isolated in `data/buckwalter.csv` and §4 amended with a narrow,
    documented ingest-only exception. No Buckwalter literal appears in `.py`.
  - Dropped 2,136 rows: 960 distinct quadriliteral (4-consonant) roots and 5
    malformed 5-segment rows. 28,356 rows were duplicate lemmas of an already
    seen root.
- **Resolved open questions:**
  - Canonical MSA source: ArabicChainBank (CamelMorph v1.0), pinned SHA;
    conflicts across future sources are representable via the `source` column.
  - Weak roots: surface form only; `و`/`ي` retained, hamza carriers collapse to
    `ء` via the encoding map.
- **Follow-ups:**
  - Classical Arabic variety (same schema, new `variety` value).
  - Dialects (schema-ready; no migration required).
  - PRD 2 oracle (`is_valid ∧ is_attested`) and PRD 3 rendering remain open.

---

## Enumeration rewrite — matrix-walk (Option A) + triple cache (Option D)

- **Completed:** 2026-10-11
- **Commit:** TBD (agent does not commit; fill in after merge)
- **Summary:** Replaced the generate-then-filter batch path
  (`itertools.product` over 28³ + `is_allowed`) with a walk that follows only
  the `1`s in the co-occurrence matrices, and memoized the materialized
  triples. `phonotactics.successors()` now exposes each glyph's allowed
  successors as an immutable `frozendict[str, tuple[str, ...]]`;
  `enumerator.iter_roots()` walks `succ_1_2` → `succ_2_3` and `count_roots()`
  returns the cached length. Output order is unchanged (ORDER-lexicographic),
  so `--output` TSV and CLI goldens stay byte-stable. The shipped matrices now
  yield **21168** roots (was `21952`): `m_1-2` has a zeroed diagonal encoding
  `C1 ≠ C2`, while `m_2-3` keeps `C2 = C3`.
- **Deliverables:**
  - `src/arabic_roots/phonotactics.py` — added `successors()`; removed
    `is_allowed`; docstring corrected for diagonal semantics.
  - `src/arabic_roots/enumerator.py` — successor walk + unbounded content-keyed
    triple cache; `count_roots` reads the cache.
  - `_Archive/is_allowed.py` — archived predicate (scratch, outside lint/tests).
  - `tests/test_enumeration.py`, `tests/test_matrices.py`, `tests/test_cli.py` —
    updated pins, embedded reference oracle, diagonal pinning test.
  - `src/arabic_roots/statemachine.py` — stale docstring fixed.
  - `AGENTS.md` — §2 tree/prose, matrix comments, §3 citation note, §5
    reproducibility note.
  - `docs/enumeration-alternatives.md` — Decision section marked A + D accepted.
- **Acceptance evidence:**
  - `uv run pytest` — 46 passed; total coverage 99.63% (`enumerator.py`,
    `phonotactics.py`, `statemachine.py` at 100%).
  - Pinned counts: repo `21168`; synthetic all-`1` still `28³ = 21952`.
  - CLI goldens: first two roots `ء-ب-ء`, `ء-ب-ب`; first TSV line `ء\tب\tء`;
    `uv run enumerate-roots --limit 5` logs `Allowed triliteral roots: 21168`.
  - `uv run ruff check src tests`, `ruff format --check`, `mypy src tests`,
    `uv run ty check` all clean.
- **Deviations:**
  - This work is not a `docs/Future.md` PRD; it originated from the matrix edit
    and `docs/enumeration-alternatives.md`, so no Future.md marker was added.
- **Resolved open questions (decisions):**
  - **Enumeration method:** Option A (precomputed adjacency lists) chosen over
    B (numpy index arrays) and C (DFS/statemachine promotion) — smallest change,
    no new dependencies, preserved output order.
  - **Caching:** Option D included; **unbounded** cache keyed by
    `(shape, values.tobytes(), order)` per matrix. Only content-distinct
    matrices create entries.
  - **`is_allowed`:** archived to `_Archive/is_allowed.py`; the equivalence test
    now uses an **embedded independent reference oracle** (`.at`-based) rather
    than importing the archived code (avoids `sys.path` hacks).
  - **Diagonal rule:** the `C1`/`C2` vs. `C2`/`C3` asymmetry is admitted as an
    evidence-based rule — `C1 ≠ C2` (Greenberg 1950, *The Patterning of Root
    Morphemes in Semitic*, WORD 6:2, p.162); `C2 = C3` permitted.
  - **Order invariant:** the walk emits ORDER-lexicographic order identical to
    the old `itertools.product` order.
- **Follow-ups:**
  - Attested-root subtraction (possible = allowed − attested): deferred to a
    separate atomic commit. The rule cache is deliberately keyed on matrix
    content only and `iter_roots`/`count_roots` stay rule-only, so a later layer
    can filter the ordered stream against `load_attested()`'s `frozenset` (O(1)
    membership) without touching the enumerator or cache. Intended shape: a new
    function/module + `--exclude-attested` CLI flag, not a change to
    `enumerator.py`.
  - `C1 ≠ C2` homorganic sub-rule (Greenberg 1950 p.162) is still unencoded.
  - PRD 2 oracle, PRD 3 rendering, PRD 4 natural classes, PRD 5 branded glyph
    remain open.

---

## PRD 6 — Data directory layout (`roots/`, `rules/`, `transliterations/`)

- **Completed:** 2026-10-11
- **Commit:** TBD (agent does not commit; fill in after merge)
- **Summary:** Split the flat `data/` directory into three typed
  sub-directories so the axes AGENTS.md §2 keeps apart are physically
  separated: `data/roots/attested.csv` (lexicon),
  `data/rules/{m_1-2,m_2-3}.csv` (phonotactic rules), and
  `data/transliterations/buckwalter.csv` (ingest-only encoding table). The
  public API is unchanged: `--data-dir` / `DATA_DIR` remain the data *root*,
  and each loader appends its own sub-directory. File bytes are unchanged, so
  pinned counts (`21168` allowed, `3959` attested) are identical.
- **Deliverables:**
  - Moved `data/attested.csv` → `data/roots/attested.csv`,
    `data/m_1-2.csv` + `data/m_2-3.csv` → `data/rules/`,
    `data/buckwalter.csv` → `data/transliterations/`.
  - `src/arabic_roots/phonotactics.py` — added `RULES_SUBDIR = "rules"`;
    `load_matrices()` reads `<data_dir>/rules/`.
  - `src/arabic_roots/attestation.py` — added `ROOTS_SUBDIR = "roots"`;
    `load_attested()` reads `<data_dir>/roots/`.
  - `scripts/fetch_attested.py` — default out/map paths updated.
  - Docstrings/paths updated: `cli.py`, `statemachine.py`, `transliteration.py`,
    `alphabet.py`, `arabic_chain_bank_provider.py`.
  - Tests updated for the new layout (`test_matrices.py`, `test_attestation.py`,
    `test_transliteration.py`, `test_arabic_chain_bank_provider.py`).
  - Docs: `AGENTS.md` (tree, §2, §4, §7), `docs/running.md`,
    `docs/Future.md` (PRD 6 + path references).
- **Acceptance evidence:**
  - `uv run pytest` — 46 passed; total coverage 99.63%.
  - Counts unchanged: `uv run enumerate-roots --limit 5` logs
    `Allowed triliteral roots: 21168`; attested golden `3959`.
  - `uv run ruff check src tests scripts`, `ruff format --check`,
    `mypy src tests`, `uv run ty check` all clean.
- **Deviations:**
  - None; files were moved with plain `mv` (agent does not stage/commit), so
    git records the renames at the human's next `git add`.
- **Resolved open questions (decisions):**
  - The data root stays `<repo>/data`; `--data-dir` names the root, not a
    sub-directory. The split is expressed with per-module sub-directory
    constants (`RULES_SUBDIR`, `ROOTS_SUBDIR`) rather than a shared registry.
  - The ingest-only Buckwalter exception (AGENTS §4) now points at
    `data/transliterations/buckwalter.csv`.
- **Follow-ups:**
  - Attested-root subtraction (from the enumeration-rewrite entry) is
    unaffected: `load_attested()` resolves its new path internally, so the
    planned filter layer needs no change.

---

## Output formats — CSV via suffix inference (+ header on TSV)

- **Completed:** 2026-10-11
- **Commit:** TBD (agent does not commit; fill in after merge)
- **Summary:** Added a streaming, suffix-driven output layer so `--output`
  writes either TSV or CSV, inferred from the file extension. Both delimited
  formats now carry the header `c1,c2,c3` (previously TSV was headerless). An
  unknown or missing suffix is a loud error (exit code `2`). The writers use
  only the standard library (`csv`) and stream one root per row, preserving
  ORDER-lexicographic order.
- **Deliverables:**
  - `src/arabic_roots/writers.py` — `format_for_suffix()` +
    `write_roots()`, a `_write_delimited` core with `_write_tsv`/`_write_csv`.
  - `src/arabic_roots/cli.py` — delegates `--output` to `write_roots`;
    `parser.error()` on an unsupported suffix; updated help/docstring.
  - `tests/test_writers.py` — suffix resolution, headers, parent-dir creation,
    unknown-suffix errors.
  - `tests/test_cli.py` — TSV header assertion, new CSV test, unknown-suffix
    `SystemExit` test.
  - Docs: `AGENTS.md` (tree + §7), `docs/running.md` (options + output
    section), `README.md` (options + output note).
- **Acceptance evidence:**
  - `uv run pytest` green; `writers.py` fully covered.
  - `uv run enumerate-roots --limit 0 --output /tmp/roots.csv` writes header
    `c1,c2,c3` then `ء,ب,ء`; `.tsv` writes the tab-separated equivalent.
  - `ruff`, `ruff format --check`, `mypy --strict`, `ty check` clean; counts
    unchanged (21168).
- **Deviations:**
  - TSV gained a header (a byte change) to match CSV and avoid the pandas
    first-row-as-header footgun; `test_main_writes_tsv` was updated.
- **Resolved open questions (decisions):**
  - Format is selected by `--output` suffix (no `--format` flag); unknown
    suffix errors rather than defaulting.
  - Headers are on for both TSV and CSV; three glyph columns only for now.
  - Writers live in a reusable module (`writers.py`), not inline in `cli.py`.
  - `--format`/`--scheme` rendering stays out of scope (PRD 3).
- **Follow-ups:**
  - `docs/Future.md` PRDs 7–9: JSONL, Parquet (`pyarrow` extra), SQLite.
  - An `attested`/`variety` column or the possible-roots output is deferred to
    the attested-subtraction work.

---

## PRD 10 — Attested-root subtraction (possible roots)

- **Completed:** 2026-10-11
- **Commit:** TBD (agent does not commit; fill in after merge)
- **Summary:** The CLI now emits **possible** roots only — phonotactically
  legal but unattested — by composing the two existing axes. A new pure module
  `possible.py` filters the memoized enumeration (`iter_roots`) against a
  variety's attested `frozenset` (O(1) membership). Shipped data yields
  **17211** possible roots (`21168` allowed − `3957` attested∩allowed); the CLI
  logs both counts and warns that **2** attested roots are phonotactically
  illegal (`ب-ب-ر`, `و-و-ح`) — a rules-vs-lexicon disagreement.
- **Deliverables:**
  - `src/arabic_roots/possible.py` — `iter_possible()` / `count_possible()` /
    `attested_illegal()` (pure, no I/O, no cache).
  - `src/arabic_roots/cli.py` — loads matrices + attested; logs `Allowed` and
    `Possible`; warns on illegal attested; stdout sample and `--output` both
    consume `iter_possible(...)`.
  - `tests/test_possible.py` — subtraction, order, unknown variety, golden
    `17211`, illegal detection.
  - `tests/test_cli.py` — `test_main_limit_two` → `["ء-ب-ء", "ء-ب-ت"]`; new
    integration test (written file has 17211 rows, no `ك-ت-ب`).
  - `tests/test_attestation.py` — stale `ض-ض-ض` "legal but unattested"
    docstring corrected.
  - Docs: `README.md`, `docs/running.md` (output scope + warning), `AGENTS.md`
    (tree/§2/§7).
  - `_Archive/include-attested-option.md` — archived (unbuilt)
    `--include-attested` opt-in with its hook point.
- **Acceptance evidence:**
  - `uv run pytest` — 62 passed; `possible.py` at 100%.
  - `uv run enumerate-roots --limit 5` prints `ء-ب-ء`, `ء-ب-ت`, `ء-ب-ث` and
    logs `Allowed: 21168` / `Possible: 17211` plus the 2-root warning.
  - `ruff`, `ruff format --check`, `mypy --strict`, `ty check` all clean.
- **Deviations:**
  - None; `README.md`'s prior "17209" was corrected to **17211** (only the
    `3957` legal attested roots can be subtracted).
- **Resolved open questions (decisions):**
  - Subtraction is always on; there is **no** opt-in flag (the include-all
    option is archived only).
  - Variety is an internal `"msa"` default; no `--variety` flag yet.
  - No separate possible-set cache — filtering the memoized enumeration is
    cheap enough.
  - Attested-but-illegal roots are logged as a warning, not a hard error.
- **Follow-ups:**
  - PRD 11 (run logging) and PRDs 7–9 (JSONL/Parquet/SQLite) remain open.
  - A `--variety` flag and additional varieties arrive with PRD 1's
    Classical/dialect work.

---

## PRDs 7–9 — Additional output formats (JSONL, Parquet, SQLite)

- **Completed:** 2026-10-11
- **Commit:** TBD (agent does not commit; fill in after merge)
- **Summary:** Extended the suffix-driven writer layer with three formats
  alongside `.tsv`/`.csv`: `.jsonl` (one JSON object per line, literal glyphs),
  `.parquet` (columnar via the opt-in `pyarrow` extra), and `.sqlite` (a
  `roots` table with a primary key over the triple). The writer contract moved
  from a text handle to the destination `Path`, since Parquet and SQLite need
  the path (not a `TextIO`). All writers consume the streaming possible-roots
  iterable and preserve ORDER; no CLI flags changed.
- **Deliverables:**
  - `src/arabic_roots/writers.py` — `_Writer = Callable[[Path, Iterable[Triple]], int]`;
    `_write_jsonl`, `_write_parquet`, `_write_sqlite`; suffix map extended.
  - `pyproject.toml` — `[project.optional-dependencies] output = ["pyarrow>=18"]`
    plus `pyarrow` in the dev group; `uv.lock` updated (pyarrow 26.0.0).
  - `src/arabic_roots/cli.py` — `--output` help lists all five suffixes.
  - `tests/test_writers.py` — JSONL bytes/key-order/no-escapes, Parquet
    round-trip + missing-engine `ValueError`, SQLite round-trip / duplicate-PK /
    replace-existing, per-suffix dispatch.
  - Docs: `README.md`, `docs/running.md` (formats + `uv sync --extra output`),
    `AGENTS.md` (tree/§5/§7).
- **Acceptance evidence:**
  - `uv run pytest` — 68 passed; `writers.py` at 100%.
  - `uv sync --locked` clean with the updated lock; `pyarrow 26.0.0` resolves
    on Python 3.14 (cp314 wheel available).
  - `enumerate-roots --limit 0 --output /tmp/roots.{jsonl,parquet,sqlite}`
    each writes 17211 rows; `.tsv`/`.csv` unchanged.
  - `ruff`, `ruff format --check`, `mypy --strict`, `ty check` clean.
- **Deviations:**
  - None. The writer contract changed from `TextIO` to `Path` (internal only;
    the public `write_roots(path, triples)` signature is unchanged).
- **Resolved open questions (decisions):**
  - Parquet engine is an opt-in `output` extra **and** a dev dependency, so
    tests exercise it while core runtime deps stay lean.
  - SQLite suffix is `.sqlite` only.
  - JSONL uses default `json.dumps` spacing with `ensure_ascii=False`.
  - Parquet uses snappy compression (explicit).
  - Single `--output` per run; multiple formats are written by separate runs
    (no multi-output, no parallel writers).
- **Follow-ups:**
  - PRD 11 (run logging) remains open.
  - Attested-aware columns (e.g. a `roots.attested` flag) are deferred; the
    output is the possible-roots set, so such a column would be constant today.

---

## PRD 3 — Output transliteration schemes + optional delimiter

- **Completed:** 2026-10-11
- **Commit:** TBD (agent does not commit; fill in after merge)
- **Summary:** Added `--scheme {arabic,din31635,ijmes,ipa}` (default `arabic`)
  and `--delimiter` (default `-`) to the CLI. A new `render.py` builds
  glyph -> symbol maps per scheme — `arabic` (identity), `din31635`/`ipa` from
  the typed `Letter` fields, and `ijmes` loaded from a new
  `data/transliterations/ijmes.csv` — and renders roots at the I/O boundary.
  The scheme applies to both stdout and `--output` cells (columns stay
  separate; the delimiter is stdout-only); a delimiter clashing with the active
  scheme's symbols is rejected (exit `2`). Default invocation is unchanged
  (`ء-ب-ء`…).
- **Deliverables:**
  - `data/transliterations/ijmes.csv` — `glyph,ijmes` (28 rows), sourced from
    the owned IJMES chart (`Notes/TransChart 1.pdf`).
  - `src/arabic_roots/render.py` — `SCHEMES`, `build_schemes`,
    `render_cell`/`render_cells`/`iter_render_cells`/`render_triple`,
    `validate_delimiter`.
  - `src/arabic_roots/transliteration.py` — `TRANSLITERATIONS_SUBDIR`;
    `build_decoder(..., symbol_column="buckwalter")` generalized for IJMES.
  - `src/arabic_roots/cli.py` — `--scheme`/`--delimiter`; stdout and `--output`
    rendering.
  - `tests/test_render.py`, `tests/test_cli.py` (scheme/delimiter cases),
    `tests/test_transliteration.py` (generic message match).
  - Docs: `AGENTS.md` (§4 exception + tree + §7), `README.md`,
    `docs/running.md` (schemes/delimiter section).
- **Acceptance evidence:**
  - `uv run pytest` — 92 passed; `render.py` and `transliteration.py` at 100%.
  - `enumerate-roots --scheme din31635 --limit 3` -> `ʾ-b-ʾ`/`ʾ-b-t`/`ʾ-b-ṯ`;
    `--scheme ijmes` -> `ʾ-b-th`; `--scheme ipa` -> `ʔ-b-θ`; `--delimiter ""`
    -> `ءبء`; default unchanged.
  - `ruff`, `ruff format --check`, `mypy --strict`, `ty check` clean.
- **Deviations:**
  - IJMES is stored as CSV data (not a `Letter` field), and its `sh|kh|gh|th|dh`
    digraphs never appear in `src/`, per the §4 policy. The render-table test
    uses IJMES literals directly (tests are exempt).
- **Resolved open questions (decisions):**
  - Schemes shipped: all four (`arabic`, `din31635`, `ijmes`, `ipa`); IPA is
    included despite being phonetic.
  - Default delimiter stays `-` (no behavior change); `""` concatenates.
  - `--scheme` applies to both stdout and `--output`; `--delimiter` is
    stdout-only.
  - Rendering lives in `render.py`; scheme symbols are data, not code.
  - AGENTS §4 amended: the digraph ban targets `src/`; scheme tables live in
    `data/transliterations/*.csv`; tests may use IJMES literals.
- **Follow-ups:**
  - PRD 11 (run logging) remains open.

---

## PRD 11 — Run logging (effective options, embedded choices, output summary)

- **Completed:** 2026-10-11
- **Commit:** TBD (agent does not commit; fill in after merge)
- **Summary:** The CLI now logs a structured run record at `INFO`: a `run:`
  banner with the effective options and embedded choices (`data_dir`, `limit`,
  `output`, inferred `format`, `scheme`, `delimiter`, `variety=msa`), an
  `inputs:` line with resolved `rules/`/`roots/`/`transliterations/` paths, the
  `Allowed`/`Possible` counts, the illegal-attested warning, and a
  `wrote N possible roots to … (format)` summary. An opt-in `--log-file PATH`
  appends the same timestamped records (UTF-8) alongside stderr. Scope was
  widened from the original PRD (file logging was a non-goal).
- **Deliverables:**
  - `src/arabic_roots/cli.py` — `--log-file`; `_configure_logging` (stderr +
    appending `FileHandler`, timestamped `%Y-%m-%dT%H:%M:%S`); banner/inputs/
    summary lines; up-front `--output` suffix validation.
  - `tests/test_cli.py` — log-file (timestamped, mirrored to stderr), append
    across runs, `caplog` banner fields, parser default.
  - Docs: `AGENTS.md` §7, `README.md` (option + note), `docs/running.md`
    (Logging section), `.gitignore` (`*.log`).
- **Acceptance evidence:**
  - `uv run pytest` — 95 passed.
  - `enumerate-roots --limit 0 --log-file /tmp/er.log` writes a timestamped log
    mirroring stderr; a second run appends a second banner.
  - `ruff`, `ruff format --check`, `mypy --strict`, `ty check` clean; stdout and
    `--output` files unchanged; no new deps.
- **Deviations:**
  - File logging was originally a PRD 11 non-goal; the user requested it, so the
    PRD was amended (opt-in `--log-file`, appended, timestamped, teeing to
    stderr).
  - Switched from `logging.basicConfig` to a `_configure_logging` helper on the
    module logger (idempotent handler setup; avoids stripping pytest's capture
    handler).
- **Resolved open questions (decisions):**
  - Format: one `key=value` banner + `inputs:`/summary lines.
  - Opt-in `--log-file PATH`; **append**; **timestamp each line**; tee to stderr.
  - No `--log-level`/`--quiet` (fixed `INFO`).
  - Paths only (no input hashes/pins); banner on every run.
- **Follow-ups:**
  - `--log-level`/`--quiet`, log rotation, and input hashes/pins remain future
    options.
