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

# Set up module search path
# This ensures imports work both when running directly and when installed
current_dir = Path(__file__).parent
project_root = current_dir.parent

# For development execution: add src to Python path
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# For package execution: ensure project structure is available
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import typer
from typer.core import TyperGroup

# Now we can use direct imports since src is in the path
from commands.check import check_command
from commands.delete import delete_command  
from commands.init import init_command
from ui.console import console_manager

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
