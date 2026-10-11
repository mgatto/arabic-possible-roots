"""Pure transforms for the ArabicChainBank attested-roots provider.

Build-time only: this module performs no network or filesystem I/O. The
``scripts/fetch_attested.py`` orchestrator reads upstream ``lemmas.csv`` and
the encoding table, then writes ``data/roots/attested.csv`` using these helpers, so
the transform stays unit-testable without the 2.5 MB source file.

Upstream (CAMeL-Lab/ArabicChainBank, ``data/lemmas.csv``) exposes the root
only in its Buckwalter ``ROOT`` column. Scheme encode/decode lives in
:mod:`arabic_roots.transliteration`; this module owns the ACB-specific
concerns: the pinned commit, the raw URL, the ``ROOT`` column and its
separator, source labeling, requiring exactly three consonants,
deduplicating, and ordering by :data:`arabic_roots.alphabet.ORDER`.

The ``_provider`` name is descriptive, not a formal interface: no shared
``Provider`` protocol exists until a second source (e.g. lisan345) lands.
"""

from collections.abc import Iterable, Iterator, Mapping
from typing import NamedTuple

from arabic_roots.alphabet import ORDER
from arabic_roots.transliteration import decode_root

__all__ = [
    "DEFAULT_SHA",
    "FIELDNAMES",
    "RAW_LEMMAS_URL",
    "REASON_NOT_THREE",
    "REASON_OUT_OF_INVENTORY",
    "ROOT_COLUMN",
    "ROOT_SEPARATOR",
    "AttestedRow",
    "ProviderResult",
    "build_rows",
    "extract_root_strings",
]

#: Upstream commit that last modified ``data/lemmas.csv`` (2025-06-04).
DEFAULT_SHA: str = "ec88574fde176e453cfa5715135a42b7a02cef98"

#: Raw URL template for the pinned upstream ``lemmas.csv`` (``{sha}`` slot).
RAW_LEMMAS_URL: str = (
    "https://raw.githubusercontent.com/CAMeL-Lab/ArabicChainBank/{sha}/data/lemmas.csv"
)

#: Upstream column holding the (Buckwalter-encoded) root.
ROOT_COLUMN: str = "ROOT"

#: Separator between the three encoded consonants in a ``ROOT`` cell.
ROOT_SEPARATOR: str = "."

#: Reason a root string was dropped: wrong number of ``.``-separated parts.
REASON_NOT_THREE: str = "not-three-consonants"

#: Reason a root string was dropped: a symbol is not in the scheme.
REASON_OUT_OF_INVENTORY: str = "out-of-inventory"

#: Output CSV header for ``data/roots/attested.csv``.
FIELDNAMES: tuple[str, ...] = ("c1", "c2", "c3", "variety", "source")

#: ``ORDER`` rank per glyph, so sorting is O(1) per consonant.
_RANK: dict[str, int] = {glyph: index for index, glyph in enumerate(ORDER)}


class AttestedRow(NamedTuple):
    """One row of ``data/roots/attested.csv``."""

    c1: str
    c2: str
    c3: str
    variety: str
    source: str


class ProviderResult(NamedTuple):
    """Deduplicated, ordered rows plus an audit trail of what was skipped."""

    rows: tuple[AttestedRow, ...]
    duplicates: int
    dropped: tuple[tuple[str, str], ...]


def _source_label(sha: str) -> str:
    """Return the provenance label stored in the ``source`` column."""
    return f"arabicchainbank@{sha}"


def _classify_root(
    root: str,
    decoder: Mapping[str, str],
) -> tuple[tuple[str, str, str] | None, str]:
    decoded = decode_root(root, decoder, separator=ROOT_SEPARATOR)
    if decoded is None:
        return None, REASON_OUT_OF_INVENTORY

    if len(decoded) != 3:
        return None, REASON_NOT_THREE

    return (decoded[0], decoded[1], decoded[2]), "ok"


def extract_root_strings(rows: Iterable[Mapping[str, object]]) -> Iterator[str]:
    """Yield non-empty ``ROOT`` cell values from upstream lemma rows.

    Args:
        rows: ArabicChainBank lemma rows (mappings with a ``ROOT`` key).

    Yields:
        Each non-empty, whitespace-stripped ``ROOT`` string.

    Notes:
        Non-string and blank cells are skipped silently; decoding and
        triliterality checks happen later in :func:`build_rows`.
    """
    for row in rows:
        root = row.get(ROOT_COLUMN)

        if isinstance(root, str) and root.strip():
            yield root.strip()


def _order_key(triple: tuple[str, str, str]) -> tuple[int, int, int]:
    return _RANK[triple[0]], _RANK[triple[1]], _RANK[triple[2]]


def build_rows(
    lemma_rows: Iterable[Mapping[str, object]],
    decoder: Mapping[str, str],
    sha: str,
    variety: str = "msa",
) -> ProviderResult:
    """Deduplicate, decode, and ``ORDER``-sort ArabicChainBank lemma rows.

    Args:
        lemma_rows: Raw upstream lemma rows; only their ``ROOT`` cells are read.
        decoder: Symbol -> glyph map from
            :func:`arabic_roots.transliteration.build_decoder`.
        sha: Pinned upstream commit, recorded as ``arabicchainbank@<sha>``.
        variety: Variety label written to every row; defaults to ``"msa"``.

    Returns:
        A :class:`ProviderResult` with ORDER-sorted :class:`AttestedRow`s plus
        duplicate and drop counts.

    Notes:
        Pure and I/O-free. Rows whose ``ROOT`` is not exactly three known
        symbols are dropped with a reason rather than raising.
    """
    source = _source_label(sha)
    seen: set[tuple[str, str, str]] = set()
    dropped: list[tuple[str, str]] = []
    duplicates = 0

    for root in extract_root_strings(lemma_rows):
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

    return ProviderResult(rows=rows, duplicates=duplicates, dropped=tuple(dropped))
