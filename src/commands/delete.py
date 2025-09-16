"""Delete command implementation for Improved-SDD CLI.

This module contains the delete command logic for removing installed templates
from development environments using AI tool-specific file management.
"""

from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Import configuration and core components
from core import (
    APP_TYPES, 
    AIToolManager, 
    FileManager, 
    UserInteractionHandler,
    config
)

# Import UI components  
from ui import console_manager

# Import shared utilities
from utils import select_app_type


def delete_command(
    app_type: str = typer.Argument(None, help="App type to delete files for: mcp-server, python-cli"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview what would be deleted without actually deleting"),
):
    """
    Delete Improved-SDD templates for a specific app type using AI tool-specific file management.

    This command will:
    1. Identify AI tool-managed files for the specified app type
    2. Show files grouped by AI tool 
    3. Handle conflicts for files that exist but aren't managed
    4. Require confirmation (unless --force is used)
    5. Safely delete only the managed files

    Examples:
        improved-sdd delete mcp-server
        improved-sdd delete python-cli --force
        improved-sdd delete python-cli --dry-run
    """

    # Show banner first
    console_manager.show_banner()

    # Validate app type
    if app_type:
        if app_type not in APP_TYPES:
            console_manager.print_error(f"Invalid app type '{app_type}'. Choose from: {', '.join(APP_TYPES.keys())}")
            raise typer.Exit(1)
        selected_app_type = app_type
    else:
        selected_app_type = select_app_type()

    # Get project path (current directory)
    project_path = Path.cwd()

    try:
        # Initialize core components
        ai_tool_manager = AIToolManager(config)
        file_manager = FileManager(ai_tool_manager)
        console = Console()
        user_interaction = UserInteractionHandler(console)

        # Discover files and detect conflicts
        console_manager.print_info(f"Analyzing {selected_app_type} files...")
        
        discovery_result = file_manager.discover_files(
            project_root=project_path,
            active_tools=None,  # Auto-detect active tools
            app_type=selected_app_type
        )

        # Check if there are any managed files to delete
        if not discovery_result.managed_files_found:
            console_manager.print_warning(f"No managed files found for app type '{selected_app_type}'")
            console_manager.print("This could mean:")
            console_manager.print("  • No AI tools are currently configured")
            console_manager.print("  • No managed files exist for the selected app type")
            console_manager.print("  • Files may have been deleted already")
            return

        # Show files grouped by AI tool
        _show_managed_files_preview(discovery_result, selected_app_type, project_path)

        # Handle conflicts if any exist
        files_to_delete = discovery_result.managed_files_found.copy()
        if discovery_result.conflicts:
            console_manager.print_warning(f"Found {len(discovery_result.conflicts)} file conflicts that need resolution")
            
            if force:
                console_manager.print_info("Force mode enabled - skipping all conflicted files")
                # In force mode, skip all conflicted files
            else:
                # Resolve conflicts through user interaction
                conflict_resolutions = user_interaction.resolve_conflicts(discovery_result.conflicts)
                
                # Check if user quit
                if user_interaction.quit_requested:
                    console_manager.print_warning("Operation cancelled by user")
                    return
                
                # Add files that user chose to delete
                for resolution in conflict_resolutions:
                    if resolution.should_delete:
                        files_to_delete.append(resolution.conflict.file_path)

        # Final confirmation if not in force mode and not dry run
        if not force and not dry_run and files_to_delete:
            console_manager.print(f"\n[bold yellow]Ready to delete {len(files_to_delete)} files[/bold yellow]")
            console_manager.print("[bold yellow][WARN]  This action cannot be undone![/bold yellow]")
            confirmation = typer.prompt("Type 'Yes' to confirm deletion", type=str, default="")
            if confirmation != "Yes":
                console_manager.print_warning("Deletion cancelled")
                return

        # Perform deletion (or dry run)
        if files_to_delete:
            deletion_result = file_manager.safe_delete_files(files_to_delete, dry_run=dry_run)
            
            # Show results
            _show_deletion_results(deletion_result, dry_run, project_path)
            
            # Clean up empty directories
            if not dry_run and deletion_result.success_count > 0:
                _cleanup_empty_directories(project_path, selected_app_type)
        else:
            console_manager.print_info("No files selected for deletion")

    except Exception as e:
        console_manager.print_error(f"Error during deletion: {e}")
        raise typer.Exit(1)


def _show_managed_files_preview(discovery_result, app_type: str, project_path: Path) -> None:
    """Show preview of managed files grouped by AI tool."""
    console = Console()
    
    # Group files by AI tool
    tool_files = {}
    for file_path in discovery_result.managed_files_found:
        # Determine which AI tool manages this file
        # For now, we'll show all managed files together
        # In future iterations, this could be enhanced to show per-tool grouping
        if "managed" not in tool_files:
            tool_files["managed"] = []
        tool_files["managed"].append(file_path)
    
    console_manager.print(f"\n[bold blue]Managed files to delete for '{app_type}':[/bold blue]")
    
    if tool_files:
        for tool_name, files in tool_files.items():
            console_manager.print(f"\n[cyan]Files ({len(files)} total):[/cyan]")
            for file_path in sorted(files):
                relative_path = file_path.relative_to(project_path)
                console_manager.print(f"  🗑️  {relative_path}")
    
    console_manager.print()


def _show_deletion_results(deletion_result, dry_run: bool, project_path: Path) -> None:
    """Show comprehensive deletion results."""
    action = "Would delete" if dry_run else "Deleted"
    mode = "DRY RUN - " if dry_run else ""
    
    console_manager.print(f"\n[bold green]{mode}Deletion Results:[/bold green]")
    
    # Success summary
    if deletion_result.success_count > 0:
        console_manager.print(f"[green]✓ {action}: {deletion_result.success_count} files[/green]")
        for file_path in deletion_result.deleted_files:
            relative_path = file_path.relative_to(project_path)
            console_manager.print(f"  ✓ {relative_path}")
    
    # Failures
    if deletion_result.failure_count > 0:
        console_manager.print(f"\n[red]✗ Failed: {deletion_result.failure_count} files[/red]")
        for attempt in deletion_result.failed_deletions:
            relative_path = attempt.file_path.relative_to(project_path)
            console_manager.print(f"  ✗ {relative_path}: {attempt.error_message}")
    
    # Skipped files
    if deletion_result.skip_count > 0:
        console_manager.print(f"\n[yellow]⚠ Skipped: {deletion_result.skip_count} files[/yellow]")
        for file_path in deletion_result.skipped_files:
            relative_path = file_path.relative_to(project_path)
            console_manager.print(f"  ⚠ {relative_path}")
    
    # Overall statistics
    console_manager.print(f"\n[bold]Success rate: {deletion_result.success_rate:.1f}%[/bold]")


def _cleanup_empty_directories(project_path: Path, app_type: str) -> None:
    """Clean up empty directories after file deletion."""
    try:
        # Standard template directories that might be empty
        template_dirs = [
            ".github/chatmodes",
            ".github/instructions", 
            ".github/prompts",
            ".github/commands"
        ]
        
        dirs_removed = []
        
        for dir_path_str in template_dirs:
            dir_path = project_path / dir_path_str
            if dir_path.exists() and dir_path.is_dir():
                # Check if directory is empty
                if not any(dir_path.iterdir()):
                    dir_path.rmdir()
                    dirs_removed.append(dir_path_str)
        
        # Check if .github is empty
        github_dir = project_path / ".github"
        if github_dir.exists() and github_dir.is_dir():
            if not any(github_dir.iterdir()):
                github_dir.rmdir()
                dirs_removed.append(".github")
        
        if dirs_removed:
            console_manager.print_info(f"Cleaned up {len(dirs_removed)} empty directories")
            
    except Exception as e:
        console_manager.print_warning(f"Warning: Could not clean up empty directories: {e}")


# Backward compatibility - keep the old function signature available
def delete_templates(app_type: str, force: bool = False) -> None:
    """
    Legacy function for backward compatibility.
    
    Args:
        app_type: Application type to delete files for
        force: Skip confirmation prompt
    """
    delete_command(app_type=app_type, force=force, dry_run=False)
