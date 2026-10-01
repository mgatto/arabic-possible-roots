"""Tests for the 28-glyph alphabet source of truth."""

import unicodedata

import pytest

from arabic_roots.alphabet import (
    LETTERS,
    LOOKUP,
    ORDER,
    Manner,
    Place,
    is_valid_glyph,
    normalize_glyph,
)


def test_order_has_28_unique_nfc_glyphs() -> None:
    """ORDER is 28 unique, NFC-normalized, single-codepoint glyphs."""
    assert len(ORDER) == 28
    assert len(set(ORDER)) == 28
    for glyph in ORDER:
        assert unicodedata.normalize("NFC", glyph) == glyph
        assert len(glyph) == 1


def test_hamza_is_single_u0621() -> None:
    """Hamza is U+0621 only; no carriers or bare alif in the inventory."""
    assert ORDER[0] == "ء"
    assert ord(ORDER[0]) == 0x0621
    for forbidden in ("أ", "إ", "آ", "ؤ", "ئ", "ا"):
        assert forbidden not in ORDER


def test_letters_cover_order_with_ipa_and_din() -> None:
    """Every glyph has a Letter row with IPA and DIN 31635 filled."""
    assert len(LETTERS) == 28
    for letter in LETTERS:
        assert letter.glyph in ORDER
        assert letter.ipa != ""
        assert letter.din31635 != ""
        assert letter.name != ""
    assert set(LOOKUP.keys()) == set(ORDER)


def test_no_ascii_escape_hatch() -> None:
    """Glyphs are literal Arabic codepoints, not ASCII keys."""
    for glyph in ORDER:
        assert ord(glyph) >= 0x0621
        assert ord(glyph) <= 0x064A
        assert glyph.isascii() is False


def test_letters_use_place_and_manner_enums() -> None:
    """Every Letter carries typed Place/Manner members."""
    for letter in LETTERS:
        assert isinstance(letter.place, Place)
        assert isinstance(letter.manner, Manner)


def test_normalize_and_validate() -> None:
    """NFC validation accepts inventory glyphs and flags the rest."""
    assert normalize_glyph("ب") == "ب"
    assert is_valid_glyph("ب") is True
    assert is_valid_glyph("A") is False
    with pytest.raises(ValueError, match="not in 28-consonant inventory"):
        normalize_glyph("A")


def test_normalize_glyph_is_idempotent() -> None:
    """normalize_glyph already returns NFC, so re-normalizing is a no-op."""
    for glyph in ORDER:
        assert normalize_glyph(glyph) == glyph
        assert normalize_glyph(normalize_glyph(glyph)) == glyph
