#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer",
#     "rich",
#     "platformdirs",
#     "httpx",
# ]
# ///
"""
Improved-SDD CLI - Setup tool for Improved Spec-Driven Development projects

Usage:
    uvx improved-sdd-cli.py init <project-name>
    uvx improved-sdd-cli.py init --here

Or install globally:
    uv tool install improved-sdd-cli.py improved-sdd
    improved-sdd init <project-name>
    improved-sdd init --here
"""

import sys
from pathlib import Path

# Add the parent directory to sys.path if running directly
if __name__ == "__main__":
    # Get the directory containing this script (src)
    script_dir = Path(__file__).parent
    # Get the project root (parent of src)
    project_root = script_dir.parent
    # Add project root to sys.path so we can import src modules
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

import typer
from typer.core import TyperGroup

# Import commands lazily to avoid import errors at module level
check_command, delete_command, init_command, console_manager = (None, None, None, None)


def _import_commands(force=False):
    """Import commands lazily to handle different execution contexts."""
    global check_command, delete_command, init_command, console_manager
    # Return cached imports if already loaded and not forcing
    if not force and all((check_command, delete_command, init_command, console_manager)):
        return check_command, delete_command, init_command, console_manager

    try:
        # Development/editable install: direct imports from src
        from commands.check import check_command as check_fn
        from commands.delete import delete_command as delete_fn
        from commands.init import init_command as init_fn
        from ui.console import console_manager as cm
    except (ImportError, ModuleNotFoundError):
        # Production install: relative imports
        from .commands.check import check_command as check_fn
        from .commands.delete import delete_command as delete_fn
        from .commands.init import init_command as init_fn
        from .ui.console import console_manager as cm

    # Assign to global variables so they can be patched in tests
    check_command = check_fn
    delete_command = delete_fn
    init_command = init_fn
    console_manager = cm
    
    return check_command, delete_command, init_command, console_manager

# Core constants and exceptions are now imported from core module


class BannerGroup(TyperGroup):
    """Custom group that shows banner before help and tip after help."""

    def format_help(self, ctx, formatter):
        # Ensure commands are imported before showing help
        _setup_app()
        _, _, _, local_console_manager = _import_commands()
        
        # Show banner before help
        if local_console_manager:
            local_console_manager.show_banner()
        super().format_help(ctx, formatter)

        # Add tip after the help content
        formatter.write("\n")
        formatter.write("Tip: Use 'COMMAND --help' for detailed options and examples.\n")
        formatter.write("   Example: improved-sdd init --help\n")
        formatter.write("\n")


app = typer.Typer(
    name="improved-sdd",
    help="Setup AI-optimized development templates and workflows.",
    add_completion=False,
    invoke_without_command=True,
    cls=BannerGroup,
)

# Track if app has been set up
_app_setup_done = False


@app.callback()
def callback(ctx: typer.Context):
    """Show banner when no subcommand is provided."""
    if ctx.invoked_subcommand is None and "--help" not in sys.argv and "-h" not in sys.argv:
        # Ensure app is set up before showing banner
        _ensure_app_setup()
        _, _, _, local_console_manager = _import_commands()
        if local_console_manager:
            local_console_manager.show_banner()
            local_console_manager.show_centered_message("[dim]Run 'improved-sdd --help' for usage information[/dim]")
            local_console_manager.print_newline()


def main():
    """Entry point for the CLI application."""
    # Ensure app is set up before running
    _ensure_app_setup()
    app()


def _ensure_app_setup(force=False):
    """Ensure the app is set up before use."""
    global _app_setup_done
    if not _app_setup_done or force:
        _setup_app()
        _app_setup_done = True


def _setup_app():
    """Import and register commands for the Typer app."""
    # Import commands at runtime to register them
    check_fn, delete_fn, init_fn, _ = _import_commands(force=True)

    # Register the commands with the app
    if init_fn:
        app.command(name="init")(init_fn)
    if delete_fn:
        app.command(name="delete")(delete_fn)
    if check_fn:
        app.command(name="check")(check_fn)
# Configure the app on first use, not at import time
# _setup_app()  # Removed to avoid circular imports



if __name__ == "__main__":
    main()
