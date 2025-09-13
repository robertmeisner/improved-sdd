"""Unit tests for core classes and functions."""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# Import after path modification - this avoids E402 since it's necessary
from src import (  # noqa: E402
    FileTracker,
    check_github_copilot,
    check_tool,
    customize_template_content,
    get_template_filename,
    load_gitlab_flow_file,
    offer_user_choice,
)
from src.core.config import config


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
        assert filename == "specMode.md"  # GitHub Copilot uses original names

        filename = get_template_filename("CLIPythonDev.md", "github-copilot", "instructions")
        assert filename == "CLIPythonDev.md"  # GitHub Copilot uses original names

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
        # File without extension - GitHub Copilot returns original
        filename = get_template_filename("noext", "github-copilot", "chatmodes")
        assert filename == "noext"

        # Multiple dots in filename - GitHub Copilot returns original
        filename = get_template_filename("file.test.md", "github-copilot", "prompts")
        assert filename == "file.test.md"


@pytest.mark.unit
class TestToolChecking:
    """Test tool checking functions."""

    @patch("shutil.which")
    @patch("src.ui.console.ConsoleManager.print_status")
    def test_check_tool_found(self, mock_print_status, mock_which):
        """Test check_tool when tool is found."""
        mock_which.return_value = "/usr/bin/python"

        result = check_tool("python", "Install from python.org")

        assert result is True
        mock_print_status.assert_called_with("python", True)

    @patch("shutil.which")
    @patch("src.ui.console.ConsoleManager.print_status")
    def test_check_tool_not_found_required(self, mock_print_status, mock_which):
        """Test check_tool when required tool is not found."""
        mock_which.return_value = None

        result = check_tool("python", "Install from python.org")

        assert result is False
        mock_print_status.assert_called_with("python", False, "Install from python.org", False)

    @patch("shutil.which")
    @patch("src.ui.console.ConsoleManager.print_status")
    def test_check_tool_not_found_optional(self, mock_print_status, mock_which):
        """Test check_tool when optional tool is not found."""
        mock_which.return_value = None

        result = check_tool("optional-tool", "Install hint", optional=True)

        assert result is False
        mock_print_status.assert_called_with("optional-tool", False, "Install hint", True)

    @patch("shutil.which")
    @patch("src.ui.console.ConsoleManager.print_success")
    @patch("src.ui.console.ConsoleManager.print_dim")
    def test_check_github_copilot_vscode_found(self, mock_print_dim, mock_print_success, mock_which):
        """Test check_github_copilot when VS Code is found."""
        mock_which.return_value = "/usr/bin/code"

        result = check_github_copilot()

        assert result is True
        mock_print_success.assert_called_with("VS Code found")

    @patch("shutil.which")
    @patch("src.ui.console.ConsoleManager.print_warning")
    @patch("src.ui.console.ConsoleManager.print")
    @patch("src.ui.console.ConsoleManager.print_dim")
    def test_check_github_copilot_vscode_not_found(self, mock_print_dim, mock_print, mock_print_warning, mock_which):
        """Test check_github_copilot when VS Code is not found."""
        mock_which.return_value = None

        result = check_github_copilot()

        assert result is False
        mock_print_warning.assert_called_with("VS Code not found")

    @patch("typer.prompt")
    @patch("src.ui.console.ConsoleManager.print")
    def test_offer_user_choice_no_missing_tools(self, mock_print, mock_prompt):
        """Test offer_user_choice with no missing tools."""
        result = offer_user_choice([])

        assert result is True
        mock_prompt.assert_not_called()

    @patch.dict(os.environ, {}, clear=True)  # Clear CI environment variables
    @patch("improved_sdd_cli.typer.prompt")
    @patch("src.ui.console.ConsoleManager.print_success")
    @patch("src.ui.console.ConsoleManager.print")
    def test_offer_user_choice_user_accepts(self, mock_print, mock_print_success, mock_prompt):
        """Test offer_user_choice when user accepts to continue."""
        mock_prompt.return_value = "y"

        result = offer_user_choice(["Tool1", "Tool2"])

        assert result is True
        mock_prompt.assert_called_once()

    @patch.dict(os.environ, {}, clear=True)  # Clear CI environment variables
    @patch("improved_sdd_cli.typer.prompt")
    @patch("src.ui.console.ConsoleManager.print_warning")
    @patch("src.ui.console.ConsoleManager.print")
    def test_offer_user_choice_user_declines(self, mock_print, mock_print_warning, mock_prompt):
        """Test offer_user_choice when user declines to continue."""
        mock_prompt.return_value = "n"

        result = offer_user_choice(["Tool1", "Tool2"])

        assert result is False
        mock_prompt.assert_called_once()

    @patch.dict(os.environ, {}, clear=True)  # Clear CI environment variables
    @patch("improved_sdd_cli.typer.prompt")
    @patch("src.ui.console.ConsoleManager.print_warning")
    @patch("src.ui.console.ConsoleManager.print")
    def test_offer_user_choice_keyboard_interrupt(self, mock_print, mock_print_warning, mock_prompt):
        """Test offer_user_choice with keyboard interrupt."""
        mock_prompt.side_effect = KeyboardInterrupt()

        result = offer_user_choice(["Tool1"])

        assert result is False
        mock_prompt.assert_called_once()

    @patch.dict(os.environ, {"CI": "true"})  # Simulate CI environment
    @patch("improved_sdd_cli.typer.prompt")
    @patch("src.ui.console.ConsoleManager.print_success")
    @patch("src.ui.console.ConsoleManager.print")
    def test_offer_user_choice_ci_mode(self, mock_print, mock_print_success, mock_prompt):
        """Test offer_user_choice in CI environment returns True without prompting."""
        result = offer_user_choice(["Tool1", "Tool2"])

        assert result is True


@pytest.mark.unit
class TestGitLabFlowConfig:
    """Test GitLab Flow configuration functionality."""

    def test_get_gitlab_flow_keywords_disabled(self):
        """Test get_gitlab_flow_keywords returns empty strings when disabled."""
        keywords = config.get_gitlab_flow_keywords(enabled=False)

        expected_keywords = ["{GITLAB_FLOW_SETUP}", "{GITLAB_FLOW_COMMIT}", "{GITLAB_FLOW_PR}"]

        # All keywords should be present but empty when disabled
        for keyword in expected_keywords:
            assert keyword in keywords
            assert keywords[keyword] == ""

    def test_get_gitlab_flow_keywords_windows_platform(self):
        """Test get_gitlab_flow_keywords with Windows platform commands."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock GitLab Flow markdown files
            gitlab_flow_dir = Path(temp_dir) / "gitlab-flow"
            gitlab_flow_dir.mkdir()

            setup_file = gitlab_flow_dir / "gitlab-flow-setup.md"
            setup_file.write_text("Setup: {GIT_STATUS} and {BRANCH_CREATE}")

            commit_file = gitlab_flow_dir / "gitlab-flow-commit.md"
            commit_file.write_text("Commit: {COMMIT}")

            pr_file = gitlab_flow_dir / "gitlab-flow-pr.md"
            pr_file.write_text("PR: {PUSH_PR}")

            keywords = config.get_gitlab_flow_keywords(enabled=True, platform="windows", template_dir=temp_dir)

            # Check Windows-specific command syntax (semicolon)
            assert ";" in keywords["{GITLAB_FLOW_COMMIT}"]  # Windows uses semicolon
            assert "git status" in keywords["{GITLAB_FLOW_SETUP}"]

    def test_get_gitlab_flow_keywords_unix_platform(self):
        """Test get_gitlab_flow_keywords with Unix platform commands."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock GitLab Flow markdown files
            gitlab_flow_dir = Path(temp_dir) / "gitlab-flow"
            gitlab_flow_dir.mkdir()

            commit_file = gitlab_flow_dir / "gitlab-flow-commit.md"
            commit_file.write_text("Commit: {COMMIT}")

            keywords = config.get_gitlab_flow_keywords(enabled=True, platform="unix", template_dir=temp_dir)

            # Check Unix-specific command syntax (double ampersand)
            assert "&&" in keywords["{GITLAB_FLOW_COMMIT}"]  # Unix uses &&

    def test_get_gitlab_flow_keywords_missing_files(self):
        """Test graceful handling of missing GitLab Flow files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Don't create any GitLab Flow files - test missing file handling
            keywords = config.get_gitlab_flow_keywords(enabled=True, template_dir=temp_dir)

            # Should return fallback comments for missing files
            for keyword in keywords.values():
                assert "GitLab Flow file not found" in keyword

    def test_get_gitlab_flow_keywords_file_read_error(self):
        """Test graceful handling of file read errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            gitlab_flow_dir = Path(temp_dir) / "gitlab-flow"
            gitlab_flow_dir.mkdir()

            # Create a file but mock open to raise an error
            setup_file = gitlab_flow_dir / "gitlab-flow-setup.md"
            setup_file.write_text("test content")

            with patch("builtins.open", side_effect=PermissionError("Access denied")):
                keywords = config.get_gitlab_flow_keywords(enabled=True, template_dir=temp_dir)

                # Should return error fallback
                assert "GitLab Flow file error" in keywords["{GITLAB_FLOW_SETUP}"]

    def test_gitlab_flow_config_structure(self):
        """Test GitLab Flow configuration structure follows expected pattern."""
        gitlab_config = config.GITLAB_FLOW_CONFIG

        # Check required structure elements
        assert "name" in gitlab_config
        assert "description" in gitlab_config
        assert "template_dir" in gitlab_config
        assert "template_files" in gitlab_config
        assert "keywords" in gitlab_config
        assert "platform_commands" in gitlab_config

        # Check platform commands exist for both platforms
        assert "windows" in gitlab_config["platform_commands"]
        assert "unix" in gitlab_config["platform_commands"]


@pytest.mark.unit
class TestGitLabFlowMarkdownLoading:
    """Test GitLab Flow markdown file loading functionality."""

    def test_load_gitlab_flow_file_success(self):
        """Test successful loading and processing of GitLab Flow markdown file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            gitlab_flow_dir = Path(temp_dir) / "gitlab-flow"
            gitlab_flow_dir.mkdir()

            # Create test markdown file with placeholders
            test_file = gitlab_flow_dir / "test-file.md"
            test_content = "Test content with {GIT_STATUS} and {COMMIT} placeholders"
            test_file.write_text(test_content)

            platform_commands = {"GIT_STATUS": "git status", "COMMIT": 'git add . ; git commit -m "{message}"'}

            result = load_gitlab_flow_file("test-file.md", temp_dir, platform_commands)

            # Check placeholders were replaced
            assert "git status" in result
            assert "git add . ; git commit" in result
            assert "{GIT_STATUS}" not in result
            assert "{COMMIT}" not in result

    def test_load_gitlab_flow_file_not_found(self):
        """Test graceful handling of missing GitLab Flow file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            platform_commands = {"GIT_STATUS": "git status"}

            result = load_gitlab_flow_file("missing-file.md", temp_dir, platform_commands)

            # Should return graceful fallback message
            assert "GitLab Flow file not found" in result
            assert "missing-file.md" in result

    def test_load_gitlab_flow_file_permission_error(self):
        """Test handling of file permission errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            gitlab_flow_dir = Path(temp_dir) / "gitlab-flow"
            gitlab_flow_dir.mkdir()

            # Create file
            test_file = gitlab_flow_dir / "test-file.md"
            test_file.write_text("test content")

            platform_commands = {}

            # Mock permission error
            with patch("builtins.open", side_effect=PermissionError("Access denied")):
                result = load_gitlab_flow_file("test-file.md", temp_dir, platform_commands)

                assert "Permission denied reading GitLab Flow file" in result
                assert "test-file.md" in result


@pytest.mark.unit
class TestGitLabFlowTemplateCustomization:
    """Test GitLab Flow integration with template customization."""

    def test_customize_template_content_gitlab_flow_enabled(self):
        """Test customize_template_content with GitLab Flow enabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create GitLab Flow markdown files
            gitlab_flow_dir = Path(temp_dir) / "gitlab-flow"
            gitlab_flow_dir.mkdir()

            setup_file = gitlab_flow_dir / "gitlab-flow-setup.md"
            setup_file.write_text("## Setup\nRun {GIT_STATUS} to check status")

            # Template content with both AI tool and GitLab Flow keywords
            content = """# Template for {AI_ASSISTANT}

{GITLAB_FLOW_SETUP}

Use {AI_SHORTNAME} for development."""

            result = customize_template_content(
                content=content,
                ai_tool="github-copilot",
                gitlab_flow_enabled=True,
                platform="windows",
                template_dir=temp_dir,
            )

            # Check AI tool keywords were replaced
            assert "GitHub Copilot" in result
            assert "Copilot" in result
            assert "{AI_ASSISTANT}" not in result
            assert "{AI_SHORTNAME}" not in result

            # Check GitLab Flow keywords were replaced
            assert "git status" in result
            assert "{GITLAB_FLOW_SETUP}" not in result

    def test_customize_template_content_gitlab_flow_disabled(self):
        """Test customize_template_content with GitLab Flow disabled."""
        content = """# Template for {AI_ASSISTANT}

{GITLAB_FLOW_SETUP}

Use {AI_SHORTNAME} for development."""

        result = customize_template_content(content=content, ai_tool="github-copilot", gitlab_flow_enabled=False)

        # AI tool keywords should still be replaced
        assert "GitHub Copilot" in result
        assert "Copilot" in result

        # GitLab Flow keywords should be empty (removed)
        assert "{GITLAB_FLOW_SETUP}" not in result
        # The empty replacement should remove the keyword entirely

    def test_customize_template_content_backward_compatibility(self):
        """Test that GitLab Flow extension maintains backward compatibility."""
        content = """# Template for {AI_ASSISTANT}

Use {AI_SHORTNAME} for development.
Command: {AI_COMMAND}"""

        # Test without GitLab Flow parameters (backward compatibility)
        result = customize_template_content(content, "claude")

        # AI tool keywords should work as before
        assert "Claude" in result
        assert "Open Claude interface" in result
        assert "{AI_ASSISTANT}" not in result
        assert "{AI_SHORTNAME}" not in result
        assert "{AI_COMMAND}" not in result

    def test_customize_template_content_unknown_ai_tool(self):
        """Test customize_template_content with unknown AI tool."""
        content = """# Template for {AI_ASSISTANT}

{GITLAB_FLOW_SETUP}"""

        result = customize_template_content(content=content, ai_tool="unknown-tool", gitlab_flow_enabled=True)

        # Should return original content for unknown AI tool
        assert result == content
