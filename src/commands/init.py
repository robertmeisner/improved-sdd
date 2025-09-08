"""Init command implementation for Improved-SDD CLI.

This module contains the init command logic for installing templates
and setting up AI-optimized development environments.
"""

import shutil
from pathlib import Path

import typer

from ..core import AI_TOOLS, APP_TYPES
from ..services import FileTracker
from ..ui import console_manager


def init_command(
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
        True,
        "--here/--new-dir",
        help="Install templates in current directory (default) or create new directory",
    ),
    force: bool = typer.Option(False, "--force", help="Overwrite existing files without asking for confirmation"),
    offline: bool = typer.Option(
        False,
        "--offline",
        help="Force offline mode - disable GitHub downloads and use only local/bundled templates",
    ),
    force_download: bool = typer.Option(
        False, "--force-download", help="Force GitHub download even if local templates exist"
    ),
    template_repo: str = typer.Option(
        None, "--template-repo", help="Custom GitHub repository for templates (format: owner/repo)"
    ),
) -> None:
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
        improved-sdd init --offline          # Use only local/bundled templates (no GitHub download)
        improved-sdd init --force-download   # Force GitHub download even with local templates
        improved-sdd init --template-repo user/repo  # Use custom GitHub repository for templates
    """
    from rich.console import Console

    from ..utils import create_project_structure, select_ai_tools, select_app_type

    # Show banner first
    console_manager.show_banner()

    # Validate arguments
    if not here and not project_name:
        console_manager.print_error("Must specify either a project name or use default --here mode")
        raise typer.Exit(1)

    # Validate template options
    if offline and force_download:
        console_manager.print_error("Cannot use --offline and --force-download together")
        raise typer.Exit(1)

    if template_repo and "/" not in template_repo:
        console_manager.print_error("--template-repo must be in format 'owner/repo'")
        raise typer.Exit(1)

    # Determine project directory
    if here or not project_name:
        project_name = Path.cwd().name
        project_path = Path.cwd()

        # Check if current directory has any files
        existing_items = list(project_path.iterdir())
        if existing_items:
            console_manager.print_warning(f"Installing templates in current directory: {project_path.name}")
            console_manager.print_dim(f"Found {len(existing_items)} existing items - templates will be added/merged")
    else:
        project_path = Path.cwd() / project_name
        # Check if project directory already exists
        if project_path.exists() and not force:
            console_manager.print_error(f"Directory '{project_name}' already exists")
            raise typer.Exit(1)

    # App type selection
    if app_type:
        if app_type not in APP_TYPES:
            console_manager.print_error(f"Invalid app type '{app_type}'. Choose from: {', '.join(APP_TYPES.keys())}")
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
            console_manager.print_error(
                f"Invalid AI tool(s): {', '.join(invalid_tools)}. Choose from: {', '.join(AI_TOOLS.keys())}"
            )
            raise typer.Exit(1)
        # Show selected tools
        tool_names = [AI_TOOLS[tool]["name"] for tool in selected_ai_tools]
        console_manager.print(f"[green]Selected AI tools: [/green] {', '.join(tool_names)}")
    else:
        selected_ai_tools = select_ai_tools()

    # Show panel with configuration information
    ai_tools_display = ", ".join([AI_TOOLS[tool]["name"] for tool in selected_ai_tools])
    panel_content = (
        "[bold cyan]Install Improved-SDD Templates for AI Assistants[/bold cyan]"
        + "\n"
        + f"{'Installing in current directory:' if here or not project_name else 'Creating new project:'} "
        + f"[green]{project_path.name}[/green]"
        + (f"\n[dim]Path: {project_path}[/dim]" if here or not project_name else "")
        + f"\n[bold blue]App type: [/bold blue] [yellow]{selected_app_type}[/yellow]"
        + "\n[bold magenta]AI tools: [/bold magenta] "
        + f"[cyan]{ai_tools_display}[/cyan]"
    )
    console_manager.show_panel(panel_content, "", "cyan")

    # Initialize file tracker
    file_tracker = FileTracker()

    try:
        # Install templates
        console_manager.print_newline()
        console_manager.print_info("Installing templates...")
        if not here and project_name:
            project_path.mkdir(parents=True, exist_ok=True)
            file_tracker.track_dir_creation(Path(project_name))
        create_project_structure(
            project_path,
            selected_app_type,
            selected_ai_tools,
            file_tracker,
            force,
            offline,
            force_download,
            template_repo,
        )
        console_manager.print_success("Templates installed")

        # Configure AI assistants
        console_manager.print_info("Configuring AI assistants...")
        # Configuration is handled in create_project_structure
        console_manager.print_success("AI assistants configured")

        console_manager.print_success("Setup complete")

    except Exception as e:
        console_manager.print_error(f"Error: {e}")
        if not here and project_name and project_path.exists():
            shutil.rmtree(project_path)
        raise typer.Exit(1)

    # Final static display
    console_manager.print("\n[bold green]Templates installed![/bold green]")

    # Show file summary
    console_manager.print_newline()
    console_manager.show_panel(file_tracker.get_summary(), "[bold cyan]Files Summary[/bold cyan]", "cyan")

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

    # Lazy import Panel when needed
    from rich.panel import Panel

    steps_panel = Panel("\n".join(steps_lines), title="Next steps", border_style="cyan", padding=(1, 2))
    console = Console()
    console.print()
    console.print(steps_panel)
    raise typer.Exit(0)
