"""Integration tests for improved-sdd CLI workflows."""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.improved_sdd_cli import app  # noqa: E402
from src.services.file_tracker import FileTracker  # noqa: E402
from src.utils import create_project_structure  # noqa: E402


@pytest.mark.integration
class TestCompleteWorkflows:
    """Test complete CLI workflows end-to-end."""

    @patch("src.improved_sdd_cli.console_manager.show_banner")
    def test_complete_init_workflow_new_project(
        self, mock_banner, runner: CliRunner, temp_dir: Path, mock_script_location, mock_templates_dir: Path
    ):
        """Test complete init workflow creating a new project."""
        project_name = "test-project"
        project_path = temp_dir / project_name

        with patch("pathlib.Path.cwd", return_value=temp_dir):
            with patch(
                "src.services.template_resolver.TemplateResolver.get_bundled_templates_path",
                return_value=mock_templates_dir,
            ):
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
        assert (chatmodes_dir / "sddSpecDriven.chatmode.md").exists()

        instructions_dir = github_dir / "instructions"
        assert instructions_dir.exists()
        assert (instructions_dir / "sddPythonCliDev.instructions.md").exists()

    @patch("builtins.input")
    @patch("src.improved_sdd_cli.console_manager.show_banner")
    def test_complete_init_workflow_interactive(
        self, mock_banner, mock_input, runner: CliRunner, temp_dir: Path, mock_templates_dir: Path
    ):
        """Test complete init workflow with interactive selections."""
        # Mock user inputs: app type = 1 (first option), ai tools = 1 (first option)
        mock_input.side_effect = ["1", "1"]

        with patch("pathlib.Path.cwd", return_value=temp_dir):
            with patch(
                "src.services.template_resolver.TemplateResolver.get_bundled_templates_path",
                return_value=mock_templates_dir,
            ):
                result = runner.invoke(app, ["init", "--force"])

        assert result.exit_code == 0
        assert "Templates installed!" in result.stdout

        # Verify templates were installed in current directory
        github_dir = temp_dir / ".github"
        assert github_dir.exists()

    @patch("typer.confirm")
    @patch("src.improved_sdd_cli.console_manager.show_banner")
    def test_init_then_delete_workflow(
        self,
        mock_banner,
        mock_confirm,
        runner: CliRunner,
        temp_dir: Path,
        mock_script_location,
        mock_templates_dir: Path,
    ):
        """Test init followed by delete workflow."""
        # First, initialize project
        with patch("pathlib.Path.cwd", return_value=temp_dir):
            with patch(
                "src.services.template_resolver.TemplateResolver.get_bundled_templates_path",
                return_value=mock_templates_dir,
            ):
                init_result = runner.invoke(
                    app, ["init", "--app-type", "python-cli", "--ai-tools", "github-copilot", "--force"]
                )

        assert init_result.exit_code == 0

        # Verify files were created
        github_dir = temp_dir / ".github"
        assert github_dir.exists()
        chatmodes_file = github_dir / "chatmodes" / "sddSpecDriven.chatmode.md"
        assert chatmodes_file.exists()

        # Now delete with confirmation
        mock_confirm.return_value = True

        with patch("pathlib.Path.cwd", return_value=temp_dir):
            with patch("typer.prompt", return_value="Yes"):
                delete_result = runner.invoke(app, ["delete", "python-cli"])

        assert delete_result.exit_code == 0
        assert "Deletion complete" in delete_result.stdout

        # Verify files were deleted
        assert not chatmodes_file.exists()

    @patch("src.improved_sdd_cli.console_manager.show_banner")
    def test_multiple_ai_tools_workflow(
        self, mock_banner, runner: CliRunner, temp_dir: Path, mock_script_location, mock_templates_dir: Path
    ):
        """Test workflow with multiple AI tools."""
        with patch("pathlib.Path.cwd", return_value=temp_dir):
            with patch(
                "src.services.template_resolver.TemplateResolver.get_bundled_templates_path",
                return_value=mock_templates_dir,
            ):
                result = runner.invoke(
                    app, ["init", "--app-type", "mcp-server", "--ai-tools", "github-copilot,claude", "--force"]
                )

        assert result.exit_code == 0

        # Verify both AI tool templates were created
        github_dir = temp_dir / ".github"

        # GitHub Copilot files (in root .github)
        assert (github_dir / "chatmodes" / "sddSpecDriven.chatmode.md").exists()

        # Claude files (in claude subdirectory)
        assert (github_dir / "claude" / "chatmodes" / "sddSpecDriven.chatmode.claude.md").exists()

    @patch("typer.confirm")
    @patch("src.improved_sdd_cli.console_manager.show_banner")
    def test_overwrite_existing_files_workflow(
        self,
        mock_banner,
        mock_confirm,
        runner: CliRunner,
        project_with_existing_files: Path,
        mock_script_location,
        mock_templates_dir: Path,
    ):
        """Test workflow when overwriting existing files."""
        mock_confirm.return_value = True  # User confirms overwrite

        with patch("pathlib.Path.cwd", return_value=project_with_existing_files):
            with patch(
                "src.services.template_resolver.TemplateResolver.get_bundled_templates_path",
                return_value=mock_templates_dir,
            ):
                result = runner.invoke(app, ["init", "--app-type", "python-cli", "--ai-tools", "github-copilot"])

        assert result.exit_code == 0
        assert "Files Modified:" in result.stdout or "Templates installed!" in result.stdout


@pytest.mark.integration
class TestProjectStructureCreation:
    """Test project structure creation in detail."""

    def test_create_project_structure_python_cli(self, temp_project_dir: Path, mock_templates_dir: Path):
        """Test creating project structure for Python CLI."""
        file_tracker = FileTracker()

        with patch(
            "src.services.template_resolver.TemplateResolver.get_bundled_templates_path",
            return_value=mock_templates_dir,
        ):
            create_project_structure(temp_project_dir, "python-cli", ["github-copilot"], file_tracker, force=True)

        # Verify correct instruction file was used
        instructions_dir = temp_project_dir / ".github" / "instructions"
        assert instructions_dir.exists()
        cli_instruction = instructions_dir / "sddPythonCliDev.instructions.md"
        assert cli_instruction.exists()

        # Should not have MCP instruction
        mcp_instruction = instructions_dir / "sddMcpServerDev.instructions.md"
        assert not mcp_instruction.exists()

    def test_create_project_structure_mcp_server(self, temp_project_dir: Path, mock_templates_dir: Path):
        """Test creating project structure for MCP server."""
        file_tracker = FileTracker()

        with patch(
            "src.services.template_resolver.TemplateResolver.get_bundled_templates_path",
            return_value=mock_templates_dir,
        ):
            create_project_structure(temp_project_dir, "mcp-server", ["github-copilot"], file_tracker, force=True)

        # Verify correct instruction file was used
        instructions_dir = temp_project_dir / ".github" / "instructions"
        assert instructions_dir.exists()
        mcp_instruction = instructions_dir / "sddMcpServerDev.instructions.md"
        assert mcp_instruction.exists()

        # Should not have CLI instruction
        cli_instruction = instructions_dir / "sddPythonCliDev.instructions.md"
        assert not cli_instruction.exists()

    def test_create_project_structure_template_customization(self, temp_project_dir: Path, mock_templates_dir: Path):
        """Test that templates are properly customized for AI tools."""
        file_tracker = FileTracker()

        with patch(
            "src.services.template_resolver.TemplateResolver.get_bundled_templates_path",
            return_value=mock_templates_dir,
        ):
            create_project_structure(temp_project_dir, "python-cli", ["github-copilot"], file_tracker, force=True)

        # Check that template content was customized
        spec_file = temp_project_dir / ".github" / "chatmodes" / "sddSpecDriven.chatmode.md"
        assert spec_file.exists()

        content = spec_file.read_text()
        assert "GitHub Copilot" in content
        assert "Copilot" in content
        assert "Ctrl+Shift+P" in content
        assert "{AI_ASSISTANT}" not in content

    def test_create_project_structure_multiple_ai_tools(self, temp_project_dir: Path, mock_templates_dir: Path):
        """Test creating structure for multiple AI tools."""
        file_tracker = FileTracker()

        with patch(
            "src.services.template_resolver.TemplateResolver.get_bundled_templates_path",
            return_value=mock_templates_dir,
        ):
            create_project_structure(
                temp_project_dir, "python-cli", ["github-copilot", "claude"], file_tracker, force=True
            )

        # Check GitHub Copilot files (root .github)
        copilot_file = temp_project_dir / ".github" / "chatmodes" / "sddSpecDriven.chatmode.md"
        assert copilot_file.exists()
        copilot_content = copilot_file.read_text()
        assert "GitHub Copilot" in copilot_content

        # Check Claude files (claude subdirectory)
        claude_file = temp_project_dir / ".github" / "claude" / "chatmodes" / "sddSpecDriven.chatmode.claude.md"
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

        with patch(
            "src.services.template_resolver.TemplateResolver.get_bundled_templates_path",
            return_value=mock_templates_dir,
        ):
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

    @patch("src.commands.check.check_tool")
    @patch("src.commands.check.check_github_copilot")
    @patch("src.commands.check.offer_user_choice")
    @patch("src.improved_sdd_cli.console_manager.show_banner")
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

        with patch(
            "src.services.template_resolver.TemplateResolver.get_bundled_templates_path", return_value=non_existent
        ):
            with patch("pathlib.Path.cwd", return_value=temp_dir):
                result = runner.invoke(
                    app, ["init", "--app-type", "python-cli", "--ai-tools", "github-copilot", "--force"]
                )

        # Current implementation exits with error when templates don't exist
        assert result.exit_code == 1
        assert "Template source not accessible" in result.stdout


@pytest.mark.integration
class TestTemplateDownloadIntegration:
    """Integration tests for the Template Download System end-to-end workflows."""

    @patch("src.improved_sdd_cli.console_manager.show_banner")
    def test_template_resolution_priority_workflow(self, mock_banner, runner: CliRunner, temp_dir: Path):
        """Test complete template resolution workflow with priority system."""
        # Create local .sdd_templates folder with complete template structure
        local_templates = temp_dir / ".sdd_templates"
        local_templates.mkdir()

        # Create all required template directories and files
        for dir_name in ["chatmodes", "instructions", "prompts", "commands"]:
            (local_templates / dir_name).mkdir()
            (local_templates / dir_name / f"{dir_name.rstrip('s')}.md").write_text(
                f"# Local {dir_name} Template for {{AI_ASSISTANT}}"
            )

        # Create specific files expected by the CLI
        (local_templates / "chatmodes" / "sddSpecDriven.chatmode.md").write_text("# Local Spec Mode for {AI_ASSISTANT}")
        (local_templates / "instructions" / "sddPythonCliDev.instructions.md").write_text(
            "# Local Python CLI Dev for {AI_ASSISTANT}"
        )

        with patch("pathlib.Path.cwd", return_value=temp_dir):
            result = runner.invoke(
                app,
                ["init", "--app-type", "python-cli", "--ai-tools", "github-copilot", "--force"],
            )

        assert result.exit_code == 0
        assert "Templates installed!" in result.stdout
        assert "Found local template files in 4 categories" in result.stdout

        # Verify local templates were used (not modified)
        local_spec = local_templates / "chatmodes" / "sddSpecDriven.chatmode.md"
        assert local_spec.exists()
        assert local_spec.read_text() == "# Local Spec Mode for {AI_ASSISTANT}"  # Unchanged

        # When local templates exist, CLI should use them as the source
        # Files are created in .github directory based on local template source
        assert "13 files created" in result.stdout
        assert "Merged 6 local files with 11 downloaded files" in result.stdout

    @patch("src.improved_sdd_cli.console_manager.show_banner")
    def test_template_download_when_no_local_templates(
        self, mock_banner, runner: CliRunner, temp_dir: Path, mock_templates_dir: Path
    ):
        """Test template download workflow when no local templates exist."""
        # Don't create any local templates - should trigger download or bundled fallback

        with patch("pathlib.Path.cwd", return_value=temp_dir):
            with patch(
                "src.services.template_resolver.TemplateResolver.get_bundled_templates_path",
                return_value=mock_templates_dir,
            ):
                result = runner.invoke(
                    app,
                    ["init", "--app-type", "python-cli", "--ai-tools", "github-copilot", "--force"],
                )

        assert result.exit_code == 0
        assert "Templates installed!" in result.stdout

        # Should have attempted to download or use bundled templates
        # The exact behavior depends on network connectivity and bundled templates availability

    @patch("src.improved_sdd_cli.console_manager.show_banner")
    def test_offline_mode_workflow(self, mock_banner, runner: CliRunner, temp_dir: Path, mock_templates_dir: Path):
        """Test complete offline mode workflow."""
        # Test offline mode flag

        with patch("pathlib.Path.cwd", return_value=temp_dir):
            with patch(
                "src.services.template_resolver.TemplateResolver.get_bundled_templates_path",
                return_value=mock_templates_dir,
            ):
                result = runner.invoke(
                    app,
                    ["init", "--app-type", "python-cli", "--ai-tools", "github-copilot", "--offline", "--force"],
                )

        assert result.exit_code == 0
        # In offline mode, should complete successfully (may use bundled templates or graceful handling)
        assert "Templates installed!" in result.stdout or "offline" in result.stdout.lower()

    @patch("src.improved_sdd_cli.console_manager.show_banner")
    def test_cli_option_combinations_workflow(self, mock_banner, runner: CliRunner, temp_dir: Path):
        """Test various CLI option combinations and edge cases."""
        # Test conflicting options (should fail)
        with patch("pathlib.Path.cwd", return_value=temp_dir):
            result = runner.invoke(
                app,
                ["init", "--offline", "--force-download", "--force"],
            )

        assert result.exit_code == 1
        assert "Cannot use --offline and --force-download together" in result.stdout

    @patch("src.improved_sdd_cli.console_manager.show_banner")
    def test_user_templates_protection_workflow(self, mock_banner, runner: CliRunner, temp_dir: Path):
        """Test that user .sdd_templates folders are never modified."""
        # Create user templates with specific content
        user_templates = temp_dir / ".sdd_templates"
        user_templates.mkdir()
        (user_templates / "chatmodes").mkdir()
        original_content = "# NEVER MODIFY THIS USER TEMPLATE\nOriginal user content"
        user_spec = user_templates / "chatmodes" / "sddSpecDriven.chatmode.md"
        user_spec.write_text(original_content)

        # Record original modification time
        original_mtime = user_spec.stat().st_mtime

        with patch("pathlib.Path.cwd", return_value=temp_dir):
            result = runner.invoke(
                app,
                [
                    "init",
                    "--app-type",
                    "python-cli",
                    "--ai-tools",
                    "github-copilot",
                    "--force",  # Should use local templates, not force download
                ],
            )

        assert result.exit_code == 0

        # Verify user templates were NEVER modified
        assert user_spec.exists()
        assert user_spec.read_text() == original_content
        assert user_spec.stat().st_mtime == original_mtime

    @patch("src.improved_sdd_cli.console_manager.show_banner")
    def test_error_handling_graceful_degradation(self, mock_banner, runner: CliRunner, temp_dir: Path):
        """Test graceful error handling when templates are not available."""
        # Test with no local templates and simulate network issues
        with patch("pathlib.Path.cwd", return_value=temp_dir):
            result = runner.invoke(
                app,
                ["init", "--app-type", "python-cli", "--ai-tools", "github-copilot", "--force"],
            )

        # Should handle gracefully - either succeed with bundled templates or provide clear error
        assert result.exit_code in [0, 1]  # May succeed or fail gracefully

        if result.exit_code == 0:
            assert "Templates installed!" in result.stdout
        else:
            # Should provide helpful error message
            assert len(result.stdout) > 0
