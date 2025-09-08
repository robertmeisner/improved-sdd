"""Shared utilities for Improved-SDD CLI.

This module contains utility functions that are shared across multiple
command modules to avoid circular imports.
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional

import typer

# Import configuration and UI components
from .core import AI_TOOLS, APP_TYPES
from .services import FileTracker, TemplateResolver
from .ui import console_manager


def check_tool(tool: str, install_hint: str, optional: bool = False) -> bool:
    """Check if a tool is installed and available in system PATH.

    Args:
        tool: Name of the tool/command to check for
        install_hint: Installation instructions to display if tool is missing
        optional: Whether the tool is optional (affects display formatting)

    Returns:
        bool: True if tool is installed and available, False otherwise
    """
    if shutil.which(tool):
        console_manager.print_status(tool, True)
        return True
    else:
        console_manager.print_status(tool, False, install_hint, optional)
        return False


def check_github_copilot() -> bool:
    """Check if GitHub Copilot is available in VS Code.

    Verifies VS Code installation and provides guidance for GitHub Copilot setup.
    Note: Does not verify actual Copilot extension installation.

    Returns:
        bool: True if VS Code is installed, False otherwise
    """
    # Check for VS Code installation
    vscode_found = shutil.which("code") is not None

    if vscode_found:
        console_manager.print_success("VS Code found")
        console_manager.print_dim("Note: GitHub Copilot availability depends on VS Code extensions")
        console_manager.print_dim(
            "Open VS Code and check if Copilot extension is installed and activated"
        )
        return True
    else:
        console_manager.print_warning("VS Code not found")
        console_manager.print(
            "   Install with: [cyan]https://code.visualstudio.com/download[/cyan]"
        )
        console_manager.print_dim("Then install GitHub Copilot extension from VS Code marketplace")
        return False


def offer_user_choice(missing_tools: List[str]) -> bool:
    """Offer user choice when optional AI tools are missing.

    Displays missing tools and asks user if they want to continue
    without them or install them first.

    Args:
        missing_tools: List of missing AI tool names

    Returns:
        bool: True if user chooses to continue, False if they want to install tools first
    """
    if not missing_tools:
        return True

    console_manager.print(f"\n[yellow]Missing optional tools: {', '.join(missing_tools)}[/yellow]")
    console_manager.print_dim(
        "These tools enhance the development experience but are not required."
    )

    # Check if we're in CI/automation mode
    if os.getenv("CI") or os.getenv("GITHUB_ACTIONS"):
        console_manager.print_success("Continuing with available tools (CI mode)...")
        return True

    try:
        choice = (
            typer.prompt("\nWould you like to continue anyway? (y/n)", type=str, default="y")
            .lower()
            .strip()
        )

        if choice in ["y", "yes"]:
            console_manager.print_success("Continuing with available tools...")
            return True
        else:
            console_manager.print_warning(
                "Setup cancelled. Please install the missing tools and try again."
            )
            return False

    except (typer.Abort, KeyboardInterrupt):
        console_manager.print_warning("\nSetup cancelled")
        return False


def select_app_type() -> str:
    """Interactive app type selection with fallback to simple prompt.

    Displays available application types and prompts user to select one.
    Provides descriptions for each app type to help user decide.

    Returns:
        str: Selected application type key from APP_TYPES configuration

    Raises:
        typer.Abort: If user cancels the selection
    """
    console_manager.print("\n🔧 What kind of app are you building?")

    # Use simple numbered selection to avoid terminal compatibility issues
    option_keys = list(APP_TYPES.keys())

    console_manager.print_newline()
    for i, key in enumerate(option_keys, 1):
        console_manager.print(
            f"[cyan]{i}.[/cyan] [white]{key}[/white]: {APP_TYPES[key]['description']}"
        )

    console_manager.print_newline()

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
                console_manager.print(f"[green]Selected: [/green] {selected}")
                return selected
            else:
                console_manager.print_error(
                    f"Please enter a number between 1 and {len(option_keys)}"
                )
        except ValueError:
            console_manager.print_error("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            console_manager.print_warning("\nSelection cancelled")
            raise typer.Exit(1)


def select_ai_tools() -> List[str]:
    """Interactive AI tool selection with multi-selection support.

    Displays available AI tools and allows user to select multiple tools.
    Templates will be customized for each selected AI assistant.

    Returns:
        List[str]: List of selected AI tool keys from AI_TOOLS configuration

    Raises:
        typer.Exit: If user cancels the selection
    """
    console_manager.print("\n🤖 Which AI assistant(s) do you want to generate templates for?")
    console_manager.print_dim(
        "You can select multiple tools (templates will be customized for each)"
    )

    # Use simple numbered selection
    tool_keys = list(AI_TOOLS.keys())

    console_manager.print_newline()
    for i, key in enumerate(tool_keys, 1):
        tool_info = AI_TOOLS[key]
        if key == "github-copilot":
            # GitHub Copilot is available now
            console_manager.print(
                f"[cyan]{i}.[/cyan] [white]{tool_info['name']}[/white]: {tool_info['description']}"
            )
        else:
            # Other tools are coming soon
            console_manager.print(
                f"[dim cyan]{i}.[/dim cyan] [dim white]{tool_info['name']}[/dim white]: "
                f"[dim]{tool_info['description']}[/dim] [yellow](coming soon)[/yellow]"
            )

    console_manager.print_dim(
        "\nEnter numbers separated by commas (e.g., 1,2) or 'all' for all tools"
    )
    console_manager.print_newline()

    while True:
        try:
            # Use input() instead of typer.prompt to avoid issues with defaults
            user_input = (
                input(f"Select options (1-{len(tool_keys)}) [default: 1]: ").strip().lower()
            )

            # Handle empty input (use default)
            if not user_input:
                choice = "1"
            else:
                choice = user_input

            if choice == "all":
                selected = tool_keys.copy()
                console_manager.print(
                    f"[green]Selected: [/green] All AI tools ({len(selected)} tools)"
                )
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
                console_manager.print(f"[green]Selected: [/green] {', '.join(tool_names)}")
                return selected
            else:
                console_manager.print_error("Please select at least one option")

        except ValueError as e:
            console_manager.print_error(f"Invalid input: {e}. Please try again.")
        except KeyboardInterrupt:
            console_manager.print_warning("\nSelection cancelled")
            raise typer.Exit(1)


def customize_template_content(content: str, ai_tool: str) -> str:
    """Customize template content for specific AI tool by replacing keywords.

    Replaces AI-tool-specific keywords in template content with appropriate
    replacements defined in the AI_TOOLS configuration.

    Args:
        content: Template content to customize
        ai_tool: AI tool key for which to customize content

    Returns:
        str: Customized template content with replaced keywords
    """
    if ai_tool not in AI_TOOLS:
        return content

    tool_config = AI_TOOLS[ai_tool]
    customized_content = content

    # Replace AI-specific keywords
    for keyword, replacement in tool_config["keywords"].items():
        customized_content = customized_content.replace(keyword, replacement)

    return customized_content


def get_template_filename(original_name: str, ai_tool: str, template_type: str) -> str:
    """Generate AI-specific template filename.

    Creates appropriate filename for AI tool templates based on template type
    and AI tool configuration.

    Args:
        original_name: Original template filename
        ai_tool: AI tool key for filename customization
        template_type: Type of template (e.g., 'chatmodes', 'instructions')

    Returns:
        str: Customized filename for the AI tool
    """
    if ai_tool not in AI_TOOLS:
        return original_name

    tool_config = AI_TOOLS[ai_tool]

    # Split the original name to get base name without extensions
    parts = original_name.split(".")
    if len(parts) >= 2:  # Has extension
        base_name = ".".join(parts[:-1])
    else:
        base_name = original_name

    # Map template types to extension keys (handle plural to singular mapping)
    extension_key_map = {
        "chatmodes": "chatmodes",  # maps to file_extensions.chatmodes
        "instructions": "instructions",  # maps to file_extensions.instructions
        "prompts": "prompts",  # maps to file_extensions.prompts
        "commands": "commands",  # maps to file_extensions.commands
    }

    extension_key = extension_key_map.get(template_type, template_type)
    extension = tool_config["file_extensions"].get(extension_key, ".md")

    # For GitHub Copilot, use simple .md extension to avoid double extensions
    if ai_tool == "github-copilot":
        # Already has .md from template, don't add another
        if base_name.endswith((".copilot", ".chatmode", ".instruction", ".prompt", ".command")):
            return f"{base_name}.md"
        else:
            return f"{base_name}.copilot.md"
    else:
        # For other tools, use configured extension
        return f"{base_name}{extension}"


def create_project_structure(
    project_path: Path,
    app_type: str,
    ai_tools: List[str],
    file_tracker: FileTracker,
    force: bool = False,
    offline: bool = False,
    force_download: bool = False,
    template_repo: Optional[str] = None,
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
    resolver = TemplateResolver(
        project_path, offline=offline, force_download=force_download, template_repo=template_repo
    )
    resolution_result = resolver.resolve_templates_with_transparency()

    if not resolution_result.success:
        console_manager.print_error("No templates available")
        console_manager.print_error("- No local templates found")
        console_manager.print_error("- No bundled templates available")
        console_manager.print_error(
            "Try downloading templates with '--force-download' or check your network connection"
        )
        raise typer.Exit(1)

    templates_source = resolution_result.source.path

    # Verify template source is accessible
    if not templates_source.exists():
        console_manager.print_error(f"Template source not accessible: {templates_source}")
        raise typer.Exit(1)

    # Show additional resolution context for transparency
    if resolution_result.fallback_attempted:
        console_manager.print_info(f"Templates found: {resolution_result.source.type.value}")
        console_manager.print_dim(f"Source: {templates_source}")
    else:
        console_manager.print_info(f"Templates found: {resolution_result.source.type.value}")
        console_manager.print_dim(f"Source: {templates_source}")

    # Template resolution successful - proceed with installation
    for ai_tool in ai_tools:
        console_manager.print_info(f"\nInstalling templates for {AI_TOOLS[ai_tool]['name']}...")

        # Install each template type for this AI tool
        template_types = ["chatmodes", "instructions", "prompts", "commands"]

        for template_type in template_types:
            template_dir = templates_source / template_type
            if not template_dir.exists():
                console_manager.print_warning(f"  No {template_type} templates found")
                continue

            target_dir = project_path / ".github" / template_type
            target_dir.mkdir(parents=True, exist_ok=True)

            # Process all .md files in the template directory
            template_files = list(template_dir.glob("*.md"))
            if not template_files:
                console_manager.print_warning(f"  No {template_type} template files found")
                continue

            console_manager.print_info(
                f"  Installing {len(template_files)} {template_type} template(s)..."
            )

            for template_file in template_files:
                # Read template content
                try:
                    content = template_file.read_text(encoding="utf-8")
                except Exception as e:
                    console_manager.print_error(f"    Failed to read {template_file.name}: {e}")
                    continue

                # Customize content for this AI tool
                customized_content = customize_template_content(content, ai_tool)

                # Generate AI-specific filename
                output_filename = get_template_filename(template_file.name, ai_tool, template_type)
                output_path = target_dir / output_filename

                # Check if file exists and handle force flag
                if output_path.exists() and not force:
                    console_manager.print_warning(f"    Skipped {output_filename} (already exists)")
                    continue

                # Write customized template
                try:
                    output_path.write_text(customized_content, encoding="utf-8")
                    file_tracker.track_file_creation(output_path)
                    console_manager.print_success(f"    Created {output_filename}")
                except Exception as e:
                    console_manager.print_error(f"    Failed to create {output_filename}: {e}")

    # Handle app-specific instructions
    ai_tools_names = [AI_TOOLS[tool]["name"] for tool in ai_tools if tool in AI_TOOLS]
    console_manager.print_info(
        f"App type '{app_type}' templates installed for: {', '.join(ai_tools_names)}"
    )


def get_app_specific_instructions(app_type: str) -> str:
    """Get app-specific development instructions.

    Provides next steps and guidance specific to the selected application type.

    Args:
        app_type: Application type to provide instructions for

    Returns:
        str: Formatted instructions text for the application type
    """
    if app_type == "mcp-server":
        return """
📋 Next Steps for MCP Server Development:
1. Review the generated instructions in .github/instructions/
2. Start with the sddMcpServerDev.instructions.md for best practices
3. Use the chat mode templates in .github/chatmodes/ for AI assistance
4. Follow the prompts in .github/prompts/ for structured development
"""
    elif app_type == "python-cli":
        return """
📋 Next Steps for Python CLI Development:
1. Review the generated instructions in .github/instructions/
2. Start with the sddPythonCliDev.instructions.md for CLI best practices
3. Use typer + rich for modern CLI development
4. Follow the development workflow in the generated prompts
"""

    return ""
