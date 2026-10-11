"""Golden-count tests for enumeration plus guard-prototype machine tests."""

import itertools

import pandas as pd

from arabic_roots.alphabet import ORDER
from arabic_roots.enumerator import count_roots, iter_roots
from arabic_roots.phonotactics import load_matrices
from arabic_roots.statemachine import TriliteralMachine


def _all_ones() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Synthetic permissive matrices: every cell ``True`` (diagonals included)."""
    order = list(ORDER)
    m_1_2 = pd.DataFrame(1, index=order, columns=order).astype(bool)
    m_2_3 = pd.DataFrame(1, index=order, columns=order).astype(bool)
    return m_1_2, m_2_3


def _reference_allowed(
    c1: str, c2: str, c3: str, m_1_2: pd.DataFrame, m_2_3: pd.DataFrame
) -> bool:
    """Independent oracle: direct cell lookups, no adjacency lists."""
    return bool(m_1_2.at[c1, c2]) and bool(m_2_3.at[c2, c3])


def test_permissive_baseline_is_28_cubed() -> None:
    """All-1 matrices yield exactly 28^3 candidates."""
    m_1_2, m_2_3 = _all_ones()
    assert count_roots(m_1_2, m_2_3) == 28**3 == 21952


def test_repo_matrix_count_is_pinned() -> None:
    """Shipped matrices yield 21168 (M_1-2 diagonal zeroed: C1 != C2)."""
    m_1_2, m_2_3 = load_matrices()
    assert count_roots(m_1_2, m_2_3) == 21168


def test_enumerator_matches_reference_oracle() -> None:
    """iter_roots agrees with an independent cell-lookup oracle."""
    m_1_2, m_2_3 = load_matrices()
    expected = [
        triple
        for triple in itertools.product(ORDER, repeat=3)
        if _reference_allowed(triple[0], triple[1], triple[2], m_1_2, m_2_3)
    ]
    assert list(iter_roots(m_1_2, m_2_3)) == expected


def test_diagonal_rule_c1_ne_c2_c2_eq_c3() -> None:
    """C1 == C2 is forbidden; C2 == C3 is permitted (Greenberg 1950, p.162)."""
    m_1_2, m_2_3 = load_matrices()
    roots = set(iter_roots(m_1_2, m_2_3))
    assert all((glyph, glyph, ORDER[0]) not in roots for glyph in ORDER)
    assert ("ب", "ب", "ب") not in roots
    assert ("ب", "ت", "ت") in roots


def test_zeroing_one_pair_removes_a_slice() -> None:
    """Blocking M_1-2[ب,ت] removes 28 roots (one C3 fan-out)."""
    m_1_2, m_2_3 = _all_ones()
    frame = m_1_2.copy()
    frame.at["ب", "ت"] = False
    assert count_roots(frame, m_2_3) == 28**3 - 28


def test_statemachine_guards_query_matrices() -> None:
    """Driver allows the permissive triple and blocks a zeroed pair."""
    m_1_2, m_2_3 = load_matrices()
    ok_machine = TriliteralMachine(m_1_2, m_2_3, c1="ب", c2="ت", c3="ث")
    assert ok_machine.pair12_allowed() is True
    assert ok_machine.pair23_allowed() is True

    blocked_m_1_2 = m_1_2.copy()
    blocked_m_1_2.at["ب", "ت"] = False
    blocked = TriliteralMachine(blocked_m_1_2, m_2_3, c1="ب", c2="ت", c3="ث")
    assert blocked.pair12_allowed() is False

    empty = TriliteralMachine(m_1_2, m_2_3)
    assert empty.pair12_allowed() is False
    assert empty.pair23_allowed() is False


def test_statemachine_emits_permissive_root() -> None:
    """An all-1 triple walks r_0 -> r_3 via events."""
    m_1_2, m_2_3 = load_matrices()
    machine = TriliteralMachine(m_1_2, m_2_3, c1="ب", c2="ت", c3="ث")
    machine.send("emit_r1")
    machine.send("emit_r2")
    machine.send("emit_r3")
    active = {state.id for state in machine.configuration}
    assert "r_3" in active
    _ = pd  # keep pandas import load-bearing for type-checkers.
