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
