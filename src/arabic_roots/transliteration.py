"""Transliteration-scheme encoding and decoding.

A *scheme* maps the 28 Arabic glyphs in :data:`arabic_roots.alphabet.ORDER`
to/from an external symbol set. The only scheme today is the ingest encoding
used by CAMeL-Lab/ArabicChainBank (Buckwalter), stored in
``data/transliterations/buckwalter.csv``; output schemes (DIN 31635, IJMES,
IPA — see ``docs/Future.md`` PRD 3) belong here too.

The mapping is data, not code: scheme symbols come from CSV and never appear
as Python literals (AGENTS.md §4). Decoding turns symbols into inventory
glyphs; encoding is its inverse and feeds output rendering.
"""

from collections.abc import Iterable, Mapping

from frozendict import frozendict

from arabic_roots.alphabet import GLYPH_SET, ORDER, nfc

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

    Args:
        rows: Mappings carrying the ``glyph`` and ``buckwalter`` columns.

    Returns:
        A ``frozendict`` mapping each scheme symbol to its NFC inventory glyph.

    Raises:
        ValueError: On non-string cells, blank symbols, duplicate symbols, or
            when the glyph column does not cover
            :data:`arabic_roots.alphabet.ORDER` exactly.

    Notes:
        The mapping is data, not code: symbols come from CSV, never literals.
        Glyphs are validated against the inventory and stored NFC-normalized.
    """
    decoder: dict[str, str] = {}
    for row in rows:
        glyph = row.get(GLYPH_COLUMN)
        symbol = row.get(BUCKWALTER_COLUMN)
        if not isinstance(glyph, str) or not isinstance(symbol, str):
            raise ValueError("map rows need 'glyph' and 'buckwalter' columns")
        normalized = nfc(glyph.strip())
        key = symbol.strip()
        if normalized not in GLYPH_SET or not key:
            raise ValueError(f"invalid mapping row: {glyph!r} -> {symbol!r}")
        if key in decoder:
            raise ValueError(f"duplicate Buckwalter symbol: {key!r}")
        decoder[key] = normalized
    if set(decoder.values()) != set(ORDER):
        raise ValueError("buckwalter map must cover the 28-glyph inventory")
    return frozendict(decoder)


def build_encoder(decoder: Mapping[str, str]) -> frozendict[str, str]:
    """Invert a symbol -> glyph decoder into a glyph -> symbol encoder.

    Args:
        decoder: A decoder from :func:`build_decoder`.

    Returns:
        A ``frozendict`` mapping each glyph to its scheme symbol.

    Notes:
        Assumes decoder values are unique, which :func:`build_decoder`
        guarantees; a colliding decoder would silently drop a glyph.
    """
    return frozendict({glyph: symbol for symbol, glyph in decoder.items()})


def decode_root(
    root: str,
    decoder: Mapping[str, str],
    separator: str = ".",
) -> tuple[str, ...] | None:
    """Decode a ``separator``-joined root into inventory glyphs.

    Args:
        root: Encoded root, e.g. ``"b.t.v"``.
        decoder: Symbol -> glyph map from :func:`build_decoder`.
        separator: Token separator between encoded consonants.

    Returns:
        The decoded glyph tuple, or ``None`` if any symbol is unknown.

    Notes:
        Length is not checked here; triliterality is enforced by the caller.
    """
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
    """Encode glyphs into a ``separator``-joined string.

    Args:
        glyphs: Inventory glyphs to encode.
        encoder: Glyph -> symbol map from :func:`build_encoder`.
        separator: Token separator between encoded consonants.

    Returns:
        The joined encoded string, or ``None`` if any glyph is unknown.
    """
    symbols: list[str] = []
    for glyph in glyphs:
        symbol = encoder.get(glyph)
        if symbol is None:
            return None
        symbols.append(symbol)
    return separator.join(symbols)
