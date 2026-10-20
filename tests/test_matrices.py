"""Tests for the M_1-2/M_2-3 co-occurrence matrices."""

import unicodedata
from pathlib import Path

import pandas as pd
import pytest

from arabic_roots.alphabet import ORDER, nfc
from arabic_roots.phonotactics import (
    DATA_DIR,
    RULES_SUBDIR,
    MatrixType,
    load_matrices,
    load_matrix,
    successors,
)


def test_matrices_shape_axes_and_diagonals() -> None:
    """Default gates are 28x28 ORDER; M_1-2 diagonal 0, M_2-3 diagonal 1."""
    m_1_2, m_2_3 = load_matrices()
    for matrix in (m_1_2, m_2_3):
        assert matrix.shape == (28, 28)
        assert list(matrix.index) == list(ORDER)
        assert list(matrix.columns) == list(ORDER)
    for glyph in ORDER:
        assert bool(m_1_2.at[glyph, glyph]) is False
        assert bool(m_2_3.at[glyph, glyph]) is True


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


def test_self_type_is_the_identity_gate() -> None:
    """self-only gates are permissive off-diagonal; M_1-2 diagonal is 0."""
    m_1_2 = load_matrix(DATA_DIR, "1-2", (MatrixType.SELF,))
    m_2_3 = load_matrix(DATA_DIR, "2-3", (MatrixType.SELF,))
    for row in ORDER:
        for column in ORDER:
            assert bool(m_1_2.at[row, column]) is (row != column)
            assert bool(m_2_3.at[row, column]) is True


def test_default_combines_self_and_homorganic() -> None:
    """The default M_1-2/M_2-3 gates are the AND of the two shipped types."""
    default_1_2, default_2_3 = load_matrices()
    self_1_2 = load_matrix(DATA_DIR, "1-2", (MatrixType.SELF,))
    hom_1_2 = load_matrix(DATA_DIR, "1-2", (MatrixType.HOMORGANIC,))
    self_2_3 = load_matrix(DATA_DIR, "2-3", (MatrixType.SELF,))
    hom_2_3 = load_matrix(DATA_DIR, "2-3", (MatrixType.HOMORGANIC,))
    assert default_1_2.equals(self_1_2 & hom_1_2)
    assert default_2_3.equals(self_2_3 & hom_2_3)
    assert bool(default_2_3.at["ت", "ث"]) is False  # same coronal-obstruent class
    assert bool(default_2_3.at["ت", "ت"]) is True  # diagonal (gemination) allowed


def test_load_matrix_composes_by_and(tmp_path: Path) -> None:
    """A pair is allowed only when every selected matrix allows it."""
    rules = tmp_path / "rules"
    rules.mkdir(parents=True)
    order = list(ORDER)
    self_frame = pd.DataFrame(1, index=order, columns=order)
    self_frame.at["ب", "ت"] = 0
    self_frame.to_csv(rules / "m_1-2_self.csv", encoding="utf-8")
    hom_frame = pd.DataFrame(1, index=order, columns=order)
    hom_frame.at["ب", "ث"] = 0
    hom_frame.to_csv(rules / "m_1-2_homorganic.csv", encoding="utf-8")

    combined = load_matrix(tmp_path, "1-2", (MatrixType.SELF, MatrixType.HOMORGANIC))
    assert bool(combined.at["ب", "ت"]) is False
    assert bool(combined.at["ب", "ث"]) is False
    assert bool(combined.at["ب", "د"]) is True

    self_only = load_matrix(tmp_path, "1-2", (MatrixType.SELF,))
    assert bool(self_only.at["ب", "ث"]) is True
    assert bool(self_only.at["ب", "ت"]) is False


def test_load_matrix_rejects_empty_selection(tmp_path: Path) -> None:
    """An empty type selection is a programming error, not a permissive gate."""
    with pytest.raises(ValueError, match="must not be empty"):
        load_matrix(tmp_path, "1-2", ())


def test_load_matrix_missing_file_raises(tmp_path: Path) -> None:
    """A requested matrix that is absent surfaces loudly."""
    with pytest.raises(FileNotFoundError):
        load_matrix(tmp_path, "1-2", (MatrixType.SELF,))


def test_csv_roundtrip_nfc(tmp_path: Path) -> None:
    """Matrices written as UTF-8 CSVs reload with NFC axes intact."""
    target = tmp_path / "data"
    rules = target / "rules"
    rules.mkdir(parents=True)
    order = [unicodedata.normalize("NFC", glyph) for glyph in ORDER]
    for position in ("1-2", "2-3"):
        for kind in MatrixType:
            frame = pd.DataFrame(1, index=order, columns=order)
            frame.to_csv(rules / f"m_{position}_{kind.value}.csv", encoding="utf-8")
    m_1_2, m_2_3 = load_matrices(target)
    assert list(m_1_2.index) == order
    assert list(m_2_3.columns) == order


def test_homorganic_matrices_encode_natural_classes() -> None:
    """Off-diagonal same-class pairs are forbidden in both homorganic CSVs.

    Source: McCarthy, J. J. (1988). *Feature geometry and dependency: A
    review*. Phonetica, 45(2-4), 84-108. No two *distinct* consonants of one
    natural class may be adjacent; the diagonal is therefore untouched, so
    every diagonal cell stays ``1``. ``m_1-2_homorganic.csv`` and
    ``m_2-3_homorganic.csv`` are byte-identical.
    """
    classes = (
        frozenset({"ب", "ف", "م"}),  # labials
        frozenset({"ت", "ث", "د", "ذ", "ز", "س", "ش", "ص", "ض", "ط", "ظ"}),
        frozenset({"ل", "ن", "ر"}),  # coronal sonorants
        frozenset({"ج", "ق", "ك"}),  # velars
        frozenset({"ح", "خ", "ه", "ء", "ع", "غ"}),  # gutturals
        frozenset({"و", "ي"}),  # dorsal sonorants
    )
    forbidden = {
        (first, second)
        for members in classes
        for first in members
        for second in members
        if first != second
    }
    assert len(forbidden) == 160

    directory = DATA_DIR / RULES_SUBDIR
    paths = (
        directory / "m_1-2_homorganic.csv",
        directory / "m_2-3_homorganic.csv",
    )
    assert paths[0].read_bytes() == paths[1].read_bytes()

    for path in paths:
        frame = pd.read_csv(path, index_col=0, encoding="utf-8")
        frame.index = frame.index.map(nfc)
        frame.columns = frame.columns.map(lambda value: nfc(str(value)))
        assert list(frame.index) == list(ORDER)
        assert list(frame.columns) == list(ORDER)
        for row in ORDER:
            for column in ORDER:
                cell = bool(frame.at[row, column])
                expected = row == column or (row, column) not in forbidden
                assert cell is expected, (path.name, row, column)


def test_bad_axes_rejected(tmp_path: Path) -> None:
    """Mismatched axes raise instead of silently misaligning."""
    order = list(ORDER)
    bad = pd.DataFrame(1, index=order, columns=order)
    bad.columns = [f"X{value}" for value in order]
    target = tmp_path / "bad"
    rules = target / "rules"
    rules.mkdir(parents=True)
    bad.to_csv(rules / "m_1-2_self.csv", encoding="utf-8")
    with pytest.raises(ValueError, match="axes must equal"):
        load_matrices(target)
