"""Unit tests for core classes and functions."""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

# Import after path modification - this avoids E402 since it's necessary
from improved_sdd_cli import (  # noqa: E402
    FileTracker,
    check_github_copilot,
    check_tool,
    customize_template_content,
    get_template_filename,
    offer_user_choice,
)


@pytest.mark.unit
class TestFileTracker:
    """Test the FileTracker class."""

    def test_init(self):
        """Test FileTracker initialization."""
        tracker = FileTracker()
        assert tracker.created_files == []
        assert tracker.modified_files == []
        assert tracker.created_dirs == []

    def test_track_file_creation(self):
        """Test tracking file creation."""
        tracker = FileTracker()
        test_path = Path("test/file.txt")

        tracker.track_file_creation(test_path)

        assert str(test_path) in tracker.created_files
        assert len(tracker.created_files) == 1

    def test_track_file_modification(self):
        """Test tracking file modification."""
        tracker = FileTracker()
        test_path = Path("test/file.txt")

        tracker.track_file_modification(test_path)

        assert str(test_path) in tracker.modified_files
        assert len(tracker.modified_files) == 1

    def test_track_dir_creation(self):
        """Test tracking directory creation."""
        tracker = FileTracker()
        test_path = Path("test/dir")

        tracker.track_dir_creation(test_path)

        assert str(test_path) in tracker.created_dirs
        assert len(tracker.created_dirs) == 1

    def test_get_summary_empty(self):
        """Test get_summary with no tracked files."""
        tracker = FileTracker()
        summary = tracker.get_summary()

        assert "No files were created or modified" in summary

    def test_get_summary_with_files(self):
        """Test get_summary with tracked files."""
        tracker = FileTracker()

        # Add various files
        tracker.track_dir_creation(Path(".github"))
        tracker.track_file_creation(Path(".github/chatmodes/test.md"))
        tracker.track_file_modification(Path(".github/instructions/existing.md"))

        summary = tracker.get_summary()

        assert "Directories Created:" in summary
        assert "Files Created:" in summary
        assert "Files Modified:" in summary
        assert ".github" in summary
        # Use platform-specific path separators
        assert str(Path(".github/chatmodes/test.md")) in summary
        assert str(Path(".github/instructions/existing.md")) in summary

    def test_group_files_by_type(self):
        """Test grouping files by type."""
        tracker = FileTracker()

        files = [
            ".github/chatmodes/spec.md",
            ".github/instructions/cli.md",
            ".github/prompts/analyze.md",
            ".github/commands/test.md",
            "README.md",
        ]

        groups = tracker._group_files_by_type(files)

        assert "Chatmodes" in groups
        assert "Instructions" in groups
        assert "Prompts" in groups
        assert "Commands" in groups
        assert "Other" in groups
        assert len(groups["Chatmodes"]) == 1
        assert len(groups["Instructions"]) == 1
        assert len(groups["Prompts"]) == 1
        assert len(groups["Commands"]) == 1
        assert len(groups["Other"]) == 1


@pytest.mark.unit
class TestTemplateCustomization:
    """Test template customization functions."""

    def test_customize_template_content_github_copilot(self):
        """Test customizing template content for GitHub Copilot."""
        content = """# Template for {AI_ASSISTANT}

Use {AI_SHORTNAME} with {AI_COMMAND} to get started.
"""

        result = customize_template_content(content, "github-copilot")

        assert "{AI_ASSISTANT}" not in result
        assert "GitHub Copilot" in result
        assert "Copilot" in result
        assert "Ctrl+Shift+P" in result

    def test_customize_template_content_claude(self):
        """Test customizing template content for Claude."""
        content = """# Template for {AI_ASSISTANT}

Use {AI_SHORTNAME} with {AI_COMMAND} to get started.
"""

        result = customize_template_content(content, "claude")

        assert "{AI_ASSISTANT}" not in result
        assert "Claude" in result
        assert "Open Claude interface" in result

    def test_customize_template_content_unknown_tool(self):
        """Test customizing template content for unknown AI tool."""
        content = "Test content with {AI_ASSISTANT}"

        result = customize_template_content(content, "unknown-tool")

        # Should return content unchanged
        assert result == content

    def test_get_template_filename_github_copilot(self):
        """Test generating template filename for GitHub Copilot."""
        filename = get_template_filename("specMode.md", "github-copilot", "chatmodes")
        assert filename == "specMode.chatmode.md"

        filename = get_template_filename("CLIPythonDev.md", "github-copilot", "instructions")
        assert filename == "CLIPythonDev.instructions.md"

    def test_get_template_filename_claude(self):
        """Test generating template filename for Claude."""
        filename = get_template_filename("specMode.md", "claude", "chatmodes")
        assert filename == "specMode.claude.md"

        filename = get_template_filename("testCommand.md", "claude", "commands")
        assert filename == "testCommand.claude.md"

    def test_get_template_filename_unknown_tool(self):
        """Test generating template filename for unknown AI tool."""
        filename = get_template_filename("test.md", "unknown-tool", "chatmodes")
        assert filename == "test.md"  # Should return original name

    def test_get_template_filename_edge_cases(self):
        """Test generating template filename edge cases."""
        # File without extension
        filename = get_template_filename("noext", "github-copilot", "chatmodes")
        assert filename == "noext.chatmode.md"

        # Multiple dots in filename
        filename = get_template_filename("file.test.md", "github-copilot", "prompts")
        assert filename == "file.prompt.md"


@pytest.mark.unit
class TestToolChecking:
    """Test tool checking functions."""

    @patch("shutil.which")
    @patch("improved_sdd_cli.console")
    def test_check_tool_found(self, mock_console, mock_which):
        """Test check_tool when tool is found."""
        mock_which.return_value = "/usr/bin/python"

        result = check_tool("python", "Install from python.org")

        assert result is True
        mock_console.print.assert_called_with("[green][OK][/green] python found")

    @patch("shutil.which")
    @patch("improved_sdd_cli.console")
    def test_check_tool_not_found_required(self, mock_console, mock_which):
        """Test check_tool when required tool is not found."""
        mock_which.return_value = None

        result = check_tool("python", "Install from python.org")

        assert result is False
        mock_console.print.assert_any_call("[red][ERROR][/red]  python not found")

    @patch("shutil.which")
    @patch("improved_sdd_cli.console")
    def test_check_tool_not_found_optional(self, mock_console, mock_which):
        """Test check_tool when optional tool is not found."""
        mock_which.return_value = None

        result = check_tool("optional-tool", "Install hint", optional=True)

        assert result is False
        mock_console.print.assert_any_call("[yellow][WARN][/yellow]  optional-tool not found")

    @patch("shutil.which")
    @patch("improved_sdd_cli.console")
    def test_check_github_copilot_vscode_found(self, mock_console, mock_which):
        """Test check_github_copilot when VS Code is found."""
        mock_which.return_value = "/usr/bin/code"

        result = check_github_copilot()

        assert result is True
        mock_console.print.assert_any_call("[green][OK][/green] VS Code found")

    @patch("shutil.which")
    @patch("improved_sdd_cli.console")
    def test_check_github_copilot_vscode_not_found(self, mock_console, mock_which):
        """Test check_github_copilot when VS Code is not found."""
        mock_which.return_value = None

        result = check_github_copilot()

        assert result is False
        mock_console.print.assert_any_call("[yellow][WARN][/yellow]  VS Code not found")

    @patch("typer.prompt")
    @patch("improved_sdd_cli.console")
    def test_offer_user_choice_no_missing_tools(self, mock_console, mock_prompt):
        """Test offer_user_choice with no missing tools."""
        result = offer_user_choice([])

        assert result is True
        mock_prompt.assert_not_called()

    @patch("typer.prompt")
    @patch("improved_sdd_cli.console")
    def test_offer_user_choice_user_accepts(self, mock_console, mock_prompt):
        """Test offer_user_choice when user accepts to continue."""
        mock_prompt.return_value = "y"

        result = offer_user_choice(["Tool1", "Tool2"])

        assert result is True
        mock_prompt.assert_called_once()

    @patch("typer.prompt")
    @patch("improved_sdd_cli.console")
    def test_offer_user_choice_user_declines(self, mock_console, mock_prompt):
        """Test offer_user_choice when user declines to continue."""
        mock_prompt.return_value = "n"

        result = offer_user_choice(["Tool1", "Tool2"])

        assert result is False
        mock_prompt.assert_called_once()

    @patch("typer.prompt")
    @patch("improved_sdd_cli.console")
    def test_offer_user_choice_keyboard_interrupt(self, mock_console, mock_prompt):
        """Test offer_user_choice with keyboard interrupt."""
        mock_prompt.side_effect = KeyboardInterrupt()

        result = offer_user_choice(["Tool1"])

        assert result is False
