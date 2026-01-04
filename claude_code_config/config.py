"""Configuration file management."""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .conversations import ConversationFile, ConversationScanner
from .models import ClaudeConfig


class ConfigManager:
    """Manages Claude configuration file operations."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the config manager.

        Args:
            config_path: Path to the config file. Defaults to ~/.claude.json
        """
        if config_path is None:
            config_path = Path.home() / ".claude.json"

        self.config_path = Path(config_path)
        self.backup_dir = self.config_path.parent / ".claude_backups"
        self._config: Optional[ClaudeConfig] = None
        self._modified = False
        
        # Initialize conversation scanner
        claude_dir = Path.home() / ".claude"
        self.conversation_scanner = ConversationScanner(claude_dir)

    def load(self) -> ClaudeConfig:
        """Load the configuration from file.

        Returns:
            ClaudeConfig object

        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._config = ClaudeConfig.from_dict(data)
        self._modified = False
        return self._config

    def save(self, config: Optional[ClaudeConfig] = None) -> None:
        """Save the configuration to file.

        Args:
            config: Config to save. If None, uses the loaded config.

        Raises:
            ValueError: If no config is provided and none is loaded
        """
        if config is None:
            if self._config is None:
                raise ValueError("No configuration to save")
            config = self._config

        # Create backup before saving
        self.create_backup()

        # Convert to dict and save
        data = config.to_dict()

        # Write with pretty formatting
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self._modified = False

    def create_backup(self) -> Path:
        """Create a timestamped backup of the current config file.

        Returns:
            Path to the backup file
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        # Create backup directory if it doesn't exist
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Generate timestamp-based backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"claude.json.backup.{timestamp}"

        # Copy file to backup
        shutil.copy2(self.config_path, backup_path)

        # Clean old backups (keep last 10)
        self._cleanup_old_backups(keep=10)

        return backup_path

    def _cleanup_old_backups(self, keep: int = 10) -> None:
        """Remove old backup files, keeping only the most recent ones.

        Args:
            keep: Number of backups to keep
        """
        if not self.backup_dir.exists():
            return

        backups = sorted(
            self.backup_dir.glob("claude.json.backup.*"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        # Remove old backups
        for backup in backups[keep:]:
            backup.unlink()

    def list_backups(self) -> list[Path]:
        """List all available backup files.

        Returns:
            List of backup file paths, sorted by modification time (newest first)
        """
        if not self.backup_dir.exists():
            return []

        return sorted(
            self.backup_dir.glob("claude.json.backup.*"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

    def restore_backup(self, backup_path: Path) -> None:
        """Restore configuration from a backup file.

        Args:
            backup_path: Path to the backup file

        Raises:
            FileNotFoundError: If backup file doesn't exist
        """
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        # Create a backup of current state before restoring
        self.create_backup()

        # Copy backup to config location
        shutil.copy2(backup_path, self.config_path)

        # Reload config
        self.load()

    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate the current configuration.

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if self._config is None:
                self.load()

            # Try to convert to dict and back to ensure serialization works
            data = self._config.to_dict()
            json.dumps(data)

            return True, None
        except Exception as e:
            return False, str(e)

    @property
    def config(self) -> Optional[ClaudeConfig]:
        """Get the current configuration."""
        return self._config

    @property
    def modified(self) -> bool:
        """Check if configuration has been modified."""
        return self._modified

    def mark_modified(self) -> None:
        """Mark configuration as modified."""
        self._modified = True
    
    def get_conversations(self, project_path: str) -> List[ConversationFile]:
        """Get conversations for a specific project.
        
        Args:
            project_path: Full path to the project
            
        Returns:
            List of ConversationFile objects
        """
        return self.conversation_scanner.get_project_conversations(project_path)
    
    def get_all_conversations(self) -> Dict[str, List[ConversationFile]]:
        """Get all conversations grouped by project.
        
        Returns:
            Dict mapping project path to list of ConversationFile objects
        """
        return self.conversation_scanner.scan_all_conversations()
    
    def get_conversation_stats(self) -> Dict[str, int]:
        """Get conversation statistics.
        
        Returns:
            Dict with total_conversations, total_projects, total_size
        """
        return self.conversation_scanner.get_stats()
