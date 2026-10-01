"""Guard: raw NFC normalization is centralized in ``alphabet.nfc``."""

from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src" / "arabic_roots"


def _python_files() -> list[Path]:
    return sorted(_SRC.glob("*.py"))


def test_raw_normalize_only_in_alphabet() -> None:
    """Only ``alphabet.py`` may call ``unicodedata.normalize``, exactly once."""
    offenders = {
        path.name: path.read_text(encoding="utf-8").count("unicodedata.normalize(")
        for path in _python_files()
        if "unicodedata.normalize(" in path.read_text(encoding="utf-8")
    }
    assert offenders == {"alphabet.py": 1}


def test_unicodedata_import_only_in_alphabet() -> None:
    """Only ``alphabet.py`` imports the ``unicodedata`` module."""
    importers = {
        path.name
        for path in _python_files()
        if "import unicodedata" in path.read_text(encoding="utf-8")
    }
    assert importers == {"alphabet.py"}
