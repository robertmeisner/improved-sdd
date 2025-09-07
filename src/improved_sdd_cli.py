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

import asyncio
import shutil
import sys
import tempfile
import time
import zipfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

import httpx
import typer
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.progress import DownloadColumn, Progress, SpinnerColumn, TimeRemainingColumn, TransferSpeedColumn
from typer.core import TyperGroup

# Constants
AI_TOOLS = {
    "github-copilot": {
        "name": "GitHub Copilot",
        "description": "GitHub Copilot in VS Code",
        "template_dir": "github",
        "file_extensions": {
            "chatmodes": ".chatmode.md",
            "instructions": ".instructions.md",
            "prompts": ".prompt.md",
            "commands": ".command.md",
        },
        "keywords": {
            "{AI_ASSISTANT}": "GitHub Copilot",
            "{AI_SHORTNAME}": "Copilot",
            "{AI_COMMAND}": "Ctrl+Shift+P → 'Chat: Open Chat'",
        },
    },
    "claude": {
        "name": "Claude (Anthropic)",
        "description": "Claude Code or Claude API",
        "template_dir": "claude",
        "file_extensions": {
            "chatmodes": ".claude.md",
            "instructions": ".claude.md",
            "prompts": ".claude.md",
            "commands": ".claude.md",
        },
        "keywords": {"{AI_ASSISTANT}": "Claude", "{AI_SHORTNAME}": "Claude", "{AI_COMMAND}": "Open Claude interface"},
    },
    "cursor": {
        "name": "Cursor AI",
        "description": "Cursor AI Editor",
        "template_dir": "cursor",
        "file_extensions": {
            "chatmodes": ".cursor.md",
            "instructions": ".cursor.md",
            "prompts": ".cursor.md",
            "commands": ".cursor.md",
        },
        "keywords": {"{AI_ASSISTANT}": "Cursor AI", "{AI_SHORTNAME}": "Cursor", "{AI_COMMAND}": "Ctrl+K or Ctrl+L"},
    },
    "gemini": {
        "name": "Google Gemini",
        "description": "Google Gemini CLI or API",
        "template_dir": "gemini",
        "file_extensions": {
            "chatmodes": ".gemini.md",
            "instructions": ".gemini.md",
            "prompts": ".gemini.md",
            "commands": ".gemini.md",
        },
        "keywords": {
            "{AI_ASSISTANT}": "Google Gemini",
            "{AI_SHORTNAME}": "Gemini",
            "{AI_COMMAND}": "Use Gemini CLI or API",
        },
    },
}

APP_TYPES = {
    "mcp-server": {
        "description": "MCP Server - Model Context Protocol server for AI integrations",
        "instruction_files": ["sddMcpServerDev", "mcpDev"],  # New naming, legacy naming
    },
    "python-cli": {
        "description": "Python CLI - Command-line application using typer and rich",
        "instruction_files": ["sddPythonCliDev", "CLIPythonDev"],  # New naming, legacy naming
    },
}

# Clean ASCII Banner (readable and perfectly aligned)
BANNER = r"""
. _   __  __ _____ _____    _____       _______ _____        _____ _____  _____
 | | |      |  __ \|  __ \ / __ \ \    / /  ___|  __ \      / ____|  __ \|  __ \
 | | | |\/| | |__) | |__) | |  | \ \  / /| |__ | |  | |____| (___ | |  | | |  | |
 | | | |  | |  ___/|  _  /| |  | |\ \/ / |  __|| |  | |_____\___ \| |  | | |  | |
 | | | |  | | |    | | \ \| |__| | \  /  | |___| |__| |     ____) | |__| | |__| |
 |_| |_|  | |_|    |_|  \_\\____/   \/   |_____|_____/     |_____/|_____/|_____/
"""

TAGLINE = "Spec-Driven Development for GitHub Copilot (soon more: Cursor, Claude, Gemini)"


class FileTracker:
    """Track files that are created or modified during installation."""

    def __init__(self):
        self.created_files = []
        self.modified_files = []
        self.created_dirs = []

    def track_file_creation(self, filepath: Path):
        """Track a file that was created."""
        self.created_files.append(str(filepath))

    def track_file_modification(self, filepath: Path):
        """Track a file that was modified."""
        self.modified_files.append(str(filepath))

    def track_dir_creation(self, dirpath: Path):
        """Track a directory that was created."""
        self.created_dirs.append(str(dirpath))

    def get_summary(self) -> str:
        """Get a formatted summary of all tracked changes."""
        lines = []

        if self.created_dirs:
            lines.append("[bold cyan]Directories Created:[/bold cyan]")
            for dir_path in sorted(self.created_dirs):
                lines.append(f"  📁 {dir_path}")
            lines.append("")

        if self.created_files:
            lines.append("[bold green]Files Created:[/bold green]")
            # Group files by type
            file_groups = self._group_files_by_type(self.created_files)
            for file_type, files in file_groups.items():
                lines.append(f"  [dim]{file_type}: [/dim]")
                for file_path in sorted(files):
                    lines.append(f"    📄 {file_path}")
                lines.append("")
            lines.append("")

        if self.modified_files:
            lines.append("[bold yellow]Files Modified:[/bold yellow]")
            # Group files by type
            file_groups = self._group_files_by_type(self.modified_files)
            for file_type, files in file_groups.items():
                lines.append(f"  [dim]{file_type}: [/dim]")
                for file_path in sorted(files):
                    lines.append(f"    ✏️  {file_path}")
                lines.append("")
            lines.append("")

        total_changes = len(self.created_dirs) + len(self.created_files) + len(self.modified_files)
        if total_changes > 0:
            lines.append(
                f"[dim]Total: {len(self.created_dirs)} directories, "
                f"{len(self.created_files)} files created, "
                f"{len(self.modified_files)} files modified[/dim]"
            )
        else:
            lines.append("[dim]No files were created or modified[/dim]")

        return "\n".join(lines)

    def _group_files_by_type(self, files: list) -> dict:
        """Group files by their type based on directory structure."""
        groups = {"Chatmodes": [], "Instructions": [], "Prompts": [], "Commands": []}

        for file_path in files:
            # Convert to string and normalize path separators
            path_str = str(file_path).replace("\\", "/")

            if "chatmodes" in path_str:
                groups["Chatmodes"].append(file_path)
            elif "instructions" in path_str:
                groups["Instructions"].append(file_path)
            elif "prompts" in path_str:
                groups["Prompts"].append(file_path)
            elif "commands" in path_str:
                groups["Commands"].append(file_path)
            else:
                # Fallback for any files not in the expected structure
                groups["Other"] = groups.get("Other", [])
                groups["Other"].append(file_path)

        # Remove empty groups
        return {k: v for k, v in groups.items() if v}


console = Console()


class BannerGroup(TyperGroup):
    """Custom group that shows banner before help and tip after help."""

    def format_help(self, ctx, formatter):
        # Show banner before help
        show_banner()
        super().format_help(ctx, formatter)

        # Add tip after the help content
        formatter.write("\n")
        formatter.write("💡 Tip: Use 'COMMAND --help' for detailed options and examples.\n")
        formatter.write("   Example: improved-sdd init --help\n")
        formatter.write("\n")


app = typer.Typer(
    name="improved-sdd",
    help="Setup AI-optimized development templates and workflows.",
    add_completion=False,
    invoke_without_command=True,
    cls=BannerGroup,
)


def show_banner():
    """Display ASCII art banner with multicolor styling."""
    # Display the ASCII banner with gradient colors
    banner_lines = BANNER.strip().split("\n")
    colors = ["bright_blue", "blue", "cyan", "bright_cyan", "white", "bright_white"]

    console.print()
    for i, line in enumerate(banner_lines):
        color = colors[i % len(colors)]
        # Use console.print with style parameter instead of markup to avoid formatting issues
        console.print(line, style=color)
    console.print(TAGLINE, style="italic bright_yellow")
    console.print()


@app.callback()
def callback(ctx: typer.Context):
    """Show banner when no subcommand is provided."""
    if ctx.invoked_subcommand is None and "--help" not in sys.argv and "-h" not in sys.argv:
        show_banner()
        console.print(Align.center("[dim]Run 'improved-sdd --help' for usage information[/dim]"))
        console.print()


def check_tool(tool: str, install_hint: str, optional: bool = False) -> bool:
    """Check if a tool is installed."""
    if shutil.which(tool):
        console.print(f"[green][OK][/green] {tool} found")
        return True
    else:
        status_icon = "[yellow][WARN][/yellow]" if optional else "[red][ERROR][/red]"
        console.print(f"{status_icon}  {tool} not found")
        console.print(f"   Install with: [cyan]{install_hint}[/cyan]")
        return False


def check_github_copilot() -> bool:
    """Check if GitHub Copilot is available in VS Code."""
    # Check for VS Code installation
    vscode_found = shutil.which("code") is not None

    if vscode_found:
        console.print("[green][OK][/green] VS Code found")
        console.print("   [dim]Note: GitHub Copilot availability depends on VS Code extensions[/dim]")
        console.print("   [dim]Open VS Code and check if Copilot extension is installed and activated[/dim]")
        return True
    else:
        console.print("[yellow][WARN][/yellow]  VS Code not found")
        console.print("   Install with: [cyan]https://code.visualstudio.com/download[/cyan]")
        console.print("   [dim]Then install GitHub Copilot extension from VS Code marketplace[/dim]")
        return False


def offer_user_choice(missing_tools: list[str]) -> bool:
    """Offer user choice when tools are missing."""
    if not missing_tools:
        return True

    console.print(f"\n[yellow]Missing optional tools: {', '.join(missing_tools)}[/yellow]")
    console.print("[dim]These tools enhance the development experience but are not required.[/dim]")

    # Check if we're in CI/automation mode
    import os

    if os.getenv("CI") or os.getenv("GITHUB_ACTIONS"):
        console.print("[green][OK][/green] Continuing with available tools (CI mode)...")
        return True

    try:
        choice = typer.prompt("\nWould you like to continue anyway? (y/n)", type=str, default="y").lower().strip()

        if choice in ["y", "yes"]:
            console.print("[green][OK][/green] Continuing with available tools...")
            return True
        else:
            console.print("[yellow]Setup cancelled. Please install the missing tools and try again.[/yellow]")
            return False

    except (typer.Abort, KeyboardInterrupt):
        console.print("\n[yellow]Setup cancelled[/yellow]")
        return False


def select_ai_tools() -> list[str]:
    """Interactive AI tool selection with multi-selection support."""
    console.print("\n🤖 Which AI assistant(s) do you want to generate templates for?")
    console.print("[dim]You can select multiple tools (templates will be customized for each)[/dim]")

    # Use simple numbered selection
    tool_keys = list(AI_TOOLS.keys())

    console.print()
    for i, key in enumerate(tool_keys, 1):
        tool_info = AI_TOOLS[key]
        if key == "github-copilot":
            # GitHub Copilot is available now
            console.print(f"[cyan]{i}.[/cyan] [white]{tool_info['name']}[/white]: {tool_info['description']}")
        else:
            # Other tools are coming soon
            console.print(
                f"[dim cyan]{i}.[/dim cyan] [dim white]{tool_info['name']}[/dim white]: "
                f"[dim]{tool_info['description']}[/dim] [yellow](coming soon)[/yellow]"
            )

    console.print("\n[dim]Enter numbers separated by commas (e.g., 1,2) or 'all' for all tools[/dim]")
    console.print()

    while True:
        try:
            # Use input() instead of typer.prompt to avoid issues with defaults
            user_input = input(f"Select options (1-{len(tool_keys)}) [default: 1]: ").strip().lower()

            # Handle empty input (use default)
            if not user_input:
                choice = "1"
            else:
                choice = user_input

            if choice == "all":
                selected = tool_keys.copy()
                console.print(f"[green]Selected: [/green] All AI tools ({len(selected)} tools)")
                return selected

            # Parse comma-separated numbers
            selected_indices = []
            for part in choice.split(","):
                part = part.strip()
                if part.isdigit():
                    idx = int(part)
                    if 1 <= idx <= len(tool_keys):
                        selected_indices.append(idx - 1)
                    else:
                        raise ValueError(f"Invalid option: {idx}")
                else:
                    raise ValueError(f"Invalid input: {part}")

            if selected_indices:
                selected = [tool_keys[i] for i in selected_indices]
                tool_names = [AI_TOOLS[key]["name"] for key in selected]
                console.print(f"[green]Selected: [/green] {', '.join(tool_names)}")
                return selected
            else:
                console.print("[red]Please select at least one option[/red]")

        except ValueError as e:
            console.print(f"[red]Invalid input: {e}. Please try again.[/red]")
        except KeyboardInterrupt:
            console.print("\n[yellow]Selection cancelled[/yellow]")
            raise typer.Exit(1)


def customize_template_content(content: str, ai_tool: str) -> str:
    """Customize template content for specific AI tool by replacing keywords."""
    if ai_tool not in AI_TOOLS:
        return content

    tool_config = AI_TOOLS[ai_tool]
    customized_content = content

    # Replace AI-specific keywords
    for keyword, replacement in tool_config["keywords"].items():
        customized_content = customized_content.replace(keyword, replacement)

    return customized_content


def get_template_filename(original_name: str, ai_tool: str, template_type: str) -> str:
    """Generate AI-specific template filename."""
    if ai_tool not in AI_TOOLS:
        return original_name

    tool_config = AI_TOOLS[ai_tool]

    # Split the original name to get base name without extensions
    parts = original_name.split(".")
    if len(parts) >= 2:  # e.g., "specMode.md"
        base_name = parts[0]  # "specMode"
    else:
        base_name = original_name

    # Map template types to extension keys (handle plural to singular mapping)
    extension_key_map = {
        "chatmodes": "chatmodes",  # already correct
        "instructions": "instructions",  # already correct
        "prompts": "prompts",  # already correct
        "commands": "commands",  # already correct
    }

    extension_key = extension_key_map.get(template_type, template_type)
    extension = tool_config["file_extensions"].get(extension_key, ".md")

    # For GitHub Copilot, use simple .md extension to avoid double extensions
    if ai_tool == "github-copilot":
        # Map plural template types to singular extensions
        singular_map = {
            "chatmodes": "chatmode",
            "instructions": "instructions",
            "prompts": "prompt",
            "commands": "command",
        }
        singular_type = singular_map.get(template_type, template_type)
        return f"{base_name}.{singular_type}.md"
    else:
        # For other AI tools, use their configured extensions
        return f"{base_name}{extension}"


def select_app_type() -> str:
    """Interactive app type selection with fallback to simple prompt."""
    console.print("\n🔧 What kind of app are you building?")

    # Use simple numbered selection to avoid terminal compatibility issues
    option_keys = list(APP_TYPES.keys())

    console.print()
    for i, key in enumerate(option_keys, 1):
        console.print(f"[cyan]{i}.[/cyan] [white]{key}[/white]: {APP_TYPES[key]['description']}")

    console.print()

    while True:
        try:
            # Use input() instead of typer.prompt to avoid issues with defaults
            user_input = input(f"Select option (1-{len(option_keys)}) [default: 1]: ").strip()

            # Handle empty input (use default)
            if not user_input:
                choice = 1
            else:
                choice = int(user_input)

            if 1 <= choice <= len(option_keys):
                selected = option_keys[choice - 1]
                console.print(f"[green]Selected: [/green] {selected}")
                return selected
            else:
                console.print(f"[red]Please enter a number between 1 and {len(option_keys)}[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter a number.[/red]")
        except KeyboardInterrupt:
            console.print("\n[yellow]Selection cancelled[/yellow]")
            raise typer.Exit(1)


# Template Download Exceptions
class TemplateError(Exception):
    """Base exception for template-related operations."""

    pass


class NetworkError(TemplateError):
    """Exception for network-related errors during template download."""

    pass


class GitHubAPIError(TemplateError):
    """Exception for GitHub API-specific errors."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class RateLimitError(GitHubAPIError):
    """Exception for GitHub API rate limit errors."""

    def __init__(self, retry_after: Optional[int] = None):
        super().__init__("GitHub API rate limit exceeded")
        self.retry_after = retry_after


class TimeoutError(NetworkError):
    """Exception for timeout errors during download."""

    pass


class ValidationError(TemplateError):
    """Exception for template validation errors."""

    pass


class TemplateSourceType(Enum):
    """Enumeration of template source types for transparency."""

    LOCAL = "local"
    BUNDLED = "bundled"
    GITHUB = "github"


@dataclass
class ProgressInfo:
    """Progress information for download and extraction operations."""

    phase: str  # "download" or "extract"
    bytes_completed: int
    bytes_total: int
    percentage: float
    speed_bps: Optional[int] = None
    eta_seconds: Optional[int] = None

    @property
    def speed_mbps(self) -> Optional[float]:
        """Download speed in MB/s."""
        return self.speed_bps / (1024 * 1024) if self.speed_bps else None


@dataclass
class TemplateSource:
    """Represents a template source with location and type information."""

    path: Path
    source_type: TemplateSourceType
    size_bytes: Optional[int] = None

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.source_type.value} templates at {self.path}"


@dataclass
class TemplateResolutionResult:
    """Tracks the result of template resolution with transparency information."""

    source: Optional[TemplateSource]
    success: bool
    message: str
    fallback_attempted: bool = False

    @property
    def is_local(self) -> bool:
        """Check if resolved source is local .sdd_templates."""
        return self.source is not None and self.source.source_type == TemplateSourceType.LOCAL

    @property
    def is_bundled(self) -> bool:
        """Check if resolved source is bundled templates."""
        return self.source is not None and self.source.source_type == TemplateSourceType.BUNDLED

    @property
    def is_github(self) -> bool:
        """Check if resolved source is GitHub download."""
        return self.source is not None and self.source.source_type == TemplateSourceType.GITHUB


class CacheManager:
    """Manages temporary cache directories for template downloads.

    Provides secure cache directory creation and management with automatic cleanup.
    Ensures cache directories are created in system temp directory with unique naming.
    """

    def __init__(self):
        """Initialize cache manager."""
        import atexit
        import os

        self.process_id = os.getpid()
        self._active_caches: list[Path] = []

        # Register atexit handler for cleanup on normal termination
        atexit.register(self.cleanup_all_caches)

    def create_cache_dir(self) -> Path:
        """Create a temporary cache directory in system temp location.

        Creates directory outside current working directory and all parent directories
        using system temp directory with process ID for uniqueness.

        Returns:
            Path: Path to created cache directory

        Raises:
            OSError: If cache directory creation fails
        """
        import tempfile

        # Create cache directory with unique naming including process ID
        cache_prefix = f"sdd_templates_{self.process_id}_"
        cache_dir = Path(tempfile.mkdtemp(prefix=cache_prefix))

        # Track active cache for cleanup
        self._active_caches.append(cache_dir)

        return cache_dir

    def cleanup_cache(self, cache_dir: Path) -> None:
        """Clean up a specific cache directory.

        Args:
            cache_dir: Path to cache directory to cleanup
        """
        try:
            if cache_dir.exists():
                import shutil

                shutil.rmtree(cache_dir, ignore_errors=True)

            # Remove from active caches
            if cache_dir in self._active_caches:
                self._active_caches.remove(cache_dir)

        except Exception as e:
            # Log warning but don't fail operation
            console.print(f"[yellow]⚠ Warning: Could not cleanup cache directory {cache_dir}: {e}[/yellow]")

    def cleanup_all_caches(self) -> None:
        """Clean up all active cache directories."""
        for cache_dir in self._active_caches.copy():
            self.cleanup_cache(cache_dir)

    def cleanup_orphaned_caches(self) -> int:
        """Clean up orphaned cache directories from interrupted runs.

        Scans system temp directory for sdd_templates_* directories and removes
        those belonging to processes that are no longer running.

        Returns:
            int: Number of orphaned caches cleaned up
        """
        import glob
        import re
        import tempfile

        cleaned_count = 0
        temp_dir = Path(tempfile.gettempdir())

        try:
            # Find all sdd_templates_* directories in temp
            pattern = temp_dir / "sdd_templates_*"
            orphan_candidates = [Path(p) for p in glob.glob(str(pattern)) if Path(p).is_dir()]

            for cache_dir in orphan_candidates:
                try:
                    # Extract process ID from directory name
                    match = re.search(r"sdd_templates_(\d+)_", cache_dir.name)
                    if not match:
                        continue

                    pid = int(match.group(1))

                    # Skip if it's our own cache
                    if pid == self.process_id:
                        continue

                    # Check if process is still running
                    if self._is_process_running(pid):
                        continue

                    # Process not running, clean up orphaned cache
                    import shutil

                    shutil.rmtree(cache_dir, ignore_errors=True)
                    cleaned_count += 1

                except (ValueError, OSError, Exception) as e:
                    # Log warning for individual failures but continue
                    console.print(f"[yellow]⚠ Warning: Could not cleanup orphaned cache {cache_dir}: {e}[/yellow]")
                    continue

            if cleaned_count > 0:
                console.print(
                    f"[cyan]🧩 Cleaned up {cleaned_count} orphaned cache director{'y' if cleaned_count == 1 else 'ies'}[/cyan]"
                )

        except Exception as e:
            # Log warning for overall failure but don't fail operation
            console.print(f"[yellow]⚠ Warning: Could not scan for orphaned caches: {e}[/yellow]")

        return cleaned_count

    def _is_process_running(self, pid: int) -> bool:
        """Check if a process with given PID is running.

        Args:
            pid: Process ID to check

        Returns:
            bool: True if process is running, False otherwise
        """
        try:
            import os

            # On Windows, use different approach
            import platform
            import signal

            if platform.system() == "Windows":
                import subprocess

                try:
                    # Use tasklist to check if process exists
                    result = subprocess.run(
                        ["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True, timeout=5
                    )
                    return str(pid) in result.stdout
                except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                    return False
            else:
                # On Unix-like systems, use os.kill with signal 0
                os.kill(pid, 0)
                return True

        except (OSError, ProcessLookupError):
            return False
        except Exception:
            # If we can't determine, assume it's running to be safe
            return True

    def get_cache_info(self, cache_dir: Path) -> dict:
        """Get information about a cache directory.

        Args:
            cache_dir: Path to cache directory

        Returns:
            dict: Cache information including size and file count
        """
        if not cache_dir.exists():
            return {"exists": False, "size_bytes": 0, "file_count": 0}

        total_size = 0
        file_count = 0

        try:
            for file_path in cache_dir.rglob("*"):
                if file_path.is_file():
                    file_count += 1
                    total_size += file_path.stat().st_size
        except Exception:
            pass  # Ignore errors during size calculation

        return {"exists": True, "size_bytes": total_size, "file_count": file_count, "path": str(cache_dir)}


class GitHubDownloader:
    """Handles downloading templates from GitHub repository with progress reporting."""

    def __init__(self, repo_owner: str = "robertmeisner", repo_name: str = "improved-sdd"):
        """Initialize GitHub downloader.

        Args:
            repo_owner: GitHub repository owner
            repo_name: GitHub repository name
        """
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.base_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"

    async def download_templates(
        self, target_dir: Path, progress_callback: Optional[Callable[[ProgressInfo], None]] = None
    ) -> TemplateSource:
        """Download templates from GitHub repository's /templates folder.

        Args:
            target_dir: Directory to download templates to
            progress_callback: Optional callback for detailed progress updates

        Returns:
            TemplateSource: Information about the downloaded templates

        Raises:
            GitHubAPIError: If GitHub API request fails
            NetworkError: If network operation fails
            TimeoutError: If download times out
        """
        console = Console()

        # Ensure target directory exists
        target_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Download repository archive
            archive_url = f"https://github.com/{self.repo_owner}/{self.repo_name}/archive/refs/heads/main.zip"

            # Setup progress tracking
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                DownloadColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
                console=console,
            ) as progress:
                # Create download task
                download_task = progress.add_task("Downloading templates...", total=None)

                async with httpx.AsyncClient(timeout=30.0) as client:
                    async with client.stream("GET", archive_url) as response:
                        if response.status_code != 200:
                            raise GitHubAPIError(
                                f"Failed to download repository: HTTP {response.status_code}", response.status_code
                            )

                        # Get content length for progress tracking
                        total_size = int(response.headers.get("content-length", 0))
                        if total_size > 0:
                            progress.update(download_task, total=total_size)

                        # Download to temporary file
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_file:
                            temp_path = Path(temp_file.name)
                            downloaded = 0
                            start_time = time.time()

                            async for chunk in response.aiter_bytes(chunk_size=8192):
                                temp_file.write(chunk)
                                downloaded += len(chunk)
                                progress.update(download_task, completed=downloaded)

                                # Enhanced progress callback
                                if progress_callback and total_size > 0:
                                    elapsed_time = time.time() - start_time
                                    if elapsed_time > 0:
                                        speed_bps = int(downloaded / elapsed_time)
                                        remaining_bytes = total_size - downloaded
                                        eta_seconds = int(remaining_bytes / speed_bps) if speed_bps > 0 else None
                                    else:
                                        speed_bps = None
                                        eta_seconds = None

                                    progress_info = ProgressInfo(
                                        phase="download",
                                        bytes_completed=downloaded,
                                        bytes_total=total_size,
                                        percentage=(downloaded / total_size) * 100,
                                        speed_bps=speed_bps,
                                        eta_seconds=eta_seconds,
                                    )
                                    progress_callback(progress_info)

                # Extract templates folder from archive
                progress.update(download_task, description="Validating and extracting templates...")

                # Extract templates with validation and progress reporting
                self.extract_templates(temp_path, target_dir, progress_callback)

                # Cleanup temporary files
                try:
                    temp_path.unlink()
                except OSError:
                    pass  # Ignore cleanup errors

                # Calculate total size of downloaded templates
                total_size = sum(f.stat().st_size for f in target_dir.rglob("*") if f.is_file())

                progress.update(download_task, description="Download complete!", completed=total_size, total=total_size)

                return TemplateSource(path=target_dir, source_type=TemplateSourceType.GITHUB, size_bytes=total_size)

        except httpx.TimeoutException:
            raise TimeoutError("Download timed out")
        except httpx.RequestError as e:
            raise NetworkError(f"Network error during download: {e}")
        except Exception as e:
            if isinstance(e, (TemplateError, NetworkError, GitHubAPIError, TimeoutError)):
                raise
            raise TemplateError(f"Unexpected error during template download: {e}")

    def extract_templates(
        self, zip_path: Path, target_dir: Path, progress_callback: Optional[Callable[[ProgressInfo], None]] = None
    ) -> None:
        """Extract templates from ZIP archive with validation and security checks.

        Args:
            zip_path: Path to the downloaded ZIP file
            target_dir: Directory to extract templates to
            progress_callback: Optional callback for extraction progress updates

        Raises:
            TemplateError: If ZIP is invalid or templates are missing
            ValidationError: If template structure is invalid
        """
        # Step 1: ZIP integrity validation
        self._validate_zip_integrity(zip_path)

        # Step 2: Extract with path traversal protection
        extracted_files = self._extract_with_protection(zip_path, target_dir, progress_callback)

        # Step 3: Template structure validation
        self._validate_template_structure(target_dir, extracted_files)

    def _validate_zip_integrity(self, zip_path: Path) -> None:
        """Validate ZIP file integrity before extraction.

        Args:
            zip_path: Path to ZIP file to validate

        Raises:
            TemplateError: If ZIP is corrupted or invalid
        """
        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                # Test ZIP integrity
                bad_file = zip_ref.testzip()
                if bad_file:
                    raise TemplateError(f"Corrupted ZIP file detected: {bad_file}")

                # Validate ZIP has content
                if not zip_ref.namelist():
                    raise TemplateError("ZIP file is empty")

                # Check for templates folder
                templates_prefix = f"{self.repo_name}-main/templates/"
                template_files = [name for name in zip_ref.namelist() if name.startswith(templates_prefix)]

                if not template_files:
                    raise TemplateError("No templates folder found in repository archive")

        except zipfile.BadZipFile:
            raise TemplateError("Downloaded file is not a valid ZIP archive")
        except Exception as e:
            if isinstance(e, TemplateError):
                raise
            raise TemplateError(f"Failed to validate ZIP file: {e}")

    def _extract_with_protection(
        self, zip_path: Path, target_dir: Path, progress_callback: Optional[Callable[[ProgressInfo], None]] = None
    ) -> list[str]:
        """Extract ZIP contents with path traversal protection.

        Args:
            zip_path: Path to ZIP file
            target_dir: Target extraction directory
            progress_callback: Optional callback for extraction progress

        Returns:
            List of extracted file paths (relative to target_dir)

        Raises:
            TemplateError: If extraction fails or path traversal detected
        """
        extracted_files = []

        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                templates_prefix = f"{self.repo_name}-main/templates/"
                template_files = [name for name in zip_ref.namelist() if name.startswith(templates_prefix)]

                # Calculate total extraction size for progress tracking
                total_files = len([f for f in template_files if not zip_ref.getinfo(f).is_dir()])
                extracted_count = 0

                for file_path in template_files:
                    # Remove prefix to get relative path
                    relative_path = file_path[len(templates_prefix) :]
                    if not relative_path:  # Skip the templates/ directory itself
                        continue

                    # Path traversal protection
                    safe_path = self._validate_safe_path(relative_path, target_dir)

                    # Extract file info
                    file_info = zip_ref.getinfo(file_path)

                    # Skip directories
                    if file_info.is_dir():
                        safe_path.mkdir(parents=True, exist_ok=True)
                        continue

                    # Create parent directories
                    safe_path.parent.mkdir(parents=True, exist_ok=True)

                    # Extract file content
                    with zip_ref.open(file_info) as source, open(safe_path, "wb") as target:
                        shutil.copyfileobj(source, target)

                    extracted_files.append(relative_path)
                    extracted_count += 1

                    # Report extraction progress
                    if progress_callback and total_files > 0:
                        progress_info = ProgressInfo(
                            phase="extract",
                            bytes_completed=extracted_count,
                            bytes_total=total_files,
                            percentage=(extracted_count / total_files) * 100,
                        )
                        progress_callback(progress_info)

                return extracted_files

        except Exception as e:
            if isinstance(e, TemplateError):
                raise
            raise TemplateError(f"Failed to extract templates: {e}")

    def _validate_safe_path(self, relative_path: str, target_dir: Path) -> Path:
        """Validate that a path is safe and doesn't escape the target directory.

        Args:
            relative_path: Relative path from ZIP archive
            target_dir: Target extraction directory

        Returns:
            Validated absolute path

        Raises:
            TemplateError: If path traversal attempt detected
        """
        # Normalize path and resolve any .. or . components
        safe_path = (target_dir / relative_path).resolve()

        # Ensure the resolved path is within target directory
        try:
            safe_path.relative_to(target_dir.resolve())
        except ValueError:
            raise TemplateError(f"Path traversal attempt detected: {relative_path}")

        return safe_path

    def _validate_template_structure(self, target_dir: Path, extracted_files: list[str]) -> None:
        """Validate that extracted templates have expected structure.

        Args:
            target_dir: Directory containing extracted templates
            extracted_files: List of extracted file paths

        Raises:
            TemplateError: If template structure is invalid
        """
        if not extracted_files:
            raise TemplateError("No template files were extracted")

        # Check for expected template directories
        expected_dirs = {"chatmodes", "commands", "instructions", "prompts"}
        found_dirs = set()

        for file_path in extracted_files:
            # Get top-level directory
            parts = Path(file_path).parts
            if parts:
                found_dirs.add(parts[0])

        # Validate at least some expected directories exist
        if not found_dirs.intersection(expected_dirs):
            raise TemplateError(
                f"Invalid template structure. Expected directories: {', '.join(expected_dirs)}, "
                f"found: {', '.join(found_dirs) if found_dirs else 'none'}"
            )

        # Check for minimum file count
        if len(extracted_files) < 3:
            raise TemplateError(f"Too few template files extracted: {len(extracted_files)}. Expected at least 3 files.")

        # Validate file sizes (basic check for empty files)
        empty_files = []
        for file_path in extracted_files:
            full_path = target_dir / file_path
            if full_path.is_file() and full_path.stat().st_size == 0:
                empty_files.append(file_path)

        if len(empty_files) > len(extracted_files) // 2:  # More than half are empty
            raise TemplateError(f"Too many empty template files detected: {len(empty_files)}/{len(extracted_files)}")


class TemplateResolver:
    """Handles template resolution with priority-based system: local .sdd_templates > bundled templates > GitHub download."""

    def __init__(self, project_path: Path):
        """Initialize the resolver for a specific project path.

        Args:
            project_path: The target project directory where templates will be installed
        """
        self.project_path = project_path
        self.script_dir = Path(__file__).parent
        self.github_downloader = GitHubDownloader()
        self.cache_manager = CacheManager()

        # Clean up orphaned caches on startup
        self.cache_manager.cleanup_orphaned_caches()

    def get_local_templates_path(self) -> Optional[Path]:
        """Check for local .sdd_templates directory in project or parent directories.

        Returns:
            Path to local .sdd_templates if found, None otherwise
        """
        # Check current project directory first
        local_path = self.project_path / ".sdd_templates"
        if local_path.exists() and local_path.is_dir():
            return local_path

        # Check parent directories up to filesystem root
        current_path = self.project_path.parent
        while current_path != current_path.parent:  # Stop at filesystem root
            local_path = current_path / ".sdd_templates"
            if local_path.exists() and local_path.is_dir():
                return local_path
            current_path = current_path.parent

        return None

    def get_bundled_templates_path(self) -> Optional[Path]:
        """Get path to bundled templates directory.

        Returns:
            Path to bundled templates if they exist, None otherwise
        """
        bundled_path = self.script_dir.parent / ".sdd_templates"
        if bundled_path.exists() and bundled_path.is_dir():
            return bundled_path
        return None

    def resolve_templates_source(self) -> Optional[Path]:
        """Resolve template source using priority system.

        Priority order:
        1. Local .sdd_templates (project or parent directories)
        2. Bundled templates directory
        3. GitHub download to temporary cache

        Returns:
            Path to templates source, None if no source found
        """
        # Priority 1: Local .sdd_templates
        local_path = self.get_local_templates_path()
        if local_path:
            return local_path

        # Priority 2: Bundled templates
        bundled_path = self.get_bundled_templates_path()
        if bundled_path:
            return bundled_path

        # Priority 3: GitHub download
        try:
            return self._download_github_templates()
        except (NetworkError, GitHubAPIError, TimeoutError, ValidationError) as e:
            console.print(f"[yellow]⚠ Could not download templates from GitHub: {e}[/yellow]")
            return None
        except Exception as e:
            console.print(f"[yellow]⚠ Unexpected error during GitHub download: {e}[/yellow]")
            return None

    def resolve_templates_with_transparency(self) -> TemplateResolutionResult:
        """Resolve template source with full transparency and logging.

        Returns:
            TemplateResolutionResult with detailed information about resolution
        """
        # Check local .sdd_templates first
        local_path = self.get_local_templates_path()
        if local_path:
            source = TemplateSource(
                path=local_path, source_type=TemplateSourceType.LOCAL, size_bytes=self._get_directory_size(local_path)
            )
            console.print(f"[green]✓ Using local templates from {local_path}[/green]")
            return TemplateResolutionResult(
                source=source,
                success=True,
                message=f"Using local templates from {local_path}",
                fallback_attempted=False,
            )

        # Fallback to bundled templates
        bundled_path = self.get_bundled_templates_path()
        if bundled_path:
            source = TemplateSource(
                path=bundled_path,
                source_type=TemplateSourceType.BUNDLED,
                size_bytes=self._get_directory_size(bundled_path),
            )
            console.print(f"[cyan]ℹ Using bundled templates from {bundled_path}[/cyan]")
            return TemplateResolutionResult(
                source=source,
                success=True,
                message=f"Using bundled templates from {bundled_path}",
                fallback_attempted=True,
            )

        # Fallback to GitHub download
        console.print("[blue]⬇ No local templates found, attempting GitHub download...[/blue]")
        try:
            github_path = self._download_github_templates()
            if github_path:
                source = TemplateSource(
                    path=github_path,
                    source_type=TemplateSourceType.GITHUB,
                    size_bytes=self._get_directory_size(github_path),
                )
                console.print(f"[green]✓ Downloaded templates from GitHub to {github_path}[/green]")
                return TemplateResolutionResult(
                    source=source, success=True, message=f"Downloaded templates from GitHub", fallback_attempted=True
                )
        except NetworkError as e:
            console.print(f"[yellow]⚠ Network error during GitHub download: {e}[/yellow]")
            self._show_offline_instructions()
        except GitHubAPIError as e:
            if isinstance(e, RateLimitError):
                retry_msg = f" (retry after {e.retry_after}s)" if hasattr(e, "retry_after") and e.retry_after else ""
                console.print(f"[yellow]⚠ GitHub API rate limit exceeded{retry_msg}[/yellow]")
            else:
                console.print(f"[yellow]⚠ GitHub API error: {e}[/yellow]")
            self._show_offline_instructions()
        except TimeoutError as e:
            console.print(f"[yellow]⚠ Download timeout: {e}[/yellow]")
            console.print("[cyan]💡 Try again with a better internet connection[/cyan]")
        except ValidationError as e:
            console.print(f"[yellow]⚠ Template validation failed: {e}[/yellow]")
            console.print("[cyan]💡 The downloaded templates may be corrupted or invalid[/cyan]")
        except Exception as e:
            console.print(f"[red]✗ Unexpected error during GitHub download: {e}[/red]")

        # All template sources failed
        console.print("[red]✗ No templates available from any source[/red]")
        self._show_manual_setup_instructions()
        return TemplateResolutionResult(
            source=None,
            success=False,
            message="No templates found from any source (local, bundled, or GitHub)",
            fallback_attempted=True,
        )

    def _get_directory_size(self, path: Path) -> Optional[int]:
        """Calculate total size of directory in bytes.

        Args:
            path: Directory path to calculate size for

        Returns:
            Size in bytes, or None if calculation fails
        """
        try:
            total_size = 0
            for file_path in path.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            return total_size
        except (OSError, PermissionError):
            return None

    def has_local_templates(self) -> bool:
        """Check if local .sdd_templates are available."""
        return self.get_local_templates_path() is not None

    def has_bundled_templates(self) -> bool:
        """Check if bundled templates are available."""
        return self.get_bundled_templates_path() is not None

    def _download_github_templates(self) -> Optional[Path]:
        """Download templates from GitHub to temporary cache.

        Returns:
            Path to cached templates if successful, None otherwise

        Raises:
            NetworkError: If network operation fails
            GitHubAPIError: If GitHub API request fails
            TimeoutError: If download times out
            ValidationError: If template validation fails
        """
        # Create cache directory using CacheManager
        cache_dir = self.cache_manager.create_cache_dir()

        try:
            # Download templates asynchronously
            import asyncio

            async def download():
                return await self.github_downloader.download_templates(cache_dir)

            # Run async download
            if hasattr(asyncio, "run"):
                source = asyncio.run(download())
            else:
                # Fallback for older Python versions
                loop = asyncio.get_event_loop()
                source = loop.run_until_complete(download())

            return source.path if source else None

        except Exception:
            # Cleanup cache directory on failure
            self.cache_manager.cleanup_cache(cache_dir)
            raise

    def _show_offline_instructions(self) -> None:
        """Show instructions for working offline with local templates."""
        from rich.panel import Panel

        offline_instructions = (
            "[bold cyan]Working Offline[/bold cyan]\n\n"
            "To use templates without internet access:\n"
            "1. Create a [bold].sdd_templates[/bold] folder in your project directory\n"
            "2. Copy template files from the repository manually:\n"
            "   [dim]https://github.com/robertmeisner/improved-sdd/tree/main/templates[/dim]\n"
            "3. Or work from a directory that already has [bold].sdd_templates[/bold]"
        )

        console.print(Panel(offline_instructions, title="💡 Offline Mode", border_style="cyan", padding=(1, 2)))

    def _show_manual_setup_instructions(self) -> None:
        """Show comprehensive manual setup instructions when all sources fail."""
        from rich.panel import Panel

        manual_instructions = (
            "[bold red]Manual Template Setup Required[/bold red]\n\n"
            "All template sources failed. To proceed manually:\n\n"
            "[bold cyan]Option 1: Download Templates[/bold cyan]\n"
            "1. Visit: [dim]https://github.com/robertmeisner/improved-sdd[/dim]\n"
            "2. Download or clone the repository\n"
            "3. Copy the [bold]templates/[/bold] folder to [bold].sdd_templates/[/bold] in your project\n\n"
            "[bold cyan]Option 2: Create Basic Structure[/bold cyan]\n"
            "1. Create [bold].sdd_templates/[/bold] folder manually\n"
            "2. Add basic template files as needed\n\n"
            "[bold cyan]Option 3: Use Different Directory[/bold cyan]\n"
            "Run this command from a directory that already has templates"
        )

        console.print(Panel(manual_instructions, title="🔧 Manual Setup", border_style="red", padding=(1, 2)))


def create_project_structure(
    project_path: Path, app_type: str, ai_tools: list[str], file_tracker: FileTracker, force: bool = False
) -> None:
    """Install Improved-SDD templates into the project directory for selected AI tools.

    Uses TemplateResolver to find templates with priority-based resolution:
    1. Local .sdd_templates (current/parent directories)
    2. Bundled templates (CLI installation)
    3. GitHub download (future implementation)

    Args:
        project_path: Target directory for template installation
        app_type: Type of application project
        ai_tools: List of AI tools to install templates for
        file_tracker: FileTracker instance for tracking created files
        force: Whether to overwrite existing files
    """

    # Use TemplateResolver for priority-based template resolution with transparency
    resolver = TemplateResolver(project_path)
    resolution_result = resolver.resolve_templates_with_transparency()

    if not resolution_result.success:
        console.print("[red]✗ No templates found from any source[/red]")
        console.print("[yellow]Future versions will support downloading templates from GitHub.[/yellow]")
        console.print(
            "[cyan]💡 To use local templates, create a `.sdd_templates` folder in your project or parent directory.[/cyan]"
        )
        return

    templates_source = resolution_result.source.path

    # Verify template source is accessible
    if not templates_source.exists():
        console.print(f"[red]✗ Template source path does not exist: {templates_source}[/red]")
        return

    # Show additional resolution context for transparency
    if resolution_result.fallback_attempted:
        console.print(
            f"[dim]📍 Template resolution: {resolution_result.source.source_type.value} source selected after fallback[/dim]"
        )
    else:
        console.print(
            f"[dim]📍 Template resolution: {resolution_result.source.source_type.value} source (primary choice)[/dim]"
        )

    # Template resolution successful - proceed with installation
    for ai_tool in ai_tools:
        if ai_tool not in AI_TOOLS:
            console.print(f"[yellow]Warning: Unknown AI tool '{ai_tool}', skipping[/yellow]")
            continue

        tool_config = AI_TOOLS[ai_tool]
        tool_name = tool_config["name"]

        console.print(f"[cyan]Installing templates for {tool_name}...[/cyan]")

        # Define categories for this AI tool
        # GitHub Copilot goes in root .github/, others get their own subdirectory
        if ai_tool == "github-copilot":
            ai_tool_dir = ""  # Root .github directory
        else:
            ai_tool_dir = ai_tool.replace("-", "_") + "/"  # Convert kebab-case to snake_case for directory

            categories = {
                "Chatmodes/Agents": {
                    "source": templates_source / "chatmodes",
                    "dest": f".github/{ai_tool_dir}chatmodes",
                    "files": [],
                    "type": "chatmodes",
                },
                "Instructions": {
                    "source": templates_source / "instructions",
                    "dest": f".github/{ai_tool_dir}instructions",
                    "files": [],
                    "type": "instructions",
                },
                "Prompts/Commands": {
                    "source": templates_source / "prompts",
                    "dest": f".github/{ai_tool_dir}prompts",
                    "files": [],
                    "type": "prompts",
                },
            }

            # Add commands to Prompts/Commands category
            commands_src = templates_source / "commands"
            if commands_src.exists():
                categories["Prompts/Commands"]["commands_source"] = commands_src
                categories["Prompts/Commands"]["commands_dest"] = f".github/{ai_tool_dir}commands"
                categories["Prompts/Commands"]["commands_type"] = "commands"

            # Collect all files for each category
            for category_name, category_info in categories.items():
                source_dir = category_info["source"]
                if source_dir.exists():
                    for template_file in source_dir.glob("*.md"):
                        # Filter instruction files based on app type
                        if category_info["type"] == "instructions":
                            # Only include the instruction file that matches the app type
                            # Check against configured instruction file patterns
                            app_config = APP_TYPES[app_type]
                            instruction_patterns = app_config["instruction_files"]

                            if not any(template_file.name.startswith(pattern) for pattern in instruction_patterns):
                                continue

                        # Generate AI-specific filename
                        new_filename = get_template_filename(template_file.name, ai_tool, category_info["type"])
                        dest_file = project_path / category_info["dest"] / new_filename
                        category_info["files"].append((template_file, dest_file, category_info["type"]))

                # Add commands files to Prompts/Commands category
                if "commands_source" in category_info:
                    commands_source = category_info["commands_source"]
                    for template_file in commands_source.glob("*.md"):
                        new_filename = get_template_filename(
                            template_file.name, ai_tool, category_info["commands_type"]
                        )
                        dest_file = project_path / category_info["commands_dest"] / new_filename
                        category_info["files"].append((template_file, dest_file, category_info["commands_type"]))

            # Create .github directory if we have any files to install
            total_files = sum(len(category_info["files"]) for category_info in categories.values())
            if total_files > 0:
                github_dir = project_path / ".github"
                if not github_dir.exists():
                    github_dir.mkdir(parents=True, exist_ok=True)
                    file_tracker.track_dir_creation(github_dir.relative_to(project_path))

            # Process each category for this AI tool
            for category_name, category_info in categories.items():
                if not category_info["files"]:
                    continue

                # Create category directory if it doesn't exist
                category_dir = project_path / category_info["dest"]
                if not category_dir.exists():
                    category_dir.mkdir(parents=True, exist_ok=True)
                    file_tracker.track_dir_creation(category_dir.relative_to(project_path))

                # Handle commands directory too
                if "commands_dest" in category_info:
                    commands_dir = project_path / category_info["commands_dest"]
                    if not commands_dir.exists():
                        commands_dir.mkdir(parents=True, exist_ok=True)
                        file_tracker.track_dir_creation(commands_dir.relative_to(project_path))

                # Check if any files in this category already exist
                existing_files = [dest_file for _, dest_file, _ in category_info["files"] if dest_file.exists()]

                category_confirmed = force
                if existing_files and not force:
                    # Ask once per category per AI tool
                    if typer.confirm(
                        f"Some {category_name.lower()} files for {tool_name} already exist. Overwrite all?"
                    ):
                        category_confirmed = True
                    else:
                        # Fall back to individual file confirmations
                        console.print(
                            f"[yellow]Asking about each {category_name.lower()} file for "
                            f"{tool_name} individually...[/yellow]"
                        )
                        category_confirmed = False

                # Copy all files in this category with AI-specific customization
                for template_file, dest_file, template_type in category_info["files"]:
                    # Read and customize template content
                    original_content = template_file.read_text(encoding="utf-8")
                    customized_content = customize_template_content(original_content, ai_tool)

                    if not dest_file.exists():
                        dest_file.write_text(customized_content, encoding="utf-8")
                        file_tracker.track_file_creation(dest_file.relative_to(project_path))
                    elif category_confirmed:
                        dest_file.write_text(customized_content, encoding="utf-8")
                        file_tracker.track_file_modification(dest_file.relative_to(project_path))
                    elif not category_confirmed and existing_files:
                        # Individual file confirmation
                        if typer.confirm(f"Overwrite {dest_file.relative_to(project_path)}?"):
                            dest_file.write_text(customized_content, encoding="utf-8")
                            file_tracker.track_file_modification(dest_file.relative_to(project_path))
                        else:
                            console.print(f"[yellow]Skipped: [/yellow] {dest_file.relative_to(project_path)}")
                    else:
                        console.print(f"[yellow]Skipped: [/yellow] {dest_file.relative_to(project_path)}")

    # Handle app-specific instructions
    ai_tools_names = [AI_TOOLS[tool]["name"] for tool in ai_tools if tool in AI_TOOLS]
    console.print(f"[cyan]App type '{app_type}' templates installed for: {', '.join(ai_tools_names)}[/cyan]")


def get_app_specific_instructions(app_type: str) -> str:
    """Get app-specific development instructions."""
    if app_type == "mcp-server":
        return """### MCP Server Development

- Follow MCP protocol specifications
- Implement proper tool interfaces
- Include comprehensive error handling
- Test with multiple MCP clients

### Key Resources
- [MCP Protocol Docs](https://spec.modelcontextprotocol.io/)
- [MCP Examples](https://github.com/modelcontextprotocol)
"""
    elif app_type == "python-cli":
        return """### Python CLI Development

- Use typer for CLI framework with type hints
- Rich for beautiful terminal output and formatting
- Follow CLI UX best practices (progress, confirmations, help)
- Implement proper error handling and user feedback
- Support configuration and environment variables
- Include comprehensive testing with typer.testing

### Key Resources
- [Typer Documentation](https://typer.tiangolo.com/)
- [Rich Documentation](https://rich.readthedocs.io/)
- [CLI Best Practices](https://clig.dev/)
- [Python CLI Template](.github/instructions/CLIPythonDev.instructions.md)
"""

    return ""


@app.command()
def init(
    project_name: str = typer.Argument(
        None, help="Name for your new project directory (optional, defaults to current directory)"
    ),
    app_type: str = typer.Option(None, "--app-type", help="App type to build: mcp-server, python-cli"),
    ai_tools: str = typer.Option(
        None,
        "--ai-tools",
        help="AI tools to generate templates for (comma-separated): github-copilot (others coming soon)",
    ),
    ignore_agent_tools: bool = typer.Option(False, "--ignore-agent-tools", help="Skip checks for AI agent tools"),
    here: bool = typer.Option(
        True, "--here/--new-dir", help="Install templates in current directory (default) or create new directory"
    ),
    force: bool = typer.Option(False, "--force", help="Overwrite existing files without asking for confirmation"),
):
    """
    Install Improved-SDD templates for selected AI assistants in your project.

    This command will:
    1. Check that required tools are installed
    2. Let you choose your app type and AI assistant(s)
    3. Install custom templates for selected AI assistants
    4. Set up AI-specific configurations

    Examples:
        improved-sdd init                    # Install in current directory
        improved-sdd init --app-type mcp-server --ai-tools github-copilot,claude
        improved-sdd init my-project --new-dir   # Create new directory
        improved-sdd init --force            # Overwrite existing files without asking
    """

    # Show banner first
    show_banner()

    # Validate arguments
    if not here and not project_name:
        console.print("[red]Error:[/red] Must specify either a project name or use default --here mode")
        raise typer.Exit(1)

    # Determine project directory
    if here or not project_name:
        project_name = Path.cwd().name
        project_path = Path.cwd()

        # Check if current directory has any files
        existing_items = list(project_path.iterdir())
        if existing_items:
            console.print(f"[yellow]Installing templates in current directory: [/yellow] {project_path.name}")
            console.print(f"[dim]Found {len(existing_items)} existing items - templates will be added/merged[/dim]")
    else:
        project_path = Path(project_name).resolve()
        # Check if project directory already exists
        if project_path.exists():
            console.print(f"[red]Error: [/red] Directory '{project_name}' already exists")
            raise typer.Exit(1)

    # App type selection
    if app_type:
        if app_type not in APP_TYPES:
            console.print(
                f"[red]Error: [/red] Invalid app type '{app_type}'. " f"Choose from: {', '.join(APP_TYPES.keys())}"
            )
            raise typer.Exit(1)
        selected_app_type = app_type
    else:
        selected_app_type = select_app_type()

    # AI tools selection
    if ai_tools:
        # Parse comma-separated AI tools
        selected_ai_tools = [tool.strip() for tool in ai_tools.split(",")]
        # Validate AI tools
        invalid_tools = [tool for tool in selected_ai_tools if tool not in AI_TOOLS]
        if invalid_tools:
            console.print(
                f"[red]Error: [/red] Invalid AI tool(s): {', '.join(invalid_tools)}. "
                f"Choose from: {', '.join(AI_TOOLS.keys())}"
            )
            raise typer.Exit(1)
        # Show selected tools
        tool_names = [AI_TOOLS[tool]["name"] for tool in selected_ai_tools]
        console.print(f"[green]Selected AI tools: [/green] {', '.join(tool_names)}")
    else:
        selected_ai_tools = select_ai_tools()

    # Show panel with configuration information
    ai_tools_display = ", ".join([AI_TOOLS[tool]["name"] for tool in selected_ai_tools])
    console.print(
        Panel.fit(
            "[bold cyan]Install Improved-SDD Templates for AI Assistants[/bold cyan]"
            + "\n"
            + f"{'Installing in current directory:' if here or not project_name else 'Creating new project:'} "
            + f"[green]{project_path.name}[/green]"
            + (f"\n[dim]Path: {project_path}[/dim]" if here or not project_name else "")
            + f"\n[bold blue]App type: [/bold blue] [yellow]{selected_app_type}[/yellow]"
            + "\n[bold magenta]AI tools: [/bold magenta] "
            + f"[cyan]{ai_tools_display}[/cyan]",
            border_style="cyan",
        )
    )

    # Initialize file tracker
    file_tracker = FileTracker()

    try:
        # Install templates
        console.print("\n[cyan]Installing templates...[/cyan]")
        if not here and project_name:
            project_path.mkdir(parents=True, exist_ok=True)
            file_tracker.track_dir_creation(Path(project_name))
        create_project_structure(project_path, selected_app_type, selected_ai_tools, file_tracker, force)
        console.print("[green][OK][/green] Templates installed")

        # Configure AI assistants
        console.print("[cyan]Configuring AI assistants...[/cyan]")
        # Configuration is handled in create_project_structure
        console.print("[green][OK][/green] AI assistants configured")

        console.print("[green][OK][/green] Setup complete")

    except Exception as e:
        console.print(f"[red][ERROR][/red] Error: {e}")
        if not here and project_name and project_path.exists():
            shutil.rmtree(project_path)
        raise typer.Exit(1)

    # Final static display
    console.print("\n[bold green]Templates installed![/bold green]")

    # Show file summary
    console.print()
    file_summary_panel = Panel(
        file_tracker.get_summary(), title="[bold cyan]Files Summary[/bold cyan]", border_style="cyan", padding=(1, 2)
    )
    console.print(file_summary_panel)

    # Next steps
    steps_lines = []
    if not here and project_name:
        steps_lines.append(f"1. [bold green]cd {project_name}[/bold green]")
        step_num = 2
    else:
        steps_lines.append("1. Open VS Code in this directory")
        step_num = 2

    steps_lines.append(f"{step_num}. Use your selected AI assistant(s) with the installed templates:")
    for ai_tool in selected_ai_tools:
        if ai_tool in AI_TOOLS:
            tool_config = AI_TOOLS[ai_tool]
            if ai_tool == "github-copilot":
                ai_dir = ""  # Root .github directory
                template_path = ".github/"
            else:
                ai_dir = ai_tool.replace("-", "_")
                template_path = f".github/{ai_dir}/"
            steps_lines.append(f"   • [bold]{tool_config['name']}[/bold]: Reference `{template_path}` templates")
            ai_command = tool_config["keywords"].get("{AI_COMMAND}", "See instructions")
            steps_lines.append(f"     Command: {ai_command}")

    if selected_app_type == "mcp-server":
        steps_lines.append(f"{step_num + 1}. Review MCP protocol documentation and examples")
        step_num += 1
    elif selected_app_type == "python-cli":
        steps_lines.append(f"{step_num + 1}. Review Python CLI development guide in AI-specific instructions")
        step_num += 1

    step_num += 1
    steps_lines.append(f"{step_num}. Start your first feature using the spec-driven workflow")

    steps_panel = Panel("\n".join(steps_lines), title="Next steps", border_style="cyan", padding=(1, 2))
    console.print()
    console.print(steps_panel)


@app.command()
def delete(
    app_type: str = typer.Argument(None, help="App type to delete files for: mcp-server, python-cli"),
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
    show_banner()

    # Validate app type
    if app_type:
        if app_type not in APP_TYPES:
            console.print(
                f"[red]Error: [/red] Invalid app type '{app_type}'. " f"Choose from: {', '.join(APP_TYPES.keys())}"
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
        console.print(f"[yellow]No files found for app type '{selected_app_type}'[/yellow]")
        return

    console.print(f"[bold red]Files to be deleted for '{selected_app_type}': [/bold red]")
    console.print()

    if files_to_delete:
        console.print("[red]Files:[/red]")
        for file_path in sorted(files_to_delete):
            console.print(f"  🗑️  {file_path.relative_to(project_path)}")
        console.print()

    if dirs_to_delete:
        console.print("[red]Directories:[/red]")
        for dir_path in sorted(dirs_to_delete):
            console.print(f"  📁 {dir_path.relative_to(project_path)}")
        console.print()

    # Confirmation
    if not force:
        console.print("[bold yellow][WARN]  This action cannot be undone![/bold yellow]")
        confirmation = typer.prompt("Type 'Yes' to confirm deletion", type=str, default="")
        if confirmation != "Yes":
            console.print("[yellow]Deletion cancelled[/yellow]")
            return

    # Delete files
    console.print("[cyan]Deleting files...[/cyan]")

    deleted_files = 0
    deleted_dirs = 0

    for file_path in files_to_delete:
        try:
            file_path.unlink()
            console.print(f"[green][OK][/green] Deleted: {file_path.relative_to(project_path)}")
            deleted_files += 1
        except Exception as e:
            console.print(f"[red][ERROR][/red] Failed to delete {file_path.relative_to(project_path)}: {e}")

    # Delete directories (in reverse order to handle nested dirs)
    for dir_path in sorted(dirs_to_delete, reverse=True):
        try:
            if not list(dir_path.glob("*")):  # Only delete if empty
                dir_path.rmdir()
                console.print(f"[green][OK][/green] Deleted directory: {dir_path.relative_to(project_path)}")
                deleted_dirs += 1
        except Exception as e:
            console.print(f"[red][ERROR][/red] Failed to delete directory {dir_path.relative_to(project_path)}: {e}")

    console.print(f"\n[green][OK][/green] Deletion complete: {deleted_files} files, {deleted_dirs} directories removed")


@app.command()
def check():
    """Check that all required tools are installed."""
    show_banner()
    console.print("[bold]Checking Improved-SDD requirements...[/bold]\n")

    console.print("[cyan]Required tools:[/cyan]")
    python_ok = check_tool("python", "Install from: https://python.org/downloads")

    console.print("\n[cyan]AI Assistant tools (optional):[/cyan]")
    claude_ok = check_tool(
        "claude", "Install from: https://docs.anthropic.com/en/docs/claude-code/setup", optional=True
    )
    copilot_ok = check_github_copilot()

    # Collect missing optional tools
    missing_tools = []
    if not claude_ok:
        missing_tools.append("Claude")
    if not copilot_ok:
        missing_tools.append("VS Code/GitHub Copilot")

    console.print("\n[green][OK] Improved-SDD CLI is ready to use![/green]")

    if not python_ok:
        console.print("[red]Python is required for this tool to work.[/red]")
        raise typer.Exit(1)

    # Offer user choice for missing optional tools
    if missing_tools:
        if not offer_user_choice(missing_tools):
            raise typer.Exit(1)
    else:
        console.print("[green][OK] All AI assistant tools are available![/green]")


def main():
    app()


if __name__ == "__main__":
    main()
