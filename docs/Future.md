# Future work — micro-PRDs

Proposed features only; nothing here is implemented yet. Each PRD respects
the standing rules in `AGENTS.md`: rules live in `data/rules/*.csv`, the state
machine queries data but encodes no rules, files are UTF-8/NFC, and every
data claim needs a citable source plus a regression test.

---

## PRD 1 — Attested-roots data source (MSA + Classical; dialects later)

> **Implemented (2026-09-29) — see `docs/Completed.md`.** Kept below as history.

### Background

Today the repo can say whether a triple is *phonotactically legal*
(`M_1-2 ∧ M_2-3`), but not whether it is *attested*. A *possible root* is defined
as legal-but-unattested, so attestation data is the missing half of the
project's core concept.

### Goals

- Ship a versioned, citable store of all attested triliteral roots for two
  varieties: Modern Standard Arabic (MSA) and Classical Arabic.
- Expose `is_attested(c1, c2, c3, variety) -> bool` alongside the existing
  `is_allowed(...)` predicate.
- Keep dialects explicitly out of v1, but choose a schema that admits them
  later without migration.

### Non-goals (v1)

- Dialect coverage (Levantine, Egyptian, Maghrebi, …) — schema-ready only.
- Semantic glosses, morphology, or frequency counts — roots only.
- Deciding a single canonical source; multiple sources may attest one root.

### Proposed design

- New files `data/roots/attested_msa.csv` and
  `data/roots/attested_classical.csv` (one row per root: `c1,c2,c3,source`),
  or a single `data/roots/attested.csv` with a `variety` column
  (`msa` | `classical`) — decide at implementation time; the single file is
  preferred for one dedupe pass.
- Schema rules: glyphs literal UTF-8/NFC from `alphabet.ORDER` (hamza =
  `ء U+0621`, no carriers, no bare alif); one NFC-normalized row per root
  per variety; `source` column cites the lexicon (e.g. Wehr, Lane,
  *Sources.md* additions) — no sourceless rows.
- Loader `attestation.load_attested(data_dir) -> frozenset[tuple[str,str,str]]`
  (per variety), mirroring `phonotactics.load_matrices()`:
  default `<repo>/data`, `data_dir` override for `tmp_path` tests, axes
  validated against `ORDER`, duplicates rejected loudly.
- Predicate `attestation.is_attested(c1, c2, c3, attested_set) -> bool`
  with NFC normalization on ingest, same as `is_allowed`.

### Tests

- Schema tests: every row NFC, glyphs ⊆ `ORDER`, no duplicate rows, CSVs
  parse as UTF-8.
- Predicate tests: known-attested (e.g. ك-ت-ب) → `True` per variety;
  known-absent → `False`; invalid glyph → `ValueError`.
- Golden counts per variety (pinned, updated only with a source citation).

### Acceptance criteria

- `uv run pytest` green with per-variety attested counts pinned in tests.
- `AGENTS.md` Architecture tree lists the new `attestation.py` + CSVs.
- Dialect follow-up requires no schema change — only new `variety` values.

### Open questions

- Which lexicons are canonical for each variety, and how are conflicts
  (attested in one, absent in another) recorded?
- Weak roots (containing و / ي): store surface form only, or also
  underlying etymological form?

### Alternative / complementary source to evaluate — lisan345

[git85hub/lisan345](https://github.com/git85hub/lisan345) may be a more
appropriate source for the Classical list: a complete root inventory extracted
from *Lisān al-ʿArab*, with **6,529** triliteral roots (plus 2,551
quadriliteral and 183 quinquiliteral). Each CSV row carries the root in Arabic
(`LAB_ar`) and transliteration (`LAB_tr`) plus per-consonant place/manner
codes (`C1…`, `P1…`, `M1…`).

Why it is attractive:

- `LAB_ar` is Arabic script, so ingest needs no Buckwalter decode at all —
  it sidesteps the `data/transliterations/buckwalter.csv` exception entirely.
- It is the full *Lisān al-ʿArab* (Classical) inventory, not MSA, so it fits a
  new `variety` value rather than replacing the `msa` rows.
- Its place/manner columns are citable evidence (Watson, *The Phonology and
  Morphology of Arabic*, p. 13) that could justify specific `0`s in
  `data/rules/m_1-2.csv` / `data/rules/m_2-3.csv`, alongside Ryder.

Before committing any derived CSV: verify the license (not stated in the
README), pin the upstream commit, and decide whether lisan345 supplements or
supersedes ArabicChainBank as the Classical source. Citation: Elmaz, Orhan.
2026. *Lisan345*. http://github.com/git85hub/lisan345; also Elmaz, *Studien zu
den koranischen Hapaxlegomena unikaler Wurzeln* (Harrassowitz, 2011),
303–317.

---



## PRD 3 — Output transliteration schemes + optional delimiter

### Background

Stdout currently renders roots as hyphen-joined Arabic script (`ك-ت-ب`;
`cli.py` hardcodes `"-"`), and `--output` TSV is always tab-separated
glyphs. For papers, cross-checking against lexicons, or phonotactic
reasoning, users need named output schemes (DIN 31635, IJMES, IPA) and a
user-supplied delimiter between root consonants — defaulting to none
(concatenated glyphs, e.g. `كتب`), preserving today's machine-readable
behavior unless asked otherwise.

### Goals

ME: note that IPA probably would not be appropriate here!

- Add `--scheme {arabic,din31635,ijmes,ipa}` (default `arabic`): render
  each root consonant in the named scheme, e.g. ص-ب-ر → DIN `ṣ-b-r`,
  IPA `sˤ-b-r`.
- Add `--delimiter TEXT` (default `""`, i.e. none): join the three
  rendered consonants with a user-supplied separator (`"-"`, `"·"`, `" "`,
  …). Composes with `--scheme` on stdout.
- Keep Arabic script the internal source of truth: transliteration happens
  only in `cli.py`'s rendering layer — the one place the
  Unicode-exclusive policy already permits romanization (I/O boundary).

### Non-goals (v1)

- Accepting transliterated *input* (enumeration input stays Arabic
  script; see PRD 2's open question for the `check` subcommand).
- New schemes beyond the four named ones; no ad-hoc ASCII digraphs
  (`sh|kh|gh`) — still forbidden by policy.
- Changing the `--output` TSV column layout (stays `c1\tc2\tc3` in the
  chosen scheme; delimiter applies to stdout only).

### Proposed design

- New `render(triple, scheme, delimiter="") -> str` in (or next to)
  `cli.py`: look up each glyph in `alphabet.LOOKUP`, pick the field
  (`glyph` | `din31635` | `ijmes` | `ipa`), NFC-normalize, join with
  the delimiter.
- Gap to close first: `Letter` currently carries `ipa` + `din31635` but
  **no** `ijmes` field. Adding one requires transcribing the IJMES
  column from the `Transliteration Schemes.md` comparison table into
  `alphabet.py`, with a roundtrip property test
  (`ijmes → glyph → ijmes`) like the planned DIN one.
- Delimiter validation: must be a short NFC string that cannot be
  confused with a letter in the active scheme (reject tab/newline and
  scheme glyphs; document that `-` is conventional, `""` is default).
- Docs: `docs/running.md` gains a schemes/delimiter section with one
  example per scheme; `--help` text shows the default explicitly.

### Tests

- Render table test: a fixed sample (e.g. ك-ت-ب, ح-م-د) across all four
  schemes × delimiters `""`, `"-"`, `" "` — pinned strings.
- Roundtrip tests per scheme (romanized → glyph → romanized) where the
  scheme is reversible; IPA documents its known lossy spots instead.
- CLI tests: `--scheme din31635 --limit 1`, `--delimiter` composition,
  and default-invocation output unchanged (no delimiter).

### Acceptance criteria

- `uv run enumerate-roots --scheme ipa --delimiter "-" --limit 3` and the
  `python -m arabic_roots` equivalent print identical, correctly joined
  output; `ruff`, `mypy --strict`, `ty check`, `pytest` green.
- No transliteration keys leak into `enumerator.py`, `phonotactics.py`,
  or `statemachine.py` — rendering stays in the CLI layer.

### Open questions

- Exact IJMES spellings per glyph (transcribe from the comparison table;
  needs a linguist pass before pinning)?
- Should `--output` TSV gain a `--scheme` too, or stay Arabic-script-only
  for stable downstream joins?

---

## PRD 4 — Citable consonant natural classes (McCarthy's excluding categories)

### Background

The provisional `CATEGORIES` map in `alphabet.py` was removed: it carried no
citation, and its `"sibilants"` set was wrong (`ض` is a stop; `ظ` is a
non-sibilant emphatic fricative). AGENTS.md §3 forbids inventing a
classification without a source, and §2 requires every matrix `0` to cite a
page. Natural-class definitions are the missing evidence layer that would let
phonotactic prohibitions be stated (and tested) as classes rather than
hand-enumerated pairs.

### Goals

- Reinstate a typed natural-class table (`CATEGORIES` or equivalent) whose
  every entry cites a named source.
- Define the classes actually used in the Arabic co-occurrence literature
  (e.g. McCarthy's OCP/root-consonant co-occurrence classes), derived from the
  typed `Letter.place` / `Letter.manner` / `Letter.emphatic` fields.
- Make each class-based prohibition traceable to a matrix `0` with a citation
  plus a regression test, per AGENTS.md §2/§3.

### Non-goals

- Inventing prohibitions from theory alone — a class without a source stays
  out.
- ML-style one-hot feature encodings; classes are linguistic, not features.
- Changing the matrices in the same PR without a paired citation.

### Proposed design

- Add a `CATEGORIES: frozendict[str, tuple[str, ...]]` (or a typed
  `NaturalClass` record) built from `LETTERS`, each key documented with its
  source (candidate: McCarthy 1986/1994; Watson, *The Phonology and Morphology
  of Arabic*, p. 13; cf. PRD 1's lisan345 `C1…`/`P1…`/`M1…` columns).
- Correct the sibilant inventory (exclude `ض`, `ظ`) and pin it with a test.
- For each class-based `0` added to `data/rules/m_1-2.csv` /
  `data/rules/m_2-3.csv`, add the page citation and a regression test in the
  same commit.

### Tests

- Per-class membership pinned to a literal expected set.
- A test asserting every `CATEGORIES` key carries a non-empty source string.
- Regression tests for each newly zeroed pair, citing the source in the test
  name or docstring.

### Acceptance criteria

- `ruff`, `mypy --strict`, `ty check`, `pytest` green.
- No category exists without a citation; `AGENTS.md` §2 lists the reinstated
  table and its source.

### Open questions

- Which source is authoritative for the classes — McCarthy's OCP classes,
  Watson's place/manner grid, or both layered?
- Does lisan345's per-consonant `C1…`/`P1…`/`M1…` coding (PRD 1) supersede a
  hand-built table?

---

## PRD 5 — Branded `NormalizedGlyph` type

### Background

`alphabet.normalize_glyph` returns a plain `str`, so its postcondition — the
result is already NFC **and** in `ORDER` — is invisible to `mypy --strict` /
`ty`. That gap allowed a redundant re-normalization
(`unicodedata.normalize("NFC", normalize_glyph(x))`) and lets any raw `str`
reach ORDER-indexed lookups. The type system cannot express "already
normalized"; a brand can.

### Goals

- Add `NormalizedGlyph = NewType("NormalizedGlyph", str)` in `alphabet.py`.
- Return it from `normalize_glyph` and accept it where ORDER-indexing
  happens, so the normalization boundary is explicit in the types.
- Keep `nfc` as the plain `str -> str` raw-boundary helper.

### Non-goals

- Runtime enforcement: no wrapper class, no `__post_init__` overhead — the
  brand is erased at runtime and costs nothing.
- Forbidding re-normalization: since `NormalizedGlyph` is a `str` subtype,
  passing it back to a normalizer is still well-typed. The idempotence test
  (`test_normalize_glyph_is_idempotent`) remains the guard for that, not the
  type. This PRD is complementary, not a replacement.

### Proposed design

- `NormalizedGlyph = NewType("NormalizedGlyph", str)`;
  `normalize_glyph(...) -> NormalizedGlyph`.
- Type ORDER-indexed APIs (`is_allowed`, `is_attested`, matrix axes, the
  transliteration decoders) to take/emit `NormalizedGlyph`.
- Migrate incrementally; `nfc` stays `str -> str` at I/O boundaries.

### Tests

- A type-check fixture asserting a raw `str` is rejected where
  `NormalizedGlyph` is required (and that `normalize_glyph` output is
  accepted).
- Existing idempotence and `tests/test_unicode_policy.py` guards stay green.

### Acceptance criteria

- `mypy --strict` and `ty check` green; zero runtime behavior change; module
  docstrings note which functions require pre-normalized input.

### Open questions

- Should `is_allowed` accept raw `str` for ergonomics (normalizing internally)
  or require `NormalizedGlyph` for strictness?
- Does the brand live in `alphabet.py` or a dedicated `types.py`?

---

## PRD 6 — Data directory layout (`roots/`, `rules/`, `transliterations/`)

> **Implemented (2026-10-11) — see `docs/Completed.md`.** Kept below as history.

### Background

`data/` had grown into a flat mix of three semantically different artifact
kinds: a lexicon (`attested.csv`), phonotactic rules (`m_1-2.csv`,
`m_2-3.csv`), and an ingest-only encoding table (`buckwalter.csv`). A flat
directory makes it easy to conflate the axes AGENTS.md §2 keeps apart — rules
vs. lexicon vs. transliteration — and the empty `roots/`, `rules/`,
`transliterations/` sub-directories already sketched the intended split.

### Goals

- Move each artifact into its typed sub-directory under `data/`:
  - `data/roots/attested.csv` — attested-roots lexicon.
  - `data/rules/m_1-2.csv`, `data/rules/m_2-3.csv` — phonotactic matrices.
  - `data/transliterations/buckwalter.csv` — ingest-only encoding table.
- Keep the public API stable: `--data-dir` / `DATA_DIR` stay the data *root*;
  loaders append their own sub-directory.

### Non-goals

- Renaming files or changing their schemas (bytes are unchanged).
- Splitting `load_matrices` / `load_attested` into per-file loaders.
- Introducing a data-registry abstraction; module-local sub-directory
  constants suffice.

### Proposed design

- `phonotactics.RULES_SUBDIR = "rules"`; `load_matrices(data_dir)` reads
  `data_dir / RULES_SUBDIR / {m_1-2,m_2-3}.csv`.
- `attestation.ROOTS_SUBDIR = "roots"`; `load_attested(data_dir)` reads
  `data_dir / ROOTS_SUBDIR / "attested.csv"`.
- `scripts/fetch_attested.py` defaults to
  `data/roots/attested.csv` (out) and
  `data/transliterations/buckwalter.csv` (map).
- Tests build the sub-directory under `tmp_path` before writing fixtures.

### Tests

- `tests/test_matrices.py` and `tests/test_attestation.py` write into the
  sub-directory and reload through the public loaders.
- `tests/test_transliteration.py` and `tests/test_arabic_chain_bank_provider.py`
  point `_MAP_PATH` at `data/transliterations/buckwalter.csv`.

### Acceptance criteria

- `ruff`, `ruff format --check`, `mypy --strict`, `ty check`, `pytest` green.
- Counts unchanged: `21168` allowed roots; `3959` attested MSA roots.

### Resolved open questions

- The data root stays `<repo>/data`; `--data-dir` continues to name the root,
  not a sub-directory. Per-module sub-directory constants keep the split
  explicit without a shared registry.

---

## PRD 7 — JSONL output format

### Background

`--output` today writes flat, positional text (TSV, plus CSV). Flat formats
are brittle to extend: adding a field (e.g. an attestation flag) means a new
column and downstream schema churn. JSON Lines gives one self-describing
object per root and streams naturally, so a 21k-row enumeration never has to
be materialized or wrapped in an array.

### Goals

- Add a `.jsonl` output selected by suffix, alongside `.tsv`/`.csv`.
- Emit one JSON object per line: `{"c1": …, "c2": …, "c3": …}`, keys in fixed
  order, values as literal NFC glyphs.
- Stream (constant memory) and keep ORDER-lexicographic order.

### Non-goals (v1)

- A single JSON array document (whole-file) — separate if needed.
- Nested objects or extra fields (attested/variety/transliteration) — future.
- Reading JSONL back in (output-only).

### Proposed design

- Register a `_write_jsonl` writer in `writers.py`: `json.dumps({...},
  ensure_ascii=False)` per line with `\n`. `ensure_ascii=False` keeps Arabic
  glyphs literal, matching the Unicode-exclusive policy (no `\uXXXX` escapes).
- The suffix map gains `.jsonl`.

### Tests

- One object per line; parse each line and assert `["c1","c2","c3"]` key order.
- `ensure_ascii=False`: literal glyph bytes appear (no `\u` escapes).
- Row count matches the input; order preserved; NFC.

### Acceptance criteria

- `ruff`, `mypy --strict`, `ty check`, `pytest` green; stdlib `json` only.

### Open questions

- Compact separators (`(",", ":")`) or default spacing?
- Add optional fields now, or keep the object minimal until attestation lands?

---

## PRD 8 — Parquet output format

### Background

TSV/CSV/JSONL are row-oriented text. Columnar Parquet is typed, compressed,
and the native exchange format for pandas/polars analysis — useful for
phonotactic statistics, joins with attestation data, and future dataset growth
(quadriliteral, dialects). The current 21k rows are small, but Parquet keeps
schema and types explicit.

### Goals

- Add a `.parquet` output selected by suffix.
- Columns `c1`, `c2`, `c3` (UTF-8 string), NFC glyphs, ORDER-lexicographic row
  order preserved.
- Keep the engine optional so the core package gains no mandatory dependency.

### Non-goals (v1)

- Analytics/derived columns; partitioning or multi-file datasets.
- A read path (output-only).

### Proposed design

- Requires a Parquet engine. pandas ≥ 2.2 writes Parquet via `pyarrow` (or
  `fastparquet`), so this is a **new dependency** and must be justified per
  AGENTS §5. Preferred: a `[project.optional-dependencies] output = ["pyarrow"]`
  extra, so core `uv sync` stays lean; the writer raises a clear error if the
  engine is missing.
- `writers.py` builds a small DataFrame and calls `to_parquet`; the suffix map
  gains `.parquet`.

### Tests

- `pytest.importorskip("pyarrow")`; write then read back, asserting schema
  (`c1,c2,c3`), row count, first/last rows, and order.
- A test asserting a clear error when the engine is absent (monkeypatched
  import).

### Acceptance criteria

- `ruff`, `mypy --strict`, `ty check`, `pytest` green; core `uv sync` unchanged
  (the extra is opt-in).

### Open questions

- Optional extra vs. a core dependency (justify per AGENTS §5)?
- Compression codec (default snappy vs. zstd)?

---

## PRD 9 — SQLite output format

### Background

A single-file, queryable database turns the enumeration into an ad-hoc query
surface: index the consonants, join against attested roots, and run SQL for
counts/patterns — with no new runtime dependency (stdlib `sqlite3`).
Complements the text formats for analysis and downstream tooling.

### Goals

- Add a `.sqlite` output selected by suffix.
- Create a `roots` table `(c1 TEXT, c2 TEXT, c3 TEXT)` with a primary key over
  the triple; NFC glyphs; deterministic insertion in ORDER order.
- Stdlib `sqlite3` only.

### Non-goals (v1)

- Storing phonotactics/attestation tables, views, or migrations.
- Incremental/upsert semantics; each run writes a fresh database.

### Proposed design

- `_write_sqlite`: `sqlite3.connect(path)`, `CREATE TABLE roots(c1, c2, c3,
  PRIMARY KEY (c1, c2, c3))`, `executemany` insert, commit, close. The suffix
  map gains `.sqlite`.
- Overwrite semantics: if the file exists, replace it (delete/recreate) so runs
  are reproducible.

### Tests

- Open with `sqlite3`, assert row count matches the input, the primary key
  rejects a duplicate insert, and a sample of rows (incl. first/last) matches
  ORDER.
- NFC glyph storage round-trip.

### Acceptance criteria

- `ruff`, `mypy --strict`, `ty check`, `pytest` green; stdlib only.

### Open questions

- Suffix: `.sqlite`, `.db`, or both?
- Add an `attested` column/table once subtraction lands?
