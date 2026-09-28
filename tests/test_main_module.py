"""Tests for the ``python -m arabic_roots`` module entry point."""

import runpy
import sys

import pytest


def test_main_module_limit_zero(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """``python -m arabic_roots --limit 0`` succeeds and prints nothing."""
    monkeypatch.setattr(sys, "argv", ["arabic_roots", "--limit", "0"])
    with pytest.raises(SystemExit) as excinfo:
        runpy.run_module("arabic_roots", run_name="__main__")
    assert excinfo.value.code == 0
    assert capsys.readouterr().out == ""


def test_main_module_help(monkeypatch: pytest.MonkeyPatch) -> None:
    """``python -m arabic_roots --help`` exits 0 via argparse."""
    monkeypatch.setattr(sys, "argv", ["arabic_roots", "--help"])
    with pytest.raises(SystemExit) as excinfo:
        runpy.run_module("arabic_roots", run_name="__main__")
    assert excinfo.value.code == 0
