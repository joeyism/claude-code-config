"""Claude Config Manager - A TUI for managing Claude Code configuration."""

__version__ = "1.0.1"
__author__ = "joeyism"
__license__ = "MIT"

from .config import ClaudeConfig, ConfigManager

__all__ = ["ClaudeConfig", "ConfigManager", "__version__"]
