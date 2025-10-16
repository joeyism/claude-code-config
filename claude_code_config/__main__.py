"""Allow running the package as a module: python -m claude_code_config"""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
