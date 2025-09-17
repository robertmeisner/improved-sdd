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
        with console.status("[bold blue]Analyzing project files...", spinner="dots") as status:
            console_manager.print_info(f"[SCAN] Analyzing {selected_app_type} files...")
            
            discovery_result = file_manager.discover_files(
                project_root=project_path,
                active_tools=None,  # Auto-detect active tools
                app_type=selected_app_type
            )
            
            status.update(f"[bold green]Found {len(discovery_result.discovered_files)} files to analyze")
            
            # Brief pause to show the status
            import time
            time.sleep(0.5)

        # Check if there are any managed files to delete
        if not discovery_result.managed_files_found:
            from rich.panel import Panel
            
            # Get more context about why no files were found
            active_tools_result = ai_tool_manager.detect_active_tools(project_path)
            active_tools = active_tools_result.active_tools
            
            # Create informative "no files" message
            no_files_content = f"[bold yellow]No managed files found for app type '{selected_app_type}'[/bold yellow]\n\n"
            
            if not active_tools:
                no_files_content += "[red][X] No AI tools are currently configured[/red]\n"
                no_files_content += "[TIP] Run [bold cyan]improved-sdd init[/bold cyan] to set up AI tools\n"
            else:
                tool_names = [ai_tool_manager.get_tool_info(tool_id).name for tool_id in active_tools 
                             if ai_tool_manager.get_tool_info(tool_id)]
                no_files_content += f"[green][OK] Active AI tools:[/green] {', '.join(tool_names)}\n\n"
                
                no_files_content += "[bold]Possible reasons:[/bold]\n"
                no_files_content += "• No managed files exist for the selected app type\n"
                no_files_content += "• Files may have been deleted already\n"
                no_files_content += "• AI tools don't define managed files for this app type\n"
                no_files_content += "• Template files are in a different directory structure\n\n"
                
                no_files_content += "[bold]What you can do:[/bold]\n"
                no_files_content += f"• Run [bold cyan]improved-sdd init {selected_app_type}[/bold cyan] to install templates\n"
                no_files_content += "• Check if files exist in different app type directories\n"
                no_files_content += "• Use [bold cyan]improved-sdd delete --dry-run[/bold cyan] to preview without changes"
            
            console = Console()
            console.print(Panel(
                no_files_content.strip(),
                title="[INFO] No Files to Delete",
                border_style="yellow",
                padding=(1, 2)
            ))
            return

        # Show files grouped by AI tool
        _show_managed_files_preview(discovery_result, selected_app_type, project_path)

        # Handle conflicts if any exist
        files_to_delete = discovery_result.managed_files_found.copy()
        if discovery_result.conflicts:
            from rich.panel import Panel
            
            conflict_count = len(discovery_result.conflicts)
            console_manager.print_warning(f"[CONFLICT] Found {conflict_count} file conflict{'' if conflict_count == 1 else 's'} that need resolution")
            
            # Show brief conflict summary
            conflict_types = {}
            for conflict in discovery_result.conflicts:
                conflict_type = conflict.conflict_type.value
                conflict_types[conflict_type] = conflict_types.get(conflict_type, 0) + 1
            
            conflict_summary = "Conflict types:\n"
            for conflict_type, count in conflict_types.items():
                conflict_summary += f"• {conflict_type.replace('_', ' ').title()}: {count}\n"
            
            console = Console()
            console.print(Panel(
                conflict_summary.strip(),
                title="[WARNING] File Conflicts Detected",
                border_style="yellow",
                padding=(0, 1)
            ))
            
            if force:
                console_manager.print_info("[FORCE] Force mode enabled - skipping all conflicted files")
                # In force mode, skip all conflicted files
            else:
                console_manager.print_info("[RESOLVE] Let's resolve these conflicts together...")
                # Resolve conflicts through user interaction
                conflict_resolutions = user_interaction.resolve_conflicts(discovery_result.conflicts)
                
                # Check if user quit
                if user_interaction.quit_requested:
                    console_manager.print_warning("[CANCEL] Operation cancelled by user")
                    return
                
                # Add files that user chose to delete
                resolved_count = 0
                for resolution in conflict_resolutions:
                    if resolution.should_delete:
                        files_to_delete.append(resolution.conflict.file_path)
                        resolved_count += 1
                
                console_manager.print_info(f"[OK] Resolved {len(conflict_resolutions)} conflicts - {resolved_count} files will be deleted")

        # Final confirmation if not in force mode and not dry run
        if not force and not dry_run and files_to_delete:
            from rich.panel import Panel
            
            confirm_content = f"""
[bold yellow][WARNING] Ready to delete {len(files_to_delete)} files[/bold yellow]

[bold red][DANGER] WARNING: This action cannot be undone![/bold red]

Files will be permanently removed from your project.
Review the file list above before confirming.

Type [bold cyan]'Yes'[/bold cyan] (case-sensitive) to proceed with deletion.
Press Enter or type anything else to cancel.
"""
            
            console = Console()
            console.print(Panel(
                confirm_content.strip(),
                title="[CONFIRM] Final Confirmation Required",
                border_style="red",
                padding=(1, 2)
            ))
            
            confirmation = typer.prompt("Confirm deletion", type=str, default="")
            if confirmation != "Yes":
                console_manager.print_warning("[CANCEL] Deletion cancelled - no files were harmed!")
                return

        # Perform deletion (or dry run)
        if files_to_delete:
            if dry_run:
                console_manager.print_info("[DRY-RUN] Starting dry run - no files will actually be deleted")
            else:
                console_manager.print_info(f"[DELETE] Starting deletion of {len(files_to_delete)} files...")
            
            # Show progress during deletion
            with console.status("[bold blue]Processing files...", spinner="dots") as status:
                deletion_result = file_manager.safe_delete_files(files_to_delete, dry_run=dry_run)
                
                # Update status with results
                if dry_run:
                    status.update(f"[bold green]Dry run complete - analyzed {len(files_to_delete)} files")
                else:
                    status.update(f"[bold green]Deletion complete - processed {deletion_result.total_processed} files")
                
                # Brief pause to show final status
                import time
                time.sleep(0.5)
            
            # Show results
            _show_deletion_results(deletion_result, dry_run, project_path)
            
            # Clean up empty directories
            if not dry_run and deletion_result.success_count > 0:
                console_manager.print_info("[CLEANUP] Cleaning up empty directories...")
                _cleanup_empty_directories(project_path, selected_app_type)
        else:
            from rich.panel import Panel
            
            no_action_content = """
[bold yellow][INFO] No files selected for deletion[/bold yellow]

This could happen when:
• All conflicted files were preserved by user choice
• Force mode skipped all conflicted files
• No managed files were found to begin with

Your project files remain unchanged. [OK]
"""
            
            console = Console()
            console.print(Panel(
                no_action_content.strip(),
                title="[INFO] No Action Taken",
                border_style="blue",
                padding=(1, 2)
            ))

    except Exception as e:
        console_manager.print_error(f"Error during deletion: {e}")
        raise typer.Exit(1)


def _show_managed_files_preview(discovery_result, app_type: str, project_path: Path) -> None:
    """Show preview of managed files grouped by AI tool."""
    from rich.table import Table
    
    console = Console()
    
    # Get AI tool manager to determine file ownership
    ai_tool_manager = AIToolManager(config)
    active_tools_result = ai_tool_manager.detect_active_tools(project_path)
    active_tools = active_tools_result.active_tools
    
    # Group files by AI tool that manages them
    tool_files = {}
    unassigned_files = []
    
    for file_path in discovery_result.managed_files_found:
        file_name = file_path.name
        assigned_to_tool = False
        
        # Check which active tool manages this file
        for tool_id in active_tools:
            tool_result = ai_tool_manager.get_managed_files_for_tool(tool_id, app_type)
            all_managed_files = tool_result.get_all_files()
            
            if file_name in all_managed_files:
                if tool_id not in tool_files:
                    tool_files[tool_id] = {
                        'name': tool_result.tool_name,
                        'files': []
                    }
                tool_files[tool_id]['files'].append(file_path)
                assigned_to_tool = True
                break
        
        if not assigned_to_tool:
            unassigned_files.append(file_path)
    
    console_manager.print(f"\n[bold blue]Managed files to delete for '{app_type}':[/bold blue]")
    
    if tool_files or unassigned_files:
        # Create a rich table for better formatting
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("AI Tool", style="cyan", width=20)
        table.add_column("Files", style="white")
        table.add_column("Count", justify="right", style="green")
        
        # Add rows for each AI tool
        for tool_id, tool_info in tool_files.items():
            files_list = []
            for file_path in sorted(tool_info['files']):
                relative_path = file_path.relative_to(project_path)
                files_list.append(f"[DEL] {relative_path}")
            
            files_display = "\n".join(files_list)
            table.add_row(
                tool_info['name'],
                files_display,
                str(len(tool_info['files']))
            )
        
        # Add unassigned files if any
        if unassigned_files:
            files_list = []
            for file_path in sorted(unassigned_files):
                relative_path = file_path.relative_to(project_path)
                files_list.append(f"[DEL] {relative_path}")
            
            files_display = "\n".join(files_list)
            table.add_row(
                "[yellow]Unassigned[/yellow]",
                files_display,
                str(len(unassigned_files))
            )
        
        console.print(table)
        
        # Show summary
        total_files = sum(len(info['files']) for info in tool_files.values()) + len(unassigned_files)
        total_tools = len(tool_files) + (1 if unassigned_files else 0)
        
        console_manager.print(f"\n[bold green]Summary:[/bold green] {total_files} files from {total_tools} source(s)")
    else:
        console_manager.print("[yellow]No managed files found to delete[/yellow]")
    
    console_manager.print()


def _show_deletion_results(deletion_result, dry_run: bool, project_path: Path) -> None:
    """Show comprehensive deletion results with AI tool context."""
    from rich.table import Table
    from rich.panel import Panel
    
    action = "Would delete" if dry_run else "Deleted"
    mode = "DRY RUN - " if dry_run else ""
    
    console = Console()
    console_manager.print(f"\n[bold green]{mode}Deletion Results:[/bold green]")
    
    # Create summary table
    summary_table = Table(show_header=True, header_style="bold cyan", box=None)
    summary_table.add_column("Status", style="bold")
    summary_table.add_column("Count", justify="right", style="bold")
    summary_table.add_column("Files", style="dim")
    
    # Add summary rows
    if deletion_result.success_count > 0:
        summary_table.add_row(
            "[green]✓ Successful[/green]", 
            str(deletion_result.success_count),
            f"Files {action.lower()}"
        )
    
    if deletion_result.failure_count > 0:
        summary_table.add_row(
            "[red]✗ Failed[/red]", 
            str(deletion_result.failure_count),
            "Deletion errors"
        )
    
    if deletion_result.skip_count > 0:
        summary_table.add_row(
            "[yellow]⚠ Skipped[/yellow]", 
            str(deletion_result.skip_count),
            "User preserved"
        )
    
    console.print(summary_table)
    
    # Detailed file results with AI tool context
    if deletion_result.success_count > 0:
        console_manager.print(f"\n[bold green]✓ Successfully {action}:[/bold green]")
        
        # Get AI tool manager to determine file ownership for context
        ai_tool_manager = AIToolManager(config)
        active_tools_result = ai_tool_manager.detect_active_tools(project_path)
        active_tools = active_tools_result.active_tools
        
        for file_path in deletion_result.deleted_files:
            relative_path = file_path.relative_to(project_path)
            
            # Determine which tool managed this file
            managing_tool = "Unknown"
            file_name = file_path.name
            
            for tool_id in active_tools:
                tool_result = ai_tool_manager.get_managed_files_for_tool(tool_id, None)  # Check all app types
                all_managed_files = tool_result.get_all_files()
                
                if file_name in all_managed_files:
                    managing_tool = tool_result.tool_name
                    break
            
            console_manager.print(f"  ✓ {relative_path} [dim]({managing_tool})[/dim]")
    
    # Show failures with detailed error information
    if deletion_result.failure_count > 0:
        console_manager.print(f"\n[bold red]✗ Failed to delete:[/bold red]")
        for attempt in deletion_result.failed_deletions:
            relative_path = attempt.file_path.relative_to(project_path)
            error_icon = "[PERM]" if attempt.permission_denied else "[MISS]" if attempt.file_not_found else "[ERR]"
            console_manager.print(f"  {error_icon} {relative_path}")
            if attempt.error_message:
                console_manager.print(f"     [dim]Reason: {attempt.error_message}[/dim]")
    
    # Show skipped files with context
    if deletion_result.skip_count > 0:
        console_manager.print(f"\n[bold yellow]⚠ Skipped files:[/bold yellow]")
        for file_path in deletion_result.skipped_files:
            relative_path = file_path.relative_to(project_path)
            console_manager.print(f"  ⚠ {relative_path}")
            console_manager.print(f"     [dim]Reason: User chose to preserve[/dim]")
    
    # Overall statistics in a panel
    total_processed = deletion_result.total_processed
    if total_processed > 0:
        success_rate = deletion_result.success_rate
        
        # Choose panel color based on success rate
        if success_rate >= 90:
            panel_style = "green"
            status_emoji = "[SUCCESS]"
        elif success_rate >= 70:
            panel_style = "yellow"
            status_emoji = "[WARNING]"
        else:
            panel_style = "red"
            status_emoji = "[ERROR]"
        
        stats_content = f"""
{status_emoji} [bold]Operation Statistics[/bold]

• Total files processed: {total_processed}
• Success rate: {success_rate:.1f}%
• Files {action.lower()}: {deletion_result.success_count}
• Files preserved: {deletion_result.skip_count + deletion_result.failure_count}
"""
        
        if dry_run:
            stats_content += "\n[dim][TIP] Use [bold]--force[/bold] to skip confirmations or remove [bold]--dry-run[/bold] to execute deletion[/dim]"
        
        console.print(Panel(
            stats_content.strip(),
            title=f"{mode}Summary",
            border_style=panel_style,
            padding=(1, 2)
        ))
    else:
        console_manager.print("\n[yellow]No files were processed[/yellow]")
        if dry_run:
            console_manager.print("[dim][TIP] This was a dry run - no actual changes were made[/dim]")


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
