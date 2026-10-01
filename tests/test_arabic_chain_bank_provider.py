"""Tests for the ArabicChainBank attested-roots provider."""

import csv
from collections.abc import Mapping
from pathlib import Path

from arabic_roots.arabic_chain_bank_provider import (
    REASON_NOT_THREE,
    REASON_OUT_OF_INVENTORY,
    AttestedRow,
    build_rows,
    extract_root_strings,
)
from arabic_roots.transliteration import build_decoder, build_encoder, encode_root

_MAP_PATH = Path(__file__).resolve().parents[1] / "data" / "buckwalter.csv"


def _real_decoder() -> Mapping[str, str]:
    with _MAP_PATH.open(encoding="utf-8") as handle:
        return build_decoder(csv.DictReader(handle))


def _encoded(glyphs: tuple[str, ...], decoder: Mapping[str, str]) -> str:
    encoded = encode_root(glyphs, build_encoder(decoder))
    assert encoded is not None
    return encoded


def _root_row(encoded: str) -> Mapping[str, object]:
    return {"ROOT": encoded}


def test_extract_root_strings_skips_blanks() -> None:
    """Only non-empty ROOT cells are yielded."""
    decoder = _real_decoder()
    encoded = _encoded(("ك", "ت", "ب"), decoder)
    rows: list[Mapping[str, object]] = [
        {"ROOT": encoded},
        {"ROOT": "   "},
        {"ROOT": None},
        {"LEMMA": "unrelated"},
    ]
    assert list(extract_root_strings(rows)) == [encoded]


def test_build_rows_dedupes_sorts_and_reports() -> None:
    """Duplicates collapse, output is ORDER-sorted, drops carry reasons."""
    decoder = _real_decoder()
    rows = [
        _root_row(_encoded(("ي", "و", "م"), decoder)),
        _root_row(_encoded(("ء", "ب", "ب"), decoder)),
        _root_row(_encoded(("ء", "ب", "ب"), decoder)),
        _root_row(_encoded(("ب", "ت", "ث", "ج"), decoder)),
        _root_row("?.?.?"),
    ]
    result = build_rows(rows, decoder, sha="unit", variety="msa")
    assert len(result.rows) == 2
    assert result.rows == (
        AttestedRow("ء", "ب", "ب", "msa", "arabicchainbank@unit"),
        AttestedRow("ي", "و", "م", "msa", "arabicchainbank@unit"),
    )
    assert result.duplicates == 1
    assert {reason for _root, reason in result.dropped} == {
        REASON_NOT_THREE,
        REASON_OUT_OF_INVENTORY,
    }
    assert len(result.dropped) == 2
