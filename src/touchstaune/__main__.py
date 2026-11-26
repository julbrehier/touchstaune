"""Allow ``python -m touchstaune``."""

import sys

from touchstaune.cli import main

if __name__ == "__main__":
    sys.exit(main())
