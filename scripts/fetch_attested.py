"""Derive ``data/attested.csv`` from CAMeL-Lab/ArabicChainBank.

Build-time orchestrator around
:mod:`arabic_roots.arabic_chain_bank_provider`. Upstream ``lemmas.csv`` is
never vendored: this script reads it from a commit-pinned raw GitHub URL (or
a local ``--lemmas`` path), decodes the Buckwalter ``ROOT`` column with
``data/buckwalter.csv``, and writes the committed ``data/attested.csv``.
Re-run only when the pinned commit changes, then re-pin the golden count in
``tests/test_attestation.py``.

Usage::

    uv run python scripts/fetch_attested.py
    uv run python scripts/fetch_attested.py --lemmas /tmp/lemmas.csv --sha ec88574
"""

import argparse
import csv
import io
import sys
import urllib.request
from collections.abc import Mapping
from pathlib import Path

from arabic_roots.arabic_chain_bank_provider import (
    DEFAULT_SHA,
    FIELDNAMES,
    RAW_LEMMAS_URL,
    build_rows,
)
from arabic_roots.transliteration import build_decoder

REPO_ROOT: Path = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT: Path = REPO_ROOT / "data" / "attested.csv"
DEFAULT_MAP: Path = REPO_ROOT / "data" / "buckwalter.csv"


def _read_text(source: str) -> str:
    if source.startswith(("http://", "https://")):
        with urllib.request.urlopen(source) as response:
            payload: bytes = response.read()
        return payload.decode("utf-8")
    return Path(source).read_text(encoding="utf-8")


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
        default=DEFAULT_MAP,
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
        default=DEFAULT_OUTPUT,
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
    if args.lemmas is not None:
        source = args.lemmas
    else:
        source = RAW_LEMMAS_URL.format(sha=args.sha)
    decoder = load_decoder(args.map)
    result = build_rows(
        csv.DictReader(io.StringIO(_read_text(source))),
        decoder=decoder,
        sha=args.sha,
        variety=args.variety,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(FIELDNAMES)
        writer.writerows(result.rows)
    print(f"wrote {len(result.rows)} roots to {args.out}", file=sys.stderr)
    print(f"duplicates skipped: {result.duplicates}", file=sys.stderr)
    print(f"dropped rows: {len(result.dropped)}", file=sys.stderr)
    for root, reason in result.dropped[:20]:
        print(f"  - {root!r}: {reason}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
