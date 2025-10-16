"""Tests for configuration management."""

import json
import tempfile
from pathlib import Path

import pytest

from claude_code_config.config import ConfigManager
from claude_code_config.models import ClaudeConfig, McpServer


class TestConfigManager:
    """Tests for ConfigManager."""

    def test_init_default_path(self):
        """Test initialization with default path."""
        manager = ConfigManager()

        assert manager.config_path == Path.home() / ".claude.json"
        assert manager.backup_dir == Path.home() / ".claude_backups"

    def test_init_custom_path(self):
        """Test initialization with custom path."""
        custom_path = Path("/tmp/custom.json")
        manager = ConfigManager(custom_path)

        assert manager.config_path == custom_path
        assert manager.backup_dir == Path("/tmp/.claude_backups")

    def test_load_and_save(self):
        """Test loading and saving configuration."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_data = {
                "mcpServers": {
                    "test": {
                        "command": "test",
                        "args": [],
                        "env": {}
                    }
                },
                "numStartups": 1
            }
            json.dump(test_data, f)
            temp_path = Path(f.name)

        try:
            manager = ConfigManager(temp_path)
            config = manager.load()

            assert "test" in config.mcp_servers
            assert config.other_settings["numStartups"] == 1

            # Modify and save
            config.mcp_servers["new_server"] = McpServer(
                name="new_server",
                command="node",
                args=["server.js"],
                env={}
            )
            manager.save(config)

            # Load again to verify
            manager2 = ConfigManager(temp_path)
            config2 = manager2.load()

            assert "new_server" in config2.mcp_servers
            assert config2.mcp_servers["new_server"].command == "node"

        finally:
            temp_path.unlink()

    def test_load_nonexistent_file(self):
        """Test loading a nonexistent file."""
        manager = ConfigManager(Path("/nonexistent/file.json"))

        with pytest.raises(FileNotFoundError):
            manager.load()

    def test_validate(self):
        """Test configuration validation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_data = {"mcpServers": {}}
            json.dump(test_data, f)
            temp_path = Path(f.name)

        try:
            manager = ConfigManager(temp_path)
            manager.load()

            is_valid, error = manager.validate()

            assert is_valid
            assert error is None

        finally:
            temp_path.unlink()
