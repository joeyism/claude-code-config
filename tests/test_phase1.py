"""Tests for Phase 1 UX improvements."""

import pytest
from claude_code_config.undo import UndoManager, UndoSnapshot
from claude_code_config.error_log import ErrorLog, ErrorEntry
from claude_code_config.models import ClaudeConfig, McpServer


class TestUndoManager:
    """Test undo/redo functionality."""
    
    def test_save_snapshot(self):
        """Test saving a snapshot."""
        manager = UndoManager(max_history=10)
        config = ClaudeConfig()
        
        manager.save_snapshot(config, "Test action")
        
        assert manager.can_undo()
        assert not manager.can_redo()
        assert len(manager.undo_stack) == 1
    
    def test_undo(self):
        """Test undo operation."""
        manager = UndoManager()
        config = ClaudeConfig()
        
        # Add server to config
        server1 = McpServer(name="server1", command="cmd1")
        config.global_mcp_servers["server1"] = server1
        manager.save_snapshot(config, "Add server1")
        
        # Add another server
        server2 = McpServer(name="server2", command="cmd2")
        config.global_mcp_servers["server2"] = server2
        manager.save_snapshot(config, "Add server2")
        
        # Undo
        snapshot = manager.undo(config)
        assert snapshot is not None
        assert "Add server1" in snapshot.description
        assert manager.can_redo()
    
    def test_redo(self):
        """Test redo operation."""
        manager = UndoManager()
        config = ClaudeConfig()
        
        manager.save_snapshot(config, "Initial")
        manager.undo(config)
        
        snapshot = manager.redo()
        assert snapshot is not None
        assert not manager.can_redo()
    
    def test_max_history(self):
        """Test that history is limited."""
        manager = UndoManager(max_history=3)
        config = ClaudeConfig()
        
        for i in range(5):
            manager.save_snapshot(config, f"Action {i}")
        
        assert len(manager.undo_stack) == 3
    
    def test_clear(self):
        """Test clearing undo/redo stacks."""
        manager = UndoManager()
        config = ClaudeConfig()
        
        manager.save_snapshot(config, "Test")
        manager.clear()
        
        assert not manager.can_undo()
        assert not manager.can_redo()


class TestErrorLog:
    """Test error logging functionality."""
    
    def test_add_error(self):
        """Test adding an error."""
        log = ErrorLog(max_entries=10)
        
        entry = log.add_error("Test error", severity="error")
        
        assert entry.message == "Test error"
        assert entry.severity == "error"
        assert len(log.entries) == 1
    
    def test_add_error_with_exception(self):
        """Test adding error with exception."""
        log = ErrorLog()
        
        try:
            raise ValueError("Test exception")
        except ValueError as e:
            entry = log.add_error("Error occurred", exception=e)
        
        assert "ValueError" in entry.traceback_str
        assert "Test exception" in entry.traceback_str
    
    def test_max_entries(self):
        """Test that entries are limited."""
        log = ErrorLog(max_entries=3)
        
        for i in range(5):
            log.add_error(f"Error {i}")
        
        assert len(log.entries) == 3
        # Most recent first
        assert log.entries[0].message == "Error 4"
    
    def test_get_entries_filtered(self):
        """Test filtering entries by severity."""
        log = ErrorLog()
        
        log.add_error("Error 1", severity="error")
        log.add_error("Warning 1", severity="warning")
        log.add_error("Error 2", severity="error")
        
        errors = log.get_entries(severity="error")
        assert len(errors) == 2
        
        warnings = log.get_entries(severity="warning")
        assert len(warnings) == 1
    
    def test_clear(self):
        """Test clearing the log."""
        log = ErrorLog()
        
        log.add_error("Test")
        log.clear()
        
        assert len(log.entries) == 0
    
    def test_format_short(self):
        """Test short formatting."""
        log = ErrorLog()
        entry = log.add_error("Test error message")
        
        short = entry.format_short()
        assert "Test error message" in short
        assert "🔴" in short
    
    def test_format_full(self):
        """Test full formatting."""
        log = ErrorLog()
        entry = log.add_error(
            "Test error",
            details="More details",
            context={"file": "test.py"}
        )
        
        full = entry.format_full()
        assert "Test error" in full
        assert "More details" in full
        assert "file" in full
        assert "test.py" in full


class TestUndoSnapshot:
    """Test UndoSnapshot functionality."""
    
    def test_format_display(self):
        """Test snapshot display formatting."""
        from datetime import datetime
        
        snapshot = UndoSnapshot(
            timestamp=datetime.now(),
            description="Delete server 'test'",
            config_state={},
            selected_node=None
        )
        
        display = snapshot.format_display()
        assert "Delete server 'test'" in display
        assert "[" in display  # Contains timestamp


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
