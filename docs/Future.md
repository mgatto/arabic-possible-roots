# Future work — micro-PRDs

Proposed features only; nothing below PRD 4/5 is fully implemented. Each PRD
respects the standing rules in `AGENTS.md`: rules live in `data/rules/*.csv`,
files are UTF-8/NFC, and every data claim needs a citable source plus a
regression test.

Implemented PRDs are **not** listed here — see `docs/Completed.md` for the
shipped ledger (PRDs 1, 3, 6–11 and the enumeration rewrite). PRD 2 (the
single-root state-machine oracle) is **dropped**: `statemachine.py` and the
`python-statemachine` dependency were archived to `_Archive/`, and the oracle
idea will not be revived on that library. `docs/releasing.md` documents the
commitizen release workflow.

---

## ToDo

- [ ] Allow use as a library, too
  - [ ] Add documentation like Readthedocs
  - [ ] (Partial) `__init__.py` now re-exports the core public API and ships
        `py.typed`; a hosted API reference is the remaining step.

---

## PRD 4 — Citable consonant natural classes (McCarthy's excluding categories)

> **Partially implemented (2026-10-19) — see `docs/Completed.md`.** The
> `homorganic` matrices are now consumed at runtime (`load_matrix` /
> `load_matrices` compose `self` + `homorganic` per position), with the class
> membership asserted in `tests/test_matrices.py`. The typed, source-carrying
> `CATEGORIES` table itself is still open.

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
