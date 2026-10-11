"""Command-line entry point: ``enumerate-roots``."""

import argparse
import logging
import sys
from pathlib import Path

from arabic_roots.attestation import load_attested
from arabic_roots.enumerator import count_roots
from arabic_roots.phonotactics import DATA_DIR, load_matrices
from arabic_roots.possible import attested_illegal, count_possible, iter_possible
from arabic_roots.render import (
    SCHEMES,
    build_schemes,
    iter_render_cells,
    render_triple,
    validate_delimiter,
)
from arabic_roots.writers import write_roots

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Build the ``enumerate-roots`` argument parser.

    Returns:
        A parser exposing ``--data-dir`` (default :data:`DATA_DIR`),
        ``--limit`` (default 10), ``--output`` (default ``None``),
        ``--scheme`` (default ``"arabic"``), and ``--delimiter``
        (default ``"-"``).
    """

    parser = argparse.ArgumentParser(
        description=(
            "Enumerate possible triliteral Arabic roots: phonotactically "
            "legal (M_1-2/M_2-3) but unattested."
        ),
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
            "Optional path for the full possible-roots set; the format is "
            "inferred from the suffix (.tsv, .csv, .jsonl, .parquet, .sqlite)."
        ),
    )

    parser.add_argument(
        "--scheme",
        choices=SCHEMES,
        default="arabic",
        help="Output transliteration scheme (default: arabic).",
    )

    parser.add_argument(
        "--delimiter",
        default="-",
        help="Separator between rendered consonants on stdout (default: '-').",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the enumeration and write the requested output.

    Args:
        argv: Argument list; defaults to ``sys.argv[1:]`` when ``None``.

    Returns:
        Process exit code: ``0`` on success, ``2`` when ``--output`` has an
        unsupported suffix or ``--delimiter`` clashes with ``--scheme``.

    Notes:
        Emits **possible** roots (legal but unattested), rendered in
        ``--scheme`` and joined by ``--delimiter`` on stdout; when ``--output``
        is set, the full set is written in the suffix-selected format
        (``.tsv``/``.csv``, header ``c1,c2,c3``) with each cell rendered in the
        scheme (no delimiter). Logs both the rule-only and possible counts, and
        warns when the lexicon attests a root the matrices forbid. The stdout
        write is the one permitted output in ``src/`` (AGENTS §5).
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = build_parser()
    args = parser.parse_args(argv)
    m_1_2, m_2_3 = load_matrices(args.data_dir)
    attested = load_attested(args.data_dir)
    schemes = build_schemes(args.data_dir)
    try:
        delimiter = validate_delimiter(args.delimiter, args.scheme, schemes)
    except ValueError as exc:
        parser.error(str(exc))

    logger.info("Allowed triliteral roots: %d", count_roots(m_1_2, m_2_3))
    logger.info(
        "Possible triliteral roots: %d",
        count_possible(m_1_2, m_2_3, attested),
    )

    illegal = attested_illegal(m_1_2, m_2_3, attested)
    if illegal:
        logger.warning(
            "%d attested roots are phonotactically illegal: %s",
            len(illegal),
            ", ".join("-".join(triple) for triple in illegal),
        )

    for index, triple in enumerate(iter_possible(m_1_2, m_2_3, attested)):
        if index >= args.limit:
            break
        sys.stdout.write(render_triple(triple, args.scheme, delimiter, schemes) + "\n")

    if args.output is not None:
        rendered = iter_render_cells(
            iter_possible(m_1_2, m_2_3, attested), args.scheme, schemes
        )
        try:
            written = write_roots(args.output, rendered)
        except ValueError as exc:
            parser.error(str(exc))

        logger.info("Wrote %d roots to %s", written, args.output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
