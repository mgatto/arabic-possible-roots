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

    Args:
        m_1_2: C1-C2 matrix from :func:`phonotactics.load_matrices`.
        m_2_3: C2-C3 matrix from :func:`phonotactics.load_matrices`.
        order: Axis order to iterate; defaults to
            :data:`arabic_roots.alphabet.ORDER`.

    Yields:
        Allowed triples of NFC inventory glyphs.

    Notes:
        Deterministic ``itertools.product`` order, so runs are reproducible
        and the golden-count test is stable across platforms. This is the
        batch enumeration path; it consults rules only, never attestation.
    """
    for first, second, third in itertools.product(order, repeat=3):
        if is_allowed(first, second, third, m_1_2, m_2_3):
            yield first, second, third


def count_roots(
    m_1_2: pd.DataFrame,
    m_2_3: pd.DataFrame,
    order: tuple[str, ...] = ORDER,
) -> int:
    """Count allowed triples without materializing the full list.

    Args:
        m_1_2: C1-C2 matrix from :func:`phonotactics.load_matrices`.
        m_2_3: C2-C3 matrix from :func:`phonotactics.load_matrices`.
        order: Axis order to iterate; defaults to
            :data:`arabic_roots.alphabet.ORDER`.

    Returns:
        The number of allowed triples, identical to ``len(list(iter_roots(
        m_1_2, m_2_3, order)))`` but streamed.
    """
    return sum(1 for _ in iter_roots(m_1_2, m_2_3, order))
