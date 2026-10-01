# Running `enumerate-roots`

Run everything from `Code/` (the project root) through `uv` so you get the
pinned Python 3.14 `.venv`:

```bash
uv sync --locked
uv run enumerate-roots --data-dir data --limit 10
```

## Correct commands

```bash
uv run enumerate-roots --data-dir data --limit 10   # primary console script
uv run python -m arabic_roots --limit 10            # module path
uv run python -m arabic_roots.cli --limit 10        # direct CLI module
```

More examples:

```bash
uv run enumerate-roots --limit 5
uv run enumerate-roots --data-dir data --limit 0 --output roots.tsv
```

Sample stdout (human-readable, hyphen-joined; `--output` TSV stays
tab-separated):

```text
ء-ء-ء
ء-ء-ب
```

## Why it fails

| Command                            | Why it fails                                                                                                                                                                  |
|------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `python enumerate-roots …`         | `python` expects a script *file*; `enumerate-roots` is a generated binary in `.venv/bin/` (from `[project.scripts]`), not `./enumerate-roots` → `can't open file … [Errno 2]` |
| `python -m enumerate-roots`        | No such module; the module is `arabic_roots.cli` (dashes aren't valid module names)                                                                                           |
| system `python` / `python3` (3.11) | Wrong interpreter; repo pins `==3.14.*` — only `uv run` guarantees 3.14.7                                                                                                     |

## Options

| Flag         | Default       | Meaning                                              |
|--------------|---------------|------------------------------------------------------|
| `--data-dir` | `<repo>/data` | Directory holding `m_1-2.csv` and `m_2-3.csv`        |
| `--limit`    | `10`          | How many sample roots to print (`0` prints none)     |
| `--output`   | none          | Optional UTF-8 NFC TSV path for the full enumeration |

## Attested roots (`data/attested.csv`)

`data/attested.csv` holds the 3,959 MSA triliteral roots derived from
[CAMeL-Lab/ArabicChainBank](https://github.com/CAMeL-Lab/ArabicChainBank) at a
pinned commit. It is regenerated build-time from upstream `lemmas.csv`,
decoding the Buckwalter `ROOT` column with `data/buckwalter.csv` (the only
place Buckwalter is allowed — see AGENTS.md §4):

```bash
uv run python scripts/fetch_attested.py                     # pinned raw URL
uv run python scripts/fetch_attested.py --lemmas /tmp/lemmas.csv --sha <sha>
```

The runtime loader is `arabic_roots.attestation.load_attested()`; query one
triple with `is_attested(c1, c2, c3, attested, variety="msa")`. Re-pin the
golden count in `tests/test_attestation.py` only when the upstream SHA changes.
Do not edit `data/attested.csv` by hand.

## Unicode note

Roots print as literal Arabic glyphs. Use a terminal that renders Arabic,
with `PYTHONUTF8=1` and `LC_ALL=C.UTF-8`.
