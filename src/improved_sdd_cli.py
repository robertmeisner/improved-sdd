#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer",
#     "rich",
#     "platformdirs",
#     "readchar",
#     "httpx",
# ]
# ///
"""
Improved-SDD CLI - Setup tool for Improved Spec-Driven Development projects

Usage:
    uvx improved-sdd-cli.py init <project-name>
    uvx improved-sdd-cli.py init --here

Or install globally:
    uv tool install --from improved-sdd-cli.py improved-sdd
    improved-sdd init <project-name>
    improved-sdd init --here
"""

import os
import subprocess
import sys
import shutil
import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.table import Table
from rich.tree import Tree
from typer.core import TyperGroup

# For cross-platform keyboard input
import readchar

# Constants
APP_TYPES = {
    "mcp-server": "MCP Server - Model Context Protocol server for AI integrations"
}

# ASCII Art Banner
BANNER = """
╦╔╦╗╔═╗╦═╗╔═╗╦  ╦╔═╗╔╦╗  ╔═╗╔╦╗╔╦╗
║║║║╠═╝╠╦╝║ ║╚╗╔╝║╣  ║║  ╚═╗ ║║ ║║
╩╩ ╩╩  ╩╚═╚═╝ ╚╝ ╚═╝═╩╝  ╚═╝═╩╝═╩╝
"""

TAGLINE = "Spec-Driven Development for Copilot Studio"

class StepTracker:
    """Track and render hierarchical steps without emojis, similar to Claude Code tree output."""
    
    def __init__(self, title: str):
        self.title = title
        self.steps = []  # list of dicts: {key, label, status, detail}
        self.status_order = {"pending": 0, "running": 1, "done": 2, "error": 3, "skipped": 4}
        self._refresh_cb = None
        
    def attach_refresh(self, cb):
        self._refresh_cb = cb
        
    def add(self, key: str, label: str):
        if key not in [s["key"] for s in self.steps]:
            self.steps.append({"key": key, "label": label, "status": "pending", "detail": ""})
        self._maybe_refresh()
        
    def start(self, key: str, detail: str = ""):
        self._update(key, status="running", detail=detail)
        
    def complete(self, key: str, detail: str = ""):
        self._update(key, status="done", detail=detail)
        
    def error(self, key: str, detail: str = ""):
        self._update(key, status="error", detail=detail)
        
    def skip(self, key: str, detail: str = ""):
        self._update(key, status="skipped", detail=detail)
        
    def _update(self, key: str, status: str, detail: str):
        for s in self.steps:
            if s["key"] == key:
                s["status"] = status
                if detail:
                    s["detail"] = detail
                self._maybe_refresh()
                return
        # If not present, add it
        self.steps.append({"key": key, "label": key, "status": status, "detail": detail})
        self._maybe_refresh()
        
    def _maybe_refresh(self):
        if self._refresh_cb:
            try:
                self._refresh_cb()
            except Exception:
                pass
                
    def render(self):
        tree = Tree(f"[bold cyan]{self.title}[/bold cyan]", guide_style="grey50")
        for step in self.steps:
            label = step["label"]
            detail_text = step["detail"].strip() if step["detail"] else ""
            
            # Status symbols
            status = step["status"]
            if status == "done":
                symbol = "[green]●[/green]"
            elif status == "pending":
                symbol = "[green dim]○[/green dim]"
            elif status == "running":
                symbol = "[cyan]○[/cyan]"
            elif status == "error":
                symbol = "[red]●[/red]"
            elif status == "skipped":
                symbol = "[yellow]○[/yellow]"
            else:
                symbol = " "
                
            if status == "pending":
                # Pending items in light gray
                if detail_text:
                    line = f"{symbol} [bright_black]{label} ({detail_text})[/bright_black]"
                else:
                    line = f"{symbol} [bright_black]{label}[/bright_black]"
            else:
                # Active/completed items
                if detail_text:
                    line = f"{symbol} [white]{label}[/white] [bright_black]({detail_text})[/bright_black]"
                else:
                    line = f"{symbol} [white]{label}[/white]"
                    
            tree.add(line)
        return tree

def get_key():
    """Get a single keypress in a cross-platform way using readchar."""
    key = readchar.readkey()
    
    # Arrow keys
    if key == readchar.key.UP:
        return 'up'
    if key == readchar.key.DOWN:
        return 'down'
    
    # Enter/Return
    if key == readchar.key.ENTER:
        return 'enter'
    
    # Escape
    if key == readchar.key.ESC:
        return 'escape'
        
    # Ctrl+C
    if key == readchar.key.CTRL_C:
        raise KeyboardInterrupt

    return key

def select_with_arrows(options: dict, prompt_text: str = "Select an option", default_key: str = None) -> str:
    """Interactive selection using arrow keys with Rich display."""
    option_keys = list(options.keys())
    if default_key and default_key in option_keys:
        selected_index = option_keys.index(default_key)
    else:
        selected_index = 0
    
    selected_key = None

    def create_selection_panel():
        """Create the selection panel with current selection highlighted."""
        table = Table.grid(padding=(0, 2))
        table.add_column(style="bright_cyan", justify="left", width=3)
        table.add_column(style="white", justify="left")
        
        for i, key in enumerate(option_keys):
            if i == selected_index:
                table.add_row("▶", f"[bright_cyan]{key}: {options[key]}[/bright_cyan]")
            else:
                table.add_row(" ", f"[white]{key}: {options[key]}[/white]")
        
        table.add_row("", "")
        table.add_row("", "[dim]Use ↑/↓ to navigate, Enter to select, Esc to cancel[/dim]")
        
        return Panel(
            table,
            title=f"[bold]{prompt_text}[/bold]",
            border_style="cyan",
            padding=(1, 2)
        )
    
    console.print()

    def run_selection_loop():
        nonlocal selected_key, selected_index
        from rich.live import Live
        
        with Live(create_selection_panel(), console=console, transient=True, auto_refresh=False) as live:
            while True:
                try:
                    key = get_key()
                    if key == 'up':
                        selected_index = (selected_index - 1) % len(option_keys)
                    elif key == 'down':
                        selected_index = (selected_index + 1) % len(option_keys)
                    elif key == 'enter':
                        selected_key = option_keys[selected_index]
                        break
                    elif key == 'escape':
                        console.print("\n[yellow]Selection cancelled[/yellow]")
                        raise typer.Exit(1)
                    
                    live.update(create_selection_panel(), refresh=True)

                except KeyboardInterrupt:
                    console.print("\n[yellow]Selection cancelled[/yellow]")
                    raise typer.Exit(1)

    run_selection_loop()
    
    if selected_key is None:
        console.print("\n[red]Selection failed.[/red]")
        raise typer.Exit(1)
        
    return selected_key

console = Console()

class BannerGroup(TyperGroup):
    """Custom group that shows banner before help."""
    
    def format_help(self, ctx, formatter):
        # Show banner before help
        show_banner()
        super().format_help(ctx, formatter)

app = typer.Typer(
    name="improved-sdd",
    help="Setup tool for Improved Spec-Driven Development projects",
    add_completion=False,
    invoke_without_command=True,
    cls=BannerGroup,
)

def show_banner():
    """Display the ASCII art banner."""
    banner_lines = BANNER.strip().split('\n')
    colors = ["bright_blue", "blue", "cyan", "bright_cyan", "white", "bright_white"]
    
    styled_banner = Text()
    for i, line in enumerate(banner_lines):
        color = colors[i % len(colors)]
        styled_banner.append(line + "\n", style=color)
    
    console.print(Align.center(styled_banner))
    console.print(Align.center(Text(TAGLINE, style="italic bright_yellow")))
    console.print()

@app.callback()
def callback(ctx: typer.Context):
    """Show banner when no subcommand is provided."""
    if ctx.invoked_subcommand is None and "--help" not in sys.argv and "-h" not in sys.argv:
        show_banner()
        console.print(Align.center("[dim]Run 'improved-sdd --help' for usage information[/dim]"))
        console.print()

def run_command(cmd: list[str], check_return: bool = True, capture: bool = False, shell: bool = False) -> Optional[str]:
    """Run a shell command and optionally capture output."""
    try:
        if capture:
            result = subprocess.run(cmd, check=check_return, capture_output=True, text=True, shell=shell)
            return result.stdout.strip()
        else:
            subprocess.run(cmd, check=check_return, shell=shell)
            return None
    except subprocess.CalledProcessError as e:
        if check_return:
            console.print(f"[red]Error running command:[/red] {' '.join(cmd)}")
            console.print(f"[red]Exit code:[/red] {e.returncode}")
            if hasattr(e, 'stderr') and e.stderr:
                console.print(f"[red]Error output:[/red] {e.stderr}")
            raise
        return None

def check_tool(tool: str, install_hint: str) -> bool:
    """Check if a tool is installed."""
    if shutil.which(tool):
        console.print(f"[green]✓[/green] {tool} found")
        return True
    else:
        console.print(f"[yellow]⚠️  {tool} not found[/yellow]")
        console.print(f"   Install with: [cyan]{install_hint}[/cyan]")
        return False

def is_git_repo(path: Path = None) -> bool:
    """Check if the specified path is inside a git repository."""
    if path is None:
        path = Path.cwd()
    
    if not path.is_dir():
        return False

    try:
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            check=True,
            capture_output=True,
            cwd=path,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def init_git_repo(project_path: Path, quiet: bool = False) -> bool:
    """Initialize a git repository in the specified path."""
    try:
        original_cwd = Path.cwd()
        os.chdir(project_path)
        if not quiet:
            console.print("[cyan]Initializing git repository...[/cyan]")
        subprocess.run(["git", "init"], check=True, capture_output=True)
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit from Improved-SDD template"], check=True, capture_output=True)
        if not quiet:
            console.print("[green]✓[/green] Git repository initialized")
        return True
        
    except subprocess.CalledProcessError as e:
        if not quiet:
            console.print(f"[red]Error initializing git repository:[/red] {e}")
        return False
    finally:
        os.chdir(original_cwd)

def select_app_type() -> str:
    """Interactive app type selection with arrow key navigation."""
    console.print("\n🔧 What kind of app are you building?")
    
    return select_with_arrows(
        APP_TYPES, 
        "Choose your app type:", 
        "mcp-server"
    )

def create_project_structure(project_path: Path, app_type: str) -> None:
    """Install Improved-SDD templates into the project directory for GitHub Copilot."""
    
    # Get the CLI script directory (where this script is located)
    script_dir = Path(__file__).parent
    templates_source = script_dir.parent / "templates"
    
    # For GitHub Copilot, we install templates in specific locations
    # .github/copilot-instructions.md - Main instructions
    # .vscode/prompts/ - Custom prompts for Copilot
    # .copilot/ - Custom templates and configurations
    
    copilot_dirs = [
        ".github",
        ".vscode/prompts", 
        ".copilot/chatmodes",
        ".copilot/instructions",
        ".copilot/prompts",
        ".copilot/commands"
    ]
    
    for dir_path in copilot_dirs:
        full_path = project_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
    
    # Copy templates to .copilot directory for reference
    if templates_source.exists():
        shutil.copytree(templates_source, project_path / ".copilot", dirs_exist_ok=True)
    
    # Copy key templates to .vscode/prompts for direct Copilot access
    if templates_source.exists():
        prompts_source = templates_source / "prompts"
        if prompts_source.exists():
            shutil.copytree(prompts_source, project_path / ".vscode" / "prompts", dirs_exist_ok=True)
    
    # Create .github/copilot-instructions.md for GitHub Copilot Studio
    copilot_instructions = f"""# Improved-SDD Development Instructions

This project follows the Improved Spec-Driven Development methodology for **{APP_TYPES.get(app_type, app_type)}**.

## Core Principles

- Requirements → Design → Implementation → Validation
- Template-driven AI interactions
- Code minimalism and quality
- GitHub Copilot Studio integration

## Workflow

Use the templates in `.copilot/` and `.vscode/prompts/` to guide development:
- `.copilot/chatmodes/` for AI behavior patterns
- `.copilot/instructions/` for context-specific guidance
- `.copilot/prompts/` for structured interactions
- `.vscode/prompts/` for direct Copilot prompt access

## Quality Standards

Follow the Improved-SDD constitutional framework for all development work.

## App-Specific Guidelines

{get_app_specific_instructions(app_type)}

## Template Usage

1. **For GitHub Copilot Chat**: Reference templates in `.copilot/` directory
2. **For VS Code Prompts**: Use files in `.vscode/prompts/` directory  
3. **For Spec Development**: Follow the spec-driven workflow with chatmodes

## Quick Start

1. Open this project in VS Code
2. Use Ctrl+Shift+P → "Chat: Open Chat" to start GitHub Copilot
3. Reference the chatmodes and prompts for structured development
4. Follow the spec-driven workflow: Requirements → Design → Implementation

"""
    (project_path / ".github" / "copilot-instructions.md").write_text(copilot_instructions, encoding='utf-8')

    # Create a simple README if it doesn't exist
    readme_path = project_path / "README.md"
    if not readme_path.exists():
        readme_content = f"""# {project_path.name}

A GitHub Copilot Studio project with Improved Spec-Driven Development templates.

## App Type: {APP_TYPES.get(app_type, app_type)}

This project is configured with custom templates for GitHub Copilot Studio development.

## Quick Start

1. Open in VS Code
2. Use GitHub Copilot with the templates in `.copilot/` and `.vscode/prompts/`
3. Follow the spec-driven development workflow
4. Reference `.github/copilot-instructions.md` for detailed guidance

## Templates Available

- **Chatmodes**: `.copilot/chatmodes/` - AI behavior patterns
- **Instructions**: `.copilot/instructions/` - Context-specific guidance
- **Prompts**: `.copilot/prompts/` and `.vscode/prompts/` - Reusable interactions
- **Commands**: `.copilot/commands/` - Command definitions

{get_app_specific_readme_section(app_type)}
"""
        readme_path.write_text(readme_content, encoding='utf-8')

def get_app_specific_readme_section(app_type: str) -> str:
    """Get app-specific README section."""
    if app_type == "mcp-server":
        return """
## MCP Server Development

This project is set up for Model Context Protocol server development:

- Follow MCP protocol specifications
- Use TypeScript for type safety
- Implement proper tool interfaces
- Include comprehensive error handling
- Test with multiple MCP clients

### Resources

- [MCP Documentation](https://spec.modelcontextprotocol.io/)
- [MCP Examples](https://github.com/modelcontextprotocol)
"""
    
    return ""

def get_app_specific_instructions(app_type: str) -> str:
    """Get app-specific development instructions."""
    if app_type == "mcp-server":
        return """### MCP Server Development

- Follow MCP protocol specifications
- Implement proper tool interfaces
- Use TypeScript for type safety
- Include comprehensive error handling
- Document all available tools and resources
- Test with multiple MCP clients"""
    
    return "Follow general development best practices."

@app.command()
def init(
    project_name: str = typer.Argument(None, help="Name for your new project directory (optional, defaults to current directory)"),
    app_type: str = typer.Option(None, "--app-type", help="App type to build: mcp-server"),
    ignore_agent_tools: bool = typer.Option(False, "--ignore-agent-tools", help="Skip checks for AI agent tools"),
    no_git: bool = typer.Option(False, "--no-git", help="Skip git repository initialization"),
    here: bool = typer.Option(True, "--here/--new-dir", help="Install templates in current directory (default) or create new directory"),
):
    """
    Install Improved-SDD templates for GitHub Copilot Studio in your project.
    
    This command will:
    1. Check that required tools are installed (git is optional)
    2. Let you choose your app type
    3. Install custom templates for GitHub Copilot
    4. Set up GitHub Copilot Studio configurations
    5. Initialize a git repository (if not --no-git and not already a repo)
    
    Examples:
        improved-sdd init                    # Install in current directory
        improved-sdd init --app-type mcp-server --no-git
        improved-sdd init my-project --new-dir   # Create new directory
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
            console.print(f"[yellow]Installing templates in current directory:[/yellow] {project_path.name}")
            console.print(f"[dim]Found {len(existing_items)} existing items - templates will be added/merged[/dim]")
    else:
        project_path = Path(project_name).resolve()
        # Check if project directory already exists
        if project_path.exists():
            console.print(f"[red]Error:[/red] Directory '{project_name}' already exists")
            raise typer.Exit(1)
    
    console.print(Panel.fit(
        "[bold cyan]Install Improved-SDD Templates for GitHub Copilot Studio[/bold cyan]\n"
        f"{'Installing in current directory:' if here or not project_name else 'Creating new project:'} [green]{project_path.name}[/green]"
        + (f"\n[dim]Path: {project_path}[/dim]" if here or not project_name else ""),
        border_style="cyan"
    ))
    
    # Check git availability
    git_available = True
    if not no_git:
        git_available = check_tool("git", "https://git-scm.com/downloads")
        if not git_available:
            console.print("[yellow]Git not found - will skip repository initialization[/yellow]")

    # App type selection
    if app_type:
        if app_type not in APP_TYPES:
            console.print(f"[red]Error:[/red] Invalid app type '{app_type}'. Choose from: {', '.join(APP_TYPES.keys())}")
            raise typer.Exit(1)
        selected_app_type = app_type
    else:
        selected_app_type = select_app_type()
    
    # Create project with progress tracking
    tracker = StepTracker("Install Improved-SDD Templates for Copilot Studio")
    
    # Add steps
    tracker.add("precheck", "Check required tools")
    tracker.complete("precheck", "ok")
    tracker.add("app-select", "Select app type")  
    tracker.complete("app-select", f"{selected_app_type}")
    tracker.add("templates", "Install Copilot templates")
    tracker.add("config", "Configure GitHub Copilot")
    if not no_git and not is_git_repo(project_path):
        tracker.add("git", "Initialize git repository")
    tracker.add("final", "Finalize setup")
    
    from rich.live import Live
    
    with Live(tracker.render(), console=console, refresh_per_second=8, transient=True) as live:
        tracker.attach_refresh(lambda: live.update(tracker.render()))
        
        try:
            # Install templates
            tracker.start("templates")
            if not here and project_name:
                project_path.mkdir(parents=True, exist_ok=True)
            create_project_structure(project_path, selected_app_type)
            tracker.complete("templates", "templates installed to .copilot/ and .vscode/")
            
            # Configure Copilot
            tracker.start("config")
            # Configuration is handled in create_project_structure
            tracker.complete("config", "GitHub Copilot configured")
            
            # Git initialization
            if not no_git and not is_git_repo(project_path):
                tracker.start("git")
                if git_available:
                    if init_git_repo(project_path, quiet=True):
                        tracker.complete("git", "initialized")
                    else:
                        tracker.error("git", "init failed")
                else:
                    tracker.skip("git", "git not available")
            
            tracker.complete("final", "templates ready for GitHub Copilot")
            
        except Exception as e:
            tracker.error("final", str(e))
            if not here and project_name and project_path.exists():
                shutil.rmtree(project_path)
            raise typer.Exit(1)
    
    # Final static display
    console.print(tracker.render())
    console.print("\n[bold green]Templates installed![/bold green]")
    
    # Next steps
    steps_lines = []
    if not here and project_name:
        steps_lines.append(f"1. [bold green]cd {project_name}[/bold green]")
        step_num = 2
    else:
        steps_lines.append("1. Open VS Code in this directory")
        step_num = 2

    steps_lines.append(f"{step_num}. Use GitHub Copilot with the installed templates:")
    steps_lines.append(f"   • Reference `.copilot/chatmodes/` for AI behavior patterns")
    steps_lines.append(f"   • Use `.vscode/prompts/` for direct prompt access")
    steps_lines.append(f"   • Check `.github/copilot-instructions.md` for guidance")
    if selected_app_type == "mcp-server":
        steps_lines.append(f"{step_num + 1}. Review MCP protocol documentation and examples")
        step_num += 1

    step_num += 1
    steps_lines.append(f"{step_num}. Start your first feature using the spec-driven workflow")
    steps_lines.append(f"{step_num + 1}. Use Ctrl+Shift+P → 'Chat: Open Chat' to start GitHub Copilot")

    steps_panel = Panel("\n".join(steps_lines), title="Next steps", border_style="cyan", padding=(1,2))
    console.print()
    console.print(steps_panel)

@app.command()
def check():
    """Check that all required tools are installed."""
    show_banner()
    console.print("[bold]Checking Improved-SDD requirements...[/bold]\n")
    
    console.print("[cyan]Required tools:[/cyan]")
    python_ok = check_tool("python", "Install from: https://python.org/downloads")
    
    console.print("\n[cyan]Optional tools:[/cyan]")
    git_ok = check_tool("git", "Install from: https://git-scm.com/downloads")
    
    console.print("\n[cyan]AI Assistant tools:[/cyan]")
    claude_ok = check_tool("claude", "Install from: https://docs.anthropic.com/en/docs/claude-code/setup")
    
    console.print(f"\n[green]✓ Improved-SDD CLI is ready to use![/green]")
    if not python_ok:
        console.print("[red]Python is required for this tool to work.[/red]")
        raise typer.Exit(1)
    if not git_ok:
        console.print("[yellow]Consider installing git for repository management[/yellow]")

def main():
    app()

if __name__ == "__main__":
    main()