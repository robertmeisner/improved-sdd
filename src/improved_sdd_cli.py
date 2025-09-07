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

import shutil
import sys
from pathlib import Path

import typer
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
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


def create_project_structure(
    project_path: Path, app_type: str, ai_tools: list[str], file_tracker: FileTracker, force: bool = False
) -> None:
    """Install Improved-SDD templates into the project directory for selected AI tools."""

    # Get the CLI script directory (where this script is located)
    script_dir = Path(__file__).parent
    templates_source = script_dir.parent / "templates"

    # Copy template files if they exist
    if templates_source.exists():
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
