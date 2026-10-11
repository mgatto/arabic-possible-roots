"""Tests for output rendering in named transliteration schemes."""

from pathlib import Path

import pytest

from arabic_roots.render import (
    SCHEMES,
    build_schemes,
    iter_render_cells,
    render_cell,
    render_cells,
    render_triple,
    validate_delimiter,
)

_SCHEMES = build_schemes()


def test_schemes_cover_the_inventory() -> None:
    """Every scheme maps all 28 glyphs."""
    assert set(_SCHEMES) == set(SCHEMES)
    for table in _SCHEMES.values():
        assert len(table) == 28


def test_schemes_are_injective() -> None:
    """Distinct glyphs map to distinct symbols, so every scheme is reversible."""
    for table in _SCHEMES.values():
        assert len(set(table.values())) == 28


@pytest.mark.parametrize(
    ("scheme", "expected"),
    [
        ("arabic", "ص-ب-ر"),
        ("din31635", "ṣ-b-r"),
        ("ijmes", "ṣ-b-r"),
        ("ipa", "sˤ-b-r"),
    ],
)
def test_render_triple_sample(scheme: str, expected: str) -> None:
    """A fixed root renders to the pinned string per scheme."""
    assert render_triple(("ص", "ب", "ر"), scheme, "-", _SCHEMES) == expected


def test_render_ijmes_digraphs() -> None:
    """IJMES uses the expected digraphs (test-only literals)."""
    assert render_cell("ث", "ijmes", _SCHEMES) == "th"
    assert render_cell("ذ", "ijmes", _SCHEMES) == "dh"
    assert render_cell("ش", "ijmes", _SCHEMES) == "sh"
    assert render_cell("خ", "ijmes", _SCHEMES) == "kh"
    assert render_cell("غ", "ijmes", _SCHEMES) == "gh"


def test_din_and_ijmes_differ_for_jiim() -> None:
    """ج is ǧ in DIN 31635 but j in IJMES."""
    assert render_cell("ج", "din31635", _SCHEMES) == "ǧ"
    assert render_cell("ج", "ijmes", _SCHEMES) == "j"


def test_render_cells_keeps_columns() -> None:
    """render_cells returns three separate rendered cells."""
    assert render_cells(("ء", "ب", "ء"), "din31635", _SCHEMES) == ("ʾ", "b", "ʾ")


def test_iter_render_cells_streams() -> None:
    """iter_render_cells lazily renders each triple."""
    triples = [("ء", "ب", "ء"), ("ء", "ب", "ت")]
    assert list(iter_render_cells(triples, "din31635", _SCHEMES)) == [
        ("ʾ", "b", "ʾ"),
        ("ʾ", "b", "t"),
    ]


@pytest.mark.parametrize("delimiter", ["", "-", " ", "·"])
def test_render_delimiter_composition(delimiter: str) -> None:
    """The delimiter joins the rendered cells on stdout."""
    assert render_triple(("ء", "ب", "ء"), "arabic", delimiter, _SCHEMES) == (
        delimiter.join(("ء", "ب", "ء"))
    )


def test_validate_delimiter_accepts_dash() -> None:
    """A hyphen is a valid separator for every scheme."""
    assert validate_delimiter("-", "arabic", _SCHEMES) == "-"


def test_validate_delimiter_allows_empty() -> None:
    """An empty delimiter (concatenation) is allowed."""
    assert validate_delimiter("", "arabic", _SCHEMES) == ""


def test_validate_delimiter_rejects_newline() -> None:
    """Tab/newline separators are rejected."""
    with pytest.raises(ValueError, match="tab or newline"):
        validate_delimiter("\n", "arabic", _SCHEMES)


def test_validate_delimiter_rejects_scheme_symbol() -> None:
    """A separator that equals an active-scheme symbol is rejected."""
    with pytest.raises(ValueError, match="collides"):
        validate_delimiter("b", "din31635", _SCHEMES)


def test_build_schemes_missing_table_raises(tmp_path: Path) -> None:
    """A data root without the IJMES table fails loudly."""
    with pytest.raises(FileNotFoundError):
        build_schemes(tmp_path)


def test_no_rendering_in_core_modules() -> None:
    """Rendering stays at the I/O boundary; core modules never import it."""
    src = Path(__file__).resolve().parents[1] / "src" / "arabic_roots"
    for name in ("enumerator.py", "phonotactics.py", "statemachine.py"):
        text = (src / name).read_text(encoding="utf-8")
        assert "arabic_roots.render" not in text
        assert "arabic_roots.transliteration" not in text
