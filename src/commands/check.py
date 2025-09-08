"""Check command implementation for Improved-SDD CLI.

This module contains the check command logic for verifying system requirements
and available AI assistant tools.
"""

import typer

# Import UI components
from ..ui import console_manager

# Import shared utilities
from ..utils import check_github_copilot, check_tool, offer_user_choice


def check_command():
    """Check that all required tools are installed."""
    console_manager.show_banner()
    console_manager.print("[bold]Checking Improved-SDD requirements...[/bold]\n")

    console_manager.print_info("Required tools:")
    python_ok = check_tool("python", "Install from: https://python.org/downloads")

    console_manager.print_info("\nAI Assistant tools (optional):")
    claude_ok = check_tool(
        "claude",
        "Install from: https://docs.anthropic.com/en/docs/claude-code/setup",
        optional=True,
    )
    copilot_ok = check_github_copilot()

    # Collect missing optional tools
    missing_tools = []
    if not claude_ok:
        missing_tools.append("Claude")
    if not copilot_ok:
        missing_tools.append("VS Code/GitHub Copilot")

    console_manager.print_success("\nImproved-SDD CLI is ready to use!")

    if not python_ok:
        console_manager.print_error("Python is required for this tool to work.")
        raise typer.Exit(1)

    # Offer user choice for missing optional tools
    if missing_tools:
        if not offer_user_choice(missing_tools):
            raise typer.Exit(1)
    else:
        console_manager.print_success("All AI assistant tools are available!")
