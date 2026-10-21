"""Attested-root lookup loaded from ``data/roots/attested.csv``.

Runtime counterpart to :mod:`arabic_possible_roots.arabic_chain_bank_provider`. The CSV
holds one row per ``(variety, c1, c2, c3)`` with literal Arabic glyphs from
:data:`arabic_possible_roots.alphabet.ORDER` and a ``source`` citation. This module
mirrors :mod:`arabic_possible_roots.phonotactics`: default ``<repo>/data`` (reading its
``roots/`` sub-directory), an explicit ``data_dir`` for tests, and loud
validation of malformed rows.
"""

from collections.abc import Mapping
from pathlib import Path

import pandas as pd
from frozendict import frozendict

from arabic_possible_roots.alphabet import normalize_glyph
from arabic_possible_roots.phonotactics import DATA_DIR

__all__ = ["ROOTS_SUBDIR", "load_attested", "is_attested"]

#: Sub-directory of the data root holding the attested-roots lexicon.
ROOTS_SUBDIR: str = "roots"

_REQUIRED_COLUMNS: frozenset[str] = frozenset({"c1", "c2", "c3", "variety", "source"})


def load_attested(
    data_dir: Path | None = None,
) -> frozendict[str, frozenset[tuple[str, str, str]]]:
    """Load ``attested.csv`` as a variety -> frozenset of triples map.

    Args:
        data_dir: Data root holding the ``roots/`` sub-directory with
            ``attested.csv``. Defaults to
            :data:`arabic_possible_roots.phonotactics.DATA_DIR`.

    Returns:
        A ``frozendict`` mapping each ``variety`` to the frozenset of its
        attested ``(c1, c2, c3)`` triples, each glyph NFC-normalized.

    Raises:
        FileNotFoundError: When ``attested.csv`` is missing.
        ValueError: On a missing column, invalid glyph, or duplicate row.

    Notes:
        Every row is validated and deduplicated per ``(variety, c1, c2, c3)``;
        this is a lexicon lookup, never a phonotactic rule source.
    """
    directory = (data_dir if data_dir is not None else DATA_DIR) / ROOTS_SUBDIR
    frame = pd.read_csv(
        directory / "attested.csv",
        dtype=str,
        keep_default_na=False,
        encoding="utf-8",
    )

    grouped: dict[str, set[tuple[str, str, str]]] = {}
    seen: set[tuple[str, str, str, str]] = set()
    missing = _REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"attested.csv missing columns: {sorted(missing)}")

    for record in frame.to_dict("records"):
        triple = (
            normalize_glyph(str(record["c1"])),
            normalize_glyph(str(record["c2"])),
            normalize_glyph(str(record["c3"])),
        )
        variety = str(record["variety"])

        key = (variety, *triple)
        if key in seen:
            raise ValueError(f"duplicate attested row: {key!r}")
        seen.add(key)

        grouped.setdefault(variety, set()).add(triple)

    return frozendict(
        {variety: frozenset(triples) for variety, triples in grouped.items()}
    )


def is_attested(
    first: str,
    second: str,
    third: str,
    attested: Mapping[str, frozenset[tuple[str, str, str]]],
    variety: str = "msa",
) -> bool:
    """Return whether the root is attested for ``variety``.

    Args:
        first: C1 glyph.
        second: C2 glyph.
        third: C3 glyph.
        attested: Variety -> frozenset map from :func:`load_attested`.
        variety: Variety label to look up; defaults to ``"msa"``.

    Returns:
        ``True`` when the NFC-normalized triple is present for ``variety``,
        ``False`` for an unknown variety or absent root.

    Raises:
        ValueError: When any glyph is outside the 28-consonant inventory.
    """
    triple = (
        normalize_glyph(first),
        normalize_glyph(second),
        normalize_glyph(third),
    )

    return triple in attested.get(variety, frozenset())
