"""Console management for Improved-SDD CLI.

This module provides centralized console operations using Rich library,
abstracting UI concerns from business logic.
"""

from typing import Optional

from rich.align import Align
from rich.console import Console
from rich.panel import Panel

# Import banner and tagline from core configuration
from core import BANNER, TAGLINE


class ConsoleManager:
    """Centralized console management for the CLI application.

    This class provides a consistent interface for all console operations,
    including success/error/warning messages, banner display, and Rich formatting.
    """

    def __init__(self):
        """Initialize console manager with Rich console."""
        self.console = Console()

    def print(self, text: str, style: Optional[str] = None) -> None:
        """Print text with optional styling."""
        self.console.print(text, style=style)

    def print_success(self, message: str) -> None:
        """Print success message with green styling."""
        self.console.print(f"[green][OK][/green] {message}")

    def print_error(self, message: str) -> None:
        """Print error message with red styling."""
        self.console.print(f"[red][ERROR][/red] {message}")

    def print_warning(self, message: str) -> None:
        """Print warning message with yellow styling."""
        self.console.print(f"[yellow][WARN][/yellow] {message}")

    def print_info(self, message: str) -> None:
        """Print info message with cyan styling."""
        self.console.print(f"[cyan]{message}[/cyan]")

    def print_status(self, tool: str, found: bool, hint: str = "", optional: bool = False) -> None:
        """Print tool status with appropriate styling."""
        if found:
            self.console.print(f"[green][OK][/green] {tool} found")
        else:
            status_icon = "[yellow][WARN][/yellow]" if optional else "[red][ERROR][/red]"
            self.console.print(f"{status_icon}  {tool} not found")
            if hint:
                self.console.print(f"   Install with: [cyan]{hint}[/cyan]")

    def show_banner(self) -> None:
        """Display ASCII art banner with multicolor styling."""
        # Display the ASCII banner with gradient colors
        banner_lines = BANNER.strip().split("\n")
        colors = ["bright_blue", "blue", "cyan", "bright_cyan", "white", "bright_white"]

        self.console.print()
        for i, line in enumerate(banner_lines):
            color = colors[i % len(colors)]
            # Use console.print with style parameter instead of markup to avoid formatting issues
            self.console.print(line, style=color)
        self.console.print(TAGLINE, style="italic bright_yellow")
        self.console.print()

    def show_panel(self, content: str, title: str, style: str = "cyan") -> None:
        """Display content in a Rich panel with title and styling."""
        panel = Panel.fit(content, title=title, border_style=style)
        self.console.print(panel)

    def show_centered_message(self, message: str) -> None:
        """Display centered message."""
        self.console.print(Align.center(message))

    def print_newline(self) -> None:
        """Print a newline for spacing."""
        self.console.print()

    def print_dim(self, message: str) -> None:
        """Print dimmed text for less important information."""
        self.console.print(f"[dim]{message}[/dim]")


# Global console manager instance
console_manager = ConsoleManager()
