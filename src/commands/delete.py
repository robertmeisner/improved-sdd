"""Delete command implementation for Improved-SDD CLI.

This module contains the delete command logic for removing installed templates
from development environments.
"""

from pathlib import Path

import typer

# Import configuration and exceptions
from ..core import APP_TYPES

# Import UI components
from ..ui import console_manager

# Import shared utilities
from ..utils import select_app_type


def delete_command(
    app_type: str = typer.Argument(
        None, help="App type to delete files for: mcp-server, python-cli"
    ),
    force: bool = typer.Option(False, "--force", help="Skip confirmation prompt"),
):
    """
    Delete Improved-SDD templates for a specific app type.

    This command will:
    1. Identify files installed for the specified app type
    2. Show what will be deleted
    3. Require confirmation (unless --force is used)
    4. Delete the files

    Examples:
        improved-sdd delete mcp-server
        improved-sdd delete python-cli --force
    """

    # Show banner first
    console_manager.show_banner()

    # Validate app type
    if app_type:
        if app_type not in APP_TYPES:
            console_manager.print_error(
                f"Invalid app type '{app_type}'. Choose from: {', '.join(APP_TYPES.keys())}"
            )
            raise typer.Exit(1)
        selected_app_type = app_type
    else:
        selected_app_type = select_app_type()

    # Get project path (current directory)
    project_path = Path.cwd()

    # Find files to delete
    files_to_delete = []
    dirs_to_delete = []

    # Check for app-specific files
    github_dir = project_path / ".github"
    if github_dir.exists():
        # Check chatmodes
        chatmodes_dir = github_dir / "chatmodes"
        if chatmodes_dir.exists():
            for file_path in chatmodes_dir.glob("*.md"):
                files_to_delete.append(file_path)

        # Check instructions
        instructions_dir = github_dir / "instructions"
        if instructions_dir.exists():
            for file_path in instructions_dir.glob("*.md"):
                files_to_delete.append(file_path)

        # Check prompts
        prompts_dir = github_dir / "prompts"
        if prompts_dir.exists():
            for file_path in prompts_dir.glob("*.md"):
                files_to_delete.append(file_path)

        # Check commands
        commands_dir = github_dir / "commands"
        if commands_dir.exists():
            for file_path in commands_dir.glob("*.md"):
                files_to_delete.append(file_path)

        # Check if directories are empty after deletion
        for dir_path in [chatmodes_dir, instructions_dir, prompts_dir, commands_dir]:
            if dir_path.exists() and not list(dir_path.glob("*")):
                dirs_to_delete.append(dir_path)

        # Check if .github is empty after deletion
        if not list(github_dir.glob("*")):
            dirs_to_delete.append(github_dir)

    # Show what will be deleted
    if not files_to_delete and not dirs_to_delete:
        console_manager.print_warning(f"No files found for app type '{selected_app_type}'")
        return

    console_manager.print(f"[bold red]Files to be deleted for '{selected_app_type}': [/bold red]")
    console_manager.print_newline()

    if files_to_delete:
        console_manager.print("[red]Files:[/red]")
        for file_path in sorted(files_to_delete):
            console_manager.print(f"  🗑️  {file_path.relative_to(project_path)}")
        console_manager.print_newline()

    if dirs_to_delete:
        console_manager.print("[red]Directories:[/red]")
        for dir_path in sorted(dirs_to_delete):
            console_manager.print(f"  📁 {dir_path.relative_to(project_path)}")
        console_manager.print_newline()

    # Confirmation
    if not force:
        console_manager.print("[bold yellow][WARN]  This action cannot be undone![/bold yellow]")
        confirmation = typer.prompt("Type 'Yes' to confirm deletion", type=str, default="")
        if confirmation != "Yes":
            console_manager.print_warning("Deletion cancelled")
            return

    # Delete files
    console_manager.print_info("Deleting files...")

    deleted_files = 0
    deleted_dirs = 0

    for file_path in files_to_delete:
        try:
            file_path.unlink()
            console_manager.print_success(f"Deleted: {file_path.relative_to(project_path)}")
            deleted_files += 1
        except Exception as e:
            console_manager.print_error(
                f"Failed to delete {file_path.relative_to(project_path)}: {e}"
            )

    # Delete directories (in reverse order to handle nested dirs)
    for dir_path in sorted(dirs_to_delete, reverse=True):
        try:
            if not list(dir_path.glob("*")):  # Only delete if empty
                dir_path.rmdir()
                console_manager.print_success(
                    f"Deleted directory: {dir_path.relative_to(project_path)}"
                )
                deleted_dirs += 1
        except Exception as e:
            console_manager.print_error(
                f"Failed to delete directory {dir_path.relative_to(project_path)}: {e}"
            )

    console_manager.print_success(
        f"\nDeletion complete: {deleted_files} files, {deleted_dirs} directories removed"
    )
