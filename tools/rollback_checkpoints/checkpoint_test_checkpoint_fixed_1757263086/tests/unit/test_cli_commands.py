"""
Unit tests for CLI commands functionality using typer.testing.CliRunner.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from typer.testing import CliRunner

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from improved_sdd_cli import (
    AI_TOOLS,
    APP_TYPES,
    FileTracker,
    app,
    create_project_structure,
    customize_template_content,
    get_template_filename,
    select_ai_tools,
    select_app_type,
)


class TestCLICommands:
    """Test CLI commands using typer.testing.CliRunner."""

    def setup_method(self):
        """Set up test environment for each test."""
        self.runner = CliRunner()

    def test_cli_help_command(self):
        """Test CLI help output."""
        result = self.runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "improved-sdd" in result.output.lower()
        assert "setup ai-optimized development templates" in result.output.lower()

    def test_init_help_command(self):
        """Test init command help output."""
        result = self.runner.invoke(app, ["init", "--help"])

        assert result.exit_code == 0
        assert "init" in result.output.lower()
        assert "project" in result.output.lower()

    @patch("src.improved_sdd_cli.select_ai_tools")
    @patch("src.improved_sdd_cli.select_app_type")
    @patch("src.improved_sdd_cli.create_project_structure")
    def test_init_command_new_project(self, mock_create_project, mock_select_app, mock_select_ai):
        """Test init command creating new project."""
        # Setup mocks
        mock_select_ai.return_value = ["github-copilot"]
        mock_select_app.return_value = "mcp-server"
        mock_create_project.return_value = None

        with tempfile.TemporaryDirectory() as temp_dir:
            with self.runner.isolated_filesystem(temp_path=temp_dir):
                result = self.runner.invoke(app, ["init", "test-project"])

                assert result.exit_code == 0
                mock_create_project.assert_called_once()

                # Verify project structure was called with correct parameters
                call_args = mock_create_project.call_args
                assert call_args[1]["app_type"] == "mcp-server"
                assert call_args[1]["ai_tools"] == ["github-copilot"]

    @patch("src.improved_sdd_cli.select_ai_tools")
    @patch("src.improved_sdd_cli.select_app_type")
    @patch("src.improved_sdd_cli.create_project_structure")
    def test_init_command_here_mode(self, mock_create_project, mock_select_app, mock_select_ai):
        """Test init command with --here flag."""
        # Setup mocks
        mock_select_ai.return_value = ["claude"]
        mock_select_app.return_value = "python-cli"
        mock_create_project.return_value = None

        with tempfile.TemporaryDirectory() as temp_dir:
            with self.runner.isolated_filesystem(temp_path=temp_dir):
                result = self.runner.invoke(app, ["init", "--here"])

                assert result.exit_code == 0
                mock_create_project.assert_called_once()

    @patch("src.improved_sdd_cli.select_ai_tools")
    @patch("src.improved_sdd_cli.select_app_type")
    @patch("src.improved_sdd_cli.create_project_structure")
    def test_init_command_with_force_flag(self, mock_create_project, mock_select_app, mock_select_ai):
        """Test init command with --force flag."""
        # Setup mocks
        mock_select_ai.return_value = ["cursor"]
        mock_select_app.return_value = "mcp-server"
        mock_create_project.return_value = None

        with tempfile.TemporaryDirectory() as temp_dir:
            with self.runner.isolated_filesystem(temp_path=temp_dir):
                result = self.runner.invoke(app, ["init", "test-project", "--force"])

                assert result.exit_code == 0

                # Verify force flag was passed
                call_args = mock_create_project.call_args
                assert call_args[1]["force"] == True

    def test_init_command_conflicting_options(self):
        """Test init command with conflicting --offline and --force-download."""
        result = self.runner.invoke(app, ["init", "test-project", "--offline", "--force-download"])

        assert result.exit_code != 0
        assert "cannot use" in result.output.lower() or "error" in result.output.lower()

    @patch("src.improved_sdd_cli.select_ai_tools")
    @patch("src.improved_sdd_cli.select_app_type")
    @patch("src.improved_sdd_cli.create_project_structure")
    def test_init_command_template_options(self, mock_create_project, mock_select_app, mock_select_ai):
        """Test init command with template-related options."""
        # Setup mocks
        mock_select_ai.return_value = ["gemini"]
        mock_select_app.return_value = "python-cli"
        mock_create_project.return_value = None

        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.runner.invoke(app, ["init", "test-project", "--offline", "--template-repo", "custom/repo"])

            assert result.exit_code == 0

            # Verify template options were passed
            call_args = mock_create_project.call_args
            assert call_args[1]["offline"] == True
            assert call_args[1]["template_repo"] == "custom/repo"

    @patch("src.improved_sdd_cli.create_project_structure")
    def test_init_command_template_creation_error(self, mock_create_project):
        """Test init command when template creation fails."""
        # Setup mock to raise exception
        mock_create_project.side_effect = Exception("Template creation failed")

        result = self.runner.invoke(app, ["init", "test-project"])

        assert result.exit_code != 0
        assert "error" in result.output.lower()

    def test_version_command(self):
        """Test version command output."""
        result = self.runner.invoke(app, ["version"])

        assert result.exit_code == 0
        assert "improved-sdd" in result.output.lower()

    @patch("src.improved_sdd_cli.check_tool")
    def test_check_tools_command(self, mock_check_tool):
        """Test check-tools command."""
        # Setup mock to return tool availability
        mock_check_tool.return_value = True

        result = self.runner.invoke(app, ["check-tools"])

        assert result.exit_code == 0
        assert "tool" in result.output.lower()

    @patch("src.improved_sdd_cli.TemplateResolver")
    def test_init_command_file_tracking(self, mock_resolver_class):
        """Test that file creation and modification tracking works."""
        # Setup complex mock for TemplateResolver
        mock_resolver = Mock()
        mock_resolver_class.return_value = mock_resolver

        # Create a mock template resolution result
        mock_result = Mock()
        mock_result.templates_path = Path("mock/templates")
        mock_result.source_type = Mock()
        mock_result.total_templates = 2
        mock_resolver.resolve_templates.return_value = mock_result

        # Mock the actual template files that would exist
        with patch("pathlib.Path.exists") as mock_exists:
            with patch("pathlib.Path.iterdir") as mock_iterdir:
                with patch("pathlib.Path.is_dir") as mock_is_dir:
                    with patch("pathlib.Path.read_text") as mock_read_text:
                        with patch("pathlib.Path.write_text") as mock_write_text:
                            with patch("pathlib.Path.mkdir") as mock_mkdir:
                                # Setup path mocking
                                mock_exists.return_value = True
                                mock_is_dir.return_value = True
                                mock_iterdir.return_value = [
                                    Path("mock/templates/instructions"),
                                    Path("mock/templates/prompts"),
                                ]
                                mock_read_text.return_value = "Template content {AI_ASSISTANT}"

                                # Use input simulation for interactive selections
                                result = self.runner.invoke(app, ["init", "test-project"], input="1\n\n1\n")

                                # Should complete successfully
                                assert result.exit_code == 0

                                # Verify that file creation methods were called
                                mock_write_text.assert_called()
                                mock_mkdir.assert_called()

    def test_init_command_output_messages(self):
        """Test that init command provides appropriate output messages."""
        # Test with invalid repository format
        result = self.runner.invoke(app, ["init", "test-project", "--template-repo", "invalid-format"])

        assert result.exit_code != 0
        assert "repository" in result.output.lower()

    def test_init_command_validation_errors(self):
        """Test init command input validation and error handling."""
        # Test invalid app type
        result = self.runner.invoke(app, ["init", "test-project", "--app-type", "invalid-type"])
        assert result.exit_code != 0

        # Test invalid AI tools
        result = self.runner.invoke(app, ["init", "test-project", "--ai-tools", "invalid-tool"])
        assert result.exit_code != 0

    @patch("src.improved_sdd_cli.select_ai_tools")
    @patch("src.improved_sdd_cli.select_app_type")
    @patch("src.improved_sdd_cli.create_project_structure")
    def test_init_command_user_interaction_simulation(self, mock_create_project, mock_select_app, mock_select_ai):
        """Test init command with simulated user interaction."""
        # Setup mocks
        mock_select_ai.return_value = ["github-copilot"]
        mock_select_app.return_value = "mcp-server"
        mock_create_project.return_value = None

        # Simulate user selecting option 1 for AI tools and app type
        result = self.runner.invoke(app, ["init", "test-project"], input="1\n\n1\n")

        assert result.exit_code == 0
        mock_select_ai.assert_called_once()
        mock_select_app.assert_called_once()
        mock_create_project.assert_called_once()

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
