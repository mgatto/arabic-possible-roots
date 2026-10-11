"""Command-line entry point: ``enumerate-roots``."""

import argparse
import logging
import sys
from pathlib import Path

from arabic_roots.attestation import ROOTS_SUBDIR, load_attested
from arabic_roots.enumerator import count_roots
from arabic_roots.phonotactics import DATA_DIR, RULES_SUBDIR, load_matrices
from arabic_roots.possible import attested_illegal, count_possible, iter_possible
from arabic_roots.render import (
    SCHEMES,
    build_schemes,
    iter_render_cells,
    render_triple,
    validate_delimiter,
)
from arabic_roots.transliteration import TRANSLITERATIONS_SUBDIR
from arabic_roots.writers import format_for_suffix, write_roots

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Build the ``enumerate-roots`` argument parser.

    Returns:
        A parser exposing ``--data-dir`` (default :data:`DATA_DIR`),
        ``--limit`` (default 10), ``--output`` (default ``None``),
        ``--scheme`` (default ``"arabic"``), ``--delimiter`` (default ``"-"``),
        and ``--log-file`` (default ``None``).
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

    parser.add_argument(
        "--log-file",
        type=Path,
        default=None,
        help="Optional path to append a timestamped UTF-8 run log.",
    )

    return parser


def _configure_logging(log_file: Path | None) -> None:
    """Point the CLI logger at stderr and, optionally, an appended log file.

    Args:
        log_file: Destination log file, or ``None`` for stderr only. Parent
            directories are created; records are appended and timestamped.
    """
    for handler in logger.handlers:
        handler.close()
    logger.handlers.clear()
    logger.setLevel(logging.INFO)
    logger.propagate = True

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%S"
    )
    stream = logging.StreamHandler(sys.stderr)
    stream.setFormatter(formatter)
    logger.addHandler(stream)

    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


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
        scheme (no delimiter). Logs the effective options, embedded choices,
        and output summary to stderr and, when ``--log-file`` is set, appends
        the same timestamped records to that file. The stdout write is the one
        permitted output in ``src/`` (AGENTS §5).
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    _configure_logging(args.log_file)

    try:
        output_format = (
            format_for_suffix(args.output) if args.output is not None else "none"
        )
    except ValueError as exc:
        parser.error(str(exc))

    m_1_2, m_2_3 = load_matrices(args.data_dir)
    attested = load_attested(args.data_dir)
    schemes = build_schemes(args.data_dir)
    try:
        delimiter = validate_delimiter(args.delimiter, args.scheme, schemes)
    except ValueError as exc:
        parser.error(str(exc))

    logger.info(
        "run: data_dir=%s limit=%d output=%s format=%s scheme=%s delimiter=%r "
        "variety=msa",
        args.data_dir,
        args.limit,
        args.output if args.output is not None else "none",
        output_format,
        args.scheme,
        delimiter,
    )
    logger.info(
        "inputs: rules=%s roots=%s transliterations=%s",
        args.data_dir / RULES_SUBDIR,
        args.data_dir / ROOTS_SUBDIR,
        args.data_dir / TRANSLITERATIONS_SUBDIR,
    )

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

        logger.info(
            "wrote %d possible roots to %s (%s)",
            written,
            args.output,
            output_format,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
