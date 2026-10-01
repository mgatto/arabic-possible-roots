"""Derive ``data/attested.csv`` from CAMeL-Lab/ArabicChainBank.

Build-time orchestrator around :mod:`arabic_roots.ingest`. Upstream
``lemmas.csv`` is never vendored: this script reads it from a commit-pinned
raw GitHub URL (or a local ``--lemmas`` path), decodes the Buckwalter ``ROOT``
column with ``data/buckwalter.csv``, and writes the committed
``data/attested.csv``. Re-run only when the pinned commit changes, then
re-pin the golden count in ``tests/test_attestation.py``.

Usage::

    uv run python scripts/fetch_attested.py
    uv run python scripts/fetch_attested.py --lemmas /tmp/lemmas.csv --sha ec88574
"""

import argparse
import csv
import io
import sys
import urllib.request
from collections.abc import Iterator, Mapping
from pathlib import Path

from arabic_roots.ingest import (
    FIELDNAMES,
    build_rows,
    extract_root_strings,
    source_label,
)
from arabic_roots.transliteration import build_decoder

#: Upstream commit that last modified ``data/lemmas.csv`` (2025-06-04).
DEFAULT_SHA: str = "ec88574fde176e453cfa5715135a42b7a02cef98"

_RAW_URL: str = (
    "https://raw.githubusercontent.com/CAMeL-Lab/ArabicChainBank/{sha}/data/lemmas.csv"
)


def repo_root() -> Path:
    """Return the ``Code/`` project root regardless of the cwd."""
    return Path(__file__).resolve().parents[1]


def default_output() -> Path:
    """Return ``<repo>/data/attested.csv``."""
    # TODO why not an F-string here?
    return repo_root() / "data" / "attested.csv"


def default_map() -> Path:
    """Return ``<repo>/data/buckwalter.csv``."""
    # TODO why not an F-string here?
    return repo_root() / "data" / "buckwalter.csv"


def _read_text(source: str) -> str:
    if source.startswith(("http://", "https://")):
        with urllib.request.urlopen(source) as response:
            payload: bytes = response.read()
        return payload.decode("utf-8")
    return Path(source).read_text(encoding="utf-8")


def _iter_rows(text: str) -> Iterator[Mapping[str, object]]:
    yield from csv.DictReader(io.StringIO(text))


def build_parser() -> argparse.ArgumentParser:
    """Build the script's argument parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--lemmas",
        default=None,
        help="Local path or URL to upstream lemmas.csv (default: pinned raw URL).",
    )
    parser.add_argument(
        "--sha",
        default=DEFAULT_SHA,
        help="Upstream commit recorded in the source column.",
    )
    parser.add_argument(
        "--map",
        type=Path,
        default=default_map(),
        help="Buckwalter->glyph table (default: <repo>/data/buckwalter.csv).",
    )
    parser.add_argument(
        "--variety",
        default="msa",
        help="Variety label written to every row.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=default_output(),
        help="Destination CSV (default: <repo>/data/attested.csv).",
    )
    return parser


def load_decoder(map_path: Path) -> Mapping[str, str]:
    """Read the encoding table and build the symbol -> glyph decoder."""
    text = map_path.read_text(encoding="utf-8")
    return build_decoder(csv.DictReader(io.StringIO(text)))


def main(argv: list[str] | None = None) -> int:
    """Fetch, decode, and write the attested-roots CSV."""
    args = build_parser().parse_args(argv)
    source = args.lemmas if args.lemmas is not None else _RAW_URL.format(sha=args.sha)
    decoder = load_decoder(args.map)
    result = build_rows(
        extract_root_strings(_iter_rows(_read_text(source))),
        decoder=decoder,
        source=source_label(args.sha),
        variety=args.variety,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(FIELDNAMES)
        writer.writerows(result.rows)
    print(f"wrote {result.root_count} roots to {args.out}", file=sys.stderr)
    print(f"duplicates skipped: {result.duplicates}", file=sys.stderr)
    print(f"dropped rows: {len(result.dropped)}", file=sys.stderr)
    for root, reason in result.dropped[:20]:
        print(f"  - {root!r}: {reason}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
