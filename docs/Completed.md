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
  - Spot checks: `ك-ت-ب` attested; `ض-ض-ض` (legal, unattested) reported fake.
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
