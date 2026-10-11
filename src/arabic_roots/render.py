"""Output rendering for enumerated roots in named transliteration schemes.

Rendering is the only place romanization appears (AGENTS §4), and it happens at
the I/O boundary — never inside the enumerator, phonotactics, or state machine.
Scheme symbols are data, not code:

- ``arabic`` — the literal inventory glyph (identity).
- ``din31635`` / ``ipa`` — typed ``Letter`` fields in
  :mod:`arabic_roots.alphabet`.
- ``ijmes`` — loaded from ``data/transliterations/ijmes.csv``; its digraph
  symbols stay out of ``src/`` per AGENTS §4.

:func:`build_schemes` performs the one-time I/O (reading the IJMES table); the
``render_*`` helpers are pure and reusable by other programs (AGENTS §1).
"""

import csv
from collections.abc import Iterable, Iterator
from pathlib import Path

from frozendict import frozendict

from arabic_roots.alphabet import LETTERS, ORDER, nfc
from arabic_roots.phonotactics import DATA_DIR
from arabic_roots.transliteration import (
    TRANSLITERATIONS_SUBDIR,
    build_decoder,
    build_encoder,
)

__all__ = [
    "SCHEMES",
    "build_schemes",
    "iter_render_cells",
    "render_cell",
    "render_cells",
    "render_triple",
    "validate_delimiter",
]

#: Supported output schemes.
SCHEMES: tuple[str, ...] = ("arabic", "din31635", "ijmes", "ipa")

#: Scheme-table column holding the IJMES symbol.
_IJMES: str = "ijmes"

type Triple = tuple[str, str, str]
type Schemes = frozendict[str, frozendict[str, str]]


def build_schemes(data_dir: Path | None = None) -> Schemes:
    """Build a glyph -> symbol map for every scheme in :data:`SCHEMES`.

    Args:
        data_dir: Data root holding ``transliterations/ijmes.csv``. Defaults to
            :data:`arabic_roots.phonotactics.DATA_DIR`.

    Returns:
        A ``frozendict`` mapping each scheme name to its glyph -> symbol map.

    Raises:
        FileNotFoundError: When the IJMES table is missing.
        ValueError: When the IJMES table does not cover the inventory exactly.
    """
    directory = data_dir if data_dir is not None else DATA_DIR
    with (directory / TRANSLITERATIONS_SUBDIR / f"{_IJMES}.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        ijmes = build_encoder(
            build_decoder(csv.DictReader(handle), symbol_column=_IJMES)
        )
    return frozendict(
        {
            "arabic": frozendict({glyph: glyph for glyph in ORDER}),
            "din31635": frozendict(
                {letter.glyph: letter.din31635 for letter in LETTERS}
            ),
            "ipa": frozendict({letter.glyph: letter.ipa for letter in LETTERS}),
            _IJMES: ijmes,
        }
    )


def render_cell(glyph: str, scheme: str, schemes: Schemes) -> str:
    """Render one inventory glyph in ``scheme``.

    Args:
        glyph: An inventory glyph (NFC).
        scheme: A name from :data:`SCHEMES`.
        schemes: Map from :func:`build_schemes`.

    Returns:
        The scheme symbol for ``glyph``.
    """
    return schemes[scheme][glyph]


def render_cells(triple: Triple, scheme: str, schemes: Schemes) -> Triple:
    """Render a triple's three glyphs, keeping the columns separate.

    Args:
        triple: ``(c1, c2, c3)`` inventory glyphs.
        scheme: A name from :data:`SCHEMES`.
        schemes: Map from :func:`build_schemes`.

    Returns:
        The three rendered cells (no delimiter; for ``--output`` files).
    """
    table = schemes[scheme]
    first, second, third = triple
    return (table[first], table[second], table[third])


def iter_render_cells(
    triples: Iterable[Triple], scheme: str, schemes: Schemes
) -> Iterator[Triple]:
    """Lazily render each triple's cells in ``scheme``."""
    table = schemes[scheme]
    for first, second, third in triples:
        yield (table[first], table[second], table[third])


def render_triple(triple: Triple, scheme: str, delimiter: str, schemes: Schemes) -> str:
    """Render a triple and join its cells with ``delimiter`` (stdout form)."""
    return delimiter.join(render_cells(triple, scheme, schemes))


def validate_delimiter(delimiter: str, scheme: str, schemes: Schemes) -> str:
    """Return the NFC delimiter, rejecting separators that clash with ``scheme``.

    Args:
        delimiter: Candidate separator (may be empty for concatenation).
        scheme: Active scheme name.
        schemes: Map from :func:`build_schemes`.

    Returns:
        The NFC-normalized delimiter.

    Raises:
        ValueError: If the delimiter contains a tab/CR/LF, or equals a symbol
            in the active scheme.
    """
    normalized = nfc(delimiter)
    if any(char in normalized for char in "\t\r\n"):
        raise ValueError(f"delimiter may not contain tab or newline: {delimiter!r}")
    if normalized and normalized in schemes[scheme].values():
        raise ValueError(f"delimiter {delimiter!r} collides with a {scheme} symbol")
    return normalized
