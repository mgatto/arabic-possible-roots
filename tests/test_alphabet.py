"""Tests for the 28-glyph alphabet source of truth."""

import unicodedata

import pytest

from arabic_roots.alphabet import (
    CATEGORIES,
    LETTERS,
    LOOKUP,
    ORDER,
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


def test_categories_derive_from_letters() -> None:
    """Grouping helpers are populated and consistent."""
    assert len(CATEGORIES["emphatics"]) == 4
    assert set(CATEGORIES["emphatics"]) == {"ص", "ض", "ط", "ظ"}
    assert set(CATEGORIES["nasals"]) == {"م", "ن"}
    assert "ب" in CATEGORIES["bilabials"]
    assert "ق" in CATEGORIES["uvulars"]


def test_normalize_and_validate() -> None:
    """NFC validation accepts inventory glyphs and flags the rest."""
    assert normalize_glyph("ب") == "ب"
    assert is_valid_glyph("ب") is True
    assert is_valid_glyph("A") is False
    with pytest.raises(ValueError, match="not in 28-consonant inventory"):
        normalize_glyph("A")
