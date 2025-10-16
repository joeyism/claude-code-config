"""Data models for Claude configuration."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class McpServer:
    """Represents an MCP server configuration."""

    name: str
    command: Optional[str] = None
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)

    # HTTP/SSE server fields
    type: Optional[str] = None  # "http" or "sse"
    url: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> "McpServer":
        """Create an McpServer from a dictionary."""
        return cls(
            name=name,
            command=data.get("command"),
            args=data.get("args", []),
            env=data.get("env", {}),
            type=data.get("type"),
            url=data.get("url"),
            headers=data.get("headers", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert McpServer to a dictionary."""
        result = {}

        if self.type:
            result["type"] = self.type
        if self.url:
            result["url"] = self.url
        if self.headers:
            result["headers"] = self.headers
        if self.command:
            result["command"] = self.command
        if self.args:
            result["args"] = self.args
        if self.env:
            result["env"] = self.env

        return result

    def is_stdio(self) -> bool:
        """Check if this is a stdio server."""
        return self.type is None or self.type == "stdio"

    def is_http(self) -> bool:
        """Check if this is an HTTP server."""
        return self.type == "http"

    def is_sse(self) -> bool:
        """Check if this is an SSE server."""
        return self.type == "sse"

    def copy(self) -> "McpServer":
        """Create a copy of this server."""
        return McpServer(
            name=self.name,
            command=self.command,
            args=self.args.copy(),
            env=self.env.copy(),
            type=self.type,
            url=self.url,
            headers=self.headers.copy(),
        )

    def __repr__(self) -> str:
        """String representation."""
        if self.is_stdio():
            return f"McpServer(name='{self.name}', command='{self.command}')"
        else:
            return f"McpServer(name='{self.name}', type='{self.type}', url='{self.url}')"


@dataclass
class Conversation:
    """Represents a conversation in a project."""

    id: str
    data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, conv_id: str, data: Dict[str, Any]) -> "Conversation":
        """Create a Conversation from a dictionary."""
        return cls(id=conv_id, data=data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert Conversation to a dictionary."""
        return self.data

    def get_title(self) -> str:
        """Get conversation title if available."""
        return self.data.get("title", self.id)


@dataclass
class HistoryItem:
    """Represents a history item in a project."""

    index: int
    display: str
    pasted_contents: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, index: int, data: Dict[str, Any]) -> "HistoryItem":
        """Create a HistoryItem from a dictionary."""
        return cls(
            index=index,
            display=data.get("display", ""),
            pasted_contents=data.get("pastedContents", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert HistoryItem to a dictionary."""
        result = {"display": self.display}
        if self.pasted_contents:
            result["pastedContents"] = self.pasted_contents
        return result

    def get_short_display(self, max_length: int = 60) -> str:
        """Get a shortened display text."""
        if len(self.display) <= max_length:
            return self.display
        return self.display[:max_length] + "..."

    def has_pasted_content(self) -> bool:
        """Check if this item has pasted content."""
        return bool(self.pasted_contents)


@dataclass
class Project:
    """Represents a project configuration."""

    path: str
    mcp_servers: Dict[str, McpServer] = field(default_factory=dict)
    conversations: Dict[str, Conversation] = field(default_factory=dict)
    history: List[HistoryItem] = field(default_factory=list)
    other_settings: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, path: str, data: Dict[str, Any]) -> "Project":
        """Create a Project from a dictionary."""
        mcp_servers = {}
        mcp_data = data.get("mcpServers", {})

        for name, server_data in mcp_data.items():
            mcp_servers[name] = McpServer.from_dict(name, server_data)

        conversations = {}
        conv_data = data.get("conversations", {})
        for conv_id, conv in conv_data.items():
            conversations[conv_id] = Conversation.from_dict(conv_id, conv)

        # Parse history
        history = []
        history_data = data.get("history", [])
        for index, item_data in enumerate(history_data):
            history.append(HistoryItem.from_dict(index, item_data))

        # Store all other settings
        other_settings = {
            k: v for k, v in data.items()
            if k not in ("mcpServers", "conversations", "history")
        }

        return cls(
            path=path,
            mcp_servers=mcp_servers,
            conversations=conversations,
            history=history,
            other_settings=other_settings,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert Project to a dictionary."""
        result = dict(self.other_settings)

        if self.mcp_servers:
            result["mcpServers"] = {
                name: server.to_dict() for name, server in self.mcp_servers.items()
            }

        if self.conversations:
            result["conversations"] = {
                conv_id: conv.to_dict() for conv_id, conv in self.conversations.items()
            }

        if self.history:
            result["history"] = [item.to_dict() for item in self.history]

        return result

    def get_display_name(self) -> str:
        """Get a display name for the project."""
        import os
        return os.path.basename(self.path) or self.path


@dataclass
class ClaudeConfig:
    """Represents the complete Claude configuration."""

    global_mcp_servers: Dict[str, McpServer] = field(default_factory=dict)
    projects: Dict[str, Project] = field(default_factory=dict)
    other_settings: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ClaudeConfig":
        """Create a ClaudeConfig from a dictionary."""
        # Parse global MCP servers
        global_mcp_servers = {}
        global_mcp_data = data.get("mcpServers", {})

        for name, server_data in global_mcp_data.items():
            global_mcp_servers[name] = McpServer.from_dict(name, server_data)

        # Parse projects
        projects = {}
        projects_data = data.get("projects", {})

        for path, project_data in projects_data.items():
            projects[path] = Project.from_dict(path, project_data)

        # Store all other settings
        other_settings = {k: v for k, v in data.items() if k not in ("mcpServers", "projects")}

        return cls(
            global_mcp_servers=global_mcp_servers, projects=projects, other_settings=other_settings
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert ClaudeConfig to a dictionary."""
        result = dict(self.other_settings)

        if self.global_mcp_servers:
            result["mcpServers"] = {
                name: server.to_dict() for name, server in self.global_mcp_servers.items()
            }

        if self.projects:
            result["projects"] = {path: project.to_dict() for path, project in self.projects.items()}

        return result

    def get_all_servers(self) -> Dict[str, tuple[str, McpServer]]:
        """Get all servers across all projects.

        Returns:
            Dict mapping server_id to (scope, server) where scope is 'global' or project path
        """
        all_servers = {}

        # Add global servers
        for name, server in self.global_mcp_servers.items():
            all_servers[f"global:{name}"] = ("global", server)

        # Add project servers
        for path, project in self.projects.items():
            for name, server in project.mcp_servers.items():
                all_servers[f"{path}:{name}"] = (path, server)

        return all_servers

    def count_servers(self) -> tuple[int, int]:
        """Count global and project servers.

        Returns:
            Tuple of (global_count, project_count)
        """
        global_count = len(self.global_mcp_servers)
        project_count = sum(len(p.mcp_servers) for p in self.projects.values())
        return global_count, project_count
