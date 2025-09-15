"""Shared utilities for Improved-SDD CLI.

This module contains utility functions that are shared across multiple
command modules to avoid circular imports.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional

import typer

# Import configuration and UI components
from core import AI_TOOLS, APP_TYPES
from core.models import MergedTemplateSource
from services import FileTracker, TemplateResolver
from ui import console_manager


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
        console_manager.print_dim("Open VS Code and check if Copilot extension is installed and activated")
        return True
    else:
        console_manager.print_warning("VS Code not found")
        console_manager.print("   Install with: [cyan]https://code.visualstudio.com/download[/cyan]")
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
    console_manager.print_dim("These tools enhance the development experience but are not required.")

    # Check if we're in CI/automation mode
    if os.getenv("CI") or os.getenv("GITHUB_ACTIONS"):
        console_manager.print_success("Continuing with available tools (CI mode)...")
        return True

    try:
        choice = typer.prompt("\nWould you like to continue anyway? (y/n)", type=str, default="y").lower().strip()

        if choice in ["y", "yes"]:
            console_manager.print_success("Continuing with available tools...")
            return True
        else:
            console_manager.print_warning("Setup cancelled. Please install the missing tools and try again.")
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
        console_manager.print(f"[cyan]{i}.[/cyan] [white]{key}[/white]: {APP_TYPES[key]['description']}")

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
                console_manager.print_error(f"Please enter a number between 1 and {len(option_keys)}")
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
    console_manager.print_dim("You can select multiple tools (templates will be customized for each)")

    # Use simple numbered selection
    tool_keys = list(AI_TOOLS.keys())

    console_manager.print_newline()
    for i, key in enumerate(tool_keys, 1):
        tool_info = AI_TOOLS[key]
        if key == "github-copilot":
            # GitHub Copilot is available now
            console_manager.print(f"[cyan]{i}.[/cyan] [white]{tool_info['name']}[/white]: {tool_info['description']}")
        else:
            # Other tools are coming soon
            console_manager.print(
                f"[dim cyan]{i}.[/dim cyan] [dim white]{tool_info['name']}[/dim white]: "
                f"[dim]{tool_info['description']}[/dim] [yellow](coming soon)[/yellow]"
            )

    console_manager.print_dim("\nEnter numbers separated by commas (e.g., 1,2) or 'all' for all tools")
    console_manager.print_newline()

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
                console_manager.print(f"[green]Selected: [/green] All AI tools ({len(selected)} tools)")
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


def customize_template_content(
    content: str, ai_tool: str, gitlab_flow_enabled: bool = False, platform: str = "windows", template_dir: str = ""
) -> str:
    """Customize template content for specific AI tool and optionally GitLab Flow.

    Replaces AI-tool-specific keywords and GitLab Flow keywords in template content.
    GitLab Flow keywords are conditionally replaced based on enablement flag.

    Args:
        content: Template content to customize
        ai_tool: AI tool key for which to customize content
        gitlab_flow_enabled: Whether GitLab Flow keywords should be processed
        platform: Target platform (windows/unix) for GitLab Flow commands
        template_dir: Base template directory path for GitLab Flow files

    Returns:
        str: Customized template content with replaced keywords
    """
    if ai_tool not in AI_TOOLS:
        return content

    tool_config = AI_TOOLS[ai_tool]
    customized_content = content

    # Replace AI-specific keywords (existing functionality)
    for keyword, replacement in tool_config["keywords"].items():
        customized_content = customized_content.replace(keyword, replacement)

    # Replace GitLab Flow keywords if enabled (new functionality)
    # Import here to avoid circular imports
    from core.config import config

    gitlab_flow_keywords = config.get_gitlab_flow_keywords(
        enabled=gitlab_flow_enabled, platform=platform, template_dir=template_dir
    )

    for keyword, replacement in gitlab_flow_keywords.items():
        customized_content = customized_content.replace(keyword, replacement)

    return customized_content


def load_gitlab_flow_file(filename: str, template_dir: str, platform_keywords: Dict[str, str]) -> str:
    """Load GitLab Flow markdown file and replace platform-specific keyword placeholders.

    Loads a GitLab Flow markdown file from the templates/gitlab-flow/ directory and
    replaces platform-specific placeholders with appropriate git commands based on
    the user's operating system.

    Args:
        filename: Name of the GitLab Flow markdown file to load
        template_dir: Base template directory path
        platform_keywords: Dictionary mapping keyword placeholders to platform-specific commands

    Returns:
        str: Processed markdown content with platform commands, or fallback message if file not found

    Examples:
        >>> keywords = {"GIT_STATUS": "git status", "COMMIT": "git add . && git commit -m \"{message}\""}
        >>> content = load_gitlab_flow_file("gitlab-flow-setup.md", "/templates", keywords)
        >>> print(content)
        # GitLab Flow Setup...
    """
    # Construct the full file path
    gitlab_flow_dir = Path(template_dir) / "gitlab-flow"
    file_path = gitlab_flow_dir / filename

    try:
        # Read the markdown file
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Replace platform-specific keyword placeholders
        processed_content = content
        for cmd_key, cmd_value in platform_keywords.items():
            processed_content = processed_content.replace(cmd_key, cmd_value)

        return processed_content

    except FileNotFoundError:
        # Graceful fallback when file is missing
        return f"<!-- GitLab Flow file not found: {filename} -->\n\n**Note**: GitLab Flow guidance not available. File `{filename}` not found in `{gitlab_flow_dir}`. You can create this file manually or proceed without GitLab Flow integration."

    except PermissionError:
        # Handle permission errors
        return f"<!-- Permission denied reading GitLab Flow file: {filename} -->\n\n**Error**: Cannot read GitLab Flow guidance file `{filename}`. Please check file permissions."

    except UnicodeDecodeError:
        # Handle encoding errors
        return f"<!-- Encoding error reading GitLab Flow file: {filename} -->\n\n**Error**: Cannot decode GitLab Flow guidance file `{filename}`. Please ensure file is UTF-8 encoded."

    except Exception as e:
        # Handle any other unexpected errors
        return f"<!-- Error loading GitLab Flow file {filename}: {str(e)} -->\n\n**Error**: Unexpected error loading GitLab Flow guidance. Please check the file and try again."


def get_template_filename(original_name: str, ai_tool: str, template_type: str) -> str:
    """Generate AI-specific template filename."""
    if ai_tool not in AI_TOOLS:
        return original_name

    # For GitHub Copilot, templates are already correctly named
    if ai_tool == "github-copilot":
        return original_name

    tool_config = AI_TOOLS[ai_tool]

    # Get base name by removing the final .md extension if present
    if original_name.endswith(".md"):
        base_name = original_name[:-3]  # Remove .md
    else:
        base_name = original_name

    # Map template types to extension keys
    extension_key_map = {
        "chatmodes": "chatmodes",
        "instructions": "instructions",
        "prompts": "prompts",
        "commands": "commands",
    }
    extension_key = extension_key_map.get(template_type, template_type)
    extension = tool_config["file_extensions"].get(extension_key, ".md")

    # Generate filename with tool-specific extension
    return f"{base_name}{extension}"


def _process_template_file(
    template_file_path: Path,
    template_type: str,
    target_dir: Path,
    app_type: str,
    ai_tool: str,
    file_tracker: FileTracker,
    force: bool,
    source_label: str,
    gitlab_flow_enabled: bool = False,
    platform: str = "windows",
    template_dir: str = "",
) -> bool:
    """Process a single template file for installation.

    Args:
        template_file_path: Path to the template file to process
        template_type: Type of template (e.g., 'prompts', 'chatmodes')
        target_dir: Target directory for installation
        app_type: Application type for filtering instructions
        ai_tool: AI tool being configured
        file_tracker: FileTracker instance for tracking changes
        force: Whether to overwrite existing files
        source_label: Label indicating source (e.g., 'local', 'downloaded')
        gitlab_flow_enabled: Whether GitLab Flow integration is enabled
        platform: Target platform (windows/unix) for GitLab Flow commands
        template_dir: Base template directory path for GitLab Flow files
    """
    # For 'instructions', only install if it matches the app_type
    if template_type == "instructions":
        allowed_instructions = APP_TYPES.get(app_type, {}).get("instructions", [])
        if template_file_path.name not in allowed_instructions:
            return False  # Skip this instruction file

    # Read template content
    try:
        content = template_file_path.read_text(encoding="utf-8")
    except Exception as e:
        console_manager.print_error(f"    Failed to read {template_file_path.name}: {e}")
        return False

    # Customize content for this AI tool and GitLab Flow
    customized_content = customize_template_content(content, ai_tool, gitlab_flow_enabled, platform, template_dir)

    # Generate AI-specific filename
    output_filename = get_template_filename(template_file_path.name, ai_tool, template_type)
    output_path = target_dir / output_filename

    # Check if file exists and handle force flag
    if output_path.exists() and not force:
        # In CI/automation mode, automatically overwrite existing files
        is_ci_mode = os.getenv("CI") or os.getenv("GITHUB_ACTIONS")
        
        if is_ci_mode:
            # Auto-approve in CI mode
            console_manager.print_info(f"    Auto-overwriting existing file in CI mode: {output_filename}")
            file_tracker.track_file_modification(output_path)
        else:
            # Interactive mode - ask user
            try:
                if typer.confirm(
                    f"  Overwrite existing file '{output_path.relative_to(target_dir.parent.parent)}'?", default=False
                ):
                    file_tracker.track_file_modification(output_path)
                else:
                    console_manager.print_warning(f"    Skipped {output_filename} (from {source_label})")
                    return False
            except (typer.Abort, KeyboardInterrupt):
                console_manager.print_warning(f"    Skipped {output_filename} (from {source_label})")
                return False
    else:
        file_tracker.track_file_creation(output_path)

    # Write customized template
    try:
        output_path.write_text(customized_content, encoding="utf-8")
        if output_path in file_tracker.created_files:
            console_manager.print_success(f"    Created {output_filename} (from {source_label})")
        else:
            console_manager.print_success(f"    Updated {output_filename} (from {source_label})")
        return True
    except Exception as e:
        console_manager.print_error(f"    Failed to write {output_filename}: {e}")
        return False


def create_project_structure(
    project_path: Path,
    app_type: str,
    ai_tools: List[str],
    file_tracker: FileTracker,
    force: bool = False,
    offline: bool = False,
    force_download: bool = False,
    template_repo: Optional[str] = None,
    template_branch: Optional[str] = None,
    gitlab_flow_enabled: bool = False,
    platform: str = "windows",
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
        offline: Force offline mode (disable GitHub downloads)
        force_download: Force GitHub download even if local templates exist
        template_repo: Custom GitHub repository for templates
        template_branch: Git branch to download templates from
        gitlab_flow_enabled: Whether GitLab Flow integration is enabled
        platform: Target platform (windows/unix) for GitLab Flow commands
    """

    # Use TemplateResolver for priority-based template resolution with transparency
    resolver = TemplateResolver(
        project_path, offline=offline, force_download=force_download, template_repo=template_repo, template_branch=template_branch
    )
    resolution_result = resolver.resolve_templates_with_transparency()

    if not resolution_result.success or not resolution_result.source:
        console_manager.print_error("No templates available")
        console_manager.print_error("- No local templates found")
        console_manager.print_error("- No bundled templates available")
        console_manager.print_error(
            "Try downloading templates with '--force-download' or check your network connection"
        )
        raise typer.Exit(1)

    # Handle different source types
    if resolution_result.is_merged:
        # Merged source - need to handle multiple paths
        merged_source = resolution_result.source
        console_manager.print_info(f"Templates found: {merged_source}")
        # For GitLab Flow, use a simple fallback path
        template_source_path = "templates"
    else:
        # Single source (local, bundled, or github)
        templates_source = resolution_result.source.path
        template_source_path = str(templates_source)

        # Verify template source is accessible
        if not templates_source.exists():
            console_manager.print_error(f"Template source not accessible: {templates_source}")
            raise typer.Exit(1)

        # Show additional resolution context for transparency
        console_manager.print_info(f"Templates found: {resolution_result.source.source_type.value}")
        console_manager.print_dim(f"Source: {templates_source}")

    # Template resolution successful - proceed with installation
    for ai_tool in ai_tools:
        console_manager.print_info(f"\nInstalling templates for {AI_TOOLS[ai_tool]['name']}...")

        # Determine target base directory
        if ai_tool == "github-copilot":
            target_base_dir = project_path / ".github"
        else:
            target_base_dir = project_path / ".github" / ai_tool

        # Install each template type for this AI tool
        template_types = ["chatmodes", "instructions", "prompts", "commands", "gitlab-flow"]

        for template_type in template_types:
            # Special handling for gitlab-flow templates - install at project root
            if template_type == "gitlab-flow":
                if not gitlab_flow_enabled:
                    continue  # Skip gitlab-flow templates if not enabled
                target_base_for_type = project_path / ".github" 
            else:
                target_base_for_type = target_base_dir
            # Determine template source for this type - now with file-level granularity
            if resolution_result.is_merged:
                merged_source = resolution_result.source
                template_dir = None
                source_label = "merged"

                # For merged sources, we need to handle file-by-file installation
                # We'll collect files from both sources as needed
                if template_type in merged_source.local_files or template_type in merged_source.downloaded_files:
                    # This template type has files available - we'll handle them individually
                    target_dir = target_base_for_type / template_type
                    target_dir.mkdir(parents=True, exist_ok=True)

                    # Get all available files for this template type
                    all_available_files = merged_source.get_all_available_files()
                    available_files_for_type = all_available_files.get(template_type, set())

                    if not available_files_for_type:
                        console_manager.print_warning(f"  No {template_type} template files found")
                        continue

                    console_manager.print_info(
                        f"  Installing {len(available_files_for_type)} {template_type} template(s) from merged sources..."
                    )

                    # Process each file individually
                    for template_filename in available_files_for_type:
                        # Determine source for this specific file
                        file_source_path = merged_source.get_file_source(template_type, template_filename)
                        if not file_source_path or not file_source_path.exists():
                            console_manager.print_warning(f"    Skipping {template_filename} - source not found")
                            continue

                        # Determine if it's from local or downloaded
                        is_local_file = (
                            template_type in merged_source.local_files
                            and template_filename in merged_source.local_files[template_type]
                        )
                        file_source_label = "local" if is_local_file else "downloaded"

                        # Process this individual template file
                        if not _process_template_file(
                            template_file_path=file_source_path,
                            template_type=template_type,
                            target_dir=target_dir,
                            app_type=app_type,
                            ai_tool=ai_tool,
                            file_tracker=file_tracker,
                            force=force,
                            source_label=file_source_label,
                            gitlab_flow_enabled=gitlab_flow_enabled,
                            platform=platform,
                            template_dir=template_source_path,
                        ):
                            continue  # Skip this file if processing failed

                    continue  # Move to next template type
                else:
                    console_manager.print_warning(f"  No {template_type} templates found in merged sources")
                    continue
            else:
                # Single source (local, bundled, or github)
                template_dir = templates_source / template_type
                source_label = resolution_result.source.source_type.value

            # Handle single-source template directories (non-merged)
            if template_dir is not None:
                if not template_dir.exists():
                    console_manager.print_warning(f"  No {template_type} templates found")
                    continue

                target_dir = target_base_for_type / template_type
                target_dir.mkdir(parents=True, exist_ok=True)

                # Process all .md files in the template directory
                template_files = list(template_dir.glob("*.md"))
                if not template_files:
                    console_manager.print_warning(f"  No {template_type} template files found")
                    continue

                console_manager.print_info(
                    f"  Installing {len(template_files)} {template_type} template(s) from {source_label}..."
                )

                for template_file in template_files:
                    _process_template_file(
                        template_file_path=template_file,
                        template_type=template_type,
                        target_dir=target_dir,
                        app_type=app_type,
                        ai_tool=ai_tool,
                        file_tracker=file_tracker,
                        force=force,
                        source_label=source_label,
                        gitlab_flow_enabled=gitlab_flow_enabled,
                        platform=platform,
                        template_dir=template_source_path,
                    )

    # Handle app-specific instructions
    ai_tools_names = [AI_TOOLS[tool]["name"] for tool in ai_tools if tool in AI_TOOLS]
    console_manager.print_info(f"App type '{app_type}' templates installed for: {', '.join(ai_tools_names)}")


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
