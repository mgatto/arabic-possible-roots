"""Module entry point: ``python -m arabic_roots`` delegates to ``cli.main``."""

from arabic_roots.cli import main

if __name__ == "__main__":
    # TODO why is this here?
    raise SystemExit(main())
