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
ء-ب-ء
ء-ب-ت
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
| `--data-dir` | `<repo>/data` | Data root holding `rules/` (`m_1-2.csv`, `m_2-3.csv`)  |
| `--limit`    | `10`          | How many sample roots to print (`0` prints none)     |
| `--output`   | none          | Output path; format inferred from suffix (`.tsv`, `.csv`) |
| `--scheme`   | `arabic`      | Output scheme: `arabic`, `din31635`, `ijmes`, `ipa`  |
| `--delimiter`| `-`           | Separator between rendered consonants on stdout      |

## Schemes and delimiter

`--scheme` renders each consonant (`arabic` default, or `din31635`, `ijmes`,
`ipa`); it applies to stdout and to `--output` cells alike (the file columns
stay separate). `--delimiter` joins the rendered consonants on stdout (default
`-`; `""` concatenates). A delimiter that clashes with the active scheme's
symbols is rejected (exit code `2`).

```bash
uv run enumerate-roots --scheme din31635 --delimiter "-" --limit 3
uv run enumerate-roots --scheme ijmes --limit 3
uv run enumerate-roots --scheme ipa --limit 3
uv run enumerate-roots --delimiter "" --limit 3
```

Sample (`--scheme din31635 --limit 3`):

```text
ʾ-b-ʾ
ʾ-b-t
ʾ-b-ṯ
```

## Output scope (possible roots)

`enumerate-roots` emits **possible** roots: phonotactically legal
(`M_1-2 ∧ M_2-3`) but *not* attested. It logs both counts and warns when the
lexicon attests a root the matrices forbid:

```text
INFO Allowed triliteral roots: 21168
INFO Possible triliteral roots: 17211
WARNING 2 attested roots are phonotactically illegal: ب-ب-ر, و-و-ح
```

Logs go to **stderr**; stdout carries only the `--limit` sample.

## Output files

`--output PATH` writes the **full** possible-roots set (ignoring `--limit`).
The format is inferred from the suffix:

- `.tsv` — tab-separated, header `c1\tc2\tc3`.
- `.csv` — comma-separated, header `c1,c2,c3`.
- `.jsonl` — one JSON object per line (`{"c1": …, "c2": …, "c3": …}`).
- `.parquet` — columnar; requires the optional extra (`uv sync --extra output`).
- `.sqlite` — a `roots(c1, c2, c3)` table with a primary key over the triple.

Text formats are UTF-8/NFC with LF line endings; parent directories are
created; ORDER is preserved. An unknown or missing suffix is an error (exit
code `2`), as is `.parquet` without `pyarrow`.

```bash
uv run enumerate-roots --limit 0 --output roots.tsv
uv run enumerate-roots --limit 0 --output roots.csv
uv run enumerate-roots --limit 0 --output roots.jsonl
uv run enumerate-roots --limit 0 --output roots.sqlite
uv sync --extra output   # one-time, for Parquet
uv run enumerate-roots --limit 0 --output roots.parquet
```

## Attested roots (`data/roots/attested.csv`)

`data/roots/attested.csv` holds the 3,959 MSA triliteral roots derived from
[CAMeL-Lab/ArabicChainBank](https://github.com/CAMeL-Lab/ArabicChainBank) at a
pinned commit. It is regenerated build-time from upstream `lemmas.csv`,
decoding the Buckwalter `ROOT` column with
`data/transliterations/buckwalter.csv` (the only place Buckwalter is allowed —
see AGENTS.md §4):

```bash
uv run python scripts/fetch_attested.py                     # pinned raw URL
uv run python scripts/fetch_attested.py --lemmas /tmp/lemmas.csv --sha <sha>
```

The runtime loader is `arabic_roots.attestation.load_attested()`; query one
triple with `is_attested(c1, c2, c3, attested, variety="msa")`. Re-pin the
golden count in `tests/test_attestation.py` only when the upstream SHA changes.
Do not edit `data/roots/attested.csv` by hand.

## Unicode note

Roots print as literal Arabic glyphs. Use a terminal that renders Arabic,
with `PYTHONUTF8=1` and `LC_ALL=C.UTF-8`.
