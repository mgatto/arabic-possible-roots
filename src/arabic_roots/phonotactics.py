"""Adjacent-pair phonotactic matrices for triliteral roots.

Two 28x28 boolean ``pandas.DataFrame`` objects share the fixed axis order
from :mod:`arabic_roots.alphabet`:

- ``M_1-2`` gates consonants 1-2 of the root.
- ``M_2-3`` gates consonants 2-3 of the root.

``1`` means the ordered pair may co-occur, ``0`` forbids it. The two
diagonals differ by design:

- ``M_1-2`` diagonal is ``0``: ``C1 == C2`` (initial gemination) is forbidden
  (Greenberg 1950, *The Patterning of Root Morphemes in Semitic*, WORD 6:2,
  p.162).
- ``M_2-3`` diagonal is ``1``: ``C2 == C3`` (medial gemination) is permitted.

That asymmetry is an evidence-based rule, not a default.

Prohibitions from Ryder (*Arabic: A Linguistic Introduction*, owned copy) are
added one pair at a time, each with a ``TODO(Ryder:p.X)`` or page citation,
plus a regression test. Rules live only in ``data/*.csv``; this module derives
per-glyph successor lists from them via :func:`successors` and never encodes
rules itself.
"""

from pathlib import Path

import pandas as pd
from frozendict import frozendict

from arabic_roots.alphabet import ORDER, nfc

__all__ = ["DATA_DIR", "load_matrices", "successors"]

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


def successors(
    matrix: pd.DataFrame,
    order: tuple[str, ...] = ORDER,
) -> frozendict[str, tuple[str, ...]]:
    """Map each glyph to its allowed successors in ``order``.

    Args:
        matrix: A boolean co-occurrence matrix from :func:`load_matrices`.
        order: Axis order to preserve in each successor tuple; defaults to
            :data:`arabic_roots.alphabet.ORDER`.

    Returns:
        A ``frozendict`` mapping each row glyph to the tuple of column glyphs
        whose cell is ``True``, in ``order`` order. Empty when a row allows
        nothing.

    Notes:
        This is the enumeration primitive: walking ``M_1-2`` then ``M_2-3``
        successor lists visits exactly the allowed triples and never inspects a
        forbidden cell. It derives from the matrices only — no rule logic here.
    """
    return frozendict(
        {
            row: tuple(column for column in order if bool(matrix.at[row, column]))
            for row in order
        }
    )
