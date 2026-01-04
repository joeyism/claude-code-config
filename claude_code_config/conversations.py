"""Conversation file management for Claude Code."""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class ConversationFile:
    """Represents a Claude Code conversation file."""
    
    file_path: Path
    conversation_id: str
    project_path: str
    title: Optional[str] = None
    created_at: Optional[datetime] = None
    message_count: int = 0
    file_size: int = 0
    
    @classmethod
    def from_file(cls, file_path: Path, project_path: str) -> "ConversationFile":
        """Create ConversationFile from a .jsonl file."""
        conversation_id = file_path.stem
        
        # Get file stats
        file_size = file_path.stat().st_size if file_path.exists() else 0
        
        # Parse first few lines to get metadata
        title = None
        created_at = None
        message_count = 0
        
        try:
            with open(file_path, 'r') as f:
                for i, line in enumerate(f):
                    if i > 50:  # Only read first 50 lines for performance
                        break
                    try:
                        data = json.loads(line.strip())
                        message_count += 1
                        
                        # Look for title in various places
                        if not title:
                            if 'title' in data:
                                title = data['title']
                            elif 'content' in data and isinstance(data['content'], str):
                                # Use first user message as title
                                if data.get('role') == 'user':
                                    title = data['content'][:100]
                        
                        # Look for timestamp
                        if not created_at and 'timestamp' in data:
                            try:
                                created_at = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
                            except:
                                pass
                    except json.JSONDecodeError:
                        continue
                
                # Count remaining lines efficiently
                for _ in f:
                    message_count += 1
        except Exception:
            pass  # File might be corrupted or locked
        
        # If no title found, use conversation ID
        if not title:
            title = f"Conversation {conversation_id[:8]}"
        
        return cls(
            file_path=file_path,
            conversation_id=conversation_id,
            project_path=project_path,
            title=title,
            created_at=created_at,
            message_count=message_count,
            file_size=file_size,
        )
    
    def get_display_title(self, max_length: int = 60) -> str:
        """Get a display-friendly title."""
        if not self.title:
            return f"Conversation {self.conversation_id[:8]}"
        
        title = self.title.strip()
        if len(title) > max_length:
            return title[:max_length] + "..."
        return title
    
    def get_size_str(self) -> str:
        """Get human-readable file size."""
        size = self.file_size
        for unit in ['B', 'KB', 'MB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} GB"
    
    def get_age_str(self) -> str:
        """Get human-readable age."""
        if not self.created_at:
            return "Unknown"
        
        delta = datetime.now() - self.created_at.replace(tzinfo=None)
        
        if delta.days > 365:
            years = delta.days // 365
            return f"{years} year{'s' if years > 1 else ''} ago"
        elif delta.days > 30:
            months = delta.days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
        elif delta.days > 0:
            return f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        else:
            minutes = delta.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    
    def delete(self) -> bool:
        """Delete the conversation file."""
        try:
            self.file_path.unlink()
            return True
        except Exception:
            return False


class ConversationScanner:
    """Scans and manages Claude Code conversations."""
    
    def __init__(self, claude_dir: Optional[Path] = None):
        """Initialize scanner.
        
        Args:
            claude_dir: Path to .claude directory. Defaults to ~/.claude
        """
        if claude_dir is None:
            claude_dir = Path.home() / ".claude"
        
        self.claude_dir = Path(claude_dir)
        self.projects_dir = self.claude_dir / "projects"
    
    def scan_all_conversations(self) -> Dict[str, List[ConversationFile]]:
        """Scan all conversations grouped by project.
        
        Returns:
            Dict mapping project path to list of ConversationFile objects
        """
        conversations = {}
        
        if not self.projects_dir.exists():
            return conversations
        
        for project_dir in self.projects_dir.iterdir():
            if not project_dir.is_dir():
                continue
            
            # Convert directory name back to project path
            # Example: -home-joeyism-Programming-python-project -> /home/joeyism/Programming/python/project
            project_name = project_dir.name
            if project_name.startswith('-'):
                project_path = project_name.replace('-', '/', 1).replace('-', '/')
            else:
                project_path = project_name
            
            # Find all .jsonl files
            jsonl_files = list(project_dir.glob("*.jsonl"))
            
            if jsonl_files:
                project_conversations = []
                for jsonl_file in jsonl_files:
                    conv = ConversationFile.from_file(jsonl_file, project_path)
                    project_conversations.append(conv)
                
                # Sort by creation date (newest first)
                # Handle timezone-aware and naive datetimes
                project_conversations.sort(
                    key=lambda c: c.created_at.replace(tzinfo=None) if c.created_at else datetime.min,
                    reverse=True
                )
                
                conversations[project_path] = project_conversations
        
        return conversations
    
    def get_project_conversations(self, project_path: str) -> List[ConversationFile]:
        """Get conversations for a specific project.
        
        Args:
            project_path: Full path to the project
            
        Returns:
            List of ConversationFile objects
        """
        all_convos = self.scan_all_conversations()
        return all_convos.get(project_path, [])
    
    def get_stats(self) -> Dict[str, int]:
        """Get overall statistics.
        
        Returns:
            Dict with total_conversations, total_projects, total_size
        """
        all_convos = self.scan_all_conversations()
        
        total_conversations = sum(len(convos) for convos in all_convos.values())
        total_projects = len(all_convos)
        total_size = sum(
            conv.file_size
            for convos in all_convos.values()
            for conv in convos
        )
        
        return {
            'total_conversations': total_conversations,
            'total_projects': total_projects,
            'total_size': total_size,
        }
