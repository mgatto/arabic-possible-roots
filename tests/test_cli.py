"""Tests for the enumerate-roots CLI."""

import logging
import re
from pathlib import Path

import pytest

from arabic_roots.cli import build_parser, main


def test_parser_defaults() -> None:
    """Parser exposes data-dir, limit, output, scheme, delimiter, log-file."""
    args = build_parser().parse_args([])
    assert args.limit == 10
    assert args.output is None
    assert args.scheme == "arabic"
    assert args.delimiter == "-"
    assert args.log_file is None


def test_main_limit_zero(capsys: pytest.CaptureFixture[str]) -> None:
    """--limit 0 prints nothing but still succeeds."""
    assert main(["--limit", "0"]) == 0
    captured = capsys.readouterr()
    assert captured.out == ""


def test_main_limit_two(capsys: pytest.CaptureFixture[str]) -> None:
    """--limit 2 prints the first two possible roots, hyphen-joined."""
    assert main(["--limit", "2"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines == ["ء-ب-ء", "ء-ب-ت"]


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


def test_main_outputs_possible_roots_only(tmp_path: Path) -> None:
    """The written file holds possible roots: 9941 rows, no attested ك-ت-ب."""
    target = tmp_path / "roots.tsv"
    assert main(["--limit", "0", "--output", str(target)]) == 0
    lines = target.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "c1\tc2\tc3"
    assert len(lines) == 9941 + 1
    assert "ك\tت\tب" not in lines


def test_main_scheme_din(capsys: pytest.CaptureFixture[str]) -> None:
    """--scheme din31635 renders each consonant in DIN 31635."""
    assert main(["--scheme", "din31635", "--limit", "1"]) == 0
    assert capsys.readouterr().out == "ʾ-b-ʾ\n"


def test_main_delimiter_empty(capsys: pytest.CaptureFixture[str]) -> None:
    """--delimiter '' concatenates the rendered consonants."""
    assert main(["--limit", "2", "--delimiter", ""]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines == ["ءبء", "ءبت"]


def test_main_output_scheme_renders_cells(tmp_path: Path) -> None:
    """--output renders cells in the chosen scheme, columns stay separate."""
    target = tmp_path / "roots.tsv"
    assert main(["--scheme", "din31635", "--limit", "0", "--output", str(target)]) == 0
    lines = target.read_text(encoding="utf-8").splitlines()
    assert lines[0] == "c1\tc2\tc3"
    assert lines[1] == "ʾ\tb\tʾ"


def test_main_delimiter_collision_errors() -> None:
    """A delimiter that clashes with the active scheme exits loudly."""
    with pytest.raises(SystemExit):
        main(["--scheme", "din31635", "--delimiter", "b", "--limit", "0"])


def test_main_writes_timestamped_log_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """--log-file appends timestamped run records, mirrored to stderr."""
    log = tmp_path / "logs" / "run.log"
    assert main(["--limit", "0", "--log-file", str(log)]) == 0
    text = log.read_text(encoding="utf-8")
    assert "run: " in text
    assert "inputs: " in text
    assert "Allowed triliteral roots: 13656" in text
    assert "Possible triliteral roots: 9941" in text
    assert "variety=msa" in text
    assert re.search(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2} ", text, re.MULTILINE)
    assert "run: " in capsys.readouterr().err


def test_main_log_file_appends(tmp_path: Path) -> None:
    """Each run appends its own banner rather than overwriting."""
    log = tmp_path / "run.log"
    main(["--limit", "0", "--log-file", str(log)])
    main(["--limit", "0", "--log-file", str(log)])
    assert log.read_text(encoding="utf-8").count("run: ") == 2


def test_main_logs_banner_fields(caplog: pytest.LogCaptureFixture) -> None:
    """The run banner records effective options and embedded choices."""
    with caplog.at_level(logging.INFO, logger="arabic_roots.cli"):
        assert main(["--limit", "0", "--scheme", "din31635"]) == 0
    messages = [record.getMessage() for record in caplog.records]
    assert any("run: " in message for message in messages)
    assert any("scheme=din31635" in message for message in messages)
    assert any("variety=msa" in message for message in messages)
