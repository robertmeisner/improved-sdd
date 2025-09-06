"""Unit tests for CLI commands."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from improved_sdd_cli import AI_TOOLS, APP_TYPES, app


@pytest.mark.cli
class TestInitCommand:
    """Test the init command."""

    def test_init_help(self, runner: CliRunner):
        """Test init command help."""
        result = runner.invoke(app, ["init", "--help"])
        assert result.exit_code == 0
        assert "Install Improved-SDD templates" in result.stdout

    def test_init_missing_project_name_without_here(self, runner: CliRunner):
        """Test init fails when project name is missing and --here is False."""
        result = runner.invoke(app, ["init", "--new-dir"])
        assert result.exit_code == 1
        assert "Must specify either a project name" in result.stdout

    @patch("improved_sdd_cli.select_app_type")
    @patch("improved_sdd_cli.select_ai_tools")
    @patch("improved_sdd_cli.create_project_structure")
    @patch("improved_sdd_cli.show_banner")
    def test_init_with_explicit_options(
        self,
        mock_banner,
        mock_create_structure,
        mock_select_ai_tools,
        mock_select_app_type,
        runner: CliRunner,
        temp_dir: Path,
    ):
        """Test init with explicit app-type and ai-tools options."""
        mock_select_app_type.return_value = "python-cli"
        mock_select_ai_tools.return_value = ["github-copilot"]

        with patch("improved_sdd_cli.Path.cwd", return_value=temp_dir):
            result = runner.invoke(app, ["init", "--app-type", "python-cli", "--ai-tools", "github-copilot"])

        assert result.exit_code == 0
        mock_create_structure.assert_called_once()
        # Should not call interactive selection when options provided
        mock_select_app_type.assert_not_called()
        mock_select_ai_tools.assert_not_called()

    def test_init_invalid_app_type(self, runner: CliRunner):
        """Test init with invalid app type."""
        result = runner.invoke(app, ["init", "--app-type", "invalid-type", "--ai-tools", "github-copilot"])
        assert result.exit_code == 1
        assert "Invalid app type" in result.stdout

    def test_init_invalid_ai_tools(self, runner: CliRunner):
        """Test init with invalid AI tools."""
        result = runner.invoke(app, ["init", "--app-type", "python-cli", "--ai-tools", "invalid-tool"])
        assert result.exit_code == 1
        assert "Invalid AI tool(s)" in result.stdout

    @patch("improved_sdd_cli.create_project_structure")
    @patch("improved_sdd_cli.show_banner")
    def test_init_new_directory_exists(self, mock_banner, mock_create_structure, runner: CliRunner, temp_dir: Path):
        """Test init fails when new directory already exists."""
        existing_dir = temp_dir / "existing-project"
        existing_dir.mkdir()

        # Change to temp_dir so the relative path resolution works correctly
        result = runner.invoke(
            app,
            [
                "init",
                str(existing_dir),  # Use absolute path to be sure
                "--new-dir",
                "--app-type",
                "python-cli",
                "--ai-tools",
                "github-copilot",
            ],
        )

        assert result.exit_code == 1
        # Check for the error message (case insensitive and flexible)
        stdout_lower = result.stdout.lower()
        assert "already" in stdout_lower and "exists" in stdout_lower

    @patch("improved_sdd_cli.input")
    @patch("improved_sdd_cli.create_project_structure")
    @patch("improved_sdd_cli.show_banner")
    def test_init_interactive_selections(
        self, mock_banner, mock_create_structure, mock_input, runner: CliRunner, temp_dir: Path
    ):
        """Test init with interactive selections."""
        # Mock user input for app type and AI tools
        mock_input.side_effect = ["1", "1"]  # Select first options

        with patch("improved_sdd_cli.Path.cwd", return_value=temp_dir):
            result = runner.invoke(app, ["init"])

        assert result.exit_code == 0
        mock_create_structure.assert_called_once()

    @patch("improved_sdd_cli.create_project_structure")
    @patch("improved_sdd_cli.show_banner")
    def test_init_force_option(self, mock_banner, mock_create_structure, runner: CliRunner, temp_dir: Path):
        """Test init with --force option."""
        with patch("improved_sdd_cli.Path.cwd", return_value=temp_dir):
            result = runner.invoke(app, ["init", "--app-type", "python-cli", "--ai-tools", "github-copilot", "--force"])

        assert result.exit_code == 0
        # Verify force=True was passed as the last positional argument
        args, kwargs = mock_create_structure.call_args
        assert len(args) == 5  # project_path, app_type, ai_tools, file_tracker, force
        assert args[4] is True  # force parameter is the 5th positional argument


@pytest.mark.cli
class TestDeleteCommand:
    """Test the delete command."""

    def test_delete_help(self, runner: CliRunner):
        """Test delete command help."""
        result = runner.invoke(app, ["delete", "--help"])
        assert result.exit_code == 0
        assert "Delete Improved-SDD templates" in result.stdout

    def test_delete_invalid_app_type(self, runner: CliRunner):
        """Test delete with invalid app type."""
        result = runner.invoke(app, ["delete", "invalid-type"])
        assert result.exit_code == 1
        assert "Invalid app type" in result.stdout

    @patch("improved_sdd_cli.input")
    @patch("improved_sdd_cli.show_banner")
    def test_delete_interactive_app_type_selection(self, mock_banner, mock_input, runner: CliRunner, temp_dir: Path):
        """Test delete with interactive app type selection."""
        mock_input.return_value = "1"  # Select first app type

        with patch("improved_sdd_cli.Path.cwd", return_value=temp_dir):
            result = runner.invoke(app, ["delete"])

        assert result.exit_code == 0
        assert "No files found" in result.stdout

    @patch("improved_sdd_cli.show_banner")
    def test_delete_no_files_found(self, mock_banner, runner: CliRunner, temp_dir: Path):
        """Test delete when no files are found."""
        with patch("improved_sdd_cli.Path.cwd", return_value=temp_dir):
            result = runner.invoke(app, ["delete", "python-cli"])

        assert result.exit_code == 0
        assert "No files found" in result.stdout

    @patch("typer.prompt")
    @patch("improved_sdd_cli.show_banner")
    def test_delete_files_with_confirmation(
        self, mock_banner, mock_prompt, runner: CliRunner, project_with_existing_files: Path
    ):
        """Test delete files with confirmation."""
        mock_prompt.return_value = "Yes"

        with patch("improved_sdd_cli.Path.cwd", return_value=project_with_existing_files):
            result = runner.invoke(app, ["delete", "python-cli"])

        assert result.exit_code == 0
        assert "Deletion complete" in result.stdout

    @patch("typer.prompt")
    @patch("improved_sdd_cli.show_banner")
    def test_delete_files_cancelled(
        self, mock_banner, mock_prompt, runner: CliRunner, project_with_existing_files: Path
    ):
        """Test delete files cancelled by user."""
        mock_prompt.return_value = "No"

        with patch("improved_sdd_cli.Path.cwd", return_value=project_with_existing_files):
            result = runner.invoke(app, ["delete", "python-cli"])

        assert result.exit_code == 0
        assert "Deletion cancelled" in result.stdout

    @patch("improved_sdd_cli.show_banner")
    def test_delete_files_with_force(self, mock_banner, runner: CliRunner, project_with_existing_files: Path):
        """Test delete files with --force option."""
        with patch("improved_sdd_cli.Path.cwd", return_value=project_with_existing_files):
            result = runner.invoke(app, ["delete", "python-cli", "--force"])

        assert result.exit_code == 0
        assert "Deletion complete" in result.stdout


@pytest.mark.cli
class TestCheckCommand:
    """Test the check command."""

    def test_check_help(self, runner: CliRunner):
        """Test check command help."""
        result = runner.invoke(app, ["check", "--help"])
        assert result.exit_code == 0
        assert "Check that all required tools are installed" in result.stdout

    @patch("improved_sdd_cli.offer_user_choice")
    @patch("improved_sdd_cli.check_github_copilot")
    @patch("improved_sdd_cli.check_tool")
    @patch("improved_sdd_cli.show_banner")
    def test_check_all_tools_available(
        self, mock_banner, mock_check_tool, mock_check_copilot, mock_offer_choice, runner: CliRunner
    ):
        """Test check when all tools are available."""
        mock_check_tool.return_value = True
        mock_check_copilot.return_value = True
        mock_offer_choice.return_value = True

        result = runner.invoke(app, ["check"])

        assert result.exit_code == 0
        assert "All AI assistant tools are available" in result.stdout

    @patch("improved_sdd_cli.offer_user_choice")
    @patch("improved_sdd_cli.check_github_copilot")
    @patch("improved_sdd_cli.check_tool")
    @patch("improved_sdd_cli.show_banner")
    def test_check_python_missing(
        self, mock_banner, mock_check_tool, mock_check_copilot, mock_offer_choice, runner: CliRunner
    ):
        """Test check when Python is missing."""

        def check_tool_side_effect(tool, hint, optional=False):
            return tool != "python"

        mock_check_tool.side_effect = check_tool_side_effect
        mock_check_copilot.return_value = True

        result = runner.invoke(app, ["check"])

        assert result.exit_code == 1
        assert "Python is required" in result.stdout

    @patch("improved_sdd_cli.offer_user_choice")
    @patch("improved_sdd_cli.check_github_copilot")
    @patch("improved_sdd_cli.check_tool")
    @patch("improved_sdd_cli.show_banner")
    def test_check_optional_tools_missing_user_declines(
        self, mock_banner, mock_check_tool, mock_check_copilot, mock_offer_choice, runner: CliRunner
    ):
        """Test check when optional tools are missing and user declines."""
        mock_check_tool.return_value = True  # Python available
        mock_check_copilot.return_value = False  # VS Code/Copilot missing
        mock_offer_choice.return_value = False  # User declines to continue

        result = runner.invoke(app, ["check"])

        assert result.exit_code == 1


@pytest.mark.cli
class TestMainApp:
    """Test main app behavior."""

    def test_app_help(self, runner: CliRunner):
        """Test main app help."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Setup tool for Improved Spec-Driven Development" in result.stdout

    @patch("improved_sdd_cli.show_banner")
    def test_app_no_command_shows_banner(self, mock_banner, runner: CliRunner):
        """Test that running app without command shows banner."""
        result = runner.invoke(app, [])
        assert result.exit_code == 0
        mock_banner.assert_called_once()

    def test_app_version_info(self, runner: CliRunner):
        """Test app has correct metadata."""
        # This tests that the app is properly configured
        assert app.info.name == "improved-sdd"
        assert app.info.help is not None
        assert "Setup tool for Improved Spec-Driven Development" in app.info.help
