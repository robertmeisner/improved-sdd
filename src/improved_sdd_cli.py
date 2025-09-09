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

# Import commands
try:
    from src.commands import check_command, delete_command, init_command
    from src.ui import console_manager
except ImportError:
    # If we're in the src directory and can't import src.*, try relative imports
    from commands import check_command, delete_command, init_command
    from ui import console_manager

# Core constants and exceptions are now imported from core module


class BannerGroup(TyperGroup):
    """Custom group that shows banner before help and tip after help."""

    def format_help(self, ctx, formatter):
        # Show banner before help
        console_manager.show_banner()
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


@app.callback()
def callback(ctx: typer.Context):
    """Show banner when no subcommand is provided."""
    if ctx.invoked_subcommand is None and "--help" not in sys.argv and "-h" not in sys.argv:
        console_manager.show_banner()
        console_manager.show_centered_message("[dim]Run 'improved-sdd --help' for usage information[/dim]")
        console_manager.print_newline()


# Register the init command with the app
app.command(name="init")(init_command)

# Register the delete command with the app
app.command(name="delete")(delete_command)

# Register the check command with the app
app.command(name="check")(check_command)


def main():
    app()


if __name__ == "__main__":
    main()
