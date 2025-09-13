"""Tests for template installation with union/merge functionality."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.core.models import MergedTemplateSource, TemplateResolutionResult, TemplateSource, TemplateSourceType
from src.services import FileTracker
from src.utils import create_project_structure


@pytest.mark.unit
@pytest.mark.services
class TestTemplateInstallationUnion:
    """Test suite for template installation with union functionality."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def file_tracker(self):
        """Create a FileTracker instance for testing."""
        return FileTracker()

    @pytest.fixture
    def merged_template_setup(self, temp_dir):
        """Create merged template scenario for testing."""
        # Create local templates with some types
        local_dir = temp_dir / "local_templates"
        local_dir.mkdir()

        chatmodes_dir = local_dir / "chatmodes"
        chatmodes_dir.mkdir()
        (chatmodes_dir / "local.chatmode.md").write_text("# Local chatmode template")

        instructions_dir = local_dir / "instructions"
        instructions_dir.mkdir()
        (instructions_dir / "sddPythonCliDev.instructions.md").write_text("# Local instructions template")

        # Create downloaded templates with missing types
        downloaded_dir = temp_dir / "downloaded_templates"
        downloaded_dir.mkdir()

        prompts_dir = downloaded_dir / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "downloaded.prompt.md").write_text("# Downloaded prompt template")

        commands_dir = downloaded_dir / "commands"
        commands_dir.mkdir()
        (commands_dir / "downloaded.command.md").write_text("# Downloaded command template")

        # Create merged source
        merged_source = MergedTemplateSource(
            local_path=local_dir,
            downloaded_path=downloaded_dir,
            local_types={"chatmodes", "instructions"},
            downloaded_types={"prompts", "commands"},
        )

        return {"local_dir": local_dir, "downloaded_dir": downloaded_dir, "merged_source": merged_source}

    def test_install_templates_with_merged_source(self, temp_dir, file_tracker, merged_template_setup):
        """Test template installation with merged source."""
        project_path = temp_dir / "project"
        project_path.mkdir()

        merged_source = merged_template_setup["merged_source"]
        resolution_result = TemplateResolutionResult(
            source=merged_source, success=True, message="Merged templates successfully"
        )

        # Mock the TemplateResolver to return our merged result
        with patch("src.utils.TemplateResolver") as mock_resolver_class:
            mock_resolver = MagicMock()
            mock_resolver.resolve_templates_with_transparency.return_value = resolution_result
            mock_resolver_class.return_value = mock_resolver

            # Install templates
            create_project_structure(
                project_path=project_path,
                app_type="python-cli",
                ai_tools=["github-copilot"],
                file_tracker=file_tracker,
                force=True,
            )

            # Verify templates were installed from correct sources
            github_dir = project_path / ".github"
            assert github_dir.exists()

            # Check chatmodes (should come from local)
            chatmodes_file = github_dir / "chatmodes" / "local.chatmode.md"
            assert chatmodes_file.exists()
            assert "Local chatmode template" in chatmodes_file.read_text()

            # Check instructions (should come from local)
            instructions_file = github_dir / "instructions" / "sddPythonCliDev.instructions.md"
            assert instructions_file.exists()
            assert "Local instructions template" in instructions_file.read_text()

            # Check prompts (should come from downloaded)
            prompts_file = github_dir / "prompts" / "downloaded.prompt.md"
            assert prompts_file.exists()
            assert "Downloaded prompt template" in prompts_file.read_text()

            # Check commands (should come from downloaded)
            commands_file = github_dir / "commands" / "downloaded.command.md"
            assert commands_file.exists()
            assert "Downloaded command template" in commands_file.read_text()

    def test_install_templates_with_regular_source(self, temp_dir, file_tracker):
        """Test template installation with regular (non-merged) source."""
        project_path = temp_dir / "project"
        project_path.mkdir()

        # Create regular template source
        templates_dir = temp_dir / "templates"
        templates_dir.mkdir()

        chatmodes_dir = templates_dir / "chatmodes"
        chatmodes_dir.mkdir()
        (chatmodes_dir / "regular.chatmode.md").write_text("# Regular chatmode template")

        source = TemplateSource(path=templates_dir, source_type=TemplateSourceType.LOCAL)

        resolution_result = TemplateResolutionResult(source=source, success=True, message="Local templates found")

        # Mock the TemplateResolver to return our regular result
        with patch("src.utils.TemplateResolver") as mock_resolver_class:
            mock_resolver = MagicMock()
            mock_resolver.resolve_templates_with_transparency.return_value = resolution_result
            mock_resolver_class.return_value = mock_resolver

            # Install templates
            create_project_structure(
                project_path=project_path,
                app_type="python-cli",
                ai_tools=["github-copilot"],
                file_tracker=file_tracker,
                force=True,
            )

            # Verify templates were installed
            chatmodes_file = project_path / ".github" / "chatmodes" / "regular.chatmode.md"
            assert chatmodes_file.exists()
            assert "Regular chatmode template" in chatmodes_file.read_text()

    def test_install_templates_merged_source_missing_type(self, temp_dir, file_tracker):
        """Test installation when merged source is missing a template type entirely."""
        project_path = temp_dir / "project"
        project_path.mkdir()

        # Create incomplete merged source (missing commands)
        local_dir = temp_dir / "local"
        local_dir.mkdir()

        downloaded_dir = temp_dir / "downloaded"
        downloaded_dir.mkdir()

        # Only create chatmodes locally
        chatmodes_dir = local_dir / "chatmodes"
        chatmodes_dir.mkdir()
        (chatmodes_dir / "test.chatmode.md").write_text("# Test chatmode")

        # Only create prompts in download
        prompts_dir = downloaded_dir / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "test.prompt.md").write_text("# Test prompt")

        merged_source = MergedTemplateSource(
            local_path=local_dir,
            downloaded_path=downloaded_dir,
            local_files={"chatmodes": {"test.chatmode.md"}},
            downloaded_files={"prompts": {"test.prompt.md"}},
        )

        resolution_result = TemplateResolutionResult(
            source=merged_source, success=True, message="Partial merged templates"
        )

        with patch("src.utils.TemplateResolver") as mock_resolver_class:
            mock_resolver = MagicMock()
            mock_resolver.resolve_templates_with_transparency.return_value = resolution_result
            mock_resolver_class.return_value = mock_resolver

            # Install templates - should handle missing types gracefully
            create_project_structure(
                project_path=project_path,
                app_type="python-cli",
                ai_tools=["github-copilot"],
                file_tracker=file_tracker,
                force=True,
            )

            # Verify available templates were installed
            assert (project_path / ".github" / "chatmodes" / "test.chatmode.md").exists()
            assert (project_path / ".github" / "prompts" / "test.prompt.md").exists()

            # Verify missing types don't break installation
            instructions_dir = project_path / ".github" / "instructions"
            commands_dir = project_path / ".github" / "commands"
            # These directories might exist but should be empty
            if instructions_dir.exists():
                assert not list(instructions_dir.glob("*.md"))
            if commands_dir.exists():
                assert not list(commands_dir.glob("*.md"))

    def test_merged_source_priority_local_over_downloaded(self, temp_dir, file_tracker):
        """Test that local templates take priority over downloaded ones for the same type."""
        project_path = temp_dir / "project"
        project_path.mkdir()

        # Create scenario where both local and downloaded have the same template type
        local_dir = temp_dir / "local"
        local_dir.mkdir()
        downloaded_dir = temp_dir / "downloaded"
        downloaded_dir.mkdir()

        # Both have chatmodes
        local_chatmodes = local_dir / "chatmodes"
        local_chatmodes.mkdir()
        (local_chatmodes / "test.chatmode.md").write_text("# LOCAL chatmode template")

        downloaded_chatmodes = downloaded_dir / "chatmodes"
        downloaded_chatmodes.mkdir()
        (downloaded_chatmodes / "test.chatmode.md").write_text("# DOWNLOADED chatmode template")

        merged_source = MergedTemplateSource(
            local_path=local_dir,
            downloaded_path=downloaded_dir,
            local_files={"chatmodes": {"test.chatmode.md"}},
            downloaded_files={"chatmodes": {"test.chatmode.md"}},  # Both have chatmodes
        )

        resolution_result = TemplateResolutionResult(
            source=merged_source, success=True, message="Merged with overlapping types"
        )

        with patch("src.utils.TemplateResolver") as mock_resolver_class:
            mock_resolver = MagicMock()
            mock_resolver.resolve_templates_with_transparency.return_value = resolution_result
            mock_resolver_class.return_value = mock_resolver

            create_project_structure(
                project_path=project_path,
                app_type="python-cli",
                ai_tools=["github-copilot"],
                file_tracker=file_tracker,
                force=True,
            )

            # Verify local template was used (has priority)
            installed_file = project_path / ".github" / "chatmodes" / "test.chatmode.md"
            assert installed_file.exists()
            content = installed_file.read_text()
            assert "LOCAL chatmode template" in content
            assert "DOWNLOADED" not in content
