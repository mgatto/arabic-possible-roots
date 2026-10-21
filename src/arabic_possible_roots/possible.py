"""Attested-root subtraction: the possible (legal but unattested) roots.

Composition layer over the two independent axes —
:mod:`arabic_possible_roots.enumerator` (rules only) and
:mod:`arabic_possible_roots.attestation` (lexicon). It filters the memoized enumeration
against a variety's attested ``frozenset`` (O(1) membership), yielding the
project's target concept: *possible roots*.

Pure and I/O-free: the attested map is passed in, so this module imports neither
the loader nor the filesystem. Attested data is a lexicon, never a rule, so it
never feeds back into the enumerator.
"""

from collections.abc import Iterator, Mapping
from itertools import filterfalse

import pandas as pd

from arabic_possible_roots.alphabet import ORDER
from arabic_possible_roots.enumerator import iter_roots

__all__ = ["attested_illegal", "count_possible", "iter_possible"]

type Triple = tuple[str, str, str]
type AttestedMap = Mapping[str, frozenset[Triple]]


def iter_possible(
    m_1_2: pd.DataFrame,
    m_2_3: pd.DataFrame,
    attested: AttestedMap,
    variety: str = "msa",
    order: tuple[str, ...] = ORDER,
) -> Iterator[Triple]:
    """Yield legal-but-unattested triples in fixed ``order``.

    Args:
        m_1_2: C1-C2 matrix from
            :func:`arabic_possible_roots.phonotactics.load_matrices`.
        m_2_3: C2-C3 matrix from
            :func:`arabic_possible_roots.phonotactics.load_matrices`.
        attested: Variety -> frozenset map from
            :func:`arabic_possible_roots.attestation.load_attested`.
        variety: Variety to subtract; unknown varieties subtract nothing.
        order: Axis order to iterate; defaults to
            :data:`arabic_possible_roots.alphabet.ORDER`.

    Yields:
        Allowed triples absent from ``attested[variety]``, in
        ORDER-lexicographic order (the enumeration order, minus attested).
    """
    known = attested.get(variety, frozenset())
    return filterfalse(known.__contains__, iter_roots(m_1_2, m_2_3, order))


def count_possible(
    m_1_2: pd.DataFrame,
    m_2_3: pd.DataFrame,
    attested: AttestedMap,
    variety: str = "msa",
    order: tuple[str, ...] = ORDER,
) -> int:
    """Count legal-but-unattested triples.

    Args:
        m_1_2: C1-C2 matrix from
            :func:`arabic_possible_roots.phonotactics.load_matrices`.
        m_2_3: C2-C3 matrix from
            :func:`arabic_possible_roots.phonotactics.load_matrices`.
        attested: Variety -> frozenset map from
            :func:`arabic_possible_roots.attestation.load_attested`.
        variety: Variety to subtract; unknown varieties subtract nothing.
        order: Axis order to iterate; defaults to
            :data:`arabic_possible_roots.alphabet.ORDER`.

    Returns:
        The number of allowed triples absent from ``attested[variety]``. Cheap
        because the underlying :func:`arabic_possible_roots.enumerator.iter_roots` walk
        is memoized.
    """
    return sum(1 for _ in iter_possible(m_1_2, m_2_3, attested, variety, order))


def attested_illegal(
    m_1_2: pd.DataFrame,
    m_2_3: pd.DataFrame,
    attested: AttestedMap,
    variety: str = "msa",
    order: tuple[str, ...] = ORDER,
) -> tuple[Triple, ...]:
    """Return attested triples that are not phonotactically legal.

    Args:
        m_1_2: C1-C2 matrix from
            :func:`arabic_possible_roots.phonotactics.load_matrices`.
        m_2_3: C2-C3 matrix from
            :func:`arabic_possible_roots.phonotactics.load_matrices`.
        attested: Variety -> frozenset map from
            :func:`arabic_possible_roots.attestation.load_attested`.
        variety: Variety to inspect; unknown varieties yield an empty tuple.
        order: Axis order to iterate; defaults to
            :data:`arabic_possible_roots.alphabet.ORDER`.

    Returns:
        The attested triples absent from the allowed set, in deterministic
        codepoint order. These are a rules-vs-lexicon disagreement: the lexicon
        attests a root the matrices forbid.
    """
    allowed = set(iter_roots(m_1_2, m_2_3, order))
    return tuple(sorted(attested.get(variety, frozenset()) - allowed))
