"""Tests for template union/merge functionality."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.models import MergedTemplateSource, TemplateResolutionResult, TemplateSource, TemplateSourceType
from src.services.template_resolver import TemplateResolver


@pytest.mark.unit
@pytest.mark.services
class TestTemplateUnion:
    """Test suite for template union/merge functionality."""

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
    def partial_local_templates(self, temp_dir):
        """Create a .sdd_templates directory with only some template types."""
        templates_dir = temp_dir / ".sdd_templates"
        templates_dir.mkdir()

        # Create only chatmodes and instructions (missing prompts and commands)
        (templates_dir / "chatmodes").mkdir()
        (templates_dir / "chatmodes" / "test.chatmode.md").write_text("# Test chatmode")

        (templates_dir / "instructions").mkdir()
        (templates_dir / "instructions" / "test.instructions.md").write_text("# Test instructions")

        return templates_dir

    @pytest.fixture
    def complete_local_templates(self, temp_dir):
        """Create a complete .sdd_templates directory with all template types."""
        templates_dir = temp_dir / ".sdd_templates"
        templates_dir.mkdir()

        # Create all required template types
        for template_type in ["chatmodes", "instructions", "prompts", "commands"]:
            type_dir = templates_dir / template_type
            type_dir.mkdir()
            (type_dir / f"test.{template_type[:-1]}.md").write_text(f"# Test {template_type}")

        return templates_dir

    @pytest.fixture
    def downloaded_templates(self, temp_dir):
        """Create a downloaded templates directory with all template types."""
        download_dir = temp_dir / "downloaded"
        download_dir.mkdir()

        # Create all required template types
        for template_type in ["chatmodes", "instructions", "prompts", "commands"]:
            type_dir = download_dir / template_type
            type_dir.mkdir()
            (type_dir / f"downloaded.{template_type[:-1]}.md").write_text(f"# Downloaded {template_type}")

        return download_dir

    def test_get_available_template_types_complete(self, complete_local_templates, resolver):
        """Test getting available template types from complete directory."""
        available = resolver.get_available_template_files(complete_local_templates)
        assert set(available.keys()) == {"chatmodes", "instructions", "prompts", "commands"}

    def test_get_available_template_types_partial(self, partial_local_templates, resolver):
        """Test getting available template types from partial directory."""
        available = resolver.get_available_template_files(partial_local_templates)
        assert set(available.keys()) == {"chatmodes", "instructions"}

    def test_get_available_template_types_empty(self, temp_dir, resolver):
        """Test getting available template types from empty directory."""
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()
        available = resolver.get_available_template_files(empty_dir)
        assert available == {}

    def test_get_available_template_types_nonexistent(self, temp_dir, resolver):
        """Test getting available template types from nonexistent directory."""
        nonexistent = temp_dir / "nonexistent"
        available = resolver.get_available_template_files(nonexistent)
        assert available == {}

    def test_get_missing_template_types_partial(self, partial_local_templates, resolver):
        """Test getting missing template types from partial directory."""
        # Create reference directory with all template types
        reference_dir = partial_local_templates.parent / "reference"
        reference_dir.mkdir()
        for template_type in ["chatmodes", "instructions", "prompts", "commands"]:
            type_dir = reference_dir / template_type
            type_dir.mkdir()
            (type_dir / f"ref.{template_type[:-1]}.md").write_text(f"# Reference {template_type}")
        
        missing = resolver.get_missing_template_files(partial_local_templates, reference_dir)
        # All reference files are missing since local has different filenames
        expected_missing = {"chatmodes", "instructions", "prompts", "commands"}
        assert set(missing.keys()) == expected_missing

    def test_get_missing_template_types_complete(self, complete_local_templates, resolver):
        """Test getting missing template types from complete directory."""
        # Create reference directory with same template types
        reference_dir = complete_local_templates.parent / "reference"
        reference_dir.mkdir()
        for template_type in ["chatmodes", "instructions", "prompts", "commands"]:
            type_dir = reference_dir / template_type
            type_dir.mkdir()
            (type_dir / f"ref.{template_type[:-1]}.md").write_text(f"# Reference {template_type}")
        
        missing = resolver.get_missing_template_files(complete_local_templates, reference_dir)
        # All reference files are missing since local has different filenames  
        expected_missing = {"chatmodes", "instructions", "prompts", "commands"}
        assert set(missing.keys()) == expected_missing

    def test_get_missing_template_types_empty(self, temp_dir, resolver):
        """Test getting missing template types from empty directory."""
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()
        # Create reference directory with all template types
        reference_dir = temp_dir / "reference"
        reference_dir.mkdir()
        for template_type in ["chatmodes", "instructions", "prompts", "commands"]:
            type_dir = reference_dir / template_type
            type_dir.mkdir()
            (type_dir / f"ref.{template_type[:-1]}.md").write_text(f"# Reference {template_type}")
        
        missing = resolver.get_missing_template_files(empty_dir, reference_dir)
        assert set(missing.keys()) == {"chatmodes", "instructions", "prompts", "commands"}

    def test_resolve_complete_local_templates(self, complete_local_templates, resolver):
        """Test resolution with complete local templates - should use merged source."""
        with patch.object(resolver, "get_local_templates_path", return_value=complete_local_templates):
            result = resolver.resolve_templates_with_transparency()

            assert result.success is True
            assert result.source is not None
            assert result.source.source_type == TemplateSourceType.MERGED
            assert isinstance(result.source, MergedTemplateSource)
            assert result.fallback_attempted is True

    def test_resolve_partial_local_templates_online_success(
        self, partial_local_templates, downloaded_templates, resolver
    ):
        """Test resolution with partial local templates and successful download."""
        with patch.object(resolver, "get_local_templates_path", return_value=partial_local_templates), patch.object(
            resolver, "_download_github_templates", return_value=downloaded_templates
        ):
            result = resolver.resolve_templates_with_transparency()

            assert result.success is True
            assert result.source is not None
            assert isinstance(result.source, MergedTemplateSource)
            assert result.source.source_type == TemplateSourceType.MERGED
            assert result.source.local_path == partial_local_templates
            assert result.source.downloaded_path == downloaded_templates
            assert set(result.source.local_files.keys()) == {"chatmodes", "instructions"}
            assert "prompts" in result.source.downloaded_files or "commands" in result.source.downloaded_files
            assert result.fallback_attempted is True

    def test_resolve_partial_local_templates_offline(self, partial_local_templates, resolver):
        """Test resolution with partial local templates in offline mode."""
        resolver.offline = True

        with patch.object(resolver, "get_local_templates_path", return_value=partial_local_templates):
            result = resolver.resolve_templates_with_transparency()

            assert result.success is True  # Updated: offline mode now succeeds with available templates
            assert result.source is not None
            assert result.source.source_type == TemplateSourceType.LOCAL
            assert result.source.path == partial_local_templates

    def test_resolve_partial_local_templates_download_failure(self, partial_local_templates, resolver):
        """Test resolution with partial local templates when download fails."""
        with patch.object(resolver, "get_local_templates_path", return_value=partial_local_templates), patch.object(
            resolver, "_download_github_templates", side_effect=Exception("Network error")
        ):
            result = resolver.resolve_templates_with_transparency()

            assert result.success is True  # Updated: fallback to local succeeds
            assert result.source is not None
            assert result.source.source_type == TemplateSourceType.LOCAL
            assert result.source.path == partial_local_templates
            assert "merge error" in result.message

    def test_resolve_partial_local_incomplete_download(self, partial_local_templates, temp_dir, resolver):
        """Test resolution when downloaded templates are also incomplete."""
        # Create downloaded templates missing one type
        incomplete_download = temp_dir / "incomplete"
        incomplete_download.mkdir()
        (incomplete_download / "prompts").mkdir()
        (incomplete_download / "prompts" / "test.prompt.md").write_text("# Test prompt")
        # Missing commands directory

        with patch.object(resolver, "get_local_templates_path", return_value=partial_local_templates), patch.object(
            resolver, "_download_github_templates", return_value=incomplete_download
        ):
            result = resolver.resolve_templates_with_transparency()

            assert result.success is True
            assert isinstance(result.source, MergedTemplateSource)
            assert set(result.source.local_files.keys()) == {"chatmodes", "instructions"}
            assert set(result.source.downloaded_files.keys()) == {"prompts"}  # Only prompts found in download

    def test_merged_template_source_str_representation(self):
        """Test string representation of MergedTemplateSource."""
        source = MergedTemplateSource(
            local_path=Path("/local"),
            downloaded_path=Path("/downloaded"),
            local_files={"chatmodes": {"test.md"}, "instructions": {"test.md"}},
            downloaded_files={"prompts": {"test.md"}, "commands": {"test.md"}},
        )

        str_repr = str(source)
        assert "local" in str_repr.lower()
        assert "downloaded" in str_repr.lower()

    def test_merged_template_source_empty_sets(self):
        """Test MergedTemplateSource with empty type sets."""
        source = MergedTemplateSource(
            local_path=None, 
            downloaded_path=Path("/downloaded"), 
            local_files={}, 
            downloaded_files={"prompts": {"test.md"}}
        )

        str_repr = str(source)
        assert "downloaded" in str_repr.lower()

    def test_template_resolution_result_is_merged_property(self):
        """Test is_merged property on TemplateResolutionResult."""
        merged_source = MergedTemplateSource(
            local_path=Path("/local"),
            downloaded_path=Path("/downloaded"),
            local_files={"chatmodes": {"test.md"}},
            downloaded_files={"prompts": {"test.md"}},
        )

        result = TemplateResolutionResult(source=merged_source, success=True, message="Merged successfully")

        assert result.is_merged is True
        assert result.is_local is False
        assert result.is_bundled is False
        assert result.is_github is False

    def test_template_resolution_result_regular_source_properties(self):
        """Test property behavior with regular TemplateSource."""
        source = TemplateSource(path=Path("/local"), source_type=TemplateSourceType.LOCAL)

        result = TemplateResolutionResult(source=source, success=True, message="Local templates")

        assert result.is_merged is False
        assert result.is_local is True
        assert result.is_bundled is False
        assert result.is_github is False
