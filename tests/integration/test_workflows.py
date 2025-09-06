"""Integration tests for improved-sdd CLI workflows."""

import os
import shutil
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from improved_sdd_cli import FileTracker, app, create_project_structure


@pytest.mark.integration
class TestCompleteWorkflows:
    """Test complete CLI workflows end-to-end."""

    @patch("improved_sdd_cli.show_banner")
    def test_complete_init_workflow_new_project(
        self, mock_banner, runner: CliRunner, temp_dir: Path, mock_script_location
    ):
        """Test complete init workflow creating a new project."""
        project_name = "test-project"
        project_path = temp_dir / project_name

        with patch("improved_sdd_cli.Path.cwd", return_value=temp_dir):
            result = runner.invoke(
                app,
                [
                    "init",
                    project_name,
                    "--new-dir",
                    "--app-type",
                    "python-cli",
                    "--ai-tools",
                    "github-copilot",
                    "--force",
                ],
            )

        assert result.exit_code == 0
        assert "Templates installed!" in result.stdout

        # Verify project structure was created
        assert project_path.exists()
        github_dir = project_path / ".github"
        assert github_dir.exists()

        # Check for expected template files
        chatmodes_dir = github_dir / "chatmodes"
        assert chatmodes_dir.exists()
        assert (chatmodes_dir / "specMode.chatmode.md").exists()

        instructions_dir = github_dir / "instructions"
        assert instructions_dir.exists()
        assert (instructions_dir / "CLIPythonDev.instructions.md").exists()

    @patch("improved_sdd_cli.input")
    @patch("improved_sdd_cli.show_banner")
    def test_complete_init_workflow_interactive(
        self, mock_banner, mock_input, runner: CliRunner, temp_dir: Path, mock_templates_dir: Path
    ):
        """Test complete init workflow with interactive selections."""
        # Mock user inputs: app type = 1 (first option), ai tools = 1 (first option)
        mock_input.side_effect = ["1", "1"]

        # Patch the templates source directly in the create_project_structure function
        def mock_create_structure(*args, **kwargs):
            # Call the original function but with our mock templates directory
            import improved_sdd_cli
            from improved_sdd_cli import create_project_structure

            # Temporarily replace the templates source resolution
            original_file = improved_sdd_cli.__file__
            try:
                # Mock the script location
                improved_sdd_cli.__file__ = str(mock_templates_dir.parent / "improved_sdd_cli.py")
                return create_project_structure(*args, **kwargs)
            finally:
                improved_sdd_cli.__file__ = original_file

        with patch("improved_sdd_cli.create_project_structure", side_effect=mock_create_structure):
            with patch("improved_sdd_cli.Path.cwd", return_value=temp_dir):
                result = runner.invoke(app, ["init", "--force"])

        assert result.exit_code == 0
        assert "Templates installed!" in result.stdout

        # Verify templates were installed in current directory
        github_dir = temp_dir / ".github"
        assert github_dir.exists()

    @patch("typer.confirm")
    @patch("improved_sdd_cli.show_banner")
    def test_init_then_delete_workflow(
        self, mock_banner, mock_confirm, runner: CliRunner, temp_dir: Path, mock_script_location
    ):
        """Test init followed by delete workflow."""
        # First, initialize project
        with patch("improved_sdd_cli.Path.cwd", return_value=temp_dir):
            init_result = runner.invoke(
                app, ["init", "--app-type", "python-cli", "--ai-tools", "github-copilot", "--force"]
            )

        assert init_result.exit_code == 0

        # Verify files were created
        github_dir = temp_dir / ".github"
        assert github_dir.exists()
        chatmodes_file = github_dir / "chatmodes" / "specMode.chatmode.md"
        assert chatmodes_file.exists()

        # Now delete with confirmation
        mock_confirm.return_value = True

        with patch("improved_sdd_cli.Path.cwd", return_value=temp_dir):
            with patch("typer.prompt", return_value="Yes"):
                delete_result = runner.invoke(app, ["delete", "python-cli"])

        assert delete_result.exit_code == 0
        assert "Deletion complete" in delete_result.stdout

        # Verify files were deleted
        assert not chatmodes_file.exists()

    @patch("improved_sdd_cli.show_banner")
    def test_multiple_ai_tools_workflow(self, mock_banner, runner: CliRunner, temp_dir: Path, mock_script_location):
        """Test workflow with multiple AI tools."""
        with patch("improved_sdd_cli.Path.cwd", return_value=temp_dir):
            result = runner.invoke(
                app, ["init", "--app-type", "mcp-server", "--ai-tools", "github-copilot,claude", "--force"]
            )

        assert result.exit_code == 0

        # Verify both AI tool templates were created
        github_dir = temp_dir / ".github"

        # GitHub Copilot files (in root .github)
        assert (github_dir / "chatmodes" / "specMode.chatmode.md").exists()

        # Claude files (in claude subdirectory)
        assert (github_dir / "claude" / "chatmodes" / "specMode.claude.md").exists()

    @patch("typer.confirm")
    @patch("improved_sdd_cli.show_banner")
    def test_overwrite_existing_files_workflow(
        self, mock_banner, mock_confirm, runner: CliRunner, project_with_existing_files: Path, mock_script_location
    ):
        """Test workflow when overwriting existing files."""
        mock_confirm.return_value = True  # User confirms overwrite

        with patch("improved_sdd_cli.Path.cwd", return_value=project_with_existing_files):
            result = runner.invoke(app, ["init", "--app-type", "python-cli", "--ai-tools", "github-copilot"])

        assert result.exit_code == 0
        assert "Files Modified:" in result.stdout or "Templates installed!" in result.stdout


@pytest.mark.integration
class TestProjectStructureCreation:
    """Test project structure creation in detail."""

    def test_create_project_structure_python_cli(self, temp_project_dir: Path, mock_templates_dir: Path):
        """Test creating project structure for Python CLI."""
        file_tracker = FileTracker()

        with patch("improved_sdd_cli.Path.__file__", str(mock_templates_dir.parent / "cli.py")):
            create_project_structure(temp_project_dir, "python-cli", ["github-copilot"], file_tracker, force=True)

        # Verify correct instruction file was used
        instructions_dir = temp_project_dir / ".github" / "instructions"
        assert instructions_dir.exists()
        cli_instruction = instructions_dir / "CLIPythonDev.instructions.md"
        assert cli_instruction.exists()

        # Should not have MCP instruction
        mcp_instruction = instructions_dir / "mcpDev.instructions.md"
        assert not mcp_instruction.exists()

    def test_create_project_structure_mcp_server(self, temp_project_dir: Path, mock_templates_dir: Path):
        """Test creating project structure for MCP server."""
        file_tracker = FileTracker()

        with patch("improved_sdd_cli.Path.__file__", str(mock_templates_dir.parent / "cli.py")):
            create_project_structure(temp_project_dir, "mcp-server", ["github-copilot"], file_tracker, force=True)

        # Verify correct instruction file was used
        instructions_dir = temp_project_dir / ".github" / "instructions"
        assert instructions_dir.exists()
        mcp_instruction = instructions_dir / "mcpDev.instructions.md"
        assert mcp_instruction.exists()

        # Should not have CLI instruction
        cli_instruction = instructions_dir / "CLIPythonDev.instructions.md"
        assert not cli_instruction.exists()

    def test_create_project_structure_template_customization(self, temp_project_dir: Path, mock_templates_dir: Path):
        """Test that templates are properly customized for AI tools."""
        file_tracker = FileTracker()

        with patch("improved_sdd_cli.Path.__file__", str(mock_templates_dir.parent / "cli.py")):
            create_project_structure(temp_project_dir, "python-cli", ["github-copilot"], file_tracker, force=True)

        # Check that template content was customized
        spec_file = temp_project_dir / ".github" / "chatmodes" / "specMode.chatmode.md"
        assert spec_file.exists()

        content = spec_file.read_text()
        assert "GitHub Copilot" in content
        assert "Copilot" in content
        assert "Ctrl+Shift+P" in content
        assert "{AI_ASSISTANT}" not in content

    def test_create_project_structure_multiple_ai_tools(self, temp_project_dir: Path, mock_templates_dir: Path):
        """Test creating structure for multiple AI tools."""
        file_tracker = FileTracker()

        with patch("improved_sdd_cli.Path.__file__", str(mock_templates_dir.parent / "cli.py")):
            create_project_structure(
                temp_project_dir, "python-cli", ["github-copilot", "claude"], file_tracker, force=True
            )

        # Check GitHub Copilot files (root .github)
        copilot_file = temp_project_dir / ".github" / "chatmodes" / "specMode.chatmode.md"
        assert copilot_file.exists()
        copilot_content = copilot_file.read_text()
        assert "GitHub Copilot" in copilot_content

        # Check Claude files (claude subdirectory)
        claude_file = temp_project_dir / ".github" / "claude" / "chatmodes" / "specMode.claude.md"
        assert claude_file.exists()
        claude_content = claude_file.read_text()
        assert "Claude" in claude_content

    @patch("typer.confirm")
    def test_create_project_structure_existing_files_ask_permission(
        self, mock_confirm, project_with_existing_files: Path, mock_templates_dir: Path
    ):
        """Test handling existing files with permission prompts."""
        mock_confirm.return_value = False  # User declines to overwrite
        file_tracker = FileTracker()

        with patch("improved_sdd_cli.Path.__file__", str(mock_templates_dir.parent / "cli.py")):
            create_project_structure(
                project_with_existing_files, "python-cli", ["github-copilot"], file_tracker, force=False
            )

        # Should have asked for confirmation
        mock_confirm.assert_called()

        # Existing files should not be in modified list since user declined
        assert len(file_tracker.modified_files) == 0


@pytest.mark.integration
@pytest.mark.slow
class TestFullSystemIntegration:
    """Test full system integration including tool checks."""

    @patch("improved_sdd_cli.offer_user_choice")
    @patch("improved_sdd_cli.check_github_copilot")
    @patch("improved_sdd_cli.check_tool")
    @patch("improved_sdd_cli.show_banner")
    def test_check_command_integration(
        self, mock_banner, mock_check_tool, mock_check_copilot, mock_offer_choice, runner: CliRunner
    ):
        """Test check command integration."""

        # Set up tool availability
        def check_tool_side_effect(tool, hint, optional=False):
            available = {"python": True, "claude": False}
            return available.get(tool, False)

        mock_check_tool.side_effect = check_tool_side_effect
        mock_check_copilot.return_value = True
        mock_offer_choice.return_value = True

        result = runner.invoke(app, ["check"])

        assert result.exit_code == 0
        assert "Improved-SDD CLI is ready to use!" in result.stdout

    def test_error_handling_missing_templates(self, runner: CliRunner, temp_dir: Path):
        """Test error handling when templates directory is missing."""
        # Mock script location to point to non-existent templates
        non_existent = temp_dir / "non-existent"

        with patch("improved_sdd_cli.Path.__file__", str(non_existent / "cli.py")):
            with patch("improved_sdd_cli.Path.cwd", return_value=temp_dir):
                result = runner.invoke(
                    app, ["init", "--app-type", "python-cli", "--ai-tools", "github-copilot", "--force"]
                )

        # Should complete without error even if templates don't exist
        assert result.exit_code == 0
