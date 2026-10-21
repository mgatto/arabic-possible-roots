"""Tests for the possible-root (attested-subtracted) layer."""

import csv
from pathlib import Path

from arabic_possible_roots.attestation import load_attested
from arabic_possible_roots.enumerator import count_roots, iter_roots
from arabic_possible_roots.phonotactics import load_matrices
from arabic_possible_roots.possible import (
    attested_illegal,
    count_possible,
    iter_possible,
)

_HEADER = ["c1", "c2", "c3", "variety", "source"]


def _write_attested(path: Path, rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(_HEADER)
        writer.writerows(rows)


def test_iter_possible_subtracts_allowed_attested(tmp_path: Path) -> None:
    """Possible = allowed − attested; order is preserved."""
    _write_attested(
        tmp_path / "roots" / "attested.csv",
        [
            ["ء", "ب", "ب", "msa", "unit"],
            ["ب", "ب", "ر", "msa", "unit"],
        ],
    )
    m_1_2, m_2_3 = load_matrices()
    attested = load_attested(tmp_path)
    allowed = list(iter_roots(m_1_2, m_2_3))
    possible = list(iter_possible(m_1_2, m_2_3, attested))
    assert possible == [triple for triple in allowed if triple != ("ء", "ب", "ب")]
    assert ("ء", "ب", "ب") not in possible
    assert ("ء", "ب", "ء") in possible


def test_unknown_variety_subtracts_nothing(tmp_path: Path) -> None:
    """A variety with no rows leaves the enumeration intact."""
    _write_attested(
        tmp_path / "roots" / "attested.csv",
        [["ء", "ب", "ب", "msa", "unit"]],
    )
    m_1_2, m_2_3 = load_matrices()
    attested = load_attested(tmp_path)
    assert count_possible(m_1_2, m_2_3, attested, variety="classical") == count_roots(
        m_1_2, m_2_3
    )


def test_golden_possible_count() -> None:
    """The shipped data yields the pinned 9941 possible roots."""
    m_1_2, m_2_3 = load_matrices()
    attested = load_attested()
    assert count_possible(m_1_2, m_2_3, attested) == 9941


def test_attested_illegal_detects_inconsistency(tmp_path: Path) -> None:
    """Attested roots that are not phonotactically legal are reported."""
    _write_attested(
        tmp_path / "roots" / "attested.csv",
        [
            ["ء", "ب", "ب", "msa", "unit"],
            ["ب", "ب", "ر", "msa", "unit"],
        ],
    )
    m_1_2, m_2_3 = load_matrices()
    attested = load_attested(tmp_path)
    assert attested_illegal(m_1_2, m_2_3, attested) == (("ب", "ب", "ر"),)


def test_shipped_illegal_attested() -> None:
    """The shipped lexicon has exactly 244 phonotactically illegal roots."""
    m_1_2, m_2_3 = load_matrices()
    attested = load_attested()
    illegal = attested_illegal(m_1_2, m_2_3, attested)
    assert len(illegal) == 244
    assert illegal[0] == ("ء", "ح", "ح")
    assert illegal[-1] == ("ي", "و", "م")
