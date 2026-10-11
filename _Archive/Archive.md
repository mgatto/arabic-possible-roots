# PRD Archives

## PRD 2 — Statemachine Yes/No oracle (`is_valid` AND `is_attested`)

### Background

`TriliteralMachine` (`statemachine.py`) is currently a single-root guard
prototype: it walks `r_0 → r_1 → r_2 → r_3` with matrix guards but sits off
the enumeration path (batch work lives in `enumerator.py`). The natural
next step is a query path that answers, for one candidate triple, two
Yes/No questions: *is it phonotactically valid?* and *is it attested?*

### Goals

- Add a single-root oracle returning a 4-way verdict:
  - valid + attested → real root (e.g. ك-ت-ب)
  - valid + unattested → **possible root** (the project's target concept)
  - invalid + unattested → impossible root
  - invalid + attested → data inconsistency (matrices vs. attestation
    disagree — must be surfaced, never silently passed)
- Keep the standing invariant: the machine encodes **no** rules; guards
  query `M_1-2`/`M_2-3` (PRD 1's attested set for the second question).

### Non-goals

- Batch enumeration (stays in `enumerator.py`).
- Explaining *why* a pair is forbidden — verdicts only in v1.

### Proposed design

- New `Verdict` result (`NamedTuple`: `is_valid: bool`,
  `is_attested: bool`, plus a `label` for the 4-way classification above).
- New machine (or extension of `TriliteralMachine`) with terminal
  classification states, e.g. `r_3 → {valid, invalid} × {attested, other}`:
  `emit` transitions guarded by `pair12_allowed` / `pair23_allowed`
  (existing), then an attestation lookup against the PRD 1 set.
  Exact state topology decided at implementation; the batch path
  (`enumerator.py`) and `is_allowed` stay the single source of truth for
  validity so driver and oracle cannot diverge.
- CLI: `uv run enumerate-roots check ك ت ب` (or `query`) printing the two
  Yes/No answers plus the label; exit code `0` always (verdicts are data,
  not errors). Depends on PRD 1 data files being present.

### Tests

- Oracle agrees with `is_allowed` + `is_attested` on a sampled grid,
  including the diagonal (geminates) and at least one pinned `0`-pair
  once Ryder prohibitions land.
- The inconsistent quadrant (invalid + attested) is constructible in a
  `tmp_path` fixture and surfaces its label.
- CLI `check` test asserting stdout lines for a real root, a possible root,
  and an impossible root.

### Acceptance criteria

- `uv run enumerate-roots check …` and `uv run python -m arabic_roots check …`
  both work; outputs documented in `../docs/running.md`.
- `mypy --strict`, `ty check`, `ruff`, `pytest` all green; no `print()` in
  `../src` outside the CLI's stdout path.
- AGENTS.md records the oracle's state diagram in one ASCII sketch.

### Open questions

- Extend `TriliteralMachine` in place vs. a separate `RootOracleMachine`
  (separation is preferred — driver vs. judge shouldn't share states)?
- Should `check` accept DIN 31635 / IPA input at the CLI boundary, or
  Arabic script only (Unicode-exclusive policy suggests script-only)?

---
