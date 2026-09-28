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

import unicodedata
from pathlib import Path

import pandas as pd

from arabic_roots.alphabet import ORDER

__all__ = ["DATA_DIR", "default_data_dir", "is_allowed", "load_matrices"]


def default_data_dir() -> Path:
    """Return ``<repo>/data`` regardless of the caller's working directory."""
    return Path(__file__).resolve().parents[2] / "data"


DATA_DIR: Path = default_data_dir()


def _normalize_pair(first: str, second: str) -> tuple[str, str]:
    return (
        unicodedata.normalize("NFC", first),
        unicodedata.normalize("NFC", second),
    )


def load_matrices(data_dir: Path | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load ``m_1-2.csv`` and ``m_2-3.csv`` as boolean DataFrames.

    Raises:
        FileNotFoundError: When either CSV is missing.
        ValueError: When axes do not match :data:`arabic_roots.alphabet.ORDER`.
    """
    directory = data_dir if data_dir is not None else default_data_dir()
    m_1_2 = pd.read_csv(directory / "m_1-2.csv", index_col=0, encoding="utf-8")
    m_2_3 = pd.read_csv(directory / "m_2-3.csv", index_col=0, encoding="utf-8")
    for name, matrix in (("m_1-2", m_1_2), ("m_2-3", m_2_3)):
        matrix.index = matrix.index.map(
            lambda value: unicodedata.normalize("NFC", value)
        )
        matrix.columns = matrix.columns.map(
            lambda value: unicodedata.normalize("NFC", str(value))
        )
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
    """Return True when both adjacent pairs are permitted.

    A root ``(c1, c2, c3)`` is allowed iff ``M_1-2[c1, c2]`` and
    ``M_2-3[c2, c3]`` are both true.
    """
    c1, c2 = _normalize_pair(first, second)
    _, c3 = _normalize_pair(second, third)
    return bool(m_1_2.at[c1, c2]) and bool(m_2_3.at[c2, c3])
