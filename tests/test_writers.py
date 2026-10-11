"""Tests for the suffix-driven output writers."""

import json
import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd
import pytest

from arabic_roots.writers import format_for_suffix, write_roots

_TRIPLES = [("ء", "ب", "ء"), ("ء", "ب", "ب")]


def test_format_for_suffix_known() -> None:
    """Registered suffixes map to their writer names."""
    assert format_for_suffix(Path("roots.tsv")) == "tsv"
    assert format_for_suffix(Path("roots.csv")) == "csv"
    assert format_for_suffix(Path("roots.jsonl")) == "jsonl"
    assert format_for_suffix(Path("roots.parquet")) == "parquet"
    assert format_for_suffix(Path("roots.sqlite")) == "sqlite"


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


def test_write_jsonl_key_order_and_literals(tmp_path: Path) -> None:
    """JSONL writes one object per line, keys ordered, glyphs literal."""
    target = tmp_path / "roots.jsonl"
    assert write_roots(target, _TRIPLES) == 2
    text = target.read_text(encoding="utf-8")
    assert text == (
        '{"c1": "ء", "c2": "ب", "c3": "ء"}\n{"c1": "ء", "c2": "ب", "c3": "ب"}\n'
    )
    assert "\\u" not in text
    for line in text.splitlines():
        assert list(json.loads(line)) == ["c1", "c2", "c3"]


def test_write_parquet_roundtrip(tmp_path: Path) -> None:
    """Parquet output round-trips columns, order, and values."""
    pytest.importorskip("pyarrow")
    target = tmp_path / "roots.parquet"
    assert write_roots(target, _TRIPLES) == 2
    frame = pd.read_parquet(target)
    assert list(frame.columns) == ["c1", "c2", "c3"]
    assert frame.to_dict("records") == [
        {"c1": "ء", "c2": "ب", "c3": "ء"},
        {"c1": "ء", "c2": "ب", "c3": "ب"},
    ]


def test_write_parquet_missing_engine(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A missing Parquet engine surfaces as a clear ValueError."""

    def _no_engine(*args: object, **kwargs: object) -> None:
        raise ImportError("pyarrow is not installed")

    monkeypatch.setattr(pd.DataFrame, "to_parquet", _no_engine)
    with pytest.raises(ValueError, match="pyarrow"):
        write_roots(tmp_path / "roots.parquet", _TRIPLES)


def test_write_sqlite_roundtrip(tmp_path: Path) -> None:
    """SQLite output stores one row per triple in insertion order."""
    target = tmp_path / "roots.sqlite"
    assert write_roots(target, _TRIPLES) == 2
    with closing(sqlite3.connect(target)) as connection:
        rows = connection.execute(
            "SELECT c1, c2, c3 FROM roots ORDER BY rowid"
        ).fetchall()
    assert rows == [("ء", "ب", "ء"), ("ء", "ب", "ب")]


def test_write_sqlite_primary_key_rejects_duplicate(tmp_path: Path) -> None:
    """The roots primary key rejects a duplicate triple."""
    target = tmp_path / "roots.sqlite"
    write_roots(target, _TRIPLES)
    with closing(sqlite3.connect(target)) as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO roots VALUES (?, ?, ?)", ("ء", "ب", "ء"))


def test_write_sqlite_replaces_existing(tmp_path: Path) -> None:
    """A second run replaces the database rather than appending."""
    target = tmp_path / "roots.sqlite"
    write_roots(target, _TRIPLES)
    assert write_roots(target, [("ب", "ت", "ث")]) == 1
    with closing(sqlite3.connect(target)) as connection:
        count = connection.execute("SELECT COUNT(*) FROM roots").fetchone()
    assert count == (1,)


def test_write_creates_parent_dirs(tmp_path: Path) -> None:
    """Missing parent directories are created."""
    target = tmp_path / "nested" / "roots.csv"
    assert write_roots(target, _TRIPLES) == 2
    assert target.exists()


def test_write_unknown_suffix_raises(tmp_path: Path) -> None:
    """write_roots rejects an unsupported suffix before writing."""
    with pytest.raises(ValueError, match="unsupported output extension"):
        write_roots(tmp_path / "roots.txt", _TRIPLES)
