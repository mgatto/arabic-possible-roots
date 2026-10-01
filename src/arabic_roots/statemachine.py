"""Single-root guard prototype built on python-statemachine.

The machine encodes no phonotactic rules and is NOT on the enumeration
path (batch enumeration lives in :mod:`arabic_roots.enumerator`, which
uses ``itertools.product`` + :func:`phonotactics.is_allowed`). It validates
one ``(c1, c2, c3)`` triple at a time, walking ``r_0 -> r_1 -> r_2 -> r_3``
with each transition guarded by a lookup into the caller's M_1-2/M_2-3 matrices
(see :mod:`arabic_roots.phonotactics`). Rule changes happen in
``data/m_1-2.csv`` / ``data/m_2-3.csv``, never here.
"""

from typing import Any

import pandas as pd
from statemachine import State, StateChart

from arabic_roots.alphabet import nfc, normalize_glyph

__all__ = ["TriliteralMachine"]


class TriliteralMachine(StateChart[Any]):
    """Validate one root triple; guards consult matrices from the caller."""

    r_0 = State(initial=True)
    r_1 = State()
    r_2 = State()
    r_3 = State(final=True)

    emit_r1 = r_0.to(r_1)
    emit_r2 = r_1.to(r_2, cond="pair12_allowed")
    emit_r3 = r_2.to(r_3, cond="pair23_allowed")

    def __init__(
        self,
        m_1_2: pd.DataFrame,
        m_2_3: pd.DataFrame,
        c1: str = "",
        c2: str = "",
        c3: str = "",
    ) -> None:
        super().__init__()
        self.m_1_2 = m_1_2
        self.m_2_3 = m_2_3
        self.c1 = nfc(c1) if c1 else ""
        self.c2 = nfc(c2) if c2 else ""
        self.c3 = nfc(c3) if c3 else ""

    def pair12_allowed(self) -> bool:
        """Guard for ``r_1 -> r_2`` consulting M_1-2."""
        if not self.c1 or not self.c2:
            return False
        first = normalize_glyph(self.c1)
        second = normalize_glyph(self.c2)
        return bool(self.m_1_2.at[first, second])

    def pair23_allowed(self) -> bool:
        """Guard for ``r_2 -> r_3`` consulting M_2-3."""
        if not self.c2 or not self.c3:
            return False
        second = normalize_glyph(self.c2)
        third = normalize_glyph(self.c3)
        return bool(self.m_2_3.at[second, third])

    def on_enter_r_1(self, _source: Any, _target: Any) -> None:
        """Hook after emitting C1 (logging only, no rule logic)."""

    def on_enter_r_2(self, _source: Any, _target: Any) -> None:
        """Hook after emitting C2 (logging only, no rule logic)."""

    def on_enter_r_3(self, _source: Any, _target: Any) -> None:
        """Hook after emitting C3 (logging only, no rule logic)."""
