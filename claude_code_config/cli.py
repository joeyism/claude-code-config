"""Command-line interface for Claude Config Manager."""

import argparse
import sys
from pathlib import Path

from . import __version__
from .tui import ClaudeConfigApp


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="claude-config",
        description="A TUI application for managing Claude Code configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  claude-config                    # Launch TUI with default config
  claude-config -c ~/custom.json   # Launch TUI with custom config file
  claude-config --version          # Show version information

For more information, visit: https://github.com/joeyism/claude-config-manager
        """,
    )

    parser.add_argument(
        "-c",
        "--config",
        type=str,
        metavar="PATH",
        help="Path to Claude config file (default: ~/.claude.json)",
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    args = parser.parse_args()

    # Validate config path if provided
    config_path = None
    if args.config:
        config_path = Path(args.config).expanduser()
        if not config_path.exists():
            print(f"Error: Config file not found: {config_path}", file=sys.stderr)
            return 1

    # Launch the TUI
    try:
        app = ClaudeConfigApp(config_path=config_path)
        app.run()
        return 0
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
