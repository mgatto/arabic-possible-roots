"""Tests for the disposable-copy Python version matrix runner."""

import importlib.util
import json
import subprocess
from collections.abc import Sequence
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "test_python_versions.py"

_PYPROJECT = """\
[project]
requires-python = "==3.14.*"

[tool.ruff]
target-version = "py314"

[tool.mypy]
python_version = "3.14"

[tool.ty.environment]
python-version = "3.14"
"""


def _load_runner() -> ModuleType:
    spec = importlib.util.spec_from_file_location("apr_test_python_versions", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runner: Any = _load_runner()


def test_parse_python_version_stable() -> None:
    version = runner.parse_python_version("3.13.5")
    assert version.major == 3
    assert version.minor == 13
    assert version.patch == 5
    assert version.pre is None
    assert version.minor_label == "3.13"
    assert version.ruff_target == "py313"
    assert version.text == "3.13.5"


def test_parse_python_version_prerelease() -> None:
    version = runner.parse_python_version("3.15.0rc2")
    assert version.minor_label == "3.15"
    assert version.ruff_target == "py315"
    assert version.text == "3.15.0rc2"


def test_parse_python_version_rejects_unknown() -> None:
    with pytest.raises(ValueError, match="unsupported Python version"):
        runner.parse_python_version("3")


def test_requires_python_stable_and_prerelease() -> None:
    stable = runner.parse_python_version("3.13.5")
    prerelease = runner.parse_python_version("3.15.0rc2")
    assert runner.requires_python(stable) == ">=3.13"
    assert runner.requires_python(prerelease) == ">=3.15.0rc2"


def test_patch_pyproject_text_replaces_all_targets() -> None:
    version = runner.parse_python_version("3.13.5")
    patched = runner.patch_pyproject_text(_PYPROJECT, version)
    assert 'requires-python = ">=3.13"' in patched
    assert 'target-version = "py313"' in patched
    assert 'python_version = "3.13"' in patched
    assert 'python-version = "3.13"' in patched
    assert "3.14" not in patched


def test_patch_pyproject_text_requires_every_setting() -> None:
    text = _PYPROJECT.replace('target-version = "py314"\n', "")
    with pytest.raises(ValueError, match="ruff target-version"):
        runner.patch_pyproject_text(text, runner.parse_python_version("3.13"))


def test_select_specs_defaults() -> None:
    specs = runner.select_specs([], False)
    assert [(spec.selector, spec.blocking) for spec in specs] == [
        ("3.12", False),
        ("3.13", True),
        ("3.14", True),
        ("3.15", False),
    ]


def test_select_specs_preserves_roles_and_strict() -> None:
    specs = runner.select_specs(["3.13", "3.12"], False)
    assert [(spec.selector, spec.blocking) for spec in specs] == [
        ("3.13", True),
        ("3.12", False),
    ]
    strict = runner.select_specs(["3.13", "3.12"], True)
    assert all(spec.blocking for spec in strict)


def test_select_specs_splits_dedupes_and_defaults_unknown_blocking() -> None:
    specs = runner.select_specs(["3.13,3.14", "3.13", "3.99"], False)
    assert [(spec.selector, spec.blocking) for spec in specs] == [
        ("3.13", True),
        ("3.14", True),
        ("3.99", True),
    ]


def test_copy_ignore_covers_only_disposable_paths() -> None:
    ignored = runner.COPY_IGNORE(
        str(runner.REPO_ROOT),
        [".git", ".venv", "_Archive", "src", "tests", "data", "scripts"],
    )
    assert {".git", ".venv", "_Archive"} <= ignored
    assert {"src", "tests", "data", "scripts"}.isdisjoint(ignored)


def test_write_summary_emits_json_and_markdown(tmp_path: Path) -> None:
    result = runner.VersionResult(
        selector="3.13",
        blocking=True,
        interpreter="3.13.5",
        status="pass",
        gates=(
            runner.CommandResult(
                name="pytest",
                command=("uv", "run", "--no-sync", "pytest"),
                returncode=0,
                duration_seconds=0.5,
                output="",
            ),
        ),
        report_dir=tmp_path / "3.13",
        copy_dir=None,
        duration_seconds=1.25,
    )
    runner.write_summary(
        [result],
        tmp_path,
        generated_at="2026-11-11T00:00:00+00:00",
        git_state=runner.GitState(commit="abc123", dirty=False, status=""),
        uv_version="uv 0.12.19",
    )
    payload = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert payload["commit"] == "abc123"
    assert payload["results"][0]["selector"] == "3.13"
    markdown = (tmp_path / "summary.md").read_text(encoding="utf-8")
    assert "| 3.13 | 3.13.5 | blocking | pass | - |" in markdown
    assert "| 3.13.5 | pass |" in markdown


def test_run_version_reports_interpreter_resolution_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail_resolve(selector: str) -> Any:
        raise RuntimeError(f"no interpreter for {selector}")

    monkeypatch.setattr(runner, "resolve_interpreter", fail_resolve)
    result = runner.run_version(runner.VersionSpec("3.99", True), tmp_path)

    assert result.status == "error"
    assert result.error == "RuntimeError: no interpreter for 3.99"
    log = (tmp_path / "3.99" / "commands.log").read_text(encoding="utf-8")
    assert "no interpreter for 3.99" in log


def test_run_version_deletes_copy_by_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    copy_root = tmp_path / "copy-root"
    _install_fakes(monkeypatch, copy_root, tmp_path)
    report_dir = tmp_path / "report"

    result = runner.run_version(
        runner.VersionSpec("3.13", True),
        report_dir,
    )

    assert result.status == "pass"
    assert result.copy_dir is None
    assert not copy_root.exists()


def test_run_version_keeps_copy_with_flag(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    copy_root = tmp_path / "copy-root"
    _install_fakes(monkeypatch, copy_root, tmp_path)
    report_dir = tmp_path / "report"

    result = runner.run_version(
        runner.VersionSpec("3.13", True),
        report_dir,
        keep=True,
    )

    assert result.status == "pass"
    assert result.copy_dir == copy_root / "repo"
    assert result.copy_dir.is_dir()


def _install_fakes(
    monkeypatch: pytest.MonkeyPatch,
    copy_root: Path,
    tmp_path: Path,
) -> None:
    def fake_mkdtemp(prefix: str = "") -> str:
        assert prefix
        copy_root.mkdir(parents=True, exist_ok=True)
        return str(copy_root)

    def fake_resolve(selector: str) -> Any:
        return runner.ResolvedInterpreter(
            selector=selector,
            path=Path("/usr/bin/python3.13"),
            version=runner.parse_python_version("3.13.5"),
        )

    def fake_copy(destination: Path) -> None:
        destination.mkdir(parents=True)
        (destination / "pyproject.toml").write_text(_PYPROJECT, encoding="utf-8")
        (destination / ".python-version").write_text("3.14\n", encoding="utf-8")
        (destination / "uv.lock").write_text("", encoding="utf-8")

    def fake_capture(
        command: Sequence[str], cwd: Path
    ) -> subprocess.CompletedProcess[str]:
        assert cwd == copy_root / "repo"
        stdout = "3.13.5\n" if "-c" in command else ""
        return subprocess.CompletedProcess(
            args=list(command), returncode=0, stdout=stdout, stderr=""
        )

    def fake_run_command(
        name: str,
        command: tuple[str, ...],
        cwd: Path,
        log: Any,
    ) -> Any:
        assert cwd == copy_root / "repo"
        log.write(f"$ {' '.join(command)}\n")
        return runner.CommandResult(
            name=name,
            command=command,
            returncode=0,
            duration_seconds=0.0,
            output="",
        )

    monkeypatch.setattr(runner.tempfile, "mkdtemp", fake_mkdtemp)
    monkeypatch.setattr(runner, "resolve_interpreter", fake_resolve)
    monkeypatch.setattr(runner, "copy_repository", fake_copy)
    monkeypatch.setattr(runner, "_capture", fake_capture)
    monkeypatch.setattr(runner, "run_command", fake_run_command)
    monkeypatch.setattr(
        runner,
        "GATES",
        (runner.Gate("pytest", ("uv", "run", "--no-sync", "pytest")),),
    )
    assert tmp_path.exists()
