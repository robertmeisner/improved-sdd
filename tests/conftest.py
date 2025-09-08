"""Test configuration and fixtures for improved-sdd CLI tests."""

import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import patch

import pytest
from typer.testing import CliRunner


@pytest.fixture
def runner() -> CliRunner:
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def temp_project_dir(temp_dir: Path) -> Path:
    """Create a temporary project directory."""
    project_dir = temp_dir / "test-project"
    project_dir.mkdir()
    return project_dir


@pytest.fixture
def mock_templates_dir(temp_dir: Path) -> Path:
    """Create a mock templates directory structure."""
    templates_dir = temp_dir / "templates"
    templates_dir.mkdir()

    # Create chatmodes directory with sample templates
    chatmodes_dir = templates_dir / "chatmodes"
    chatmodes_dir.mkdir()
    (chatmodes_dir / "sddSpecDriven.chatmode.md").write_text(
        """# Spec Mode for {AI_ASSISTANT}

This is a test template for {AI_SHORTNAME}.

Command: {AI_COMMAND}
"""
    )
    (chatmodes_dir / "sddTesting.chatmode.md").write_text(
        """# Test Mode for {AI_ASSISTANT}

Testing with {AI_SHORTNAME}.
"""
    )

    # Create instructions directory with sample templates
    instructions_dir = templates_dir / "instructions"
    instructions_dir.mkdir()
    (instructions_dir / "sddPythonCliDev.instructions.md").write_text(
        """# Python CLI Development

Development instructions for {AI_ASSISTANT}.
"""
    )
    (instructions_dir / "sddMcpServerDev.instructions.md").write_text(
        """# MCP Development

MCP development instructions for {AI_ASSISTANT}.
"""
    )

    # Create prompts directory with sample templates
    prompts_dir = templates_dir / "prompts"
    prompts_dir.mkdir()
    (prompts_dir / "sddProjectAnalysis.prompt.md").write_text(
        """# Analyze Project

Project analysis prompt for {AI_ASSISTANT}.
"""
    )

    # Create commands directory with sample templates
    commands_dir = templates_dir / "commands"
    commands_dir.mkdir()
    (commands_dir / "sddTest.command.md").write_text(
        """# Test Command

Test command for {AI_ASSISTANT}.
"""
    )

    return templates_dir


@pytest.fixture
def mock_script_location(temp_dir: Path, mock_templates_dir: Path):
    """Mock the script location to use test templates."""
    script_file = temp_dir / "improved_sdd_cli.py"
    script_file.write_text("# Mock CLI script")

    # Rather than mock Path, let's just patch the specific location where templates_source is set
    # In create_project_structure function

    # We'll use this in the integration tests by manually patching where needed
    yield script_file


@pytest.fixture
def sample_ai_tools():
    """Sample AI tools configuration for testing."""
    return {
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
            "keywords": {
                "{AI_ASSISTANT}": "Claude",
                "{AI_SHORTNAME}": "Claude",
                "{AI_COMMAND}": "Open Claude interface",
            },
        },
    }


@pytest.fixture
def sample_app_types():
    """Sample app types configuration for testing."""
    return {
        "mcp-server": "MCP Server - Model Context Protocol server for AI integrations",
        "python-cli": "Python CLI - Command-line application using typer and rich",
    }


@pytest.fixture
def mock_user_input():
    """Mock user input for interactive prompts."""

    def _mock_input(inputs):
        input_iter = iter(inputs)
        return lambda prompt="": next(input_iter, "")

    return _mock_input


@pytest.fixture
def mock_tools_available():
    """Mock tool availability checks."""

    def _mock_which(tool):
        available_tools = ["python", "code", "git"]
        return "/usr/bin/" + tool if tool in available_tools else None

    with patch("shutil.which", side_effect=_mock_which):
        yield


@pytest.fixture
def mock_tools_missing():
    """Mock missing tool availability."""
    with patch("shutil.which", return_value=None):
        yield


@pytest.fixture
def mock_typer_confirm():
    """Mock typer.confirm for testing."""

    def _mock_confirm(responses):
        response_iter = iter(responses)
        return lambda prompt, default=None: next(response_iter, default)

    return _mock_confirm


@pytest.fixture
def project_with_existing_files(temp_project_dir: Path) -> Path:
    """Create a project directory with existing files that will conflict."""
    github_dir = temp_project_dir / ".github"
    github_dir.mkdir(parents=True, exist_ok=True)

    # Add an existing instruction file that will conflict
    instructions_dir = github_dir / "instructions"
    instructions_dir.mkdir(exist_ok=True)
    (instructions_dir / "sddPythonCliDev.instructions.md").write_text("# Existing Instruction")

    # Add an existing chatmode file that will conflict
    chatmodes_dir = github_dir / "chatmodes"
    chatmodes_dir.mkdir(exist_ok=True)
    (chatmodes_dir / "sddSpecDriven.chatmode.md").write_text("# Existing Chatmode")

    return temp_project_dir
