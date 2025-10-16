# Quick Start Guide

Get started with Claude Config Manager in 5 minutes.

## Installation

```bash
pip install claude-code-config
```

## First Launch

```bash
claude-config
```

On first launch, you'll see:
- **Global Servers**: MCP servers available to all projects
- **Projects**: Your Claude Code projects with their servers and conversations

## Basic Operations

### 1. Add a New MCP Server

Press `a` to add a server. You'll be prompted for:

- **Server Name**: Give it a descriptive name (e.g., `github-mcp`)
- **Scope**: Choose "Global" or a specific project
- **Type**: Leave empty for stdio, or enter "http" or "sse"
- **Command**: For stdio servers (e.g., `npx -y @modelcontextprotocol/server-github`)
- **Args**: Command arguments, comma-separated
- **Environment Variables**: In format `KEY=value, KEY2=value2`

**Example - Adding a GitHub MCP Server**:
```
Name: github-mcp
Scope: Global
Type: (empty)
Command: npx
Args: -y, @modelcontextprotocol/server-github
Env: GITHUB_TOKEN=${GITHUB_TOKEN}
```

### 2. Edit an Existing Server

1. Navigate to a server using arrow keys
2. Press `e` to edit
3. Modify any fields
4. Click "Save"

### 3. Copy a Server

1. Select a server
2. Press `c` to copy
3. A duplicate is created with `_copy` suffix
4. Edit the copy as needed

### 4. Delete a Server or Conversation

1. Select the item
2. Press `d` to delete
3. Confirm the deletion

### 5. Save Your Changes

Press `s` to save. A backup is automatically created before saving.

### 6. Navigate the Tree

- `↑/↓` or `j/k`: Move up/down
- `Enter`: Expand/collapse folders
- Click on items to view details in the right panel

## Common Tasks

### Clean Up Old Conversations

Conversations can take up significant space:

1. Expand a project in the tree
2. Expand "Conversations"
3. Select a conversation you don't need
4. Press `d` to delete
5. Press `s` to save

### Move a Server Between Projects

(Coming soon - currently you can copy a server to a new scope and delete the old one)

1. Select the server you want to move
2. Press `c` to copy it
3. Press `e` to edit the copy
4. Change the "Scope" field to your target project
5. Save the edited server
6. Delete the original server
7. Press `s` to save all changes

### View Your Configuration

The right panel shows details about the selected item:
- **Servers**: Command, args, environment variables, type
- **Projects**: Path, server count, conversation count
- **Conversations**: ID and title

## Keyboard Shortcuts Reference

| Key | Action |
|-----|--------|
| `a` | Add new server |
| `e` | Edit selected server |
| `d` | Delete selected item |
| `c` | Copy selected server |
| `s` | Save changes |
| `r` | Reload from disk |
| `q` | Quit |
| `?` | Show help |

## Tips

1. **Save Often**: Press `s` regularly to save your changes
2. **Backups**: Automatic backups are stored in `~/.claude_backups/`
3. **Large Files**: The tool handles multi-MB config files efficiently
4. **Environment Variables**: Use `${VAR}` syntax for environment variable expansion
5. **Confirmation**: You'll be prompted to confirm before deleting or quitting with unsaved changes

## Troubleshooting

### "Config file not found"

Make sure `~/.claude.json` exists. If you're using Claude Code, this file is created automatically when you first run Claude.

### "Error loading config"

Your config file might be corrupted. Check the error message and restore from a backup if needed:

```bash
cp ~/.claude_backups/claude.json.backup.TIMESTAMP ~/.claude.json
```

### Changes Not Appearing in Claude Code

After saving changes in Claude Config Manager:
1. Restart Claude Code
2. Or reload the project

## Next Steps

- Read the full [README](README.md) for more details
- Check out [programmatic usage examples](examples/programmatic_usage.py)
- See [CONTRIBUTING.md](CONTRIBUTING.md) to contribute

## Getting Help

- Press `?` in the application for help
- Open an issue on [GitHub](https://github.com/joeyism/claude-code-config/issues)
- Read the [documentation](README.md)

## Example Workflow

Here's a complete workflow for adding a new MCP server:

```
1. Launch: claude-config
2. Press 'a' (add server)
3. Fill in the form:
   Name: my-api-server
   Scope: Global
   Type: http
   URL: https://api.example.com/mcp
   Headers: Authorization=Bearer ${API_TOKEN}
4. Click "Save"
5. Press 's' (save changes)
6. Press 'q' (quit)
7. Restart Claude Code
```

Your new server is now available in Claude Code!
