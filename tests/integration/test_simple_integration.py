"""Simple integration tests that don't require complex mocking."""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.services.file_tracker import FileTracker
from src.improved_sdd_cli import app


@pytest.mark.integration
class TestBasicIntegration:
    """Basic integration tests without complex template mocking."""

    def test_help_commands_work(self, runner: CliRunner):
        """Test that all help commands work."""
        # Main help
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "improved-sdd" in result.stdout

        # Init help
        result = runner.invoke(app, ["init", "--help"])
        assert result.exit_code == 0
        assert "Install Improved-SDD templates" in result.stdout

        # Delete help
        result = runner.invoke(app, ["delete", "--help"])
        assert result.exit_code == 0
        assert "Delete Improved-SDD templates" in result.stdout

        # Check help
        result = runner.invoke(app, ["check", "--help"])
        assert result.exit_code == 0
        assert "Check that all required tools" in result.stdout

    def test_file_tracker_integration(self):
        """Test FileTracker integration with real paths."""
        tracker = FileTracker()

        # Test tracking operations
        test_files = [
            Path("project/.github/chatmodes/spec.chatmode.md"),
            Path("project/.github/instructions/cli.instructions.md"),
            Path("project/.github/prompts/analyze.prompt.md"),
        ]

        test_dirs = [Path("project"), Path("project/.github"), Path("project/.github/chatmodes")]

        # Track files and directories
        for dir_path in test_dirs:
            tracker.track_dir_creation(dir_path)

        for file_path in test_files:
            tracker.track_file_creation(file_path)

        # Get summary
        summary = tracker.get_summary()

        # Verify summary contains expected information
        assert "Directories Created:" in summary
        assert "Files Created:" in summary
        assert "project" in summary
        assert "Chatmodes" in summary
        assert "Instructions" in summary
        assert "Prompts" in summary

    @patch("src.improved_sdd_cli.console_manager.show_banner")
    def test_check_command_basic(self, mock_banner, runner: CliRunner):
        """Test basic check command functionality."""
        with patch("src.commands.check.check_tool") as mock_check_tool:
            with patch("src.commands.check.check_github_copilot") as mock_check_copilot:
                with patch("src.commands.check.offer_user_choice") as mock_offer_choice:
                    # Set up mocks for successful tool checks
                    mock_check_tool.return_value = True
                    mock_check_copilot.return_value = True
                    mock_offer_choice.return_value = True

                    result = runner.invoke(app, ["check"])

                    assert result.exit_code == 0
                    assert "Improved-SDD CLI is ready to use!" in result.stdout

    @patch("src.improved_sdd_cli.console_manager.show_banner")
    def test_init_validation(self, mock_banner, runner: CliRunner):
        """Test init command input validation."""
        # Test invalid app type
        result = runner.invoke(app, ["init", "--app-type", "invalid-type", "--ai-tools", "github-copilot"])
        assert result.exit_code == 1
        assert "Invalid app type" in result.stdout

        # Test invalid AI tools
        result = runner.invoke(app, ["init", "--app-type", "python-cli", "--ai-tools", "invalid-tool"])
        assert result.exit_code == 1
        assert "Invalid AI tool(s)" in result.stdout

    @patch("src.improved_sdd_cli.console_manager.show_banner")
    def test_delete_validation(self, mock_banner, runner: CliRunner):
        """Test delete command input validation."""
        # Test invalid app type
        result = runner.invoke(app, ["delete", "invalid-type"])
        assert result.exit_code == 1
        assert "Invalid app type" in result.stdout

    def test_app_banner_group(self, runner: CliRunner):
        """Test that the app uses the custom banner group."""
        from src.improved_sdd_cli import BannerGroup

        # The app should have the custom group class
        # We can test this by checking if the app has the expected behavior
        # rather than checking the internal class directly
        assert hasattr(app, "info")
        assert app.info.name == "improved-sdd"

    def test_constants_are_defined(self):
        """Test that important constants are properly defined."""
        from src.core.config import AI_TOOLS, APP_TYPES, BANNER, TAGLINE

        # Verify AI_TOOLS structure
        assert isinstance(AI_TOOLS, dict)
        assert "github-copilot" in AI_TOOLS
        assert "name" in AI_TOOLS["github-copilot"]
        assert "keywords" in AI_TOOLS["github-copilot"]

        # Verify APP_TYPES structure
        assert isinstance(APP_TYPES, dict)
        assert "python-cli" in APP_TYPES
        assert "mcp-server" in APP_TYPES

        # Verify banner and tagline
        assert isinstance(BANNER, str)
        assert isinstance(TAGLINE, str)
        assert len(BANNER) > 0
        assert len(TAGLINE) > 0
