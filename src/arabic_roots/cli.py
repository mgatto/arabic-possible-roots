"""Command-line entry point: ``enumerate-roots``."""

import argparse
import logging
import sys
from pathlib import Path

from arabic_roots.enumerator import count_roots, iter_roots
from arabic_roots.phonotactics import DATA_DIR, load_matrices
from arabic_roots.writers import write_roots

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Build the ``enumerate-roots`` argument parser.

    Returns:
        A parser exposing ``--data-dir`` (default :data:`DATA_DIR`),
        ``--limit`` (default 10), and ``--output`` (default ``None``).
    """

    parser = argparse.ArgumentParser(
        description="Enumerate triliteral Arabic roots filtered by M_1-2/M_2-3.",
    )

    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DATA_DIR,
        help="Data root holding rules/ with m_1-2.csv and m_2-3.csv.",
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
        help=(
            "Optional path for the full enumeration; the format is inferred "
            "from the suffix (.tsv, .csv)."
        ),
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the enumeration and write the requested output.

    Args:
        argv: Argument list; defaults to ``sys.argv[1:]`` when ``None``.

    Returns:
        Process exit code: ``0`` on success, ``2`` when ``--output`` has an
        unsupported suffix.

    Notes:
        Writes up to ``--limit`` hyphen-joined roots to stdout and, when
        ``--output`` is set, the full enumeration in the suffix-selected
        format (``.tsv``/``.csv``, header ``c1,c2,c3``). The stdout write is
        the one permitted output in ``src/`` (AGENTS §5).
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = build_parser()
    args = parser.parse_args(argv)
    m_1_2, m_2_3 = load_matrices(args.data_dir)
    total = count_roots(m_1_2, m_2_3)
    logger.info("Allowed triliteral roots: %d", total)

    for index, triple in enumerate(iter_roots(m_1_2, m_2_3)):
        if index >= args.limit:
            break
        sys.stdout.write("-".join(triple) + "\n")

    if args.output is not None:
        try:
            written = write_roots(args.output, iter_roots(m_1_2, m_2_3))
        except ValueError as exc:
            parser.error(str(exc))

        logger.info("Wrote %d roots to %s", written, args.output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
