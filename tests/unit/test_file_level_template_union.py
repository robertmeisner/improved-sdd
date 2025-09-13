"""Tests for file-level template union/merge functionality."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.core.models import MergedTemplateSource, TemplateResolutionResult, TemplateSource, TemplateSourceType
from src.services.template_resolver import TemplateResolver


@pytest.mark.unit
@pytest.mark.services
class TestFileLevelTemplateUnion:
    """Test suite for file-level template union/merge functionality."""

    @pytest.fixture
    def resolver(self, temp_dir):
        """Create a TemplateResolver instance for testing."""
        return TemplateResolver(project_path=temp_dir)

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def local_templates_mixed_files(self, temp_dir):
        """Create .sdd_templates with some files in different categories."""
        templates_dir = temp_dir / ".sdd_templates"
        templates_dir.mkdir()

        # Create prompts with only one custom file
        prompts_dir = templates_dir / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "sddCommitWorkflow.prompt.md").write_text("# Custom commit workflow")

        # Create chatmodes with one custom file
        chatmodes_dir = templates_dir / "chatmodes"
        chatmodes_dir.mkdir()
        (chatmodes_dir / "customMode.chatmode.md").write_text("# Custom chat mode")

        # Instructions directory exists but is empty
        instructions_dir = templates_dir / "instructions"
        instructions_dir.mkdir()

        # No commands directory at all

        return templates_dir

    @pytest.fixture
    def downloaded_templates_complete(self, temp_dir):
        """Create a complete downloaded templates set."""
        download_dir = temp_dir / "downloaded"
        download_dir.mkdir()

        # Create complete template sets
        prompts_dir = download_dir / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "sddCommitWorkflow.prompt.md").write_text("# Downloaded commit workflow")  # Same file as local
        (prompts_dir / "sddTaskExecution.prompt.md").write_text("# Downloaded task execution")
        (prompts_dir / "sddProjectAnalysis.prompt.md").write_text("# Downloaded project analysis")

        chatmodes_dir = download_dir / "chatmodes"
        chatmodes_dir.mkdir()
        (chatmodes_dir / "sddSpecDriven.chatmode.md").write_text("# Downloaded spec driven")
        (chatmodes_dir / "sddTesting.chatmode.md").write_text("# Downloaded testing")

        instructions_dir = download_dir / "instructions"
        instructions_dir.mkdir()
        (instructions_dir / "sddPythonCliDev.instructions.md").write_text("# Downloaded python cli")

        commands_dir = download_dir / "commands"
        commands_dir.mkdir()
        (commands_dir / "basicCommand.command.md").write_text("# Downloaded basic command")

        return download_dir

    def test_get_available_template_files(self, resolver, local_templates_mixed_files):
        """Test getting available template files organized by type."""
        available_files = resolver.get_available_template_files(local_templates_mixed_files)

        expected = {
            "prompts": {"sddCommitWorkflow.prompt.md"},
            "chatmodes": {"customMode.chatmode.md"}
            # instructions directory exists but is empty, so not included
            # commands directory doesn't exist, so not included
        }

        assert available_files == expected

    def test_get_available_template_files_empty_dirs_ignored(self, resolver, temp_dir):
        """Test that empty directories are ignored when getting available files."""
        templates_dir = temp_dir / "templates"
        templates_dir.mkdir()

        # Create empty directories
        (templates_dir / "prompts").mkdir()
        (templates_dir / "chatmodes").mkdir()

        # Create one directory with content
        instructions_dir = templates_dir / "instructions"
        instructions_dir.mkdir()
        (instructions_dir / "test.instructions.md").write_text("# Test")

        available_files = resolver.get_available_template_files(templates_dir)

        # Only instructions should be included
        assert available_files == {"instructions": {"test.instructions.md"}}

    def test_merged_template_source_file_level_operations(
        self, local_templates_mixed_files, downloaded_templates_complete
    ):
        """Test MergedTemplateSource operations at file level."""
        local_files = {"prompts": {"sddCommitWorkflow.prompt.md"}, "chatmodes": {"customMode.chatmode.md"}}

        downloaded_files = {
            "prompts": {"sddCommitWorkflow.prompt.md", "sddTaskExecution.prompt.md", "sddProjectAnalysis.prompt.md"},
            "chatmodes": {"sddSpecDriven.chatmode.md", "sddTesting.chatmode.md"},
            "instructions": {"sddPythonCliDev.instructions.md"},
            "commands": {"basicCommand.command.md"},
        }

        merged_source = MergedTemplateSource(
            local_path=local_templates_mixed_files,
            downloaded_path=downloaded_templates_complete,
            local_files=local_files,
            downloaded_files=downloaded_files,
        )

        # Test get_file_source - local files take priority
        commit_workflow_source = merged_source.get_file_source("prompts", "sddCommitWorkflow.prompt.md")
        assert commit_workflow_source == local_templates_mixed_files / "prompts" / "sddCommitWorkflow.prompt.md"

        # Test get_file_source - downloaded file when not available locally
        task_execution_source = merged_source.get_file_source("prompts", "sddTaskExecution.prompt.md")
        assert task_execution_source == downloaded_templates_complete / "prompts" / "sddTaskExecution.prompt.md"

        # Test get_file_source - file from downloaded-only category
        instruction_source = merged_source.get_file_source("instructions", "sddPythonCliDev.instructions.md")
        assert instruction_source == downloaded_templates_complete / "instructions" / "sddPythonCliDev.instructions.md"

        # Test get_all_available_files - should combine but prioritize local
        all_files = merged_source.get_all_available_files()
        expected_all_files = {
            "prompts": {
                "sddCommitWorkflow.prompt.md",  # From local (priority)
                "sddTaskExecution.prompt.md",  # From downloaded
                "sddProjectAnalysis.prompt.md",  # From downloaded
            },
            "chatmodes": {
                "customMode.chatmode.md",  # From local
                "sddSpecDriven.chatmode.md",  # From downloaded
                "sddTesting.chatmode.md",  # From downloaded
            },
            "instructions": {"sddPythonCliDev.instructions.md"},  # From downloaded only
            "commands": {"basicCommand.command.md"},  # From downloaded only
        }

        assert all_files == expected_all_files

    def test_file_level_merge_resolution_offline(self, resolver, local_templates_mixed_files):
        """Test file-level resolution in offline mode with partial local templates."""
        resolver.offline = True

        with patch.object(resolver, "get_local_templates_path", return_value=local_templates_mixed_files):
            result = resolver.resolve_templates_with_transparency()

            assert result.success is True
            assert result.source is not None
            assert result.source.source_type == TemplateSourceType.LOCAL
            assert "2 local template files" in result.message

    def test_file_level_merge_resolution_online_success(
        self, resolver, local_templates_mixed_files, downloaded_templates_complete
    ):
        """Test file-level resolution online with successful merge."""
        with patch.object(resolver, "get_local_templates_path", return_value=local_templates_mixed_files), patch.object(
            resolver, "_download_github_templates", return_value=downloaded_templates_complete
        ):
            result = resolver.resolve_templates_with_transparency()

            assert result.success is True
            assert result.source is not None
            assert isinstance(result.source, MergedTemplateSource)
            assert result.source.source_type == TemplateSourceType.MERGED

            # Verify file counts in the result
            assert "2 local files" in result.message
            assert "7 downloaded files" in result.message
            assert "8 unique files total" in result.message  # 2 local + 6 unique downloaded (1 overlap)

    def test_merged_template_source_string_representation(self):
        """Test string representation of file-level MergedTemplateSource."""
        local_files = {"prompts": {"file1.md", "file2.md"}, "chatmodes": {"mode1.md"}}

        downloaded_files = {"prompts": {"file3.md"}, "instructions": {"inst1.md", "inst2.md"}, "commands": {"cmd1.md"}}

        merged_source = MergedTemplateSource(
            local_path=Path("/local"),
            downloaded_path=Path("/downloaded"),
            local_files=local_files,
            downloaded_files=downloaded_files,
        )

        str_repr = str(merged_source)
        assert "3 local files" in str_repr
        assert "4 downloaded files" in str_repr
        # Total unique files: 3 local + 4 downloaded = 7 (no overlap in this test)
        assert "7 total unique files" in str_repr

    def test_file_level_priority_local_over_downloaded(self):
        """Test that local files take priority over downloaded files with same name."""
        local_files = {"prompts": {"sddCommitWorkflow.prompt.md"}}

        downloaded_files = {"prompts": {"sddCommitWorkflow.prompt.md", "other.prompt.md"}}  # Same file in both

        merged_source = MergedTemplateSource(
            local_path=Path("/local"),
            downloaded_path=Path("/downloaded"),
            local_files=local_files,
            downloaded_files=downloaded_files,
        )

        # Should get local version
        source_path = merged_source.get_file_source("prompts", "sddCommitWorkflow.prompt.md")
        assert source_path == Path("/local/prompts/sddCommitWorkflow.prompt.md")

        # Should get downloaded version for file not in local
        source_path = merged_source.get_file_source("prompts", "other.prompt.md")
        assert source_path == Path("/downloaded/prompts/other.prompt.md")

        # All available files should show only unique files (local takes priority)
        all_files = merged_source.get_all_available_files()
        assert all_files == {"prompts": {"sddCommitWorkflow.prompt.md", "other.prompt.md"}}

    def test_get_missing_template_files(self, resolver, local_templates_mixed_files, downloaded_templates_complete):
        """Test getting missing template files compared to reference set."""
        missing_files = resolver.get_missing_template_files(local_templates_mixed_files, downloaded_templates_complete)

        expected_missing = {
            "prompts": {
                "sddTaskExecution.prompt.md",
                "sddProjectAnalysis.prompt.md",
            },  # These are in downloaded but not local
            "chatmodes": {
                "sddSpecDriven.chatmode.md",
                "sddTesting.chatmode.md",
            },  # These are in downloaded but not local
            "instructions": {"sddPythonCliDev.instructions.md"},  # Entire category missing locally
            "commands": {"basicCommand.command.md"},  # Entire category missing locally
        }

        assert missing_files == expected_missing

    def test_empty_local_templates_directory(self, resolver, temp_dir):
        """Test behavior when .sdd_templates exists but is completely empty."""
        empty_templates = temp_dir / ".sdd_templates"
        empty_templates.mkdir()

        available_files = resolver.get_available_template_files(empty_templates)
        assert available_files == {}

        # Should fall back to normal resolution when local templates are empty
        with (
            patch.object(resolver, "get_local_templates_path", return_value=empty_templates),
            patch.object(resolver, "get_bundled_templates_path", return_value=None),
            patch.object(resolver, "_attempt_github_download") as mock_download,
        ):
            mock_download.return_value = TemplateResolutionResult(
                source=None, success=False, message="No GitHub download", fallback_attempted=True
            )

            result = resolver.resolve_templates_with_transparency()

            # Should have attempted GitHub download since local is empty
            mock_download.assert_called_once()
