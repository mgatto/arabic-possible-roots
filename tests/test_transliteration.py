"""Tests for transliteration-scheme encoding and decoding."""

import csv
from collections.abc import Mapping
from pathlib import Path

import pytest

from arabic_possible_roots.alphabet import ORDER
from arabic_possible_roots.transliteration import (
    build_decoder,
    build_encoder,
    decode_root,
    encode_root,
)

_MAP_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "transliterations" / "buckwalter.csv"
)


def _real_decoder() -> Mapping[str, str]:
    with _MAP_PATH.open(encoding="utf-8") as handle:
        return build_decoder(csv.DictReader(handle))


def test_map_is_inventory_bijection() -> None:
    """The table maps 28 unique symbols onto the 28-glyph inventory."""
    decoder = _real_decoder()
    assert len(decoder) == 28
    assert set(decoder.values()) == set(ORDER)


def test_decode_encode_roundtrip() -> None:
    """Encoding then decoding a triple returns the same glyphs."""
    decoder = _real_decoder()
    encoder = build_encoder(decoder)
    for triple in (("ك", "ت", "ب"), ("ء", "د", "ب"), ("ض", "و", "ء")):
        encoded = encode_root(triple, encoder)
        assert encoded is not None
        assert decode_root(encoded, decoder) == triple


def test_decode_keeps_arbitrary_length() -> None:
    """Decoding preserves length; the triliteral check lives in the provider."""
    decoder = _real_decoder()
    encoded = encode_root(("ب", "ت"), build_encoder(decoder))
    assert encoded is not None
    assert decode_root(encoded, decoder) == ("ب", "ت")


def test_unknown_symbol_decodes_to_none() -> None:
    """An unknown symbol makes the whole decode fail."""
    assert decode_root("?.?.?", _real_decoder()) is None


def test_unknown_glyph_encodes_to_none() -> None:
    """A non-inventory glyph makes the whole encode fail."""
    encoder = build_encoder(_real_decoder())
    assert encode_root(("X", "ب", "ت"), encoder) is None


def test_build_decoder_rejects_duplicate_symbol() -> None:
    """A repeated symbol is rejected."""
    decoder = _real_decoder()
    rows: list[Mapping[str, object]] = [
        {"glyph": glyph, "buckwalter": symbol} for symbol, glyph in decoder.items()
    ]
    symbol, glyph = next(iter(decoder.items()))
    rows.append({"glyph": glyph, "buckwalter": symbol})
    with pytest.raises(ValueError, match="duplicate scheme symbol"):
        build_decoder(rows)


def test_build_decoder_rejects_incomplete_map() -> None:
    """A map that does not cover the inventory is rejected."""
    decoder = _real_decoder()
    symbol, glyph = next(iter(decoder.items()))
    with pytest.raises(ValueError, match="cover"):
        build_decoder([{"glyph": glyph, "buckwalter": symbol}])


def test_build_decoder_rejects_invalid_glyph() -> None:
    """A non-inventory glyph is rejected."""
    decoder = _real_decoder()
    symbol, _glyph = next(iter(decoder.items()))
    with pytest.raises(ValueError, match="invalid mapping"):
        build_decoder([{"glyph": "X", "buckwalter": symbol}])


def test_build_decoder_rejects_missing_columns() -> None:
    """Rows without both columns are rejected."""
    with pytest.raises(ValueError, match="need 'glyph' and 'buckwalter'"):
        build_decoder([{"glyph": "ب"}])
