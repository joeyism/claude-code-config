"""Textual TUI application for Claude config management with project support."""

from pathlib import Path
from typing import Optional

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Label,
    Select,
    Static,
    Tree,
)

from .config import ConfigManager
from .error_log import ErrorLog
from .models import McpServer, Project
from .undo import UndoManager


class ConfirmDialog(ModalScreen[bool]):
    """A modal confirmation dialog."""

    DEFAULT_CSS = """
    ConfirmDialog {
        align: center middle;
    }

    ConfirmDialog > Container {
        width: 60;
        height: auto;
        border: thick $background 80%;
        background: $surface;
        padding: 1 2;
    }

    ConfirmDialog > Container > #question {
        width: 100%;
        height: auto;
        content-align: center middle;
        margin-bottom: 1;
    }

    ConfirmDialog > Container > Horizontal {
        width: 100%;
        height: auto;
        align: center middle;
    }

    ConfirmDialog Button {
        margin: 0 2;
    }
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("q", "cancel", "Cancel"),
        ("n", "cancel", "No"),
        ("y", "confirm", "Yes"),
    ]

    def __init__(self, message: str, title: str = "Confirm"):
        super().__init__()
        self.message = message
        self.title = title

    def compose(self) -> ComposeResult:
        with Container():
            yield Label(self.message, id="question")
            with Horizontal():
                yield Button("Yes", variant="primary", id="yes")
                yield Button("No", variant="default", id="no")

    def action_confirm(self) -> None:
        """Confirm action."""
        self.dismiss(True)

    def action_cancel(self) -> None:
        """Cancel action."""
        self.dismiss(False)

    @on(Button.Pressed, "#yes")
    def handle_yes(self) -> None:
        self.dismiss(True)

    @on(Button.Pressed, "#no")
    def handle_no(self) -> None:
        self.dismiss(False)


class ServerFormScreen(ModalScreen[Optional[tuple[McpServer, str]]]):
    """Modal screen for editing/creating MCP servers."""

    DEFAULT_CSS = """
    ServerFormScreen {
        align: center middle;
    }

    ServerFormScreen > Container {
        width: 80;
        height: 90%;
        border: thick $background 80%;
        background: $surface;
    }

    ServerFormScreen VerticalScroll {
        width: 100%;
        height: 100%;
        padding: 1 2;
    }

    ServerFormScreen Label {
        margin-top: 1;
    }

    ServerFormScreen Input, ServerFormScreen Select {
        margin-bottom: 1;
    }

    ServerFormScreen Horizontal {
        width: 100%;
        height: auto;
        align: center middle;
        margin-top: 1;
    }

    ServerFormScreen Button {
        margin: 0 2;
    }
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("q", "cancel", "Cancel"),
        ("ctrl+s", "save_form", "Save"),
    ]

    def __init__(
        self,
        server: Optional[McpServer] = None,
        current_scope: str = "global",
        available_projects: Optional[list[str]] = None,
    ):
        super().__init__()
        self.server = server
        self.current_scope = current_scope
        self.available_projects = available_projects or []

    def compose(self) -> ComposeResult:
        with Container():
            with VerticalScroll():
                yield Label("Server Name:")
                yield Input(
                    value=self.server.name if self.server else "",
                    placeholder="e.g., my-mcp-server",
                    id="name",
                )

                yield Label("Scope:")
                scope_options = [("Global", "global")] + [
                    (Path(p).name, p) for p in self.available_projects
                ]

                # Create Select without initial value if empty list
                if scope_options:
                    yield Select(
                        options=scope_options,
                        value=self.current_scope,
                        id="scope",
                        allow_blank=False,
                    )
                else:
                    yield Select(
                        options=[("Global", "global")],
                        value="global",
                        id="scope",
                        allow_blank=False,
                    )

                yield Label("Type (leave empty for stdio):")
                yield Input(
                    value=self.server.type if self.server and self.server.type else "",
                    placeholder="stdio, http, or sse",
                    id="type",
                )

                yield Label("Command (for stdio):")
                yield Input(
                    value=self.server.command if self.server and self.server.command else "",
                    placeholder="/path/to/server or npx server",
                    id="command",
                )

                yield Label("Args (comma-separated):")
                yield Input(
                    value=", ".join(self.server.args) if self.server else "",
                    placeholder="arg1, arg2, arg3",
                    id="args",
                )

                yield Label("URL (for http/sse):")
                yield Input(
                    value=self.server.url if self.server and self.server.url else "",
                    placeholder="https://api.example.com/mcp",
                    id="url",
                )

                yield Label("Environment Variables (key=value, comma-separated) - for stdio:")
                yield Input(
                    value=", ".join(f"{k}={v}" for k, v in self.server.env.items())
                    if self.server
                    else "",
                    placeholder="API_KEY=${API_KEY}, DEBUG=true",
                    id="env",
                )

                yield Label("Headers (key=value, comma-separated) - for http/sse:")
                yield Input(
                    value=", ".join(f"{k}={v}" for k, v in self.server.headers.items())
                    if self.server
                    else "",
                    placeholder="Authorization=Bearer ${TOKEN}, Content-Type=application/json",
                    id="headers",
                )

                with Horizontal():
                    yield Button("Save", variant="primary", id="save")
                    yield Button("Cancel", variant="default", id="cancel")

    def on_mount(self) -> None:
        """Set focus to the name input when mounted."""
        self.query_one("#name", Input).focus()

    def action_save_form(self) -> None:
        """Save action triggered by Ctrl+S."""
        self.handle_save()

    def action_cancel(self) -> None:
        """Cancel action triggered by ESC."""
        self.dismiss(None)

    @on(Button.Pressed, "#save")
    def handle_save(self) -> None:
        name_input = self.query_one("#name", Input)
        scope_select = self.query_one("#scope", Select)
        type_input = self.query_one("#type", Input)
        command_input = self.query_one("#command", Input)
        args_input = self.query_one("#args", Input)
        url_input = self.query_one("#url", Input)
        env_input = self.query_one("#env", Input)
        headers_input = self.query_one("#headers", Input)

        name = name_input.value.strip()
        if not name:
            self.app.notify("Server name is required!", severity="error")
            name_input.focus()
            return

        scope = str(scope_select.value) if scope_select.value else "global"

        # Parse args
        args = [arg.strip() for arg in args_input.value.split(",") if arg.strip()]

        # Parse env
        env = {}
        if env_input.value.strip():
            for pair in env_input.value.split(","):
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    env[key.strip()] = value.strip()

        # Parse headers
        headers = {}
        if headers_input.value.strip():
            for pair in headers_input.value.split(","):
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    headers[key.strip()] = value.strip()

        server_type = type_input.value.strip() or None
        command = command_input.value.strip() or None
        url = url_input.value.strip() or None

        server = McpServer(
            name=name,
            type=server_type,
            command=command,
            args=args,
            env=env,
            url=url,
            headers=headers,
        )

        self.dismiss((server, scope))

    @on(Button.Pressed, "#cancel")
    def handle_cancel(self) -> None:
        self.dismiss(None)


class HistoryFormScreen(ModalScreen[Optional[tuple[str, str]]]):
    """Modal screen for editing/creating history items."""

    DEFAULT_CSS = """
    HistoryFormScreen {
        align: center middle;
    }

    HistoryFormScreen > Container {
        width: 90%;
        height: 80%;
        border: thick $background 80%;
        background: $surface;
        padding: 1 2;
    }

    HistoryFormScreen VerticalScroll {
        width: 100%;
        height: 1fr;
        margin-bottom: 1;
    }

    HistoryFormScreen Label {
        margin-top: 1;
        margin-bottom: 1;
    }

    HistoryFormScreen #content {
        height: 20;
        width: 100%;
        margin-bottom: 2;
    }

    HistoryFormScreen Select {
        margin-bottom: 1;
    }

    HistoryFormScreen #button_container {
        width: 100%;
        height: auto;
        align: center middle;
        dock: bottom;
    }

    HistoryFormScreen Button {
        margin: 0 2;
    }
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("q", "cancel", "Cancel"),
        ("ctrl+s", "save_form", "Save"),
    ]

    def __init__(
        self,
        current_content: str = "",
        current_project: str = "global",
        available_projects: Optional[list[str]] = None,
    ):
        super().__init__()
        self.current_content = current_content
        self.current_project = current_project
        self.available_projects = available_projects or []

    def compose(self) -> ComposeResult:
        from textual.widgets import TextArea

        with Container():
            with VerticalScroll():
                yield Label("History Content:")
                yield TextArea(
                    text=self.current_content,
                    id="content",
                    language="markdown",
                    show_line_numbers=False,
                )

                yield Label("Project:")
                project_options = [
                    (Path(p).name, p) for p in self.available_projects
                ]

                if project_options:
                    yield Select(
                        options=project_options,
                        value=self.current_project,
                        id="project",
                        allow_blank=False,
                    )
                else:
                    yield Label("[yellow]No projects available[/yellow]")

            with Horizontal(id="button_container"):
                yield Button("Save", variant="primary", id="save")
                yield Button("Cancel", variant="default", id="cancel")

    def on_mount(self) -> None:
        """Set focus to the content input when mounted."""
        from textual.widgets import TextArea
        self.query_one("#content", TextArea).focus()

    def action_save_form(self) -> None:
        """Save action triggered by Ctrl+S."""
        self.handle_save()

    def action_cancel(self) -> None:
        """Cancel action triggered by ESC."""
        self.dismiss(None)

    @on(Button.Pressed, "#save")
    def handle_save(self) -> None:
        from textual.widgets import TextArea

        content_input = self.query_one("#content", TextArea)
        project_select = self.query_one("#project", Select)

        content = content_input.text.strip()
        if not content:
            self.app.notify("History content is required!", severity="error")
            content_input.focus()
            return

        project = str(project_select.value) if project_select.value else self.available_projects[0] if self.available_projects else None

        if not project:
            self.app.notify("No project selected!", severity="error")
            return

        self.dismiss((content, project))

    @on(Button.Pressed, "#cancel")
    def handle_cancel(self) -> None:
        self.dismiss(None)


class PastedContentsViewer(ModalScreen[None]):
    """Modal screen for viewing pasted contents in detail."""

    DEFAULT_CSS = """
    PastedContentsViewer {
        align: center middle;
    }

    PastedContentsViewer > Container {
        width: 90%;
        height: 90%;
        border: thick $background 80%;
        background: $surface;
        padding: 1 2;
    }

    PastedContentsViewer Label {
        margin-bottom: 1;
    }

    PastedContentsViewer #content_area {
        width: 100%;
        height: 1fr;
        margin-bottom: 1;
    }

    PastedContentsViewer Horizontal {
        width: 100%;
        height: auto;
        align: center middle;
        margin-top: 1;
    }

    PastedContentsViewer Button {
        margin: 0 2;
    }
    """

    BINDINGS = [
        ("escape", "close", "Close"),
        ("q", "close", "Close"),
    ]

    def __init__(self, pasted_contents: dict):
        super().__init__()
        self.pasted_contents = pasted_contents

    def compose(self) -> ComposeResult:
        from textual.widgets import TextArea
        import json

        with Container():
            yield Label(f"[bold]Pasted Contents ({len(self.pasted_contents)} item(s))[/bold]")

            # Format all pasted contents as readable text
            content_lines = []
            for key, value in self.pasted_contents.items():
                content_lines.append(f"{'='*60}")
                content_lines.append(f"KEY: {key}")
                content_lines.append(f"{'='*60}")
                content_lines.append("")

                if isinstance(value, (dict, list)):
                    # Pretty print JSON-like structures
                    try:
                        formatted = json.dumps(value, indent=2, ensure_ascii=False)
                        content_lines.append(formatted)
                    except:
                        content_lines.append(str(value))
                else:
                    content_lines.append(str(value))

                content_lines.append("")
                content_lines.append("")

            yield TextArea(
                text="\n".join(content_lines),
                id="content_area",
                read_only=True,
                show_line_numbers=True,
            )

            with Horizontal():
                yield Button("Close", variant="primary", id="close")

    def action_close(self) -> None:
        """Close the viewer."""
        self.dismiss(None)

    @on(Button.Pressed, "#close")
    def handle_close(self) -> None:
        self.dismiss(None)


class MoveHistoryScreen(ModalScreen[Optional[str]]):
    """Modal screen for moving history items to a different project."""

    DEFAULT_CSS = """
    MoveHistoryScreen {
        align: center middle;
    }

    MoveHistoryScreen > Container {
        width: 60;
        height: auto;
        border: thick $background 80%;
        background: $surface;
        padding: 1 2;
    }

    MoveHistoryScreen Label {
        margin-top: 1;
        margin-bottom: 1;
    }

    MoveHistoryScreen Select {
        margin-bottom: 1;
    }

    MoveHistoryScreen Horizontal {
        width: 100%;
        height: auto;
        align: center middle;
        margin-top: 1;
    }

    MoveHistoryScreen Button {
        margin: 0 2;
    }
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("q", "cancel", "Cancel"),
        ("ctrl+s", "move_item", "Move"),
    ]

    def __init__(self, current_project: str, available_projects: list[str], item_preview: str):
        super().__init__()
        self.current_project = current_project
        self.available_projects = available_projects
        self.item_preview = item_preview

    def compose(self) -> ComposeResult:
        with Container():
            yield Label(f"Move history item to:")
            yield Label(f"[dim]{self.item_preview}[/dim]")

            # Filter out current project from options
            project_options = [
                (Path(p).name, p) for p in self.available_projects
                if p != self.current_project
            ]

            if project_options:
                yield Select(
                    options=project_options,
                    id="target_project",
                    allow_blank=False,
                )
            else:
                yield Label("[yellow]No other projects available[/yellow]")

            with Horizontal():
                yield Button("Move", variant="primary", id="move")
                yield Button("Cancel", variant="default", id="cancel")

    def on_mount(self) -> None:
        """Set focus to the select widget when mounted."""
        try:
            self.query_one("#target_project", Select).focus()
        except:
            pass  # No select widget if no projects available

    def action_move_item(self) -> None:
        """Move action triggered by Ctrl+S."""
        self.handle_move()

    def action_cancel(self) -> None:
        """Cancel action triggered by ESC."""
        self.dismiss(None)

    @on(Button.Pressed, "#move")
    def handle_move(self) -> None:
        try:
            target_select = self.query_one("#target_project", Select)
            target_project = str(target_select.value) if target_select.value else None

            if not target_project:
                self.app.notify("Please select a target project", severity="warning")
                return

            self.dismiss(target_project)
        except:
            # No select widget available
            self.app.notify("No projects available to move to", severity="warning")
            self.dismiss(None)

    @on(Button.Pressed, "#cancel")
    def handle_cancel(self) -> None:
        self.dismiss(None)


class ClaudeConfigApp(App):
    """Main TUI application for managing Claude configuration."""

    TITLE = "Claude Config Manager"
    SUB_TITLE = "Manage your MCP servers and settings"

    CSS = """
    Screen {
        background: $surface;
    }

    #main_container {
        width: 100%;
        height: 100%;
    }

    #sidebar {
        width: 50;
        min-width: 35;
        height: 100%;
        background: $panel;
        border-right: solid $primary;
    }

    #content {
        width: 1fr;
        height: 100%;
    }

    #tree_container {
        height: 1fr;
        width: 100%;
        padding: 1;
        overflow-y: auto;
        overflow-x: hidden;
        scrollbar-size-horizontal: 0;
    }

    #detail_panel {
        height: 100%;
        padding: 1 2;
        overflow-y: auto;
        overflow-x: auto;
    }

    #actions {
        height: auto;
        width: 100%;
        padding: 1;
        background: $panel;
        border-top: solid $primary;
        overflow: hidden;
    }

    #button_row_1, #button_row_2 {
        width: 100%;
        height: 3;
        align: center middle;
    }

    #actions Button {
        width: 1fr;
        min-width: 8;
        height: 3;
        margin: 0 1;
    }

    .info-line {
        margin-bottom: 1;
    }

    Tree {
        width: 100%;
        height: 100%;
        scrollbar-gutter: stable;
        overflow-x: hidden;
    }

    Tree:focus {
        border: tall $accent;
    }
    
    #clipboard_status {
        width: 100%;
        height: 1;
        background: $panel;
        padding: 0 2;
        text-align: center;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("a", "add_server", "Add"),
        ("e", "edit_item", "Edit"),
        ("d", "delete_item", "Delete"),
        ("c", "copy_item", "Copy"),
        ("p", "paste_item", "Paste"),
        ("m", "move_server", "Move"),
        ("v", "view_pasted", "View Pasted"),
        ("V", "toggle_mask", "Toggle Mask"),
        ("s", "save", "Save"),
        ("r", "reload", "Reload"),
        ("?", "help", "Help"),
        ("right", "expand_node", "Expand"),
        ("left", "collapse_node", "Collapse"),
        ("ctrl+z", "undo", "Undo"),
        ("ctrl+y", "redo", "Redo"),
        ("u", "view_undo_history", "Undo History"),
        ("l", "view_errors", "Error Log"),
        ("x", "clear_clipboard", "Clear Clipboard"),
    ]

    def __init__(self, config_path: Optional[str] = None):
        super().__init__()
        self.config_manager = ConfigManager(Path(config_path) if config_path else None)
        self.modified = False
        self.selected_node_data = None
        self.copy_buffer = None  # Store copied items
        self.copy_buffer_type = None  # Track what type is in clipboard
        
        # Phase 1 additions - must be before calling methods that use them
        self.base_title = "Claude Config Manager"
        self.base_subtitle = "Manage your MCP servers and settings"
        self.undo_manager = UndoManager(max_history=50)
        self.error_log = ErrorLog(max_entries=100)
        
        # Security feature - mask sensitive values by default
        self.mask_sensitive_values = True
    
    def mask_value(self, value: str) -> str:
        """Mask a sensitive value with asterisks.
        
        Args:
            value: The value to mask
            
        Returns:
            Masked string (e.g., "****") or original value if masking is off
        """
        if self.mask_sensitive_values and value:
            return "****"
        return value
    
    def update_modified_indicators(self) -> None:
        """Update all UI elements that show modification state."""
        if self.modified:
            self.title = f"{self.base_title} *"
            self.sub_title = "⚠ Unsaved changes"
        else:
            self.title = self.base_title
            self.sub_title = self.base_subtitle
        
        try:
            save_btn = self.query_one("#btn_save", Button)
            if self.modified:
                save_btn.variant = "warning"
                save_btn.label = "Save *"
            else:
                save_btn.variant = "success"
                save_btn.label = "Save [s]"
        except:
            pass  # Button might not be mounted yet

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("[dim]Clipboard: Empty[/dim]", id="clipboard_status")
        with Horizontal(id="main_container"):
            with Vertical(id="sidebar"):
                with VerticalScroll(id="tree_container"):
                    yield Tree("Claude Configuration", id="config_tree")
                with Container(id="actions"):
                    with Horizontal(id="button_row_1"):
                        yield Button("Add", id="btn_add", variant="primary")
                        yield Button("Edit", id="btn_edit")
                        yield Button("Del", id="btn_delete")
                    with Horizontal(id="button_row_2"):
                        yield Button("Copy [c]", id="btn_copy")
                        yield Button("Paste [p]", id="btn_paste")
                        yield Button("Save [s]", id="btn_save", variant="success")
            with VerticalScroll(id="detail_panel"):
                yield Static("Select an item to view details", id="detail_content")
        yield Footer()

    def on_mount(self) -> None:
        """Load configuration on mount and set focus to tree."""
        try:
            self.config_manager.load()
            self.refresh_tree()

            # Set focus to the tree so keyboard navigation works
            tree = self.query_one("#config_tree", Tree)
            tree.focus()

            if self.config_manager.config:
                global_count, project_count = self.config_manager.config.count_servers()
                self.notify(
                    f"Loaded {global_count} global + {project_count} project servers",
                    severity="information",
                )
        except FileNotFoundError:
            self.notify(
                f"Config file not found: {self.config_manager.config_path}",
                severity="error",
                timeout=10,
            )
        except Exception as e:
            self.notify(f"Error loading config: {e}", severity="error", timeout=10)

    def refresh_tree(self) -> None:
        """Refresh the configuration tree view."""
        tree = self.query_one("#config_tree", Tree)
        tree.clear()

        if not self.config_manager.config:
            return

        config = self.config_manager.config

        # Add global servers
        if config.global_mcp_servers:
            global_node = tree.root.add(
                f"[bold cyan]Global Servers ({len(config.global_mcp_servers)})[/bold cyan]",
                data={"type": "global_container"}
            )
            for name, server in sorted(config.global_mcp_servers.items()):
                global_node.add_leaf(
                    f"📡 {name}",
                    data={"type": "server", "scope": "global", "name": name, "server": server}
                )

        # Add projects
        if config.projects:
            for path in sorted(config.projects.keys()):
                project = config.projects[path]
                display_name = project.get_display_name()
                server_count = len(project.mcp_servers)
                real_conversations = self.config_manager.get_conversations(path)
                conv_count = len(real_conversations)
                history_count = len(project.history)

                project_label = f"[bold yellow]📁 {display_name}[/bold yellow]"
                counts = []
                if server_count > 0:
                    counts.append(f"{server_count}s")
                if conv_count > 0:
                    counts.append(f"{conv_count}c")
                if history_count > 0:
                    counts.append(f"{history_count}h")
                if counts:
                    project_label += f" [dim]({', '.join(counts)})[/dim]"

                project_node = tree.root.add(
                    project_label,
                    data={"type": "project", "path": path, "project": project}
                )

                # Add MCP servers
                if project.mcp_servers:
                    servers_node = project_node.add(
                        f"[cyan]MCP Servers ({len(project.mcp_servers)})[/cyan]",
                        data={"type": "servers_container", "path": path}
                    )
                    for name, server in sorted(project.mcp_servers.items()):
                        servers_node.add_leaf(
                            f"📡 {name}",
                            data={"type": "server", "scope": path, "name": name, "server": server}
                        )

                # Add conversations - load from filesystem, not config
                real_conversations = self.config_manager.get_conversations(path)
                if real_conversations:
                    convs_node = project_node.add(
                        f"[magenta]Conversations ({len(real_conversations)})[/magenta]",
                        data={"type": "conversations_container", "path": path}
                    )
                    for conv in real_conversations[:50]:  # Limit to 50 for performance
                        title = conv.get_display_title(40)
                        age = conv.get_age_str()
                        convs_node.add_leaf(
                            f"💬 {title} [dim]({age})[/dim]",
                            data={"type": "conversation", "path": path, "conv_file": conv}
                        )

                # Add history
                if project.history:
                    history_node = project_node.add(
                        f"[green]History ({len(project.history)})[/green]",
                        data={"type": "history_container", "path": path}
                    )
                    for item in project.history[:50]:  # Limit to first 50 for performance
                        display = item.get_short_display(50)
                        pasted_indicator = " 📎" if item.has_pasted_content() else ""
                        history_node.add_leaf(
                            f"📝 {display}{pasted_indicator}",
                            data={"type": "history", "path": path, "index": item.index, "item": item}
                        )

        tree.root.expand()

    def update_detail_panel(self, node_data: Optional[dict]) -> None:
        """Update the detail panel with selected item information."""
        detail = self.query_one("#detail_content", Static)

        if not node_data:
            detail.update("Select an item to view details\n\nKeyboard shortcuts:\na - Add server/history\ne - Edit\nd - Delete\nc - Copy to clipboard\np - Paste from clipboard\nm - Move\ns - Save\nq - Quit\n? - Help")
            return

        item_type = node_data.get("type")

        if item_type == "server":
            server = node_data["server"]
            scope = node_data["scope"]
            info = [
                f"[bold]Server: {server.name}[/bold]",
                f"[bold cyan]Scope:[/bold cyan] {'Global' if scope == 'global' else Path(scope).name}",
                "",
            ]

            if server.is_stdio():
                info.extend([
                    "[bold cyan]Type:[/bold cyan] stdio",
                    f"[bold cyan]Command:[/bold cyan] {server.command or 'N/A'}",
                    f"[bold cyan]Args:[/bold cyan] {', '.join(server.args) if server.args else 'None'}",
                ])
            elif server.is_http():
                info.extend([
                    "[bold cyan]Type:[/bold cyan] http",
                    f"[bold cyan]URL:[/bold cyan] {server.url or 'N/A'}",
                ])
            elif server.is_sse():
                info.extend([
                    "[bold cyan]Type:[/bold cyan] sse",
                    f"[bold cyan]URL:[/bold cyan] {server.url or 'N/A'}",
                ])

            if server.env:
                info.append("")
                info.append("[bold cyan]Environment Variables:[/bold cyan]")
                for key, value in server.env.items():
                    masked_value = self.mask_value(value)
                    info.append(f"  {key} = {masked_value}")

            if server.headers:
                info.append("")
                info.append("[bold cyan]Headers:[/bold cyan]")
                for key, value in server.headers.items():
                    masked_value = self.mask_value(value)
                    info.append(f"  {key} = {masked_value}")

            info.append("")
            mask_indicator = "[*****]" if self.mask_sensitive_values else "[SHOWN]"
            info.append(f"[dim]Press 'e' to edit, 'd' to delete, 'c' to copy, 'p' to paste | {mask_indicator} (V)[/dim]")
            detail.update("\n".join(info))

        elif item_type == "project":
            project = node_data["project"]
            path = node_data["path"]
            real_conversations = self.config_manager.get_conversations(path)
            info = [
                f"[bold]Project: {project.get_display_name()}[/bold]",
                f"[bold cyan]Path:[/bold cyan] {path}",
                "",
                f"[bold cyan]MCP Servers:[/bold cyan] {len(project.mcp_servers)}",
                f"[bold cyan]Conversations:[/bold cyan] {len(real_conversations)}",
                f"[bold cyan]History:[/bold cyan] {len(project.history)}",
                "",
                "[dim]Expand to see servers, conversations, and history[/dim]",
            ]
            detail.update("\n".join(info))

        elif item_type == "conversation":
            # Handle both old format (conv) and new format (conv_file)
            if "conv_file" in node_data:
                conv_file = node_data["conv_file"]
                info = [
                    f"[bold]Conversation[/bold]",
                    "",
                    f"[bold cyan]Title:[/bold cyan] {conv_file.title or 'Untitled'}",
                    f"[bold cyan]ID:[/bold cyan] {conv_file.conversation_id}",
                    f"[bold cyan]Messages:[/bold cyan] {conv_file.message_count}",
                    f"[bold cyan]Size:[/bold cyan] {conv_file.get_size_str()}",
                    f"[bold cyan]Age:[/bold cyan] {conv_file.get_age_str()}",
                    "",
                    f"[bold cyan]Location:[/bold cyan]",
                    f"{conv_file.file_path}",
                    "",
                    "[dim]Press 'd' to delete this conversation[/dim]",
                ]
            else:
                # Old format from .claude.json (shouldn't happen anymore)
                conv = node_data["conv"]
                info = [
                    f"[bold]Conversation[/bold]",
                    f"[bold cyan]ID:[/bold cyan] {conv.id}",
                    f"[bold cyan]Title:[/bold cyan] {conv.get_title()}",
                    "",
                    "[dim]Press 'd' to delete this conversation[/dim]",
                ]
            detail.update("\n".join(info))

        elif item_type == "history":
            item = node_data["item"]
            info = [
                f"[bold]History Item #{item.index + 1}[/bold]",
                "",
                f"[bold cyan]Content:[/bold cyan]",
                item.display[:500],  # Show first 500 chars
            ]

            if len(item.display) > 500:
                info.append("...")
                info.append(f"[dim](Total: {len(item.display)} characters)[/dim]")

            if item.has_pasted_content():
                info.append("")
                info.append(f"[bold cyan]Pasted Contents ({len(item.pasted_contents)} item(s)):[/bold cyan]")
                info.append("")

                # Display each pasted content item
                for key, value in item.pasted_contents.items():
                    info.append(f"[yellow]• {key}:[/yellow]")

                    # Handle different types of pasted content
                    if isinstance(value, str):
                        # Show first 300 chars of string content
                        content_preview = value[:300]
                        if len(value) > 300:
                            content_preview += "..."
                        info.append(f"  {content_preview}")
                    elif isinstance(value, dict):
                        # Show dict structure
                        info.append(f"  [dim]Type: Dictionary with {len(value)} key(s)[/dim]")
                        # Show first few keys
                        dict_keys = list(value.keys())[:5]
                        if dict_keys:
                            info.append(f"  [dim]Keys: {', '.join(str(k) for k in dict_keys)}[/dim]")
                        if len(value) > 5:
                            info.append(f"  [dim]... and {len(value) - 5} more[/dim]")
                    elif isinstance(value, list):
                        # Show list info
                        info.append(f"  [dim]Type: List with {len(value)} item(s)[/dim]")
                        if value and len(value) > 0:
                            first_item = str(value[0])[:100]
                            info.append(f"  [dim]First item: {first_item}[/dim]")
                    else:
                        # Show other types
                        info.append(f"  [dim]Type: {type(value).__name__}[/dim]")
                        info.append(f"  {str(value)[:200]}")

                    info.append("")

                info.append("[dim]Press 'v' to view full pasted contents[/dim]")

            info.append("")
            info.append("[dim]Press 'd' to delete, 'm' to move, 'e' to edit[/dim]")
            detail.update("\n".join(info))

        else:
            detail.update(f"Container: {item_type}\n\n[dim]Expand to see contents[/dim]")

    @on(Tree.NodeHighlighted)
    def handle_tree_selected(self, event: Tree.NodeHighlighted) -> None:
        """Handle tree node selection."""
        if event.node.data:
            self.selected_node_data = event.node.data
            self.update_detail_panel(event.node.data)
        else:
            self.selected_node_data = None
            self.update_detail_panel(None)

    def action_add_server(self) -> None:
        """Add a new server or history item based on context."""
        if not self.config_manager.config:
            self.notify("Configuration not loaded", severity="error")
            return

        projects = list(self.config_manager.config.projects.keys())

        # Check if we're in a history container or have a history item selected
        if self.selected_node_data:
            item_type = self.selected_node_data.get("type")
            if item_type == "history_container":
                # Add history to the current project
                project_path = self.selected_node_data["path"]
                self.push_screen(
                    HistoryFormScreen(current_project=project_path, available_projects=projects),
                    self.handle_history_form_result
                )
                return
            elif item_type == "history":
                # Add history to the same project as the selected history item
                project_path = self.selected_node_data["path"]
                self.push_screen(
                    HistoryFormScreen(current_project=project_path, available_projects=projects),
                    self.handle_history_form_result
                )
                return

        # Default: add server
        self.push_screen(
            ServerFormScreen(available_projects=projects),
            self.handle_server_form_result
        )

    def action_edit_item(self) -> None:
        """Edit the selected item."""
        if not self.selected_node_data:
            self.notify("No item selected", severity="warning")
            return

        item_type = self.selected_node_data.get("type")

        if item_type == "server":
            server = self.selected_node_data["server"]
            scope = self.selected_node_data["scope"]
            projects = list(self.config_manager.config.projects.keys())
            self.push_screen(
                ServerFormScreen(server, scope, projects),
                self.handle_server_form_result
            )
        elif item_type == "history":
            item = self.selected_node_data["item"]
            current_path = self.selected_node_data["path"]
            projects = list(self.config_manager.config.projects.keys())
            self.push_screen(
                HistoryFormScreen(item.display, current_path, projects),
                self.handle_history_form_result
            )
        else:
            self.notify("Only servers and history items can be edited", severity="warning")

    def action_delete_item(self) -> None:
        """Delete the selected item."""
        if not self.selected_node_data:
            self.notify("No item selected", severity="warning")
            return

        item_type = self.selected_node_data.get("type")

        if item_type == "server":
            server_name = self.selected_node_data["name"]
            self.push_screen(
                ConfirmDialog(f"Delete server '{server_name}'?", "Delete Server"),
                lambda result: self.handle_delete_server(result if result is not None else False)
            )
        elif item_type == "conversation":
            # Handle new format with conv_file
            if "conv_file" in self.selected_node_data:
                conv_file = self.selected_node_data["conv_file"]
                title = conv_file.get_display_title(40)
                self.push_screen(
                    ConfirmDialog(f"Delete conversation '{title}'?", "Delete Conversation"),
                    lambda result: self.handle_delete_conversation(result if result is not None else False)
                )
            else:
                # Fallback for old .claude.json format (for safety)
                self.push_screen(
                    ConfirmDialog(f"Delete conversation?", "Delete Conversation"),
                    lambda result: self.handle_delete_conversation(result if result is not None else False)
                )
        elif item_type == "history":
            item = self.selected_node_data["item"]
            display_preview = item.get_short_display(40)
            self.push_screen(
                ConfirmDialog(f"Delete history item?\n\n{display_preview}", "Delete History"),
                lambda result: self.handle_delete_history(result if result is not None else False)
            )
        else:
            self.notify("Cannot delete this type of item", severity="warning")

    def action_move_server(self) -> None:
        """Move a server or history item to a different scope/project."""
        if not self.selected_node_data:
            self.notify("Select an item to move", severity="warning")
            return

        item_type = self.selected_node_data.get("type")

        if item_type == "server":
            # Moving server is the same as editing - just change the scope in the form
            self.notify("Tip: Change the 'Scope' field to move the server", severity="information", timeout=3)
            self.action_edit_item()
        elif item_type == "history":
            # Show move dialog for history items
            item = self.selected_node_data["item"]
            current_path = self.selected_node_data["path"]
            projects = list(self.config_manager.config.projects.keys())

            if len(projects) < 2:
                self.notify("Need at least 2 projects to move history", severity="warning")
                return

            item_preview = item.get_short_display(40)
            self.push_screen(
                MoveHistoryScreen(current_path, projects, item_preview),
                self.handle_move_history
            )
        else:
            self.notify("Select a server or history item to move", severity="warning")

    def action_view_pasted(self) -> None:
        """View pasted contents of a history item in detail."""
        if not self.selected_node_data:
            self.notify("No item selected", severity="warning")
            return

        if self.selected_node_data.get("type") != "history":
            self.notify("Select a history item to view pasted contents", severity="warning")
            return

        item = self.selected_node_data["item"]

        if not item.has_pasted_content():
            self.notify("This history item has no pasted contents", severity="information")
            return

        self.push_screen(PastedContentsViewer(item.pasted_contents))

    def action_expand_node(self) -> None:
        """Expand the currently selected tree node."""
        tree = self.query_one("#config_tree", Tree)
        if tree.cursor_node:
            # If node has children and is collapsed, expand it
            if not tree.cursor_node.is_expanded and tree.cursor_node.children:
                tree.cursor_node.expand()
            # If already expanded and has children, move to first child
            elif tree.cursor_node.is_expanded and tree.cursor_node.children:
                tree.select_node(tree.cursor_node.children[0])

    def action_collapse_node(self) -> None:
        """Collapse the currently selected tree node or move to parent."""
        tree = self.query_one("#config_tree", Tree)
        if tree.cursor_node:
            # If node is expanded, collapse it
            if tree.cursor_node.is_expanded and tree.cursor_node.children:
                tree.cursor_node.collapse()
            # If node is collapsed or a leaf, move to parent
            elif tree.cursor_node.parent and tree.cursor_node.parent != tree.root:
                tree.select_node(tree.cursor_node.parent)
                tree.cursor_node.parent.collapse()

    def handle_delete_server(self, confirmed: bool) -> None:
        """Handle server deletion confirmation."""
        if not confirmed or not self.selected_node_data:
            return

        # Save undo snapshot before deleting
        self.undo_manager.save_snapshot(
            self.config_manager.config,
            f"Delete server '{self.selected_node_data['name']}'",
            self.selected_node_data
        )

        scope = self.selected_node_data["scope"]
        name = self.selected_node_data["name"]

        if scope == "global":
            del self.config_manager.config.global_mcp_servers[name]
        else:
            project = self.config_manager.config.projects.get(scope)
            if project:
                del project.mcp_servers[name]

        self.config_manager.mark_modified()
        self.modified = True
        self.update_modified_indicators()
        self.refresh_tree()
        self.update_detail_panel(None)
        self.selected_node_data = None

        # Refocus tree after deletion
        self.query_one("#config_tree", Tree).focus()

        self.notify(f"Server '{name}' deleted", severity="information")

    def handle_delete_conversation(self, confirmed: bool) -> None:
        """Handle conversation deletion confirmation."""
        if not confirmed or not self.selected_node_data:
            return

        # Handle new format (conv_file from filesystem)
        if "conv_file" in self.selected_node_data:
            conv_file = self.selected_node_data["conv_file"]
            
            # Delete the actual file
            if conv_file.delete():
                self.refresh_tree()
                self.update_detail_panel(None)
                self.selected_node_data = None
                self.query_one("#config_tree", Tree).focus()
                self.notify(f"✓ Conversation '{conv_file.get_display_title(40)}' deleted", severity="information")
            else:
                self.notify(f"✗ Failed to delete conversation file", severity="error")
        else:
            # Old format from .claude.json (fallback)
            path = self.selected_node_data["path"]
            conv_id = self.selected_node_data["id"]

            project = self.config_manager.config.projects.get(path)
            if project and conv_id in project.conversations:
                del project.conversations[conv_id]
                self.config_manager.mark_modified()
                self.modified = True
                self.update_modified_indicators()
                self.refresh_tree()
                self.update_detail_panel(None)
                self.selected_node_data = None
                self.query_one("#config_tree", Tree).focus()
                self.notify(f"Conversation deleted", severity="information")

    def handle_delete_history(self, confirmed: bool) -> None:
        """Handle history deletion confirmation."""
        if not confirmed or not self.selected_node_data:
            return

        path = self.selected_node_data["path"]
        index = self.selected_node_data["index"]

        project = self.config_manager.config.projects.get(path)
        if project and index < len(project.history):
            # Remove the item at the specified index
            project.history.pop(index)

            # Update indices for remaining items
            for i, item in enumerate(project.history):
                item.index = i

            self.config_manager.mark_modified()
            self.modified = True
            self.refresh_tree()
            self.update_detail_panel(None)
            self.selected_node_data = None

            # Refocus tree after deletion
            self.query_one("#config_tree", Tree).focus()

            self.notify(f"History item deleted", severity="information")

    def handle_move_history(self, target_project: Optional[str]) -> None:
        """Handle moving history item to another project."""
        if not target_project or not self.selected_node_data:
            # Refocus tree when form is cancelled
            self.query_one("#config_tree", Tree).focus()
            return

        source_path = self.selected_node_data["path"]
        index = self.selected_node_data["index"]

        source_project = self.config_manager.config.projects.get(source_path)
        target_proj = self.config_manager.config.projects.get(target_project)

        if not source_project or not target_proj:
            self.notify("Source or target project not found", severity="error")
            self.query_one("#config_tree", Tree).focus()
            return

        if index >= len(source_project.history):
            self.notify("History item not found", severity="error")
            self.query_one("#config_tree", Tree).focus()
            return

        # Remove from source project
        history_item = source_project.history.pop(index)

        # Update indices for remaining items in source
        for i, item in enumerate(source_project.history):
            item.index = i

        # Add to target project
        history_item.index = len(target_proj.history)
        target_proj.history.append(history_item)

        self.config_manager.mark_modified()
        self.modified = True
        self.refresh_tree()
        self.update_detail_panel(None)
        self.selected_node_data = None

        # Refocus tree after move
        self.query_one("#config_tree", Tree).focus()

        target_name = Path(target_project).name
        self.notify(f"History item moved to {target_name}", severity="information")

    def handle_history_form_result(self, result: Optional[tuple[str, str]]) -> None:
        """Handle result from history form."""
        if not result or not self.config_manager.config:
            # Refocus tree when form is cancelled
            self.query_one("#config_tree", Tree).focus()
            return

        from .models import HistoryItem

        content, project_path = result

        # Check if we're editing or adding
        if self.selected_node_data and self.selected_node_data.get("type") == "history":
            # Editing existing history
            old_path = self.selected_node_data["path"]
            index = self.selected_node_data["index"]

            old_project = self.config_manager.config.projects.get(old_path)
            new_project = self.config_manager.config.projects.get(project_path)

            if not old_project or not new_project:
                self.notify("Project not found", severity="error")
                self.query_one("#config_tree", Tree).focus()
                return

            if index >= len(old_project.history):
                self.notify("History item not found", severity="error")
                self.query_one("#config_tree", Tree).focus()
                return

            # Get the old item to preserve pasted contents
            old_item = old_project.history[index]

            # If moving to a different project
            if old_path != project_path:
                # Remove from old project
                old_project.history.pop(index)
                # Update indices in old project
                for i, item in enumerate(old_project.history):
                    item.index = i

                # Create new item in new project
                new_item = HistoryItem(
                    index=len(new_project.history),
                    display=content,
                    pasted_contents=old_item.pasted_contents.copy()
                )
                new_project.history.append(new_item)
            else:
                # Update in same project
                old_item.display = content

            self.notify(f"History item updated", severity="information")
        else:
            # Adding new history
            project = self.config_manager.config.projects.get(project_path)
            if not project:
                self.notify(f"Project not found: {project_path}", severity="error")
                self.query_one("#config_tree", Tree).focus()
                return

            new_item = HistoryItem(
                index=len(project.history),
                display=content,
                pasted_contents={}
            )
            project.history.append(new_item)

            self.notify(f"History item added", severity="information")

        self.config_manager.mark_modified()
        self.modified = True
        self.refresh_tree()

        # Refocus tree after save
        self.query_one("#config_tree", Tree).focus()

    def handle_server_form_result(self, result: Optional[tuple[McpServer, str]]) -> None:
        """Handle result from server form."""
        if not result or not self.config_manager.config:
            # Refocus tree when form is cancelled
            self.query_one("#config_tree", Tree).focus()
            return

        server, new_scope = result

        # Remove old server if editing and name/scope changed
        if self.selected_node_data and self.selected_node_data.get("type") == "server":
            old_scope = self.selected_node_data["scope"]
            old_name = self.selected_node_data["name"]

            if old_scope != new_scope or old_name != server.name:
                if old_scope == "global":
                    if old_name in self.config_manager.config.global_mcp_servers:
                        del self.config_manager.config.global_mcp_servers[old_name]
                else:
                    project = self.config_manager.config.projects.get(old_scope)
                    if project and old_name in project.mcp_servers:
                        del project.mcp_servers[old_name]

        # Add server to new scope
        if new_scope == "global":
            self.config_manager.config.global_mcp_servers[server.name] = server
        else:
            project = self.config_manager.config.projects.get(new_scope)
            if project:
                project.mcp_servers[server.name] = server
            else:
                self.notify(f"Project not found: {new_scope}", severity="error")
                self.query_one("#config_tree", Tree).focus()
                return

        self.config_manager.mark_modified()
        self.modified = True
        self.refresh_tree()

        # Refocus tree after save
        self.query_one("#config_tree", Tree).focus()

        self.notify(f"Server '{server.name}' saved", severity="information")

    def action_copy_item(self) -> None:
        """Copy the selected item to clipboard."""
        if not self.selected_node_data:
            self.notify("No item selected", severity="warning")
            return

        item_type = self.selected_node_data.get("type")

        if item_type == "server":
            server = self.selected_node_data["server"]
            self.copy_buffer = server.copy()
            self.copy_buffer_type = "server"
            # Update clipboard status with masked details
            try:
                clipboard_status = self.query_one("#clipboard_status", Static)
                # Build detailed summary
                details = []
                if server.env:
                    details.append(f"Env: {len(server.env)} vars")
                if server.headers:
                    details.append(f"Headers: {len(server.headers)} items")
                
                details_str = f" | {' | '.join(details)}" if details else ""
                clipboard_status.update(f"[cyan]📋 Clipboard: Server '{server.name}'{details_str}[/cyan] (Press 'p' to paste, 'x' to clear)")
            except:
                pass
            self.notify(f"✓ Copied server '{server.name}' to clipboard", severity="information")
        elif item_type == "history":
            item = self.selected_node_data["item"]
            # Copy the history item
            from .models import HistoryItem
            self.copy_buffer = HistoryItem(
                index=0,  # Will be set on paste
                display=item.display,
                pasted_contents=item.pasted_contents.copy()
            )
            self.copy_buffer_type = "history"
            preview = item.get_short_display(30)
            # Update clipboard status
            try:
                clipboard_status = self.query_one("#clipboard_status", Static)
                clipboard_status.update(f"[green]📋 Clipboard: History '{preview}'[/green] (Press 'p' to paste, 'x' to clear)")
            except:
                pass
            self.notify(f"✓ Copied history item to clipboard", severity="information")
        else:
            self.notify("Can only copy servers and history items", severity="warning")

    def action_paste_item(self) -> None:
        """Paste item from clipboard to current location."""
        if not self.copy_buffer:
            self.notify("Clipboard is empty - copy something first with 'c'", severity="warning")
            return

        if self.copy_buffer_type == "server":
            # Determine target scope based on selection
            target_scope = "global"
            if self.selected_node_data:
                item_type = self.selected_node_data.get("type")
                if item_type == "project":
                    target_scope = self.selected_node_data["path"]
                elif item_type == "servers_container":
                    target_scope = self.selected_node_data["path"]
                elif item_type == "server":
                    target_scope = self.selected_node_data["scope"]

            # Find unique name
            base_name = self.copy_buffer.name
            new_name = base_name
            counter = 1

            if target_scope == "global":
                while new_name in self.config_manager.config.global_mcp_servers:
                    new_name = f"{base_name}_{counter}"
                    counter += 1
                new_server = self.copy_buffer.copy()
                new_server.name = new_name
                self.config_manager.config.global_mcp_servers[new_name] = new_server
                scope_name = "Global"
            else:
                project = self.config_manager.config.projects.get(target_scope)
                if not project:
                    self.notify("Target project not found", severity="error")
                    return
                while new_name in project.mcp_servers:
                    new_name = f"{base_name}_{counter}"
                    counter += 1
                new_server = self.copy_buffer.copy()
                new_server.name = new_name
                project.mcp_servers[new_name] = new_server
                scope_name = Path(target_scope).name

            self.config_manager.mark_modified()
            self.modified = True
            self.refresh_tree()
            self.notify(f"Pasted server '{new_name}' to {scope_name}", severity="information")

        elif self.copy_buffer_type == "history":
            # Determine target project
            target_path = None
            if self.selected_node_data:
                item_type = self.selected_node_data.get("type")
                if item_type == "project":
                    target_path = self.selected_node_data["path"]
                elif item_type in ["history_container", "history"]:
                    target_path = self.selected_node_data["path"]

            if not target_path:
                self.notify("Select a project or history location to paste", severity="warning")
                return

            project = self.config_manager.config.projects.get(target_path)
            if not project:
                self.notify("Target project not found", severity="error")
                return

            from .models import HistoryItem
            new_item = HistoryItem(
                index=len(project.history),
                display=self.copy_buffer.display,
                pasted_contents=self.copy_buffer.pasted_contents.copy()
            )
            project.history.append(new_item)

            self.config_manager.mark_modified()
            self.modified = True
            self.refresh_tree()
            project_name = Path(target_path).name
            self.notify(f"Pasted history item to {project_name}", severity="information")

    def action_save(self) -> None:
        """Save configuration."""
        try:
            self.config_manager.save()
            self.modified = False
            self.notify("Configuration saved successfully ✓", severity="information")
        except Exception as e:
            self.notify(f"Error saving configuration: {e}", severity="error", timeout=10)

    def action_reload(self) -> None:
        """Reload configuration from disk."""
        if self.modified:
            self.push_screen(
                ConfirmDialog("You have unsaved changes. Reload anyway?", "Confirm Reload"),
                lambda result: self.handle_reload_confirm(result if result is not None else False)
            )
        else:
            self.do_reload()

    def handle_reload_confirm(self, confirmed: bool) -> None:
        """Handle reload confirmation."""
        if confirmed:
            self.do_reload()
        else:
            # Refocus tree if reload cancelled
            self.query_one("#config_tree", Tree).focus()

    def do_reload(self) -> None:
        """Perform the reload."""
        try:
            self.config_manager.load()
            self.modified = False
            self.update_modified_indicators()
            self.undo_manager.clear()
            self.selected_node_data = None
            self.refresh_tree()
            self.update_detail_panel(None)

            # Refocus tree after reload
            self.query_one("#config_tree", Tree).focus()

            if self.config_manager.config:
                global_count, project_count = self.config_manager.config.count_servers()
                self.notify(
                    f"Reloaded {global_count} global + {project_count} project servers",
                    severity="information"
                )
        except Exception as e:
            self.notify(f"Error reloading configuration: {e}", severity="error", timeout=10)

    def action_help(self) -> None:
        """Show help information."""
        help_text = """
[bold]Keyboard Shortcuts:[/bold]

a - Add new server or history (context-aware)
e - Edit selected item (servers, history)
d - Delete selected item (servers, conversations, history)
c - Copy item to clipboard (servers, history)
p - Paste item from clipboard
x - Clear clipboard
m - Move server or history item
v - View full pasted contents (for history items)
s - Save changes
r - Reload from disk
q - Quit / Exit any dialog
? - Show this help

[bold]Undo/Redo:[/bold] [green](NEW!)[/green]
Ctrl+Z - Undo last action
Ctrl+Y - Redo previously undone action
u - View undo/redo history

[bold]Error Management:[/bold] [green](NEW!)[/green]
l - View error log (browse, export, clear)

[bold]Tree Navigation:[/bold]
↑↓ - Navigate up/down
j/k - Navigate up/down (vim style)
→ - Expand node (unfold >)
← - Collapse node
Enter - Toggle expand/collapse
Space - Toggle expand/collapse

[bold]In Dialogs:[/bold]
ESC - Cancel/close dialog
q - Close dialog
Tab - Move between fields
Ctrl+S - Save in forms

[bold]Features:[/bold]
• Manage MCP servers (global & project-level)
• Copy-paste workflow for servers and history
• Undo/redo system with 50-action history
• Persistent error log viewer
• Visual indicators for unsaved changes
• Add, edit, and delete history items
• View full pasted contents in detail
• Move history between projects
• Clean up conversations
        """
        self.notify(help_text.strip(), severity="information", timeout=20)

    def action_quit(self) -> None:
        """Quit the application."""
        if self.modified:
            self.push_screen(
                ConfirmDialog("You have unsaved changes. Quit anyway?", "Confirm Quit"),
                lambda result: self.exit() if (result if result is not None else False) else None
            )
        else:
            self.exit()

    # Button click handlers (for mouse users)
    @on(Button.Pressed, "#btn_add")
    def on_add_button(self) -> None:
        self.action_add_server()

    @on(Button.Pressed, "#btn_edit")
    def on_edit_button(self) -> None:
        self.action_edit_item()

    @on(Button.Pressed, "#btn_delete")
    def on_delete_button(self) -> None:
        self.action_delete_item()

    @on(Button.Pressed, "#btn_copy")
    def on_copy_button(self) -> None:
        self.action_copy_item()

    @on(Button.Pressed, "#btn_paste")
    def on_paste_button(self) -> None:
        self.action_paste_item()

    @on(Button.Pressed, "#btn_move")
    def on_move_button(self) -> None:
        self.action_move_server()

    @on(Button.Pressed, "#btn_save")
    def on_save_button(self) -> None:
        self.action_save()
# This file contains all new methods to be added to ClaudeConfigApp
# Copy these to the end of the tui.py file

    def action_undo(self) -> None:
        """Undo last action."""
        from .models import ClaudeConfig
        
        if not self.undo_manager.can_undo():
            self.notify("Nothing to undo", severity="information")
            return
        
        snapshot = self.undo_manager.undo(
            self.config_manager.config,
            self.selected_node_data
        )
        
        if not snapshot:
            return
        
        # Restore config from snapshot
        config_data = snapshot.config_state
        self.config_manager._config = ClaudeConfig.from_dict(config_data)
        
        # Mark as modified
        self.config_manager.mark_modified()
        self.modified = True
        self.update_modified_indicators()
        
        # Refresh UI
        self.refresh_tree()
        self.update_detail_panel(None)
        self.selected_node_data = None
        self.query_one("#config_tree", Tree).focus()
        
        self.notify(f"✓ Undone: {snapshot.description}", severity="information")

    def action_redo(self) -> None:
        """Redo previously undone action."""
        from .models import ClaudeConfig
        
        if not self.undo_manager.can_redo():
            self.notify("Nothing to redo", severity="information")
            return
        
        snapshot = self.undo_manager.redo()
        
        if not snapshot:
            return
        
        # Restore config from snapshot
        config_data = snapshot.config_state
        self.config_manager._config = ClaudeConfig.from_dict(config_data)
        
        # Mark as modified
        self.config_manager.mark_modified()
        self.modified = True
        self.update_modified_indicators()
        
        # Refresh UI
        self.refresh_tree()
        self.update_detail_panel(None)
        self.selected_node_data = None
        self.query_one("#config_tree", Tree).focus()
        
        self.notify(f"✓ Redone: {snapshot.description}", severity="information")

    def action_view_undo_history(self) -> None:
        """Show undo/redo history viewer."""
        class UndoHistoryScreen(ModalScreen[None]):
            """Modal screen for viewing undo history."""
            
            DEFAULT_CSS = """
            UndoHistoryScreen {
                align: center middle;
            }
            
            UndoHistoryScreen > Container {
                width: 70;
                height: auto;
                max-height: 80%;
                border: thick $background 80%;
                background: $surface;
                padding: 1 2;
            }
            """
            
            BINDINGS = [
                ("escape", "close", "Close"),
                ("q", "close", "Close"),
            ]
            
            def __init__(self, undo_manager):
                super().__init__()
                self.undo_manager = undo_manager
            
            def compose(self) -> ComposeResult:
                with Container():
                    yield Label("[bold]Undo/Redo History[/bold]")
                    yield Label("")
                    
                    if self.undo_manager.can_undo():
                        yield Label("[bold cyan]Can Undo:[/bold cyan]")
                        for action in self.undo_manager.get_undo_history():
                            yield Label(f"  ← {action}")
                    else:
                        yield Label("[dim]No undo history[/dim]")
                    
                    yield Label("")
                    
                    if self.undo_manager.can_redo():
                        yield Label("[bold green]Can Redo:[/bold green]")
                        for action in self.undo_manager.get_redo_history():
                            yield Label(f"  → {action}")
                    else:
                        yield Label("[dim]No redo history[/dim]")
                    
                    yield Label("")
                    yield Label("[dim]Use Ctrl+Z to undo, Ctrl+Y to redo[/dim]")
                    
                    with Horizontal():
                        yield Button("Close", variant="primary", id="close")
            
            @on(Button.Pressed, "#close")
            def handle_close(self) -> None:
                self.dismiss(None)
            
            def action_close(self) -> None:
                self.dismiss(None)
        
        self.push_screen(UndoHistoryScreen(self.undo_manager))

    def action_view_errors(self) -> None:
        """Show error log viewer."""
        from datetime import datetime
        
        class ErrorLogScreen(ModalScreen[None]):
            """Modal screen for viewing error log."""
            
            DEFAULT_CSS = """
            ErrorLogScreen {
                align: center middle;
            }
            
            ErrorLogScreen > Container {
                width: 90%;
                height: 90%;
                border: thick $background 80%;
                background: $surface;
                padding: 1 2;
            }
            
            ErrorLogScreen #error_list {
                width: 35%;
                height: 100%;
                border-right: solid $primary;
            }
            
            ErrorLogScreen #error_detail {
                width: 65%;
                height: 100%;
                padding: 0 2;
            }
            """
            
            BINDINGS = [
                ("escape", "close", "Close"),
                ("q", "close", "Close"),
                ("c", "clear_log", "Clear Log"),
                ("e", "export_log", "Export"),
            ]
            
            def __init__(self, error_log):
                super().__init__()
                self.error_log = error_log
            
            def compose(self) -> ComposeResult:
                with Container():
                    yield Label(f"[bold]Error Log ({len(self.error_log.entries)} entries)[/bold]")
                    
                    with Horizontal():
                        with VerticalScroll(id="error_list"):
                            if not self.error_log.entries:
                                yield Label("[green]No errors logged[/green]")
                            else:
                                error_tree = Tree("Errors", id="error_tree")
                                for entry in self.error_log.entries:
                                    error_tree.root.add_leaf(
                                        entry.format_short(),
                                        data={"entry": entry}
                                    )
                                yield error_tree
                        
                        with VerticalScroll(id="error_detail"):
                            yield Static("Select an error to view details", id="detail_content")
                    
                    with Horizontal():
                        yield Button("Clear Log [c]", id="clear")
                        yield Button("Export [e]", id="export")
                        yield Button("Close [esc]", variant="primary", id="close")
            
            @on(Tree.NodeHighlighted)
            def show_error_details(self, event: Tree.NodeHighlighted) -> None:
                if event.node.data:
                    entry = event.node.data["entry"]
                    detail = self.query_one("#detail_content", Static)
                    detail.update(entry.format_full())
            
            @on(Button.Pressed, "#clear")
            def handle_clear(self) -> None:
                self.action_clear_log()
            
            @on(Button.Pressed, "#export")
            def handle_export(self) -> None:
                self.action_export_log()
            
            @on(Button.Pressed, "#close")
            def handle_close(self) -> None:
                self.dismiss(None)
            
            def action_clear_log(self) -> None:
                def do_clear(confirmed: Optional[bool]) -> None:
                    if confirmed:
                        self.error_log.clear()
                        self.app.notify("Error log cleared", severity="information")
                        self.dismiss(None)
                
                self.app.push_screen(
                    ConfirmDialog("Clear all errors from log?", "Clear Log"),
                    do_clear
                )
            
            def action_export_log(self) -> None:
                export_path = Path.home() / f"claude-config-errors-{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                try:
                    self.error_log.export_to_file(export_path)
                    self.app.notify(f"✓ Exported errors to {export_path}", severity="information")
                except Exception as e:
                    self.app.notify(f"Export failed: {e}", severity="error")
            
            def action_close(self) -> None:
                self.dismiss(None)
        
        self.push_screen(ErrorLogScreen(self.error_log))

    def action_clear_clipboard(self) -> None:
        """Clear the clipboard."""
        if self.copy_buffer:
            old_type = self.copy_buffer_type
            self.copy_buffer = None
            self.copy_buffer_type = None
            self.notify(f"Clipboard cleared ({old_type})", severity="information")
        else:
            self.notify("Clipboard is already empty", severity="information")
    
    def action_toggle_mask(self) -> None:
        """Toggle masking of sensitive values."""
        self.mask_sensitive_values = not self.mask_sensitive_values
        
        # Refresh detail panel to show new state
        if self.selected_node_data:
            self.update_detail_panel(self.selected_node_data)
        
        # Notify user with appropriate icon and severity
        if self.mask_sensitive_values:
            self.notify("🔒 Sensitive values masked", severity="information")
        else:
            self.notify("👁 Sensitive values visible", severity="warning")
