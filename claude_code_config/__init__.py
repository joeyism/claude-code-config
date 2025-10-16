"""Claude Config Manager - A TUI for managing Claude Code configuration."""

__version__ = "0.1.0"
__author__ = "Joey"
__license__ = "MIT"

from .config import ClaudeConfig, ConfigManager

__all__ = ["ClaudeConfig", "ConfigManager", "__version__"]
