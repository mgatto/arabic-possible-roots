"""Tests for the M_1-2/M_2-3 co-occurrence matrices."""

import unicodedata
from pathlib import Path

import pandas as pd
import pytest

from arabic_roots.alphabet import ORDER
from arabic_roots.phonotactics import is_allowed, load_matrices


def test_matrices_shape_all_ones_diag_one() -> None:
    """Both repo matrices are 28x28, all-1 init, diagonals 1."""
    m_1_2, m_2_3 = load_matrices()
    for matrix in (m_1_2, m_2_3):
        assert matrix.shape == (28, 28)
        assert list(matrix.index) == list(ORDER)
        assert list(matrix.columns) == list(ORDER)
        assert bool((matrix.to_numpy() == 1).all())
        for glyph in ORDER:
            assert bool(matrix.at[glyph, glyph]) is True


def test_is_allowed_conjunction(tmp_path: Path) -> None:
    """A root needs both M_1-2[c1,c2] and M_2-3[c2,c3] to pass."""
    order = list(ORDER)
    m_1_2 = pd.DataFrame(1, index=order, columns=order).astype(bool)
    m_2_3 = pd.DataFrame(1, index=order, columns=order).astype(bool)
    assert is_allowed("ب", "ت", "ث", m_1_2, m_2_3) is True
    m_1_2.at["ب", "ت"] = False
    assert is_allowed("ب", "ت", "ث", m_1_2, m_2_3) is False
    m_1_2.at["ب", "ت"] = True
    m_2_3.at["ت", "ث"] = False
    assert is_allowed("ب", "ت", "ث", m_1_2, m_2_3) is False
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
