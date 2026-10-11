"""Streaming output writers for enumerated roots, selected by file suffix.

The batch enumerator yields ``(c1, c2, c3)`` triples; this module turns them
into a serialized file whose format is inferred from the ``--output`` suffix.
Supported today:

- ``.tsv`` / ``.csv`` — delimited text, header ``c1,c2,c3``, one root per row.
- ``.jsonl`` — one JSON object per line (literal NFC glyphs).
- ``.parquet`` — columnar, requires the optional ``output`` extra (``pyarrow``).
- ``.sqlite`` — a ``roots`` table with a primary key over the triple.

All writers consume a streaming iterable and preserve the enumerator's
ORDER-lexicographic order. Only ``.parquet`` needs a non-stdlib dependency, and
it is imported lazily (via pandas) so the core install stays lean. The layer is
reusable by other programs (AGENTS §1).
"""

import csv
import json
import sqlite3
from collections.abc import Callable, Iterable
from contextlib import closing
from pathlib import Path

import pandas as pd
from frozendict import frozendict

from arabic_roots.alphabet import nfc

__all__ = ["format_for_suffix", "write_roots"]

type Triple = tuple[str, str, str]
type _Writer = Callable[[Path, Iterable[Triple]], int]

_HEADER: tuple[str, str, str] = ("c1", "c2", "c3")


def _write_delimited(path: Path, triples: Iterable[Triple], delimiter: str) -> int:
    """Write the header and one row per triple, returning the row count."""
    count = 0
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter=delimiter, lineterminator="\n")
        writer.writerow(_HEADER)
        for first, second, third in triples:
            writer.writerow((nfc(first), nfc(second), nfc(third)))
            count += 1
    return count


def _write_tsv(path: Path, triples: Iterable[Triple]) -> int:
    """Tab-separated writer (``.tsv``)."""
    return _write_delimited(path, triples, "\t")


def _write_csv(path: Path, triples: Iterable[Triple]) -> int:
    """Comma-separated writer (``.csv``)."""
    return _write_delimited(path, triples, ",")


def _write_jsonl(path: Path, triples: Iterable[Triple]) -> int:
    """One JSON object per line (``.jsonl``); glyphs stay literal."""
    count = 0
    with path.open("w", encoding="utf-8", newline="") as handle:
        for first, second, third in triples:
            row = {"c1": nfc(first), "c2": nfc(second), "c3": nfc(third)}
            handle.write(json.dumps(row, ensure_ascii=False))
            handle.write("\n")
            count += 1
    return count


def _write_parquet(path: Path, triples: Iterable[Triple]) -> int:
    """Columnar writer (``.parquet``); needs the optional ``pyarrow`` engine."""
    frame = pd.DataFrame(triples, columns=list(_HEADER)).map(nfc)
    try:
        frame.to_parquet(path, index=False, compression="snappy")
    except ImportError as exc:
        raise ValueError(
            "parquet output requires the 'pyarrow' extra: uv sync --extra output"
        ) from exc
    return len(frame)


def _write_sqlite(path: Path, triples: Iterable[Triple]) -> int:
    """Database writer (``.sqlite``): a ``roots`` table, replacing any existing file."""
    path.unlink(missing_ok=True)
    rows = [(nfc(first), nfc(second), nfc(third)) for first, second, third in triples]
    with closing(sqlite3.connect(path)) as connection:
        connection.execute(
            "CREATE TABLE roots (c1 TEXT, c2 TEXT, c3 TEXT, PRIMARY KEY (c1, c2, c3))"
        )
        connection.executemany("INSERT INTO roots VALUES (?, ?, ?)", rows)
        connection.commit()
    return len(rows)


_WRITERS: frozendict[str, _Writer] = frozendict(
    {
        "tsv": _write_tsv,
        "csv": _write_csv,
        "jsonl": _write_jsonl,
        "parquet": _write_parquet,
        "sqlite": _write_sqlite,
    }
)

_SUFFIXES: frozendict[str, str] = frozendict(
    {
        ".tsv": "tsv",
        ".csv": "csv",
        ".jsonl": "jsonl",
        ".parquet": "parquet",
        ".sqlite": "sqlite",
    }
)


def format_for_suffix(path: Path) -> str:
    """Return the writer name for ``path``'s suffix.

    Args:
        path: Destination path; only its (lowercased) suffix is inspected.

    Returns:
        The registered format name, e.g. ``"tsv"`` or ``"parquet"``.

    Raises:
        ValueError: When the suffix is missing or not one of
            :data:`_SUFFIXES`.
    """
    fmt = _SUFFIXES.get(path.suffix.lower())
    if fmt is None:
        supported = ", ".join(sorted(_SUFFIXES))
        raise ValueError(
            f"unsupported output extension {path.suffix!r}; expected one of {supported}"
        )
    return fmt


def write_roots(path: Path, triples: Iterable[Triple]) -> int:
    """Write ``triples`` to ``path`` in the format its suffix selects.

    Args:
        path: Destination file; the suffix picks the format. Parent directories
            are created as needed.
        triples: Streaming iterable of ``(c1, c2, c3)`` glyphs.

    Returns:
        The number of roots written (excluding any header).

    Raises:
        ValueError: When the suffix is missing/unsupported, or when ``.parquet``
            is requested without the ``pyarrow`` extra installed.
    """
    writer = _WRITERS[format_for_suffix(path)]
    path.parent.mkdir(parents=True, exist_ok=True)
    return writer(path, triples)
