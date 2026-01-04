"""Undo/redo functionality for configuration changes."""

import copy
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class UndoSnapshot:
    """Represents a state snapshot for undo/redo."""
    
    timestamp: datetime
    description: str
    config_state: Dict[str, Any]  # Serialized ClaudeConfig
    selected_node: Optional[Dict[str, Any]]  # What was selected
    
    def format_display(self) -> str:
        """Format for display in undo history."""
        time_str = self.timestamp.strftime("%H:%M:%S")
        return f"[{time_str}] {self.description}"


class UndoManager:
    """Manages undo/redo state for config changes."""
    
    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self.undo_stack: List[UndoSnapshot] = []
        self.redo_stack: List[UndoSnapshot] = []
    
    def save_snapshot(
        self,
        config,  # ClaudeConfig
        description: str,
        selected_node: Optional[Dict[str, Any]] = None
    ) -> None:
        """Save current state for undo."""
        snapshot = UndoSnapshot(
            timestamp=datetime.now(),
            description=description,
            config_state=config.to_dict(),
            selected_node=copy.deepcopy(selected_node) if selected_node else None
        )
        
        self.undo_stack.append(snapshot)
        
        # Clear redo stack when new action performed
        self.redo_stack.clear()
        
        # Limit stack size
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)
    
    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self.undo_stack) > 0
    
    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self.redo_stack) > 0
    
    def undo(self, current_config, current_node: Optional[Dict[str, Any]] = None) -> Optional[UndoSnapshot]:
        """Undo last action."""
        if not self.can_undo():
            return None
        
        # Save current state to redo stack
        current_snapshot = UndoSnapshot(
            timestamp=datetime.now(),
            description="(current state)",
            config_state=current_config.to_dict(),
            selected_node=copy.deepcopy(current_node) if current_node else None
        )
        self.redo_stack.append(current_snapshot)
        
        # Pop and return previous state
        return self.undo_stack.pop()
    
    def redo(self) -> Optional[UndoSnapshot]:
        """Redo previously undone action."""
        if not self.can_redo():
            return None
        
        snapshot = self.redo_stack.pop()
        self.undo_stack.append(snapshot)
        return snapshot
    
    def get_undo_history(self) -> List[str]:
        """Get list of undoable actions."""
        return [s.format_display() for s in reversed(self.undo_stack)]
    
    def get_redo_history(self) -> List[str]:
        """Get list of redoable actions."""
        return [s.format_display() for s in reversed(self.redo_stack)]
    
    def clear(self) -> None:
        """Clear all undo/redo history."""
        self.undo_stack.clear()
        self.redo_stack.clear()
