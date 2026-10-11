"""Tests for the M_1-2/M_2-3 co-occurrence matrices."""

import unicodedata
from pathlib import Path

import pandas as pd
import pytest

from arabic_roots.alphabet import ORDER
from arabic_roots.phonotactics import load_matrices, successors


def test_matrices_shape_axes_and_diagonals() -> None:
    """28x28 ORDER axes; M_1-2 diagonal 0 (C1!=C2), M_2-3 diagonal 1."""
    m_1_2, m_2_3 = load_matrices()
    for matrix in (m_1_2, m_2_3):
        assert matrix.shape == (28, 28)
        assert list(matrix.index) == list(ORDER)
        assert list(matrix.columns) == list(ORDER)
    for glyph in ORDER:
        assert bool(m_1_2.at[glyph, glyph]) is False
        assert bool(m_2_3.at[glyph, glyph]) is True
    for row in ORDER:
        for column in ORDER:
            if row != column:
                assert bool(m_1_2.at[row, column]) is True
                assert bool(m_2_3.at[row, column]) is True


def test_successors_lists_true_columns_in_order(tmp_path: Path) -> None:
    """successors() maps each row to its True columns, ORDER-ordered."""
    order = list(ORDER)
    frame = pd.DataFrame(1, index=order, columns=order).astype(bool)
    frame.at["ب", "ت"] = False
    frame.at["ب", "ب"] = False
    succ = successors(frame)
    assert set(succ) == set(ORDER)
    assert succ["ء"] == ORDER
    assert succ["ب"] == tuple(glyph for glyph in ORDER if glyph not in {"ت", "ب"})
    _ = tmp_path  # keeps tmp_path fixture pattern explicit for future pinning tests.


def test_csv_roundtrip_nfc(tmp_path: Path) -> None:
    """Matrices written as UTF-8 CSVs reload with NFC axes intact."""
    target = tmp_path / "data"
    target.mkdir()
    order = [unicodedata.normalize("NFC", glyph) for glyph in ORDER]
    for name in ("m_1-2", "m_2-3"):
        frame = pd.DataFrame(1, index=order, columns=order)
        frame.to_csv(target / f"{name}.csv", encoding="utf-8")
    m_1_2, m_2_3 = load_matrices(target)
    assert list(m_1_2.index) == order
    assert list(m_2_3.columns) == order


def test_bad_axes_rejected(tmp_path: Path) -> None:
    """Mismatched axes raise instead of silently misaligning."""
    order = list(ORDER)
    bad = pd.DataFrame(1, index=order, columns=order)
    bad.columns = [f"X{value}" for value in order]
    target = tmp_path / "bad"
    target.mkdir()
    bad.to_csv(target / "m_1-2.csv", encoding="utf-8")
    good = pd.DataFrame(1, index=order, columns=order)
    good.to_csv(target / "m_2-3.csv", encoding="utf-8")
    with pytest.raises(ValueError, match="axes must equal"):
        load_matrices(target)
