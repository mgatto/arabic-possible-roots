"""Tests for the ``python -m arabic_possible_roots`` module entry point."""

import runpy
import sys
from importlib.metadata import version as package_version

import pytest

import arabic_possible_roots


def test_main_module_limit_zero(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """``python -m arabic_possible_roots --limit 0`` succeeds and prints nothing."""
    monkeypatch.setattr(sys, "argv", ["arabic_possible_roots", "--limit", "0"])
    with pytest.raises(SystemExit) as excinfo:
        runpy.run_module("arabic_possible_roots", run_name="__main__")
    assert excinfo.value.code == 0
    assert capsys.readouterr().out == ""


def test_main_module_help(monkeypatch: pytest.MonkeyPatch) -> None:
    """``python -m arabic_possible_roots --help`` exits 0 via argparse."""
    monkeypatch.setattr(sys, "argv", ["arabic_possible_roots", "--help"])
    with pytest.raises(SystemExit) as excinfo:
        runpy.run_module("arabic_possible_roots", run_name="__main__")
    assert excinfo.value.code == 0


def test_version_single_sourced() -> None:
    """``__version__`` mirrors pyproject.toml via importlib.metadata."""
    assert arabic_possible_roots.__version__ == package_version("arabic-possible-roots")
    assert arabic_possible_roots.__version__ == "0.6.0"
