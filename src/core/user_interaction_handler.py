"""User Interaction Handler for file conflict resolution.

This module provides the UserInteractionHandler class that handles:
- Rich console integration for beautiful conflict prompts
- File preview functionality with syntax highlighting
- User choice persistence and "skip all" functionality
- Conflict resolution with multiple options
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union
import logging

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from .file_manager import FileConflict, ConflictType


class UserChoice(Enum):
    """User choices for file conflict resolution."""
    
    SKIP = "skip"                    # Skip this file, keep it
    DELETE = "delete"                # Delete this file
    PREVIEW = "preview"              # Show file preview
    SKIP_ALL = "skip_all"            # Skip all remaining conflicts
    DELETE_ALL = "delete_all"        # Delete all remaining conflicts
    QUIT = "quit"                    # Quit the operation


@dataclass
class ConflictResolution:
    """Result of user conflict resolution."""
    
    conflict: FileConflict
    choice: UserChoice
    apply_to_all: bool = False
    
    @property
    def should_delete(self) -> bool:
        """Check if file should be deleted."""
        return self.choice in [UserChoice.DELETE, UserChoice.DELETE_ALL]
    
    @property
    def should_skip(self) -> bool:
        """Check if file should be skipped."""
        return self.choice in [UserChoice.SKIP, UserChoice.SKIP_ALL]


class UserInteractionHandler:
    """Handles user interactions for file conflict resolution."""
    
    def __init__(self, console: Optional[Console] = None):
        """Initialize user interaction handler.
        
        Args:
            console: Optional Rich console instance. Creates new one if None.
        """
        self.console = console or Console()
        self.logger = logging.getLogger(__name__)
        
        # State management for "apply to all" functionality
        self._skip_all = False
        self._delete_all = False
        self._quit_requested = False
    
    def resolve_conflicts(self, conflicts: List[FileConflict]) -> List[ConflictResolution]:
        """Resolve file conflicts through user interaction.
        
        Args:
            conflicts: List of file conflicts to resolve
            
        Returns:
            List of conflict resolutions
        """
        if not conflicts:
            return []
        
        resolutions = []
        self.console.print(f"\n[yellow]Found {len(conflicts)} file conflicts to resolve.[/yellow]")
        
        for i, conflict in enumerate(conflicts, 1):
            if self._quit_requested:
                break
                
            # Apply previous "all" choices
            if self._skip_all:
                resolution = ConflictResolution(conflict, UserChoice.SKIP_ALL, True)
                resolutions.append(resolution)
                continue
                
            if self._delete_all:
                resolution = ConflictResolution(conflict, UserChoice.DELETE_ALL, True)
                resolutions.append(resolution)
                continue
            
            # Show conflict details
            self._show_conflict_header(conflict, i, len(conflicts))
            
            # Get user choice
            choice = self._prompt_user_choice(conflict)
            
            # Handle choice
            resolution = self._handle_user_choice(conflict, choice)
            resolutions.append(resolution)
            
            # Update state based on choice
            self._update_state(choice)
        
        return resolutions
    
    def _show_conflict_header(self, conflict: FileConflict, current: int, total: int) -> None:
        """Show conflict information header."""
        conflict_info = f"Conflict {current}/{total}: {conflict.conflict_type.value}"
        file_info = f"File: {conflict.file_path}"
        
        if conflict.details:
            details = f"Details: {conflict.details}"
        else:
            details = ""
        
        panel_content = f"[bold]{conflict_info}[/bold]\n{file_info}"
        if details:
            panel_content += f"\n{details}"
        
        self.console.print(Panel(panel_content, border_style="yellow"))
    
    def _prompt_user_choice(self, conflict: FileConflict) -> UserChoice:
        """Prompt user for choice on how to handle conflict.
        
        Args:
            conflict: File conflict to resolve
            
        Returns:
            User's choice
        """
        choices = {
            "s": UserChoice.SKIP,
            "d": UserChoice.DELETE,
            "p": UserChoice.PREVIEW,
            "sa": UserChoice.SKIP_ALL,
            "da": UserChoice.DELETE_ALL,
            "q": UserChoice.QUIT
        }
        
        choice_text = (
            "[s]kip, [d]elete, [p]review, "
            "[sa]kip all, [da]elete all, [q]uit"
        )
        
        while True:
            choice_input = Prompt.ask(
                f"What would you like to do? ({choice_text})",
                default="s"
            ).lower().strip()
            
            if choice_input in choices:
                choice = choices[choice_input]
                
                # Handle preview choice
                if choice == UserChoice.PREVIEW:
                    self._show_file_preview(conflict.file_path)
                    continue  # Ask again after preview
                
                return choice
            
            self.console.print("[red]Invalid choice. Please try again.[/red]")
    
    def _show_file_preview(self, file_path: Path) -> None:
        """Show file preview with syntax highlighting.
        
        Args:
            file_path: Path to file to preview
        """
        try:
            if not file_path.exists():
                self.console.print(f"[red]File does not exist: {file_path}[/red]")
                return
            
            # Read file content
            content = file_path.read_text(encoding='utf-8', errors='replace')
            
            # Limit preview size
            max_lines = 50
            lines = content.splitlines()
            if len(lines) > max_lines:
                content = '\n'.join(lines[:max_lines])
                content += f"\n... ({len(lines) - max_lines} more lines)"
            
            # Determine file type for syntax highlighting
            suffix = file_path.suffix.lower()
            lexer_map = {
                '.py': 'python',
                '.js': 'javascript',
                '.ts': 'typescript',
                '.html': 'html',
                '.css': 'css',
                '.json': 'json',
                '.md': 'markdown',
                '.yml': 'yaml',
                '.yaml': 'yaml',
                '.xml': 'xml',
                '.sh': 'bash',
                '.ps1': 'powershell'
            }
            
            lexer = lexer_map.get(suffix, 'text')
            
            # Create syntax highlighted preview
            syntax = Syntax(content, lexer, theme="monokai", line_numbers=True)
            
            # Show in panel
            self.console.print(Panel(
                syntax,
                title=f"Preview: {file_path.name}",
                border_style="blue"
            ))
            
        except Exception as e:
            self.console.print(f"[red]Error previewing file: {e}[/red]")
            self.logger.error(f"Error previewing file {file_path}: {e}")
    
    def _handle_user_choice(self, conflict: FileConflict, choice: UserChoice) -> ConflictResolution:
        """Handle user choice and create resolution.
        
        Args:
            conflict: File conflict
            choice: User's choice
            
        Returns:
            Conflict resolution
        """
        apply_to_all = choice in [UserChoice.SKIP_ALL, UserChoice.DELETE_ALL]
        
        resolution = ConflictResolution(
            conflict=conflict,
            choice=choice,
            apply_to_all=apply_to_all
        )
        
        # Log the choice
        action = "skip" if resolution.should_skip else "delete" if resolution.should_delete else choice.value
        self.logger.info(f"User chose to {action} file: {conflict.file_path}")
        
        return resolution
    
    def _update_state(self, choice: UserChoice) -> None:
        """Update handler state based on user choice.
        
        Args:
            choice: User's choice
        """
        if choice == UserChoice.SKIP_ALL:
            self._skip_all = True
        elif choice == UserChoice.DELETE_ALL:
            self._delete_all = True
        elif choice == UserChoice.QUIT:
            self._quit_requested = True
    
    def reset_state(self) -> None:
        """Reset handler state."""
        self._skip_all = False
        self._delete_all = False
        self._quit_requested = False
    
    @property
    def quit_requested(self) -> bool:
        """Check if user requested to quit."""
        return self._quit_requested