# Claude Code Config

A modern Terminal User Interface (TUI) application for managing Claude Code configuration files (`~/.claude.json`). Simplify the management of MCP servers, projects, and conversations with an intuitive hierarchical interface.

## Features

### MCP Server Management
- **Hierarchical View**: Browse global and project-level MCP servers in a tree structure
- **Add, Edit, Delete**: Full CRUD operations for MCP server configurations
- **Copy Servers**: Quickly duplicate server configurations
- **Move Servers**: Move servers between global scope and projects
- **Multi-Scope Support**: Manage both global and project-specific servers

### Project & Conversation Management
- **Project Browser**: View all your Claude Code projects with server, conversation, and history counts
- **Conversation Cleanup**: Delete old conversations you no longer need
- **History Management**: View, delete, and move history items between projects
- **Project Organization**: See which MCP servers are configured for each project

### Safety & Reliability
- **Automatic Backups**: Creates timestamped backups before every save
- **JSON Validation**: Ensures your configuration remains valid
- **Rollback Support**: Easily restore from backups if needed
- **Non-destructive Operations**: Confirm before deleting

### Advanced Features
- **Environment Variable Support**: Handle `${VAR}` syntax in server configs
- **HTTP/SSE Servers**: Support for stdio, HTTP, and SSE server types
- **Large File Handling**: Efficiently manages large config files (handles multi-MB files)
- **Visual Navigation**: Intuitive tree-based navigation

## Installation

### From PyPI

```bash
pip install claude-code-config
```

### From Source

```bash
git clone https://github.com/joeyism/claude-code-config.git
cd claude-code-config
pip install -e .
```

## Usage

Launch the TUI application:

```bash
claude-config
# or use the short alias
ccm
```

### Keyboard Shortcuts

- `↑/↓` or `j/k`: Navigate tree
- `Enter`: Expand/collapse tree nodes
- `a`: Add new MCP server
- `e`: Edit selected server
- `d`: Delete selected item (servers, conversations, or history)
- `c`: Copy selected server
- `m`: Move server or history item to different project
- `s`: Save changes
- `r`: Reload from disk
- `q` or `Ctrl+C`: Quit (with confirmation if unsaved changes)
- `?`: Show help

## Configuration File Structure

The tool manages `~/.claude.json`, which contains:

- **mcpServers**: Global MCP (Model Context Protocol) server configurations
- **projects**: Project-specific settings, including:
  - **mcpServers**: Project-level MCP server configurations
  - **conversations**: Conversation history for each project
  - **history**: User input history for quick access
  - Various project-specific settings
- **other settings**: Various Claude Code settings (preserved)

### Hierarchical Structure

```
Claude Configuration
├── Global Servers (1)
│   └── 📡 terraform-cloud-mcp
└── Projects
    ├── 📁 delorean (3s, 15c, 14h)
    │   ├── MCP Servers (3)
    │   │   ├── 📡 mcp_server_mysql
    │   │   ├── 📡 replicate_server
    │   │   └── 📡 bigquery
    │   ├── Conversations (15)
    │   │   └── 💬 ...
    │   └── History (14)
    │       └── 📝 ...
    └── 📁 web (2s, 8c, 20h)
        └── ...
```

### MCP Server Format

**Stdio Server:**
```json
{
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-example"],
  "env": {
    "API_KEY": "${API_KEY}"
  }
}
```

**HTTP Server:**
```json
{
  "type": "http",
  "url": "https://api.example.com/mcp",
  "headers": {
    "Authorization": "Bearer ${API_TOKEN}"
  }
}
```

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/joeyism/claude-code-config.git
cd claude-code-config

# Install with development dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black claude_code_config/
ruff check claude_code_config/
```

## Why Use Claude Code Config?

The `~/.claude.json` file can grow to several megabytes with hundreds of projects and servers. Manual editing becomes:
- **Error-prone**: Easy to break JSON syntax
- **Difficult**: Hard to find specific servers across projects
- **Risky**: No automatic backups
- **Time-consuming**: Navigating large nested structures

Claude Code Config solves these problems with:
- Visual tree navigation
- Safe editing with validation
- Automatic backups
- Quick search and filtering

## Common Use Cases

1. **Clean up old conversations**: Free up space by deleting conversations you no longer need
2. **Manage history items**: View, delete, or move history entries between projects
3. **Organize MCP servers**: Move servers between global and project scopes
4. **Copy server configs**: Duplicate working configurations for new projects
5. **Audit server usage**: See which projects use which MCP servers
6. **Safely edit configs**: Make changes without risk of corrupting your file

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Textual](https://textual.textualize.io/) - a modern TUI framework
- Designed for use with [Claude Code](https://claude.com/code) by Anthropic
- Inspired by the need for better configuration management tools

## Support

If you encounter any issues or have suggestions, please [open an issue](https://github.com/joeyism/claude-code-config/issues) on GitHub.
