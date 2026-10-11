# Enumeration alternatives — matrix-walking vs. generate-then-check

Design options for replacing the current "generate all `28³` triples, then
filter with `is_allowed`" enumeration with a walk that follows only the `1`s
encoded in `m_1-2.csv` / `m_2-3.csv`. Nothing here is implemented yet; this
file exists so the four candidates can be built and benchmarked before a
choice is made.

## Background

Current production path (`src/arabic_roots/enumerator.py`):

```python
for first, second, third in itertools.product(order, repeat=3):
    if is_allowed(first, second, third, m_1_2, m_2_3):
        yield first, second, third
```

`is_allowed` (`phonotactics.py`) does, per triple: three `normalize_glyph`
calls (each NFC + inventory validation) and two `pandas.DataFrame.at` lookups
(`m_1_2[c1, c2]` and `m_2_3[c2, c3]`). For a permissive matrix this is
`28³ = 21952` iterations regardless of how many pairs are forbidden, and every
iteration pays the pandas + normalization overhead.

The matrices are the rules. The desired shape is a traversal that emits only
allowed roots, i.e. visits exactly the triples where `M_1-2[c1, c2]` and
`M_2-3[c2, c3]` are both `1`.

### Current data state (drives the expected counts)

`data/rules/m_1-2.csv` now has a **zeroed diagonal** (C1 == C2 gemination
forbidden); `data/rules/m_2-3.csv` still has an all-`1` diagonal (C2 == C3
gemination permitted).
Read-only measurement:

- `m_1-2` diagonal `0` for all 28 glyphs → every `c1 == c2` triple removed →
  `28 × 28 = 784` forbidden triples.
- `count_roots` = **21168** (was `21952`).
- `m_2-3` diagonal still `1` → no additional removals.

Any option below must reproduce **21168** on the current data, and must be
validated against synthetic matrices too (all-`1` → `21952`; single zeroed
pair `M_1-2[ب,ت]` → `21952 − 28`).

## Invariants every option must preserve

1. **Output order** must remain byte-identical to today: lexicographic by
   `ORDER` index (outer `c1`, then `c2`, then `c3`), i.e. exactly
   `itertools.product(ORDER, repeat=3)` restricted to allowed triples. Any
   successor list must therefore be emitted in `ORDER` order. This keeps
   `--output` TSV joins and any golden first-`N` output stable.
2. **Equivalence** with `is_allowed`: for every triple,
   `triple in iter_roots(...) == is_allowed(...)`. Keep this as a regression
   test (`tests/test_enumeration.py::test_enumerator_matches_is_allowed`).
3. **Determinism / reproducibility** (AGENTS §5): no set iteration, no dict
   ordering dependence beyond insertion in `ORDER`.
4. **Immutability** (AGENTS §5): `tuple` / `frozendict`, no mutation of caller
   matrices.
5. **No new dependencies** without justification.
6. `order` parameter semantics preserved: callers may pass a custom axis order.

---

## Option A — Precomputed adjacency lists (recommended)

Add a helper to `phonotactics.py`:

```python
def successors(
    matrix: pd.DataFrame, order: tuple[str, ...] = ORDER
) -> frozendict[str, tuple[str, ...]]:
    # for each row glyph, the column glyphs (in `order`) whose cell is True
```

Enumerator becomes a triple nested loop that never consults pandas or
`normalize_glyph` in the hot path:

```python
def iter_roots(m_1_2, m_2_3, order=ORDER):
    succ12 = successors(m_1_2, order)
    succ23 = successors(m_2_3, order)
    for c1 in order:
        for c2 in succ12[c1]:
            for c3 in succ23[c2]:
                yield c1, c2, c3
```

Count becomes closed-form (no yielding at all):

```python
def count_roots(m_1_2, m_2_3, order=ORDER):
    succ12 = successors(m_1_2, order)
    succ23 = successors(m_2_3, order)
    return sum(len(succ23[c2]) for c1 in order for c2 in succ12[c1])
```

- **Cost**: preprocess `O(28²)`; enumerate `O(#allowed)`; count `O(28²)`.
- **Pros**: pure Python; no new deps; smallest diff; preserves order trivially;
  immutable tuples; removes all pandas/`normalize_glyph` calls from the loop.
- **Cons**: rebuilds two dicts per call (cheap; see Option D if it matters).
- **Keeps** `is_allowed` as the single-triple predicate / state-machine guard.

## Option B — numpy index arrays

Convert each matrix once with `matrix.to_numpy()`; per row use
`np.flatnonzero(row)` to get allowed column indices, walk integer indices, and
map index → glyph only when yielding.

```python
a12 = m_1_2.to_numpy()
a23 = m_2_3.to_numpy()
for i, c1 in enumerate(order):
    for j in np.flatnonzero(a12[i]):
        for k in np.flatnonzero(a23[j]):
            yield order[i], order[j], order[k]
```

- **Cost**: preprocess `O(28²)`; enumerate `O(#allowed)`.
- **Pros**: fast numeric indexing; avoids per-triple dict lookups.
- **Cons**: adds numpy to the hot path and index↔glyph bookkeeping; at width 28
  the gain over A is marginal; more code and a second representation of the
  same data to keep in sync.
- **Note**: `pandas` already vendors numpy, but relying on it directly in the
  enumerator is a new coupling; benchmark before choosing.

## Option C — DFS generator (promote the state machine)

Replace the nested loops with an explicit depth-first walk over positions
`r0 → r3`, consulting the matrices per transition, in the spirit of
`statemachine.py`:

```python
def iter_roots(m_1_2, m_2_3, order=ORDER):
    def walk(prefix):
        if len(prefix) == 3:
            yield prefix
            return
        # choose the gating matrix by position; iterate allowed successors
        ...
    yield from walk(())
```

- **Cost**: same asymptotic class as A/B, higher constant factor (function-call
  per node).
- **Pros**: generalizes to quadriliteral/quinquiliteral later; conceptually
  matches the existing `TriliteralMachine`.
- **Cons**: `statemachine.py` is explicitly **not** on the enumeration path and
  must not carry rule logic (AGENTS §2). Promoting it means moving the guard
  logic out and re-documenting the architecture. Slower per triple than A.
  Larger refactor / review surface.

## Option D — Cache materialized triples (complements A/B/C)

Memoize the full `tuple[tuple[str, str, str], ...]` (keyed on matrix identity
or a content hash) so repeated traversals are free. Relevant because
`cli.py` currently walks three times: `count_roots` (line 68), the sample
`iter_roots` (line 71), and the `--output` `iter_roots` (line 80).

- **Pros**: removes redundant traversals; a single materialization serves
  count + sample + output.
- **Cons**: module/state caching to key and invalidate; materializes
  `#allowed` tuples in memory (trivial here, ~21k). Unnecessary if A's cost is
  already acceptable. Composable with any of A–C.

---

## Benchmark plan (for later)

Build all four behind the same `iter_roots` / `count_roots` signatures, then
compare with `timeit` on the repo data and on synthetic stress matrices:

- **Correctness first**: each option must equal the `is_allowed` filter
  (`test_enumerator_matches_is_allowed`) and must yield identical ordered
  output to today's product order.
- **Fixtures**: (1) repo data (21168); (2) all-`1` (21952); (3) sparse
  synthetic (e.g. zero out a whole row/column to widen the allowed/forbidden
  gap); (4) single-zeroed-pair (21924).
- **Metrics**: `iter_roots` full consumption; `count_roots`; cold vs. warm
  (Option D); peak allocations if desired.
- **Report**: wall time per fixture per option, plus a note on code size /
  review surface, so the choice is not made on speed alone.

## Decision

**Accepted: Option A + Option D** (2026-10-11). Enumeration walks per-glyph
successor lists (`phonotactics.successors()`) and the materialized triples are
memoized on matrix content (unbounded cache). `is_allowed` was archived to
`_Archive/is_allowed.py`; the equivalence test now uses an embedded independent
reference oracle. The `C1 ≠ C2` / `C2 = C3` diagonal asymmetry is admitted as
an evidence-based rule (Greenberg 1950, WORD 6:2, p.162). See
`docs/Completed.md` for the shipped ledger entry.

## Follow-ups regardless of choice

- `data/rules/m_1-2.csv` diagonal rule needs a citation and a pinning regression
  test (AGENTS §3/§7); `phonotactics.py` docstring and AGENTS §1/§2 currently
  state "diagonal is `1` / gemination permitted", which is now wrong for
  C1-C2.
- Golden tests to update: `tests/test_matrices.py` (all-cells-`1` assertion),
  `tests/test_enumeration.py` (`28³` baseline). Keep a synthetic all-`1`
  fixture so the `28³` permissive baseline stays covered.
