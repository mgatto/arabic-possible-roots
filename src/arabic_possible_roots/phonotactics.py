"""Adjacent-pair phonotactic matrices for triliteral roots.

Two 28x28 boolean ``pandas.DataFrame`` objects share the fixed axis order
from :mod:`arabic_possible_roots.alphabet`:

- ``M_1-2`` gates consonants 1-2 of the root.
- ``M_2-3`` gates consonants 2-3 of the root.

``1`` means the ordered pair may co-occur, ``0`` forbids it. Each position is
assembled from one or more *matrix types*, one CSV per type named
``m_{position}_{type}.csv``:

- ``self`` (``m_1-2_self.csv`` / ``m_2-3_self.csv``): the identity/gemination
  gate. The ``M_1-2`` diagonal is ``0`` (``C1 == C2`` forbidden; Greenberg
  1950, *The Patterning of Root Morphemes in Semitic*, WORD 6:2, p.162) while
  the ``M_2-3`` diagonal stays ``1`` (``C2 == C3`` permitted). That asymmetry
  is an evidence-based rule, not a default.
- ``homorganic`` (``m_1-2_homorganic.csv`` / ``m_2-3_homorganic.csv``): the
  natural-class gate — no two *distinct* consonants of one class may be
  adjacent (McCarthy, *Feature geometry and dependency*, Phonetica 45:84-108,
  1988).

The types for a position are combined by logical **AND**: a pair is legal only
if *every* selected matrix allows it. ``load_matrices`` composes the default
set for each position; ``load_matrix`` composes one position explicitly.

Prohibitions from Ryder (*Arabic: A Linguistic Introduction*, owned copy) are
added one pair at a time, each with a ``TODO(Ryder:p.X)`` or page citation,
plus a regression test. Rules live only in ``data/rules/*.csv``; this module derives
per-glyph successor lists from them via :func:`successors` and never encodes
rules itself.
"""

from collections.abc import Sequence
from enum import StrEnum
from pathlib import Path

import pandas as pd
from frozendict import frozendict

from arabic_possible_roots.alphabet import ORDER, nfc

__all__ = [
    "DATA_DIR",
    "DEFAULT_TYPES",
    "RULES_SUBDIR",
    "MatrixType",
    "load_matrices",
    "load_matrix",
    "successors",
]

#: Default ``<repo>/data`` regardless of the caller's working directory.
DATA_DIR: Path = Path(__file__).resolve().parents[2] / "data"

#: Sub-directory of the data root holding the co-occurrence matrices.
RULES_SUBDIR: str = "rules"


class MatrixType(StrEnum):
    """Kind of rule matrix composing a position's final gate.

    Each value names a CSV ``m_{position}_{type}.csv`` under ``rules/``.
    """

    SELF = "self"
    HOMORGANIC = "homorganic"


#: Types composed (by AND) for each position when none are given explicitly.
DEFAULT_TYPES: tuple[MatrixType, ...] = (MatrixType.SELF, MatrixType.HOMORGANIC)


def load_matrix(
    data_dir: Path | None = None,
    position: str = "1-2",
    matrix_types: Sequence[MatrixType] = DEFAULT_TYPES,
) -> pd.DataFrame:
    """Load and AND one position's rule matrices into a final gate.

    Args:
        data_dir: Data root holding the ``rules/`` sub-directory. Defaults to
            :data:`DATA_DIR`.
        position: Root positions to gate, ``"1-2"`` or ``"2-3"``.
        matrix_types: Ordered kinds to compose; a pair is legal only if every
            listed matrix allows it. Defaults to :data:`DEFAULT_TYPES`.

    Returns:
        A boolean frame whose index and columns equal
        :data:`arabic_possible_roots.alphabet.ORDER`; a ``True`` cell means every
        selected matrix allows the ordered pair.

    Raises:
        ValueError: When ``matrix_types`` is empty or a matrix's axes do not
            match :data:`arabic_possible_roots.alphabet.ORDER`.
        FileNotFoundError: When a requested ``m_{position}_{type}.csv`` is
            missing.

    Notes:
        Axis labels are NFC-normalized before the ORDER check, so CSV files
        written on any platform validate identically. Each file is validated
        before the next is read, so a bad axis fails fast.
    """
    directory = (data_dir if data_dir is not None else DATA_DIR) / RULES_SUBDIR
    if not matrix_types:
        raise ValueError("matrix_types must not be empty")

    combined: pd.DataFrame | None = None
    for matrix_type in matrix_types:
        name = f"m_{position}_{matrix_type.value}"
        matrix = pd.read_csv(directory / f"{name}.csv", index_col=0, encoding="utf-8")
        matrix.index = matrix.index.map(nfc)
        matrix.columns = matrix.columns.map(lambda value: nfc(str(value)))
        if list(matrix.index) != list(ORDER) or list(matrix.columns) != list(ORDER):
            raise ValueError(f"{name}.csv axes must equal alphabet.ORDER")
        frame = matrix.astype(bool)
        combined = frame if combined is None else combined & frame

    assert combined is not None  # matrix_types is non-empty, checked above.
    return combined


def load_matrices(
    data_dir: Path | None = None,
    *,
    c1_c2: Sequence[MatrixType] = DEFAULT_TYPES,
    c2_c3: Sequence[MatrixType] = DEFAULT_TYPES,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compose the ``M_1-2`` and ``M_2-3`` gates from their rule matrices.

    Args:
        data_dir: Data root holding the ``rules/`` sub-directory with the
            per-type CSVs. Defaults to :data:`DATA_DIR`.
        c1_c2: Matrix kinds composed for the C1-C2 position.
        c2_c3: Matrix kinds composed for the C2-C3 position.

    Returns:
        ``(m_1_2, m_2_3)`` boolean frames whose index and columns are exactly
        :data:`arabic_possible_roots.alphabet.ORDER`. A ``True`` cell means every
        selected matrix allows the ordered pair.

    Raises:
        FileNotFoundError: When a requested CSV is missing.
        ValueError: When a selection is empty or axes do not match
            :data:`arabic_possible_roots.alphabet.ORDER`.
    """
    return (
        load_matrix(data_dir, "1-2", c1_c2),
        load_matrix(data_dir, "2-3", c2_c3),
    )


def successors(
    matrix: pd.DataFrame,
    order: tuple[str, ...] = ORDER,
) -> frozendict[str, tuple[str, ...]]:
    """Map each glyph to its allowed successors in ``order``.

    Args:
        matrix: A boolean co-occurrence matrix from :func:`load_matrices`.
        order: Axis order to preserve in each successor tuple; defaults to
            :data:`arabic_possible_roots.alphabet.ORDER`.

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
