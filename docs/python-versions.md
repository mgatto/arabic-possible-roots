# Python version compatibility and certification

Status: the disposable-copy certification runner is implemented (2026-11-11). The proposed change from a 3.14 floor to a 3.13 floor is still a plan; `pyproject.toml`, `.python-version`, and `uv.lock` remain pinned to 3.14 for now.

## Current state

| Item | Current value | Location |
|---|---|---|
| Package metadata | `requires-python = "==3.14.*"` | `pyproject.toml` |
| Local interpreter pin | `3.14` | `.python-version` |
| Lockfile metadata | `requires-python = "==3.14.*"` | `uv.lock` |
| Ruff target | `py314` | `[tool.ruff]` |
| Mypy target | `3.14` | `[tool.mypy]` |
| Ty target | `3.14` | `[tool.ty.environment]` |

The source itself is already compatible with 3.13. All modules and tests parse under 3.13, and the runtime dependencies (`pandas`, `frozendict`, `pyarrow`) publish 3.13 builds. The only blockers are the metadata pins above.

The real syntax floor is **3.12**, not 3.14: `enumerator.py` and `writers.py` use PEP 695 `type` aliases (`type _Triples = ...`), which require Python 3.12. Python 3.11 and older cannot import the package without rewriting those aliases.

## Certification method: disposable copies only

All multi-version certification runs through `scripts/test_python_versions.py`. The script copies the working tree to a temporary directory, patches only the copy, and runs the gates there. The repository configuration is never modified.

Testing in-place is not accepted: do not run `uv sync --python <other>` in the repository, bootstrap a different interpreter into the repository `.venv`, or certify a source-only `PYTHONPATH` run. Those paths bypass or mutate the pinned project configuration and are not reproducible evidence.

The script's copy is disposable:

- By default, the copy is deleted after the run, whether the run passes or fails.
- `--keep` preserves the copy and prints its path for debugging.
- Reports are written outside the copy, so evidence survives cleanup.

## Automated runner

```bash
uv run python scripts/test_python_versions.py
```

Default matrix:

| Selector | Role | Blocking |
|---|---|---|
| `3.12` | experimental | no |
| `3.13` | minimum supported target | yes |
| `3.14` | current supported version | yes |
| `3.15` | pre-release experiment | no |

The runner exits nonzero when a blocking version fails. Experimental failures are reported but do not fail the run unless `--strict` is used.

Options:

| Option | Meaning |
|---|---|
| `VERSIONS...` | Selectors to test; overrides the default set and preserves known roles. Comma-separated values are accepted. |
| `--strict` | Treat every selected version as blocking. |
| `--report-dir PATH` | Use an exact report directory instead of `.python-matrix/<timestamp>/`. |
| `--dry-run` | Print the copy, patch, and command plan without installing or running anything. |
| `--keep` | Preserve disposable copies and print their paths. |
| `--allow-dirty` | Run from a dirty working tree; evidence is marked dirty. Without this flag, a dirty tree is rejected. |

Examples:

```bash
uv run python scripts/test_python_versions.py
uv run python scripts/test_python_versions.py 3.13 3.14
uv run python scripts/test_python_versions.py --strict
uv run python scripts/test_python_versions.py --report-dir /tmp/apr-matrix
uv run python scripts/test_python_versions.py --dry-run
uv run python scripts/test_python_versions.py --allow-dirty
```

For each selected version the runner:

1. Installs/locates the interpreter with `uv python install` and `uv python find`, then records the exact version.
2. Copies the working tree, excluding `.git`, `.venv`, caches, coverage, build outputs, `.python-matrix`, and `_Archive`.
3. Patches only the copy's `pyproject.toml`: `requires-python`, the ruff target, the mypy target, and the ty target.
4. Deletes the copy's `.python-version` and `uv.lock`, so dependencies resolve fresh for that interpreter.
5. Runs `uv sync --python <resolved-path>`, then the gates from AGENTS.md §5:
   - `pytest`
   - `ruff check src tests`
   - `ruff format --check src tests`
   - `mypy src tests`
   - `ty check`
   - `enumerate-roots --limit 5`
6. Continues to the next version after a failure.

Reports are written to `.python-matrix/<timestamp>/` by default and are ignored by git:

- `<selector>/commands.log` — full command output.
- `summary.json` — machine-readable evidence, including commit, dirty state, interpreter, gate results, durations, and kept-copy paths.
- `summary.md` — Markdown summary and certification rows for the ledger below.

The runner never edits this document. A human reviews the report and records certified rows here.

## Proposed change: lower the floor from 3.14 to 3.13

When this is executed, it should be a metadata and tooling change, not a source change. The following edits are expected:

| File / setting | Proposed value | Reason |
|---|---|---|
| `pyproject.toml` → `requires-python` | `">=3.13"` | Allow 3.13 while remaining open to 3.14 and newer |
| `pyproject.toml` → `[tool.ruff] target-version` | `"py313"` | Do not allow lint rules for syntax newer than the supported floor |
| `pyproject.toml` → `[tool.mypy] python_version` | `"3.13"` | Type-check against the minimum supported version |
| `pyproject.toml` → `[tool.ty.environment] python-version` | `"3.13"` | Same as mypy |
| `pyproject.toml` → optional `[project] classifiers` | add 3.13 and 3.14 | Advertise the certified versions |
| `.python-version` | open decision: keep `3.14` or change to `3.13` | See below |
| `uv.lock` | regenerate with `uv lock` | Re-lock against the loosened requirement |
| `README.md` → Requirements | update the 3.14-only wording | Keep public docs truthful |
| `docs/running.md` → failure table | update the “only 3.14” row | Same |
| `AGENTS.md` §2 → Runtime | replace “Python 3.14 only” | Same |

No matrix, alphabet, enumeration, attestation, or test logic should need to change. The golden counts are interpreter-independent.

Recommended shape: `requires-python = ">=3.13"` with no upper bound, and let the certification matrix cover supported versions. An upper bound such as `">=3.13,<3.15"` would block future 3.15 users even when the code works.

### Open decision: `.python-version`

- **Keep `3.14`:** development uses the newest stable interpreter; 3.13 is certified by the matrix. Ruff, mypy, and ty can still target `py313`, so newer syntax is caught statically.
- **Move to `3.13`:** the default development environment is the minimum supported version, so accidental 3.14-only runtime behavior is caught immediately.

Either is workable. The important invariant is that at least one routine run uses the minimum supported version.

### Constraints while supporting 3.13

Python 3.14 implements PEP 649 (via PEP 749), so annotations are lazily evaluated. Python 3.13 evaluates annotations eagerly by default. The current code does not depend on lazy evaluation: it has no `TYPE_CHECKING` forward references and no `typing.get_type_hints` usage. Future code must avoid relying on 3.14-only deferred annotation behavior, because this repository also forbids `from __future__ import annotations` (AGENTS.md §2).

## Certification model

Formal certification is recorded here, in one canonical ledger. When a version is certified, record the exact patch release, commit SHA, date, and the runner report. “Python 3.13” is not enough evidence; record `3.13.5`, `3.13.15`, and so on.

### Status values

| Status | Meaning |
|---|---|
| Certified | Full quality gates passed on a recorded commit and date |
| Experimental | Tested, but not a support promise; may be re-tested later |
| Unsupported | Known not to work, or outside the tested range |

### Proposed initial ledger

| Interpreter | Status | Rationale |
|---|---|---|
| 3.11 and older | Unsupported | PEP 695 `type` aliases do not parse; `StrEnum` also starts at 3.11 |
| 3.12 | Experimental | Current syntax parses; run the matrix before making any support claim |
| 3.13 | Target certified version | Current code parses; dependencies publish 3.13 builds |
| 3.14 | Current certified version | Existing pinned development and lock environment |
| 3.15 | Experimental / pre-release | Available as a release candidate; test only, no support promise |

After the floor is lowered, the minimum support statement should be 3.13. Older versions remain documented as unsupported unless a separate backport is attempted.

### Evidence template

```text
Interpreter: CPython 3.13.5
Commit: <git rev-parse HEAD>
Date: YYYY-MM-DD
Command: uv run python scripts/test_python_versions.py 3.13
Report: .python-matrix/<timestamp>/summary.json
Result: pass
Notes: <dependency or platform caveats>
```

The runner records the exact interpreter with `python -VV` from the resolved interpreter path, and records the repository commit and dirty state before running.

### Where certification appears

- `docs/python-versions.md` is the canonical ledger and procedure.
- `README.md` should carry a short support statement once the floor changes, for example “Python 3.13 and 3.14 are certified; see `docs/python-versions.md` for evidence.”
- `docs/Completed.md` should get an entry only when the support-floor change ships, not when a version is merely tested.
- A CI status badge can point to the matrix once CI exists, but the ledger here remains the durable record.

## Future automation

The local certification runner exists; the repository still has no CI configuration. When CI is added, each version should run in a fresh checkout or through the same disposable-copy runner. Never run multiple versions against one shared workspace or mutate the repository metadata for a single job.

Recommended matrix:

- 3.13: minimum supported version, required to pass.
- 3.14: current stable, required to pass.
- 3.15: pre-release, allowed to fail until dependencies catch up.
- 3.12: experimental, only while a backport or compatibility claim is under consideration.

Once `requires-python` is `>=3.13`, a clean CI checkout per version is equivalent to a disposable copy. Until then, invoke the runner so the metadata patch stays confined to the copy.

## Caveats

- Pre-release interpreters may need an explicit version such as `3.15.0rc2`; `uv python install 3.15` may not select a pre-release automatically.
- `pyarrow` is the most likely dependency bottleneck for a new interpreter. The core package only imports it lazily through the Parquet writer, but the dev group installs it, and `tests/test_writers.py` exercises it when available.
- macOS system Python is not part of the support target. Always use `uv` or the disposable-copy runner.
- The version-single-sourcing test requires an installed distribution, so the disposable copy must be synchronized and installed. Source-only `PYTHONPATH` runs are smoke tests, not certification.
- Tests are deterministic across supported interpreters; no golden count should change when only the interpreter changes.
- Formal certification requires a clean working tree. Use `--allow-dirty` only for local experiments; dirty reports are not suitable as ledger evidence.
