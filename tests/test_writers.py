"""Tests for the suffix-driven output writers."""

from pathlib import Path

import pytest

from arabic_roots.writers import format_for_suffix, write_roots

_TRIPLES = [("ء", "ب", "ء"), ("ء", "ب", "ب")]


def test_format_for_suffix_known() -> None:
    """Registered suffixes map to their writer names."""
    assert format_for_suffix(Path("roots.tsv")) == "tsv"
    assert format_for_suffix(Path("roots.csv")) == "csv"


def test_format_for_suffix_is_case_insensitive() -> None:
    """Suffix matching ignores case."""
    assert format_for_suffix(Path("roots.CSV")) == "csv"


def test_format_for_suffix_unknown_raises() -> None:
    """An unrecognized suffix is a loud error."""
    with pytest.raises(ValueError, match="unsupported output extension"):
        format_for_suffix(Path("roots.txt"))


def test_format_for_suffix_missing_raises() -> None:
    """A path with no suffix is a loud error."""
    with pytest.raises(ValueError, match="unsupported output extension"):
        format_for_suffix(Path("roots"))


def test_write_tsv_header_and_rows(tmp_path: Path) -> None:
    """TSV output carries the c1/c2/c3 header then tab-separated rows."""
    target = tmp_path / "roots.tsv"
    assert write_roots(target, _TRIPLES) == 2
    assert target.read_text(encoding="utf-8") == "c1\tc2\tc3\nء\tب\tء\nء\tب\tب\n"


def test_write_csv_header_and_rows(tmp_path: Path) -> None:
    """CSV output carries the c1/c2/c3 header then comma-separated rows."""
    target = tmp_path / "roots.csv"
    assert write_roots(target, _TRIPLES) == 2
    assert target.read_text(encoding="utf-8") == "c1,c2,c3\nء,ب,ء\nء,ب,ب\n"


def test_write_creates_parent_dirs(tmp_path: Path) -> None:
    """Missing parent directories are created."""
    target = tmp_path / "nested" / "roots.csv"
    assert write_roots(target, _TRIPLES) == 2
    assert target.exists()


def test_write_unknown_suffix_raises(tmp_path: Path) -> None:
    """write_roots rejects an unsupported suffix before writing."""
    with pytest.raises(ValueError, match="unsupported output extension"):
        write_roots(tmp_path / "roots.txt", _TRIPLES)
