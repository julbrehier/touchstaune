"""Allow ``python -m riftlens``."""

import sys

from riftlens.cli import main

if __name__ == "__main__":
    sys.exit(main())
