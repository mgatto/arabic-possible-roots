"""Pure transforms for ingesting attested roots from ArabicChainBank.

Build-time only: this module performs no network or filesystem I/O. The
``scripts/fetch_attested.py`` orchestrator reads upstream ``lemmas.csv`` and
the encoding table, then writes ``data/attested.csv`` using these helpers, so
the transform stays unit-testable without the 2.5 MB source file.

Upstream (CAMeL-Lab/ArabicChainBank, ``data/lemmas.csv``) exposes the root
only in its Buckwalter ``ROOT`` column. Scheme encode/decode lives in
:mod:`arabic_roots.transliteration`; this module owns the root-level concerns:
extracting ``ROOT`` cells, requiring exactly three consonants, deduplicating,
and ordering by :data:`arabic_roots.alphabet.ORDER`.
"""

from collections.abc import Iterable, Iterator, Mapping
from typing import NamedTuple

from arabic_roots.alphabet import ORDER
from arabic_roots.transliteration import decode_root

__all__ = [
    "FIELDNAMES",
    "REASON_NOT_THREE",
    "REASON_OUT_OF_INVENTORY",
    "ROOT_COLUMN",
    "AttestedRow",
    "IngestResult",
    "build_rows",
    "extract_root_strings",
    "source_label",
]

#: Upstream column holding the (scheme-encoded) root.
ROOT_COLUMN: str = "ROOT"

#: Reason a root string was dropped: wrong number of ``.``-separated parts.
REASON_NOT_THREE: str = "not-three-consonants"

#: Reason a root string was dropped: a symbol is not in the scheme.
REASON_OUT_OF_INVENTORY: str = "out-of-inventory"


# TODO shouldn't this be a dataclass?
class AttestedRow(NamedTuple):
    """One row of ``data/attested.csv``."""

    c1: str
    c2: str
    c3: str
    variety: str
    source: str


class IngestResult(NamedTuple):
    """Deduplicated, ordered rows plus an audit trail of what was skipped."""

    rows: tuple[AttestedRow, ...]
    duplicates: int
    dropped: tuple[tuple[str, str], ...]

    @property
    def root_count(self) -> int:
        """Number of attested roots written."""
        return len(self.rows)


FIELDNAMES: tuple[str, ...] = ("c1", "c2", "c3", "variety", "source")


def source_label(commit: str) -> str:
    """Return the provenance label stored in the ``source`` column."""
    return f"arabicchainbank@{commit}"


def _classify_root(
    root: str,
    decoder: Mapping[str, str],
) -> tuple[tuple[str, str, str] | None, str]:
    decoded = decode_root(root, decoder)
    if decoded is None:
        return None, REASON_OUT_OF_INVENTORY
    if len(decoded) != 3:
        return None, REASON_NOT_THREE
    return (decoded[0], decoded[1], decoded[2]), "ok"


def extract_root_strings(rows: Iterable[Mapping[str, object]]) -> Iterator[str]:
    """Yield non-empty ``ROOT`` cell values from upstream rows."""
    for row in rows:
        root = row.get(ROOT_COLUMN)
        if isinstance(root, str) and root.strip():
            yield root.strip()


def _order_key(triple: tuple[str, str, str]) -> tuple[int, int, int]:
    return (ORDER.index(triple[0]), ORDER.index(triple[1]), ORDER.index(triple[2]))


def build_rows(
    root_strings: Iterable[str],
    decoder: Mapping[str, str],
    source: str,
    variety: str = "msa",
) -> IngestResult:
    """Deduplicate, decode, and ``ORDER``-sort upstream root strings."""
    seen: set[tuple[str, str, str]] = set()
    dropped: list[tuple[str, str]] = []
    duplicates = 0
    for root in root_strings:
        triple, reason = _classify_root(root, decoder)
        if triple is None:
            dropped.append((root, reason))
            continue
        if triple in seen:
            duplicates += 1
            continue
        seen.add(triple)
    ordered = sorted(seen, key=_order_key)
    rows = tuple(
        AttestedRow(first, second, third, variety, source)
        for first, second, third in ordered
    )
    return IngestResult(rows=rows, duplicates=duplicates, dropped=tuple(dropped))
