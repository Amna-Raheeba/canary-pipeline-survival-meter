"""Entry point: python -m canary_meter [demo|evaluate]."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
