"""Adjacent-pair phonotactic matrices for triliteral roots.

Two 28x28 boolean ``pandas.DataFrame`` objects share the fixed axis order
from :mod:`arabic_roots.alphabet`:

- ``M_1-2`` gates consonants 1-2 of the root.
- ``M_2-3`` gates consonants 2-3 of the root.

``1`` means the ordered pair may co-occur, ``0`` forbids it. Diagonals are
``1`` because gemination (doubled consonants) is permitted in some positions.

Initial state is all-``1`` (permissive). Prohibitions from Ryder
(*Arabic: A Linguistic Introduction*, owned copy) are added one pair at a
time, each with a ``TODO(Ryder:p.X)`` or page citation, plus a regression
test. The state machine never encodes rules itself; it only queries these
matrices via :func:`is_allowed`.
"""

from pathlib import Path

import pandas as pd

from arabic_roots.alphabet import ORDER, nfc, normalize_glyph

__all__ = ["DATA_DIR", "is_allowed", "load_matrices"]

#: Default ``<repo>/data`` regardless of the caller's working directory.
DATA_DIR: Path = Path(__file__).resolve().parents[2] / "data"


def load_matrices(data_dir: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load ``m_1-2.csv`` and ``m_2-3.csv`` as boolean DataFrames.

    Args:
        data_dir: Directory holding the two CSVs. Defaults to :data:`DATA_DIR`.

    Returns:
        ``(m_1_2, m_2_3)`` boolean frames whose index and columns are exactly
        :data:`arabic_roots.alphabet.ORDER`. A ``True`` cell means the ordered
        pair may co-occur; the diagonal is ``True`` (gemination permitted).

    Raises:
        FileNotFoundError: When either CSV is missing.
        ValueError: When axes do not match :data:`arabic_roots.alphabet.ORDER`.

    Notes:
        Axis labels are NFC-normalized before the ORDER check, so CSV files
        written on any platform validate identically.
    """
    directory = data_dir if data_dir is not None else DATA_DIR

    m_1_2 = pd.read_csv(directory / "m_1-2.csv", index_col=0, encoding="utf-8")
    m_2_3 = pd.read_csv(directory / "m_2-3.csv", index_col=0, encoding="utf-8")

    for name, matrix in (("m_1-2", m_1_2), ("m_2-3", m_2_3)):
        matrix.index = matrix.index.map(nfc)
        matrix.columns = matrix.columns.map(lambda value: nfc(str(value)))

        if list(matrix.index) != list(ORDER) or list(matrix.columns) != list(ORDER):
            raise ValueError(f"{name}.csv axes must equal alphabet.ORDER")

    return m_1_2.astype(bool), m_2_3.astype(bool)


def is_allowed(
    first: str,
    second: str,
    third: str,
    m_1_2: pd.DataFrame,
    m_2_3: pd.DataFrame,
) -> bool:
    """Return whether the root ``(first, second, third)`` is permitted.

    Args:
        first: C1 glyph.
        second: C2 glyph.
        third: C3 glyph.
        m_1_2: C1-C2 matrix from :func:`load_matrices`.
        m_2_3: C2-C3 matrix from :func:`load_matrices`.

    Returns:
        ``True`` iff ``M_1-2[c1, c2]`` and ``M_2-3[c2, c3]`` are both true.

    Raises:
        ValueError: If any glyph is outside the 28-consonant inventory.

    Notes:
        Inputs are NFC-normalized and validated by :func:`normalize_glyph`;
        the matrices must be indexed by :data:`arabic_roots.alphabet.ORDER`.
    """
    c1 = normalize_glyph(first)
    c2 = normalize_glyph(second)
    c3 = normalize_glyph(third)

    return bool(m_1_2.at[c1, c2]) and bool(m_2_3.at[c2, c3])
