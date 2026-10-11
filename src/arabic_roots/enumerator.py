"""Deterministic enumeration of triliteral candidates.

Walks the co-occurrence matrices directly, following only ``1`` cells via
:func:`arabic_roots.phonotactics.successors`, so forbidden pairs are never
generated. The fully materialized result is memoized on matrix content, so
repeated ``iter_roots`` / ``count_roots`` calls (the CLI makes three) reuse a
single traversal.
"""

from collections.abc import Iterator

import pandas as pd

from arabic_roots.alphabet import ORDER
from arabic_roots.phonotactics import successors

__all__ = ["count_roots", "iter_roots"]

type _Triples = tuple[tuple[str, str, str], ...]
type _CacheKey = tuple[tuple[int, int], bytes, tuple[int, int], bytes, tuple[str, ...]]

#: Unbounded memo of materialized triples, keyed by matrix content + order.
#: Only content-distinct matrices create entries, and matrices are few in
#: practice. Attestation is a separate axis and must never enter this key.
_CACHE: dict[_CacheKey, _Triples] = {}


def _compiled(
    m_1_2: pd.DataFrame,
    m_2_3: pd.DataFrame,
    order: tuple[str, ...],
) -> _Triples:
    """Return the cached, fully materialized allowed triples.

    Args:
        m_1_2: C1-C2 matrix from :func:`arabic_roots.phonotactics.load_matrices`.
        m_2_3: C2-C3 matrix from :func:`arabic_roots.phonotactics.load_matrices`.
        order: Axis order to iterate.

    Returns:
        Every allowed ``(c1, c2, c3)`` triple in ORDER-lexicographic order.

    Notes:
        Memoized on ``(m_1_2 values, m_2_3 values, order)``. The key is matrix
        content only; the cache is unbounded because content-distinct matrices
        are few. Attestation is deliberately excluded so the rule cache stays
        reusable by a later subtraction layer.
    """
    key: _CacheKey = (
        m_1_2.shape,
        m_1_2.values.tobytes(),
        m_2_3.shape,
        m_2_3.values.tobytes(),
        tuple(order),
    )
    cached = _CACHE.get(key)
    if cached is None:
        succ_1_2 = successors(m_1_2, order)
        succ_2_3 = successors(m_2_3, order)
        cached = tuple(
            (first, second, third)
            for first in order
            for second in succ_1_2[first]
            for third in succ_2_3[second]
        )
        _CACHE[key] = cached
    return cached


def iter_roots(
    m_1_2: pd.DataFrame,
    m_2_3: pd.DataFrame,
    order: tuple[str, ...] = ORDER,
) -> Iterator[tuple[str, str, str]]:
    """Yield allowed ``(c1, c2, c3)`` triples in fixed ``order``.

    Args:
        m_1_2: C1-C2 matrix from :func:`arabic_roots.phonotactics.load_matrices`.
        m_2_3: C2-C3 matrix from :func:`arabic_roots.phonotactics.load_matrices`.
        order: Axis order to iterate; defaults to
            :data:`arabic_roots.alphabet.ORDER`.

    Yields:
        Allowed triples of NFC inventory glyphs, in ORDER-lexicographic order
        (identical to the old ``itertools.product`` order restricted to
        allowed triples).

    Notes:
        Deterministic successor walk, so runs are reproducible and the
        golden-count test is stable across platforms. This is the batch
        enumeration path; it consults rules only, never attestation.
    """
    yield from _compiled(m_1_2, m_2_3, order)


def count_roots(
    m_1_2: pd.DataFrame,
    m_2_3: pd.DataFrame,
    order: tuple[str, ...] = ORDER,
) -> int:
    """Count allowed triples without re-walking the matrices.

    Args:
        m_1_2: C1-C2 matrix from :func:`arabic_roots.phonotactics.load_matrices`.
        m_2_3: C2-C3 matrix from :func:`arabic_roots.phonotactics.load_matrices`.
        order: Axis order to iterate; defaults to
            :data:`arabic_roots.alphabet.ORDER`.

    Returns:
        The number of allowed triples, identical to
        ``len(list(iter_roots(m_1_2, m_2_3, order)))`` but served from the
        memoized enumeration.
    """
    return len(_compiled(m_1_2, m_2_3, order))
