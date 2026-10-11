"""Tests for the enumerate-roots CLI."""

from pathlib import Path

import pytest

from arabic_roots.cli import build_parser, main


def test_parser_defaults() -> None:
    """Parser exposes data-dir, limit, and output options."""
    args = build_parser().parse_args([])
    assert args.limit == 10
    assert args.output is None


def test_main_limit_zero(capsys: pytest.CaptureFixture[str]) -> None:
    """--limit 0 prints nothing but still succeeds."""
    assert main(["--limit", "0"]) == 0
    captured = capsys.readouterr()
    assert captured.out == ""


def test_main_limit_two(capsys: pytest.CaptureFixture[str]) -> None:
    """--limit 2 prints the first two deterministic roots, hyphen-joined."""
    assert main(["--limit", "2"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines == ["ء-ب-ء", "ء-ب-ب"]


def test_main_writes_tsv(tmp_path: Path) -> None:
    """--output writes a header then one NFC triple per line as TSV."""
    target = tmp_path / "roots.tsv"
    assert main(["--limit", "0", "--output", str(target)]) == 0
    assert target.exists()
    lines = target.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "c1\tc2\tc3"
    assert lines[1] == "ء\tب\tء"


def test_main_writes_csv(tmp_path: Path) -> None:
    """--output infers CSV from the .csv suffix and writes a header."""
    target = tmp_path / "roots.csv"
    assert main(["--limit", "0", "--output", str(target)]) == 0
    lines = target.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "c1,c2,c3"
    assert lines[1] == "ء,ب,ء"


def test_main_unknown_suffix_errors(tmp_path: Path) -> None:
    """An unsupported --output suffix exits loudly."""
    target = tmp_path / "roots.txt"
    with pytest.raises(SystemExit):
        main(["--limit", "0", "--output", str(target)])
