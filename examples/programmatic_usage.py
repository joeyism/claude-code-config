"""Example of programmatic usage of Claude Config Manager."""

from pathlib import Path

from claude_code_config import ConfigManager
from claude_code_config.models import McpServer


def main():
    """Demonstrate programmatic configuration management."""
    # Initialize the config manager
    # Use default path (~/.claude.json) or provide custom path
    manager = ConfigManager()

    # Load existing configuration
    try:
        config = manager.load()
        print(f"Loaded configuration with {len(config.mcp_servers)} MCP servers")
    except FileNotFoundError:
        print("Config file not found, creating new configuration")
        from claude_code_config.models import ClaudeConfig
        config = ClaudeConfig()

    # Add a new MCP server
    new_server = McpServer(
        name="example-server",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-example"],
        env={"DEBUG": "true"}
    )
    config.mcp_servers[new_server.name] = new_server
    print(f"Added server: {new_server.name}")

    # Add an HTTP server
    http_server = McpServer(
        name="api-server",
        type="http",
        url="https://api.example.com/mcp",
        headers={"Authorization": "Bearer ${API_TOKEN}"}
    )
    config.mcp_servers[http_server.name] = http_server
    print(f"Added HTTP server: {http_server.name}")

    # List all servers
    print("\nAll MCP servers:")
    for name, server in config.mcp_servers.items():
        if server.is_stdio():
            print(f"  - {name} (stdio): {server.command}")
        elif server.is_http():
            print(f"  - {name} (http): {server.url}")
        elif server.is_sse():
            print(f"  - {name} (sse): {server.url}")

    # Validate configuration
    is_valid, error = manager.validate()
    if is_valid:
        print("\nConfiguration is valid")
    else:
        print(f"\nConfiguration validation failed: {error}")
        return

    # Create backup before saving
    backup_path = manager.create_backup()
    print(f"\nCreated backup: {backup_path}")

    # Save configuration
    manager.save(config)
    print("Configuration saved successfully")

    # List available backups
    backups = manager.list_backups()
    print(f"\nAvailable backups: {len(backups)}")
    for backup in backups[:3]:
        print(f"  - {backup.name}")


if __name__ == "__main__":
    main()
