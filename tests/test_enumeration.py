"""Golden-count tests for enumeration plus guard-prototype machine tests."""

import itertools

import pandas as pd

from arabic_roots.alphabet import ORDER
from arabic_roots.enumerator import count_roots, iter_roots
from arabic_roots.phonotactics import is_allowed, load_matrices
from arabic_roots.statemachine import TriliteralMachine


def test_permissive_baseline_is_28_cubed() -> None:
    """All-1 matrices yield exactly 28^3 candidates."""
    m_1_2, m_2_3 = load_matrices()
    assert count_roots(m_1_2, m_2_3) == 28**3 == 21952


def test_enumerator_matches_is_allowed() -> None:
    """iter_roots agrees with the is_allowed predicate on every triple."""
    m_1_2, m_2_3 = load_matrices()
    expected = [
        triple
        for triple in itertools.product(ORDER, repeat=3)
        if is_allowed(triple[0], triple[1], triple[2], m_1_2, m_2_3)
    ]
    assert list(iter_roots(m_1_2, m_2_3)) == expected


def test_zeroing_one_pair_removes_a_slice() -> None:
    """Blocking M_1-2[ب,ت] removes 28 roots (one C3 fan-out)."""
    m_1_2, m_2_3 = load_matrices()
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
