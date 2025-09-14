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

        expected_keywords = ["{GITLAB_FLOW_SETUP}", "{GITLAB_FLOW_WORKFLOW}", "{GITLAB_FLOW_PR}"]

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

            workflow_file = gitlab_flow_dir / "gitlab-flow-workflow.md"
            workflow_file.write_text("Workflow: {COMMIT}")

            pr_file = gitlab_flow_dir / "gitlab-flow-pr.md"
            pr_file.write_text("PR: {PUSH_PR}")

            keywords = config.get_gitlab_flow_keywords(enabled=True, platform="windows", template_dir=temp_dir)

            # Check Windows-specific command syntax (semicolon)
            assert ";" in keywords["{GITLAB_FLOW_WORKFLOW}"]  # Windows uses semicolon
            assert "git status" in keywords["{GITLAB_FLOW_SETUP}"]

    def test_get_gitlab_flow_keywords_unix_platform(self):
        """Test get_gitlab_flow_keywords with Unix platform commands."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock GitLab Flow markdown files
            gitlab_flow_dir = Path(temp_dir) / "gitlab-flow"
            gitlab_flow_dir.mkdir()

            workflow_file = gitlab_flow_dir / "gitlab-flow-workflow.md"
            workflow_file.write_text("Workflow: {COMMIT}")

            keywords = config.get_gitlab_flow_keywords(enabled=True, platform="unix", template_dir=temp_dir)

            # Check Unix-specific command syntax (double ampersand)
            assert "&&" in keywords["{GITLAB_FLOW_WORKFLOW}"]  # Unix uses &&

    def test_get_gitlab_flow_keywords_missing_files(self):
        """Test graceful handling of missing GitLab Flow files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Don't create any GitLab Flow files - test missing file handling
            keywords = config.get_gitlab_flow_keywords(enabled=True, template_dir=temp_dir)

            # Should return enhanced fallback comments for missing files
            for keyword in keywords.values():
                assert "GitLab Flow Template Missing" in keyword
                assert "template not found" in keyword
                assert "Troubleshooting:" in keyword

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

                # Should return enhanced error fallback
                assert "GitLab Flow Template Error" in keywords["{GITLAB_FLOW_SETUP}"]
                assert "Error loading GitLab Flow template" in keywords["{GITLAB_FLOW_SETUP}"]
                assert "Troubleshooting:" in keywords["{GITLAB_FLOW_SETUP}"]

    def test_validate_gitlab_flow_templates_valid_directory(self):
        """Test template validation with valid directory and files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create GitLab Flow directory and files
            gitlab_flow_dir = Path(temp_dir) / "gitlab-flow"
            gitlab_flow_dir.mkdir()
            
            # Create all expected template files (based on actual mapping)
            (gitlab_flow_dir / "gitlab-flow-setup.md").write_text("Setup content")
            (gitlab_flow_dir / "gitlab-flow-workflow.md").write_text("Workflow content")  # Updated filename
            (gitlab_flow_dir / "gitlab-flow-pr.md").write_text("PR content")
            
            # Should pass validation
            result = config.validate_gitlab_flow_templates(temp_dir)
            assert result["valid"] is True
            assert len(result["existing_files"]) == 3
            assert len(result["missing_files"]) == 0

    def test_validate_gitlab_flow_templates_missing_directory(self):
        """Test template validation with missing gitlab-flow directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Don't create gitlab-flow directory
            result = config.validate_gitlab_flow_templates(temp_dir)
            
            assert result["valid"] is False
            assert len(result["missing_files"]) > 0
            assert any("gitlab-flow" in rec for rec in result["recommendations"])

    def test_validate_gitlab_flow_templates_missing_files(self):
        """Test template validation with missing template files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create GitLab Flow directory but not all files
            gitlab_flow_dir = Path(temp_dir) / "gitlab-flow"
            gitlab_flow_dir.mkdir()
            
            # Only create some files
            (gitlab_flow_dir / "gitlab-flow-setup.md").write_text("Setup content")
            # Missing: commit, pr files
            
            result = config.validate_gitlab_flow_templates(temp_dir)
            
            assert result["valid"] is False
            assert len(result["missing_files"]) == 2  # missing 2 files
            assert len(result["existing_files"]) == 1  # setup file exists
            
            # Check that missing files include the expected ones
            missing_filenames = [f["filename"] for f in result["missing_files"]]
            assert "gitlab-flow-workflow.md" in missing_filenames  # Updated to current file structure
            assert "gitlab-flow-pr.md" in missing_filenames

    def test_validate_gitlab_flow_templates_empty_files(self):
        """Test template validation with empty template files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create GitLab Flow directory and empty files
            gitlab_flow_dir = Path(temp_dir) / "gitlab-flow"
            gitlab_flow_dir.mkdir()
            
            # Create all files but make some empty
            (gitlab_flow_dir / "gitlab-flow-setup.md").write_text("")
            (gitlab_flow_dir / "gitlab-flow-workflow.md").write_text("")  # Updated filename
            (gitlab_flow_dir / "gitlab-flow-pr.md").write_text("PR content")  # One valid
            
            result = config.validate_gitlab_flow_templates(temp_dir)
            
            # All files exist, so validation should pass structurally
            # The function checks existence, not content
            assert result["valid"] is True
            assert len(result["existing_files"]) == 3
            assert len(result["missing_files"]) == 0
            
            # Check file sizes - empty files should have 0 bytes
            file_sizes = {f["filename"]: f["size_bytes"] for f in result["existing_files"]}
            assert file_sizes["gitlab-flow-setup.md"] == 0
            assert file_sizes["gitlab-flow-commit.md"] == 0
            assert file_sizes["gitlab-flow-pr.md"] > 0  # Has content

    def test_validate_gitlab_flow_templates_permission_error(self):
        """Test template validation with permission errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create GitLab Flow directory
            gitlab_flow_dir = Path(temp_dir) / "gitlab-flow"
            gitlab_flow_dir.mkdir()
            (gitlab_flow_dir / "gitlab-flow-setup.md").write_text("Content")
            
            # The function currently doesn't handle permission errors
            # This test verifies the current behavior - error propagation
            with patch("pathlib.Path.exists", side_effect=PermissionError("Access denied")):
                with pytest.raises(PermissionError):
                    config.validate_gitlab_flow_templates(temp_dir)

    def test_gitlab_flow_template_caching(self):
        """Test GitLab Flow template caching mechanism."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create GitLab Flow directory and files
            gitlab_flow_dir = Path(temp_dir) / "gitlab-flow"
            gitlab_flow_dir.mkdir()
            (gitlab_flow_dir / "gitlab-flow-setup.md").write_text("Setup content")
            (gitlab_flow_dir / "gitlab-flow-commit.md").write_text("Commit content")
            (gitlab_flow_dir / "gitlab-flow-pr.md").write_text("PR content")
            
            # Clear any existing cache
            config._gitlab_flow_cache = {
                "last_template_dir": "",
                "cached_content": {},
                "cache_valid": False
            }
            
            # First call should cache the content
            keywords1 = config.get_gitlab_flow_keywords(enabled=True, template_dir=temp_dir)
            
            # Verify cache is populated
            assert config._gitlab_flow_cache["cache_valid"] is True
            assert config._gitlab_flow_cache["last_template_dir"] == temp_dir
            # Cache stores content by platform-specific key
            assert len(config._gitlab_flow_cache["cached_content"]) == 1
            
            # Second call should use cache (modify file to test cache)
            (gitlab_flow_dir / "gitlab-flow-setup.md").write_text("Modified content")
            keywords2 = config.get_gitlab_flow_keywords(enabled=True, template_dir=temp_dir)
            
            # Should be same content from cache (not modified file)
            assert keywords1["{GITLAB_FLOW_SETUP}"] == keywords2["{GITLAB_FLOW_SETUP}"]
            assert "Setup content" in keywords2["{GITLAB_FLOW_SETUP}"]
            assert "Modified content" not in keywords2["{GITLAB_FLOW_SETUP}"]

    def test_gitlab_flow_cache_invalidation(self):
        """Test GitLab Flow cache invalidation when template directory changes."""
        with tempfile.TemporaryDirectory() as temp_dir1, tempfile.TemporaryDirectory() as temp_dir2:
            # Setup first directory
            gitlab_flow_dir1 = Path(temp_dir1) / "gitlab-flow"
            gitlab_flow_dir1.mkdir()
            (gitlab_flow_dir1 / "gitlab-flow-setup.md").write_text("Content 1")
            (gitlab_flow_dir1 / "gitlab-flow-commit.md").write_text("Content 1")
            (gitlab_flow_dir1 / "gitlab-flow-pr.md").write_text("Content 1")
            
            # Setup second directory with different content
            gitlab_flow_dir2 = Path(temp_dir2) / "gitlab-flow"
            gitlab_flow_dir2.mkdir()
            (gitlab_flow_dir2 / "gitlab-flow-setup.md").write_text("Content 2")
            (gitlab_flow_dir2 / "gitlab-flow-commit.md").write_text("Content 2")
            (gitlab_flow_dir2 / "gitlab-flow-pr.md").write_text("Content 2")
            
            # Get keywords from first directory
            keywords1 = config.get_gitlab_flow_keywords(enabled=True, template_dir=temp_dir1)
            assert "Content 1" in keywords1["{GITLAB_FLOW_SETUP}"]
            
            # Get keywords from second directory (should invalidate cache)
            keywords2 = config.get_gitlab_flow_keywords(enabled=True, template_dir=temp_dir2)
            assert "Content 2" in keywords2["{GITLAB_FLOW_SETUP}"]
            assert "Content 1" not in keywords2["{GITLAB_FLOW_SETUP}"]

    def test_gitlab_flow_config_structure(self):
        """Test GitLab Flow configuration structure follows expected pattern."""
        gitlab_config = config.GITLAB_FLOW_CONFIG

        # Check required structure elements
        assert "name" in gitlab_config
        assert "description" in gitlab_config
        assert "template_dir" in gitlab_config
        assert "template_files" in gitlab_config
        assert "template_file_mapping" in gitlab_config  # Updated to use actual config structure
        assert "platform_keywords" in gitlab_config

        # Check platform commands exist for both platforms
        assert "windows" in gitlab_config["platform_keywords"]
        assert "unix" in gitlab_config["platform_keywords"]

    def test_gitlab_flow_default_config(self):
        """Test GitLab Flow default configuration."""
        gitlab_config = config._gitlab_flow_config
        
        # Test default state is enabled (aligned with CLI default)
        assert gitlab_config["enabled"] == True

    def test_platform_detection_helper_windows(self):
        """Test platform detection helper for Windows commands."""
        commands = config._detect_platform_keywords("windows")
        
        # Verify Windows-specific command syntax
        assert "git add . ;" in commands["{COMMIT}"]
        assert "git push -u origin feature/spec-{feature-name} ;" in commands["{PUSH_PR}"]
        
    def test_platform_detection_helper_unix(self):
        """Test platform detection helper for Unix/Linux commands."""
        commands = config._detect_platform_keywords("unix")
        
        # Verify Unix-specific command syntax (&&)
        assert "git add . &&" in commands["{COMMIT}"]
        assert "git push -u origin feature/spec-{feature-name} &&" in commands["{PUSH_PR}"]
        
    def test_gitlab_flow_config_export(self):
        """Test GitLab Flow config is properly exported."""
        from src.core.config import GITLAB_FLOW_CONFIG
        
        # Verify export exists and has expected structure
        assert GITLAB_FLOW_CONFIG is not None
        assert "enabled" in GITLAB_FLOW_CONFIG
        assert "template_dir" in GITLAB_FLOW_CONFIG
        assert "template_file_mapping" in GITLAB_FLOW_CONFIG


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

            platform_keywords = {"{GIT_STATUS}": "git status", "{COMMIT}": 'git add . ; git commit -m "{message}"'}
            
            result = load_gitlab_flow_file("test-file.md", temp_dir, platform_keywords)            # Check placeholders were replaced
            assert "git status" in result
            assert "git add . ; git commit" in result
            assert "{GIT_STATUS}" not in result
            assert "{COMMIT}" not in result

    def test_load_gitlab_flow_file_not_found(self):
        """Test graceful handling of missing GitLab Flow file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            platform_keywords = {"GIT_STATUS": "git status"}
            
            result = load_gitlab_flow_file("missing-file.md", temp_dir, platform_keywords)            # Should return graceful fallback message
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

            platform_keywords = {}

            # Mock permission error
            with patch("builtins.open", side_effect=PermissionError("Access denied")):
                result = load_gitlab_flow_file("test-file.md", temp_dir, platform_keywords)

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
