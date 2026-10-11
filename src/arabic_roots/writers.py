"""Streaming output writers for enumerated roots, selected by file suffix.

The batch enumerator yields ``(c1, c2, c3)`` triples; this module turns them
into a serialized file whose format is inferred from the ``--output`` suffix.
Today the delimited text formats ``.tsv`` and ``.csv`` are supported; both
carry the header ``c1,c2,c3`` and stream one root per row (constant memory),
preserving the enumerator's ORDER-lexicographic order.

Only the standard library is used (``csv``), so this layer adds no dependency
and is reusable by other programs (AGENTS §1).
"""

import csv
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import TextIO

from frozendict import frozendict

from arabic_roots.alphabet import nfc

__all__ = ["format_for_suffix", "write_roots"]

type Triple = tuple[str, str, str]
type _Writer = Callable[[TextIO, Iterable[Triple]], int]

_HEADER: tuple[str, str, str] = ("c1", "c2", "c3")


def _write_delimited(
    handle: TextIO,
    triples: Iterable[Triple],
    delimiter: str,
) -> int:
    """Write the header and one row per triple, returning the row count."""
    writer = csv.writer(handle, delimiter=delimiter, lineterminator="\n")
    writer.writerow(_HEADER)
    count = 0
    for first, second, third in triples:
        writer.writerow((nfc(first), nfc(second), nfc(third)))
        count += 1
    return count


def _write_tsv(handle: TextIO, triples: Iterable[Triple]) -> int:
    """Tab-separated writer (``.tsv``)."""
    return _write_delimited(handle, triples, "\t")


def _write_csv(handle: TextIO, triples: Iterable[Triple]) -> int:
    """Comma-separated writer (``.csv``)."""
    return _write_delimited(handle, triples, ",")


_WRITERS: frozendict[str, _Writer] = frozendict({"tsv": _write_tsv, "csv": _write_csv})

_SUFFIXES: frozendict[str, str] = frozendict({".tsv": "tsv", ".csv": "csv"})


def format_for_suffix(path: Path) -> str:
    """Return the writer name for ``path``'s suffix.

    Args:
        path: Destination path; only its (lowercased) suffix is inspected.

    Returns:
        The registered format name, e.g. ``"tsv"`` or ``"csv"``.

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
        path: Destination file; the suffix picks the format (``.tsv``/``.csv``).
            Parent directories are created as needed.
        triples: Streaming iterable of ``(c1, c2, c3)`` glyphs.

    Returns:
        The number of roots written (excluding the header).

    Raises:
        ValueError: When the suffix is missing or unsupported.
    """
    writer = _WRITERS[format_for_suffix(path)]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        return writer(handle, triples)
