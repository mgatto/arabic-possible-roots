"""Public API for :mod:`arabic_possible_roots`.

The distribution version is single-sourced from ``pyproject.toml``
(``[project] version``) and read back here via :mod:`importlib.metadata`, so it
is never duplicated in source. The core public surface is re-exported so the
package is usable as a library without reaching into submodules.
"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _package_version

from arabic_possible_roots.alphabet import ORDER
from arabic_possible_roots.attestation import is_attested, load_attested
from arabic_possible_roots.enumerator import count_roots, iter_roots
from arabic_possible_roots.phonotactics import load_matrices, load_matrix, successors
from arabic_possible_roots.possible import (
    attested_illegal,
    count_possible,
    iter_possible,
)
from arabic_possible_roots.render import build_schemes, render_triple
from arabic_possible_roots.writers import format_for_suffix, write_roots

__all__ = [
    "ORDER",
    "__version__",
    "attested_illegal",
    "build_schemes",
    "count_possible",
    "count_roots",
    "format_for_suffix",
    "is_attested",
    "iter_possible",
    "iter_roots",
    "load_attested",
    "load_matrices",
    "load_matrix",
    "render_triple",
    "successors",
    "write_roots",
]

try:
    __version__ = _package_version("arabic-possible-roots")
except PackageNotFoundError:  # pragma: no cover - unbundled source tree only
    __version__ = "0.0.0"
