"""Tests for the attested-root loader and predicate."""

import csv
from pathlib import Path

import pytest

from arabic_roots.alphabet import ORDER
from arabic_roots.attestation import is_attested, load_attested

#: Pinned count of MSA triliteral roots derived from ArabicChainBank.
GOLDEN_MSA_COUNT = 3959

_HEADER = ["c1", "c2", "c3", "variety", "source"]


def _write(path: Path, rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(_HEADER)
        writer.writerows(rows)


def test_golden_count_and_variety() -> None:
    """The shipped CSV holds the pinned MSA count under one variety."""
    attested = load_attested()
    assert set(attested) == {"msa"}
    assert len(attested["msa"]) == GOLDEN_MSA_COUNT


def test_all_glyphs_are_inventory() -> None:
    """Every attested triple uses only the 28 NFC-normalized glyphs."""
    attested = load_attested()
    for triple in attested["msa"]:
        assert all(glyph in ORDER for glyph in triple)


def test_known_attested_and_known_possible() -> None:
    """ك-ت-ب is attested; a legal-but-unattested triple is not."""
    attested = load_attested()
    assert is_attested("ك", "ت", "ب", attested) is True
    assert is_attested("ء", "ب", "ء", attested) is False


def test_unknown_variety_is_false() -> None:
    """An unpopulated variety never reports attestation."""
    attested = load_attested()
    assert is_attested("ك", "ت", "ب", attested, variety="classical") is False


def test_invalid_glyph_raises() -> None:
    """A glyph outside the inventory is a loud error, not False."""
    attested = load_attested()
    with pytest.raises(ValueError, match="not in 28-consonant inventory"):
        is_attested("X", "ت", "ب", attested)


def test_tmp_path_roundtrip(tmp_path: Path) -> None:
    """A minimal CSV loads with per-variety grouping."""
    _write(
        tmp_path / "roots" / "attested.csv",
        [["ب", "ت", "ث", "msa", "unit-test"], ["ب", "ت", "ث", "classical", "unit"]],
    )
    attested = load_attested(tmp_path)
    assert attested["msa"] == frozenset({("ب", "ت", "ث")})
    assert attested["classical"] == frozenset({("ب", "ت", "ث")})


def test_duplicate_rows_rejected(tmp_path: Path) -> None:
    """Two identical (variety, c1, c2, c3) rows raise."""
    _write(
        tmp_path / "roots" / "attested.csv",
        [["ب", "ت", "ث", "msa", "a"], ["ب", "ت", "ث", "msa", "b"]],
    )
    with pytest.raises(ValueError, match="duplicate attested row"):
        load_attested(tmp_path)


def test_missing_columns_rejected(tmp_path: Path) -> None:
    """A CSV without the required columns raises."""
    target = tmp_path / "roots" / "attested.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("c1,c2,variety\nب,ت,msa\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing columns"):
        load_attested(tmp_path)


def test_missing_file_raises(tmp_path: Path) -> None:
    """A missing attested.csv surfaces as FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_attested(tmp_path)
