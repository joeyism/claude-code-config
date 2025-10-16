"""Tests for data models."""

import pytest

from claude_code_config.models import McpServer, ClaudeConfig


class TestMcpServer:
    """Tests for McpServer model."""

    def test_stdio_server_creation(self):
        """Test creating a stdio server."""
        server = McpServer(
            name="test-server",
            command="npx",
            args=["test-mcp-server"],
            env={"API_KEY": "${API_KEY}"}
        )

        assert server.name == "test-server"
        assert server.command == "npx"
        assert server.args == ["test-mcp-server"]
        assert server.env == {"API_KEY": "${API_KEY}"}
        assert server.is_stdio()
        assert not server.is_http()
        assert not server.is_sse()

    def test_http_server_creation(self):
        """Test creating an HTTP server."""
        server = McpServer(
            name="http-server",
            type="http",
            url="https://api.example.com/mcp",
            headers={"Authorization": "Bearer token"}
        )

        assert server.name == "http-server"
        assert server.type == "http"
        assert server.url == "https://api.example.com/mcp"
        assert server.headers == {"Authorization": "Bearer token"}
        assert server.is_http()
        assert not server.is_stdio()

    def test_from_dict(self):
        """Test creating server from dictionary."""
        data = {
            "command": "python",
            "args": ["-m", "server"],
            "env": {"DEBUG": "true"}
        }

        server = McpServer.from_dict("test", data)

        assert server.name == "test"
        assert server.command == "python"
        assert server.args == ["-m", "server"]
        assert server.env == {"DEBUG": "true"}

    def test_to_dict(self):
        """Test converting server to dictionary."""
        server = McpServer(
            name="test",
            command="node",
            args=["server.js"],
            env={"PORT": "3000"}
        )

        result = server.to_dict()

        assert result["command"] == "node"
        assert result["args"] == ["server.js"]
        assert result["env"] == {"PORT": "3000"}
        assert "name" not in result  # name is not in the dict


class TestClaudeConfig:
    """Tests for ClaudeConfig model."""

    def test_config_creation(self):
        """Test creating a config."""
        config = ClaudeConfig()

        assert config.mcp_servers == {}
        assert config.other_settings == {}

    def test_from_dict(self):
        """Test creating config from dictionary."""
        data = {
            "mcpServers": {
                "test-server": {
                    "command": "npx",
                    "args": ["test"],
                    "env": {}
                }
            },
            "numStartups": 100,
            "autoUpdates": True
        }

        config = ClaudeConfig.from_dict(data)

        assert "test-server" in config.mcp_servers
        assert config.mcp_servers["test-server"].command == "npx"
        assert config.other_settings["numStartups"] == 100
        assert config.other_settings["autoUpdates"] is True

    def test_to_dict(self):
        """Test converting config to dictionary."""
        config = ClaudeConfig()
        config.mcp_servers["server1"] = McpServer(
            name="server1",
            command="test",
            args=[],
            env={}
        )
        config.other_settings["customSetting"] = "value"

        result = config.to_dict()

        assert "mcpServers" in result
        assert "server1" in result["mcpServers"]
        assert result["customSetting"] == "value"
