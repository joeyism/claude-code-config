"""Error logging functionality for the application."""

import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ErrorEntry:
    """Represents a single error entry."""
    
    timestamp: datetime
    severity: str  # "error", "warning", "critical"
    message: str
    details: str = ""
    traceback_str: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    
    def format_short(self) -> str:
        """Format for list view."""
        time_str = self.timestamp.strftime("%H:%M:%S")
        severity_icon = "🔴" if self.severity == "error" else "⚠️" if self.severity == "warning" else "💥"
        return f"{severity_icon} [{time_str}] {self.message[:60]}"
    
    def format_full(self) -> str:
        """Format for detail view."""
        lines = [
            f"[bold]Time:[/bold] {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"[bold]Severity:[/bold] {self.severity.upper()}",
            "",
            f"[bold]Message:[/bold]",
            self.message,
        ]
        
        if self.details:
            lines.extend(["", "[bold]Details:[/bold]", self.details])
        
        if self.context:
            lines.extend(["", "[bold]Context:[/bold]"])
            for key, value in self.context.items():
                lines.append(f"  {key}: {value}")
        
        if self.traceback_str:
            lines.extend(["", "[bold]Traceback:[/bold]", self.traceback_str])
        
        return "\n".join(lines)


class ErrorLog:
    """Manages application error log."""
    
    def __init__(self, max_entries: int = 100):
        self.max_entries = max_entries
        self.entries: List[ErrorEntry] = []
    
    def add_error(
        self,
        message: str,
        severity: str = "error",
        details: str = "",
        exception: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ErrorEntry:
        """Add an error to the log."""
        entry = ErrorEntry(
            timestamp=datetime.now(),
            severity=severity,
            message=message,
            details=details,
            context=context or {},
        )
        
        if exception:
            entry.traceback_str = "".join(traceback.format_exception(
                type(exception), exception, exception.__traceback__
            ))
        
        self.entries.insert(0, entry)  # Most recent first
        
        # Keep only max_entries
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[:self.max_entries]
        
        return entry
    
    def get_entries(self, severity: Optional[str] = None, limit: Optional[int] = None) -> List[ErrorEntry]:
        """Get error entries, optionally filtered."""
        entries = self.entries
        
        if severity:
            entries = [e for e in entries if e.severity == severity]
        
        if limit:
            entries = entries[:limit]
        
        return entries
    
    def clear(self) -> None:
        """Clear all errors."""
        self.entries.clear()
    
    def export_to_file(self, filepath: Path) -> None:
        """Export errors to a text file."""
        with open(filepath, "w") as f:
            for entry in self.entries:
                f.write("=" * 80 + "\n")
                f.write(entry.format_full() + "\n\n")
