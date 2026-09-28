"""Deterministic enumeration of triliteral candidates."""

import itertools
from collections.abc import Iterator

import pandas as pd

from arabic_roots.alphabet import ORDER
from arabic_roots.phonotactics import is_allowed

__all__ = ["count_roots", "iter_roots"]


def iter_roots(
    m_1_2: pd.DataFrame,
    m_2_3: pd.DataFrame,
    order: tuple[str, ...] = ORDER,
) -> Iterator[tuple[str, str, str]]:
    """Yield allowed ``(c1, c2, c3)`` triples in fixed ``order``.

    The product order is deterministic so runs are reproducible and the
    golden count test is stable across platforms.
    """
    for first, second, third in itertools.product(order, repeat=3):
        if is_allowed(first, second, third, m_1_2, m_2_3):
            yield (first, second, third)


def count_roots(m_1_2: pd.DataFrame, m_2_3: pd.DataFrame) -> int:
    """Count allowed triples without materializing the full list."""
    return sum(1 for _ in iter_roots(m_1_2, m_2_3))
