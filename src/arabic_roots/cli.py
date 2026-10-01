"""Command-line entry point: ``enumerate-roots``."""

import argparse
import logging
import sys
import unicodedata
from pathlib import Path

from arabic_roots.enumerator import count_roots, iter_roots
from arabic_roots.phonotactics import default_data_dir, load_matrices

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""

    parser = argparse.ArgumentParser(
        description="Enumerate triliteral Arabic roots filtered by M_1-2/M_2-3.",
    )

    parser.add_argument(
        "--data-dir",
        type=Path,
        default=default_data_dir(),
        help="Directory holding m_1-2.csv and m_2-3.csv.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="How many sample roots to print (0 prints none).",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional UTF-8 TSV path for the full enumeration.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the enumeration; return a process exit code."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = build_parser().parse_args(argv)
    m_1_2, m_2_3 = load_matrices(args.data_dir)
    total = count_roots(m_1_2, m_2_3)
    logger.info("Allowed triliteral roots: %d", total)
    for index, triple in enumerate(iter_roots(m_1_2, m_2_3)):
        if index >= args.limit:
            break
        # TODO should prefix with linguistics convention of "*" to show it's unattested
        sys.stdout.write("*" + "-".join(triple) + "\n")
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8", newline="\n") as handle:
            for first, second, third in iter_roots(m_1_2, m_2_3):
                row = "\t".join((first, second, third))
                handle.write(unicodedata.normalize("NFC", row) + "\n")
        logger.info("Wrote full enumeration to %s", args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
