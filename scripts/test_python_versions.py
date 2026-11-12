"""Run the project's quality gates across Python versions in disposable copies.

The repository pins Python 3.14 and owns a 3.14-specific lockfile, so testing
another interpreter in-place would mutate or bypass the project configuration.
This runner therefore copies the working tree to a temporary directory for each
selected version, patches the copy's metadata and tool targets, synchronizes a
fresh environment there, and runs the same gates as AGENTS.md §5.

Usage::

    uv run python scripts/test_python_versions.py
    uv run python scripts/test_python_versions.py 3.13 3.14
    uv run python scripts/test_python_versions.py --strict --allow-dirty

The default matrix is 3.12 (experimental), 3.13 (blocking), 3.14 (blocking),
and 3.15 (experimental). Copies are deleted after each run unless ``--keep`` is
given. Reports are written under ``.python-matrix/<timestamp>/`` and never edit
``docs/python-versions.md``.
"""

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TextIO

REPO_ROOT: Path = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_ROOT: Path = REPO_ROOT / ".python-matrix"

COPY_IGNORE: Callable[[str, list[str]], set[str]] = shutil.ignore_patterns(
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".ty",
    ".coverage",
    "coverage.xml",
    "htmlcov",
    ".idea",
    ".python-matrix",
    "_Archive",
    "dist",
    "build",
    "*.egg-info",
    ".DS_Store",
    "*.log",
)

_VERSION_RE = re.compile(
    r"^(?P<major>\d+)\.(?P<minor>\d+)(?:\.(?P<patch>\d+))?"
    r"(?P<pre>(?:a|b|rc)\d+)?$"
)


@dataclass(frozen=True)
class PythonVersion:
    """Parsed Python version or version selector."""

    major: int
    minor: int
    patch: int | None = None
    pre: str | None = None

    @property
    def minor_label(self) -> str:
        """Return ``major.minor`` for mypy and ty."""
        return f"{self.major}.{self.minor}"

    @property
    def ruff_target(self) -> str:
        """Return the ruff target-version value."""
        return f"py{self.major}{self.minor}"

    @property
    def text(self) -> str:
        """Return the full version string, including a pre-release suffix."""
        base = self.minor_label
        if self.patch is not None:
            base = f"{base}.{self.patch}"
        return base + (self.pre or "")


@dataclass(frozen=True)
class VersionSpec:
    """One row of the version matrix."""

    selector: str
    blocking: bool


@dataclass(frozen=True)
class ResolvedInterpreter:
    """An interpreter selected by uv for one matrix row."""

    selector: str
    path: Path
    version: PythonVersion


@dataclass(frozen=True)
class CommandResult:
    """The outcome of one command."""

    name: str
    command: tuple[str, ...]
    returncode: int
    duration_seconds: float
    output: str


@dataclass(frozen=True)
class Gate:
    """A named quality-gate command."""

    name: str
    command: tuple[str, ...]


@dataclass(frozen=True)
class GitState:
    """Repository identity for certification evidence."""

    commit: str
    dirty: bool
    status: str


@dataclass(frozen=True)
class VersionResult:
    """The outcome of one matrix row."""

    selector: str
    blocking: bool
    interpreter: str
    status: str
    gates: tuple[CommandResult, ...]
    report_dir: Path
    copy_dir: Path | None
    duration_seconds: float
    error: str | None = None


DEFAULT_MATRIX: tuple[VersionSpec, ...] = (
    VersionSpec("3.12", False),
    VersionSpec("3.13", True),
    VersionSpec("3.14", True),
    VersionSpec("3.15", False),
)

GATES: tuple[Gate, ...] = (
    Gate("pytest", ("uv", "run", "--no-sync", "pytest")),
    Gate("ruff-check", ("uv", "run", "--no-sync", "ruff", "check", "src", "tests")),
    Gate(
        "ruff-format",
        ("uv", "run", "--no-sync", "ruff", "format", "--check", "src", "tests"),
    ),
    Gate("mypy", ("uv", "run", "--no-sync", "mypy", "src", "tests")),
    Gate("ty", ("uv", "run", "--no-sync", "ty", "check")),
    Gate(
        "enumerate-roots",
        ("uv", "run", "--no-sync", "enumerate-roots", "--limit", "5"),
    ),
)


def parse_python_version(value: str) -> PythonVersion:
    """Parse a selector such as ``3.13``, ``3.13.5``, or ``3.15.0rc2``."""
    match = _VERSION_RE.fullmatch(value.strip())
    if match is None:
        raise ValueError(f"unsupported Python version selector: {value!r}")
    patch = match.group("patch")
    return PythonVersion(
        major=int(match.group("major")),
        minor=int(match.group("minor")),
        patch=int(patch) if patch is not None else None,
        pre=match.group("pre"),
    )


def requires_python(version: PythonVersion) -> str:
    """Return the copy's requires-python constraint for a target version."""
    if version.pre is not None:
        return f">={version.text}"
    return f">={version.minor_label}"


def _replace_once(text: str, pattern: str, replacement: str, label: str) -> str:
    new_text, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise ValueError(
            f"expected exactly one {label} setting in pyproject.toml, found {count}"
        )
    return new_text


def patch_pyproject_text(text: str, version: PythonVersion) -> str:
    """Patch the copy's interpreter and tool targets in pyproject text."""
    text = _replace_once(
        text,
        r'^requires-python\s*=\s*"[^"]*"\s*$',
        f'requires-python = "{requires_python(version)}"',
        "requires-python",
    )
    text = _replace_once(
        text,
        r'^target-version\s*=\s*"[^"]*"\s*$',
        f'target-version = "{version.ruff_target}"',
        "ruff target-version",
    )
    text = _replace_once(
        text,
        r'^python_version\s*=\s*"[^"]*"\s*$',
        f'python_version = "{version.minor_label}"',
        "mypy python_version",
    )
    return _replace_once(
        text,
        r'^python-version\s*=\s*"[^"]*"\s*$',
        f'python-version = "{version.minor_label}"',
        "ty python-version",
    )


def select_specs(versions: Sequence[str], strict: bool) -> tuple[VersionSpec, ...]:
    """Resolve positional selectors against the default matrix roles."""
    if not versions:
        chosen = DEFAULT_MATRIX
    else:
        roles = {spec.selector: spec.blocking for spec in DEFAULT_MATRIX}
        selectors: list[str] = []
        for raw in versions:
            selectors.extend(part.strip() for part in raw.split(",") if part.strip())
        deduped = list(dict.fromkeys(selectors))
        chosen = tuple(
            VersionSpec(selector, roles.get(selector, True)) for selector in deduped
        )
    if strict:
        return tuple(VersionSpec(spec.selector, True) for spec in chosen)
    return chosen


def _capture(command: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def resolve_interpreter(selector: str) -> ResolvedInterpreter:
    """Install and locate the interpreter for a selector, recording its version."""
    install = _capture(("uv", "python", "install", selector), cwd=REPO_ROOT)
    if install.returncode != 0:
        raise RuntimeError(
            f"uv python install {selector} failed:\n{install.stderr.strip()}"
        )
    find = _capture(("uv", "python", "find", selector), cwd=REPO_ROOT)
    if find.returncode != 0:
        raise RuntimeError(f"uv python find {selector} failed:\n{find.stderr.strip()}")
    path = Path(find.stdout.strip().splitlines()[-1])
    version = _capture(
        (str(path), "-c", "import platform; print(platform.python_version())"),
        cwd=REPO_ROOT,
    )
    if version.returncode != 0:
        raise RuntimeError(
            f"could not read the version of {path}:\n{version.stderr.strip()}"
        )
    return ResolvedInterpreter(
        selector=selector,
        path=path,
        version=parse_python_version(version.stdout.strip()),
    )


def copy_repository(destination: Path) -> None:
    """Copy the working tree into a disposable directory."""
    shutil.copytree(REPO_ROOT, destination, ignore=COPY_IGNORE)


def patch_copy(pyproject: Path, version: PythonVersion) -> None:
    """Rewrite interpreter and tool targets in a copied pyproject.toml."""
    text = pyproject.read_text(encoding="utf-8")
    pyproject.write_text(
        patch_pyproject_text(text, version),
        encoding="utf-8",
    )


def _venv_python(copy_dir: Path) -> Path:
    if os.name == "nt":
        return copy_dir / ".venv" / "Scripts" / "python.exe"
    return copy_dir / ".venv" / "bin" / "python"


def _write_command_log(log: TextIO, result: CommandResult) -> None:
    log.write(f"$ {shlex.join(result.command)}\n")
    log.write(f"exit: {result.returncode}\n")
    if result.output:
        log.write(result.output)
        if not result.output.endswith("\n"):
            log.write("\n")
    log.write("\n")


def run_command(
    name: str,
    command: tuple[str, ...],
    cwd: Path,
    log: TextIO,
) -> CommandResult:
    """Run one command, capture its combined output, and log it."""
    started = time.monotonic()
    try:
        completed = _capture(command, cwd=cwd)
        returncode = completed.returncode
        output = completed.stdout
    except OSError as exc:
        returncode = 127
        output = f"{type(exc).__name__}: {exc}"
    result = CommandResult(
        name=name,
        command=command,
        returncode=returncode,
        duration_seconds=time.monotonic() - started,
        output=output,
    )
    _write_command_log(log, result)
    status = "ok" if returncode == 0 else f"FAILED ({returncode})"
    print(f"  {name}: {status}")
    return result


def _record_environment(
    log: TextIO,
    copy_dir: Path,
    interpreter: ResolvedInterpreter,
) -> None:
    log.write(f"selector: {interpreter.selector}\n")
    log.write(f"interpreter: {interpreter.path}\n")
    log.write(f"version: {interpreter.version.text}\n")
    for command in (
        (str(interpreter.path), "-VV"),
        (
            "uv",
            "pip",
            "freeze",
            "--python",
            str(_venv_python(copy_dir)),
        ),
    ):
        completed = _capture(command, cwd=copy_dir)
        log.write(f"$ {shlex.join(command)}\n")
        log.write(completed.stdout)
        if completed.stderr:
            log.write(completed.stderr)
        if not completed.stdout.endswith("\n"):
            log.write("\n")
    log.write("\n")


def _status(gates: tuple[CommandResult, ...], error: str | None) -> str:
    if error is not None:
        return "error"
    if any(gate.returncode != 0 for gate in gates):
        return "fail"
    return "pass"


def run_version(
    spec: VersionSpec,
    report_dir: Path,
    *,
    keep: bool = False,
    dry_run: bool = False,
) -> VersionResult:
    """Run the full gate set for one matrix row in a disposable copy."""
    started = time.monotonic()
    version_dir = report_dir / spec.selector
    version_dir.mkdir(parents=True, exist_ok=True)
    if dry_run:
        version = parse_python_version(spec.selector)
        commands = [
            f"uv sync --python {spec.selector}",
            *(shlex.join(gate.command) for gate in GATES),
        ]
        print(f"[{spec.selector}] dry run")
        for command in commands:
            print(f"  {command}")
        return VersionResult(
            selector=spec.selector,
            blocking=spec.blocking,
            interpreter=version.text,
            status="dry-run",
            gates=(),
            report_dir=version_dir,
            copy_dir=None,
            duration_seconds=time.monotonic() - started,
        )

    error: str | None = None
    try:
        interpreter = resolve_interpreter(spec.selector)
    except (OSError, RuntimeError, ValueError) as exc:
        error = f"{type(exc).__name__}: {exc}"
        (version_dir / "commands.log").write_text(
            f"error: {error}\n",
            encoding="utf-8",
        )
        print(f"[{spec.selector}] error: {error}", file=sys.stderr)
        return VersionResult(
            selector=spec.selector,
            blocking=spec.blocking,
            interpreter=spec.selector,
            status="error",
            gates=(),
            report_dir=version_dir,
            copy_dir=None,
            duration_seconds=time.monotonic() - started,
            error=error,
        )
    copy_root = Path(tempfile.mkdtemp(prefix=f"apr-{spec.selector}-"))
    copy_dir = copy_root / "repo"
    gates: list[CommandResult] = []
    kept_copy: Path | None = None
    try:
        copy_repository(copy_dir)
        patch_copy(copy_dir / "pyproject.toml", interpreter.version)
        (copy_dir / ".python-version").unlink(missing_ok=True)
        (copy_dir / "uv.lock").unlink(missing_ok=True)
        log_path = version_dir / "commands.log"
        with log_path.open("w", encoding="utf-8") as log:
            log.write(f"# {spec.selector} ({interpreter.version.text})\n\n")
            print(f"[{spec.selector}] syncing {interpreter.version.text}")
            sync = run_command(
                "uv sync",
                ("uv", "sync", "--python", str(interpreter.path)),
                cwd=copy_dir,
                log=log,
            )
            gates.append(sync)
            if sync.returncode == 0:
                _record_environment(log, copy_dir, interpreter)
                print(f"[{spec.selector}] running gates")
                for gate in GATES:
                    gates.append(
                        run_command(
                            gate.name,
                            gate.command,
                            cwd=copy_dir,
                            log=log,
                        )
                    )
    except (OSError, RuntimeError, ValueError) as exc:
        error = f"{type(exc).__name__}: {exc}"
    finally:
        if keep:
            kept_copy = copy_dir
            print(f"[{spec.selector}] kept copy: {copy_dir}")
        else:
            shutil.rmtree(copy_root, ignore_errors=True)

    gate_tuple = tuple(gates)
    status = _status(gate_tuple, error)
    print(f"[{spec.selector}] {status}")
    return VersionResult(
        selector=spec.selector,
        blocking=spec.blocking,
        interpreter=interpreter.version.text,
        status=status,
        gates=gate_tuple,
        report_dir=version_dir,
        copy_dir=kept_copy,
        duration_seconds=time.monotonic() - started,
        error=error,
    )


def read_git_state() -> GitState:
    """Read the commit and dirty status for evidence."""
    try:
        commit = _capture(("git", "rev-parse", "HEAD"), cwd=REPO_ROOT)
        status = _capture(("git", "status", "--porcelain"), cwd=REPO_ROOT)
    except OSError as exc:
        return GitState(commit="unknown", dirty=True, status=str(exc))
    return GitState(
        commit=commit.stdout.strip() or "unknown",
        dirty=bool(status.stdout.strip()),
        status=status.stdout.strip(),
    )


def _report_payload(
    results: Sequence[VersionResult],
    report_dir: Path,
    *,
    generated_at: str,
    git_state: GitState,
    uv_version: str,
) -> dict[str, object]:
    return {
        "generated_at": generated_at,
        "report_dir": str(report_dir),
        "commit": git_state.commit,
        "dirty": git_state.dirty,
        "git_status": git_state.status,
        "uv_version": uv_version,
        "results": [
            {
                "selector": result.selector,
                "interpreter": result.interpreter,
                "blocking": result.blocking,
                "status": result.status,
                "duration_seconds": round(result.duration_seconds, 3),
                "error": result.error,
                "copy_dir": str(result.copy_dir) if result.copy_dir else None,
                "gates": [
                    {
                        "name": gate.name,
                        "command": list(gate.command),
                        "returncode": gate.returncode,
                        "duration_seconds": round(gate.duration_seconds, 3),
                    }
                    for gate in result.gates
                ],
            }
            for result in results
        ],
    }


def write_summary(
    results: Sequence[VersionResult],
    report_dir: Path,
    *,
    generated_at: str,
    git_state: GitState,
    uv_version: str,
) -> None:
    """Write JSON and Markdown evidence for a matrix run."""
    report_dir.mkdir(parents=True, exist_ok=True)
    payload = _report_payload(
        results,
        report_dir,
        generated_at=generated_at,
        git_state=git_state,
        uv_version=uv_version,
    )
    (report_dir / "summary.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Python version matrix",
        "",
        f"- Generated: {generated_at}",
        f"- Commit: `{git_state.commit}`",
        f"- Dirty working tree: {git_state.dirty}",
        f"- uv: `{uv_version}`",
        "",
        "| Selector | Interpreter | Role | Status | Failed gates |",
        "|---|---|---|---|---|",
    ]
    for result in results:
        failed = [gate.name for gate in result.gates if gate.returncode != 0]
        role = "blocking" if result.blocking else "experimental"
        lines.append(
            "| "
            f"{result.selector} | {result.interpreter} | {role} | "
            f"{result.status} | {', '.join(failed) or '-'} |"
        )
    lines.extend(
        [
            "",
            "## Certification rows",
            "",
            "| Interpreter | Status | Evidence |",
            "|---|---|---|",
        ]
    )
    for result in results:
        evidence = result.report_dir / "commands.log"
        lines.append(f"| {result.interpreter} | {result.status} | `{evidence}` |")
    (report_dir / "summary.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def _timestamped_report_dir() -> Path:
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    candidate = DEFAULT_REPORT_ROOT / stamp
    suffix = 1
    while candidate.exists():
        suffix += 1
        candidate = DEFAULT_REPORT_ROOT / f"{stamp}-{suffix}"
    return candidate


def build_parser() -> argparse.ArgumentParser:
    """Build the script's argument parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Run the quality gates across Python versions in disposable copies."
        ),
        epilog=(
            "Reports go to .python-matrix/<timestamp>/; copies are deleted "
            "unless --keep is given."
        ),
    )
    parser.add_argument(
        "versions",
        nargs="*",
        help="Selectors to test (default: 3.12 3.13 3.14 3.15).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat every selected version as blocking.",
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=None,
        help="Exact report directory (default: .python-matrix/<timestamp>).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the copy, patch, and command plan without executing.",
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep disposable copies and print their paths.",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Run from a dirty working tree; evidence is marked dirty.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the selected Python-version matrix."""
    args = build_parser().parse_args(argv)
    if shutil.which("uv") is None:
        print("error: uv is not on PATH", file=sys.stderr)
        return 2
    specs = select_specs(args.versions, args.strict)
    git_state = read_git_state()
    if not args.dry_run and git_state.dirty and not args.allow_dirty:
        print(
            "error: working tree is dirty; commit first or pass --allow-dirty",
            file=sys.stderr,
        )
        return 2
    report_dir = args.report_dir or _timestamped_report_dir()
    uv_version = _capture(("uv", "--version"), cwd=REPO_ROOT).stdout.strip()
    results = [
        run_version(
            spec,
            report_dir,
            keep=args.keep,
            dry_run=args.dry_run,
        )
        for spec in specs
    ]
    generated_at = datetime.now(tz=UTC).isoformat()
    if not args.dry_run:
        write_summary(
            results,
            report_dir,
            generated_at=generated_at,
            git_state=git_state,
            uv_version=uv_version,
        )
        print(f"report: {report_dir}")
    blocking_failures = [
        result for result in results if result.blocking and result.status != "pass"
    ]
    if args.dry_run:
        return 0
    return 1 if blocking_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
