"""Transliteration-scheme encoding and decoding.

A *scheme* maps the 28 Arabic glyphs in :data:`arabic_roots.alphabet.ORDER`
to/from an external symbol set. The only scheme today is the ingest encoding
used by CAMeL-Lab/ArabicChainBank (Buckwalter), stored in
``data/buckwalter.csv``; output schemes (DIN 31635, IJMES, IPA — see
``docs/Future.md`` PRD 3) belong here too.

The mapping is data, not code: scheme symbols come from CSV and never appear
as Python literals (AGENTS.md §4). Decoding turns symbols into inventory
glyphs; encoding is its inverse and feeds output rendering.
"""

import unicodedata
from collections.abc import Iterable, Mapping

from frozendict import frozendict

from arabic_roots.alphabet import ORDER, is_valid_glyph

__all__ = [
    "BUCKWALTER_COLUMN",
    "GLYPH_COLUMN",
    "build_decoder",
    "build_encoder",
    "decode_root",
    "encode_root",
]

#: Scheme-table column holding the Arabic glyph.
GLYPH_COLUMN: str = "glyph"

#: Scheme-table column holding the external (here: Buckwalter) symbol.
BUCKWALTER_COLUMN: str = "buckwalter"


def build_decoder(rows: Iterable[Mapping[str, object]]) -> frozendict[str, str]:
    """Invert a scheme table into a symbol -> glyph decoder.

    Raises:
        ValueError: On missing/duplicate symbols or when the glyph column
            does not cover :data:`arabic_roots.alphabet.ORDER` exactly.
    """
    decoder: dict[str, str] = {}
    for row in rows:
        glyph = row.get(GLYPH_COLUMN)
        symbol = row.get(BUCKWALTER_COLUMN)
        if not isinstance(glyph, str) or not isinstance(symbol, str):
            raise ValueError("map rows need 'glyph' and 'buckwalter' columns")
        normalized = unicodedata.normalize("NFC", glyph.strip())
        key = symbol.strip()
        if not is_valid_glyph(normalized) or not key:
            raise ValueError(f"invalid mapping row: {glyph!r} -> {symbol!r}")
        if key in decoder:
            raise ValueError(f"duplicate Buckwalter symbol: {key!r}")
        decoder[key] = normalized
    if set(decoder.values()) != set(ORDER):
        raise ValueError("buckwalter map must cover the 28-glyph inventory")
    return frozendict(decoder)


def build_encoder(decoder: Mapping[str, str]) -> frozendict[str, str]:
    """Invert a symbol -> glyph decoder into a glyph -> symbol encoder."""
    return frozendict({glyph: symbol for symbol, glyph in decoder.items()})


def decode_root(
    root: str,
    decoder: Mapping[str, str],
    separator: str = ".",
) -> tuple[str, ...] | None:
    """Decode a ``separator``-joined root; None if any symbol is unknown."""
    glyphs: list[str] = []
    for symbol in root.split(separator):
        glyph = decoder.get(symbol)
        if glyph is None:
            return None
        glyphs.append(glyph)
    return tuple(glyphs)


def encode_root(
    glyphs: Iterable[str],
    encoder: Mapping[str, str],
    separator: str = ".",
) -> str | None:
    """Encode glyphs into a ``separator``-joined string; None if unknown."""
    symbols: list[str] = []
    for glyph in glyphs:
        symbol = encoder.get(glyph)
        if symbol is None:
            return None
        symbols.append(symbol)
    return separator.join(symbols)
