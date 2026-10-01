"""Attested-root lookup loaded from ``data/attested.csv``.

Runtime counterpart to :mod:`arabic_roots.ingest`. The CSV holds one row per
``(variety, c1, c2, c3)`` with literal Arabic glyphs from
:data:`arabic_roots.alphabet.ORDER` and a ``source`` citation. This module
mirrors :mod:`arabic_roots.phonotactics`: default ``<repo>/data``, an
explicit ``data_dir`` for tests, and loud validation of malformed rows.
"""

import unicodedata
from collections.abc import Mapping
from pathlib import Path

import pandas as pd
from frozendict import frozendict

from arabic_roots.alphabet import normalize_glyph
from arabic_roots.phonotactics import default_data_dir

__all__ = ["load_attested", "is_attested"]

_REQUIRED_COLUMNS: frozenset[str] = frozenset({"c1", "c2", "c3", "variety", "source"})


def load_attested(
    data_dir: Path | None = None,
) -> frozendict[str, frozenset[tuple[str, str, str]]]:
    """Load ``attested.csv`` as a variety -> frozenset of triples map.

    Raises:
        FileNotFoundError: When ``attested.csv`` is missing.
        ValueError: On a missing column, invalid glyph, or duplicate row.
    """
    directory = data_dir if data_dir is not None else default_data_dir()
    frame = pd.read_csv(
        directory / "attested.csv",
        dtype=str,
        keep_default_na=False,
        encoding="utf-8",
    )
    missing = _REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"attested.csv missing columns: {sorted(missing)}")
    grouped: dict[str, set[tuple[str, str, str]]] = {}
    seen: set[tuple[str, str, str, str]] = set()
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
    """Return True when the NFC-normalized triple is attested for ``variety``.

    Raises:
        ValueError: When any glyph is outside the 28-consonant inventory.
    """
    triple = (
        unicodedata.normalize("NFC", normalize_glyph(first)),
        unicodedata.normalize("NFC", normalize_glyph(second)),
        unicodedata.normalize("NFC", normalize_glyph(third)),
    )
    return triple in attested.get(variety, frozenset())
