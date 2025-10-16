#!/usr/bin/env python3
"""Test script to verify TUI functionality."""

import sys
from pathlib import Path

def test_imports():
    """Test all imports work."""
    print("Testing imports...")
    try:
        from claude_code_config import ConfigManager, ClaudeConfig
        from claude_code_config.models import McpServer, Project, Conversation
        from claude_code_config.tui import ClaudeConfigApp, ConfirmDialog, ServerFormScreen
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_models():
    """Test model creation and serialization."""
    print("\nTesting models...")
    try:
        from claude_code_config.models import McpServer, Project, ClaudeConfig

        # Test McpServer
        server = McpServer(
            name="test-server",
            command="npx",
            args=["-y", "test"],
            env={"KEY": "${KEY}"}
        )
        server_dict = server.to_dict()
        assert "command" in server_dict
        assert server.copy().name == "test-server"
        print("  ✓ McpServer works")

        # Test Project
        project = Project(
            path="/test/path",
            mcp_servers={"test": server},
            conversations={},
            other_settings={}
        )
        project_dict = project.to_dict()
        assert "mcpServers" in project_dict
        print("  ✓ Project works")

        # Test ClaudeConfig
        config = ClaudeConfig(
            global_mcp_servers={"global_test": server},
            projects={"/test": project},
            other_settings={"numStartups": 1}
        )
        config_dict = config.to_dict()
        assert "mcpServers" in config_dict
        assert "projects" in config_dict
        assert "numStartups" in config_dict

        global_count, project_count = config.count_servers()
        assert global_count == 1
        assert project_count == 1

        all_servers = config.get_all_servers()
        assert len(all_servers) == 2
        print("  ✓ ClaudeConfig works")

        return True
    except Exception as e:
        print(f"  ✗ Model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_manager():
    """Test config manager with a test file."""
    print("\nTesting ConfigManager...")
    try:
        import tempfile
        import json
        from claude_code_config import ConfigManager

        # Create a test config file
        test_data = {
            "mcpServers": {
                "test": {
                    "command": "test",
                    "args": [],
                    "env": {}
                }
            },
            "projects": {
                "/test/path": {
                    "mcpServers": {
                        "project_server": {
                            "command": "npx",
                            "args": ["test"],
                            "env": {}
                        }
                    },
                    "conversations": {},
                    "other": "data"
                }
            },
            "numStartups": 1
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = Path(f.name)

        try:
            # Test loading
            manager = ConfigManager(temp_path)
            config = manager.load()
            assert len(config.global_mcp_servers) == 1
            assert len(config.projects) == 1
            print("  ✓ Load works")

            # Test validation
            is_valid, error = manager.validate()
            assert is_valid, f"Validation failed: {error}"
            print("  ✓ Validation works")

            # Test modification
            manager.mark_modified()
            assert manager.modified
            print("  ✓ Modification tracking works")

            # Test save
            manager.save()
            assert not manager.modified
            print("  ✓ Save works")

            # Verify backup was created
            backups = manager.list_backups()
            assert len(backups) > 0
            print("  ✓ Backup creation works")

            return True
        finally:
            temp_path.unlink()
            # Clean up backups
            if manager.backup_dir.exists():
                for backup in manager.backup_dir.iterdir():
                    backup.unlink()
                manager.backup_dir.rmdir()

    except Exception as e:
        print(f"  ✗ ConfigManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Claude Config Manager - Test Suite")
    print("=" * 60)

    tests = [
        test_imports,
        test_models,
        test_config_manager,
    ]

    results = [test() for test in tests]

    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)

    if all(results):
        print("\n✓ All tests passed! The application is ready to use.")
        print("\nTry it now:")
        print("  claude-config")
        return 0
    else:
        print("\n✗ Some tests failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
