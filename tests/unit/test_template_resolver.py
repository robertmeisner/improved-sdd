"""Tests for the TemplateResolver service module."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.core.models import TemplateResolutionResult, TemplateSourceType
from src.services.template_resolver import TemplateResolver


@pytest.mark.unit
@pytest.mark.services
class TestTemplateResolver:
    """Test suite for the TemplateResolver service."""

    @pytest.fixture
    def resolver(self, temp_dir):
        """Create a TemplateResolver instance for testing."""
        return TemplateResolver(project_path=temp_dir)

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_init_default_paths(self, temp_dir):
        """Test TemplateResolver initialization with default paths."""
        resolver = TemplateResolver(project_path=temp_dir)
        assert resolver is not None
        assert resolver.project_path == temp_dir

    def test_has_local_templates_true(self, temp_dir):
        """Test has_local_templates returns True when templates exist."""
        resolver = TemplateResolver(project_path=temp_dir)
        templates_dir = temp_dir / "sdd_templates"
        templates_dir.mkdir()

        with patch.object(resolver, "get_local_templates_path", return_value=templates_dir):
            assert resolver.has_local_templates() is True

    def test_has_local_templates_false(self, temp_dir):
        """Test has_local_templates returns False when no templates."""
        resolver = TemplateResolver(project_path=temp_dir)

        with patch.object(resolver, "get_local_templates_path", return_value=None):
            assert resolver.has_local_templates() is False

    def test_has_bundled_templates_true(self, temp_dir):
        """Test has_bundled_templates returns True when templates exist."""
        resolver = TemplateResolver(project_path=temp_dir)
        templates_dir = temp_dir / "sdd_templates"
        templates_dir.mkdir()

        with patch.object(resolver, "get_bundled_templates_path", return_value=templates_dir):
            assert resolver.has_bundled_templates() is True

    def test_has_bundled_templates_false(self, temp_dir):
        """Test has_bundled_templates returns False when no templates."""
        resolver = TemplateResolver(project_path=temp_dir)

        with patch.object(resolver, "get_bundled_templates_path", return_value=None):
            assert resolver.has_bundled_templates() is False

    def test_resolve_templates_with_transparency_local_success(self, temp_dir):
        """Test resolve_templates_with_transparency with local templates."""
        resolver = TemplateResolver(project_path=temp_dir)
        templates_dir = temp_dir / "sdd_templates"
        templates_dir.mkdir()

        # Create required subdirectories
        (templates_dir / "chatmodes").mkdir()
        (templates_dir / "instructions").mkdir()
        (templates_dir / "prompts").mkdir()

        with patch.object(resolver, "get_local_templates_path", return_value=templates_dir):
            result = resolver.resolve_templates_with_transparency()
            assert result.success is True
            assert result.source is not None
            assert result.source.source_type == TemplateSourceType.LOCAL

    def test_resolve_templates_with_transparency_bundled_fallback(self, temp_dir):
        """Test resolve_templates_with_transparency falls back to bundled."""
        resolver = TemplateResolver(project_path=temp_dir)
        bundled_dir = temp_dir / "sdd_templates"
        bundled_dir.mkdir()

        # Create required subdirectories
        (bundled_dir / "chatmodes").mkdir()
        (bundled_dir / "instructions").mkdir()
        (bundled_dir / "prompts").mkdir()

        with patch.object(resolver, "get_local_templates_path", return_value=None), patch.object(
            resolver, "get_bundled_templates_path", return_value=bundled_dir
        ):
            result = resolver.resolve_templates_with_transparency()
            assert result.success is True
            assert result.source is not None
            assert result.source.source_type == TemplateSourceType.BUNDLED

    def test_resolve_templates_with_transparency_all_fail(self, temp_dir):
        """Test resolve_templates_with_transparency when all sources fail."""
        resolver = TemplateResolver(project_path=temp_dir)

        with patch.object(resolver, "get_local_templates_path", return_value=None), patch.object(
            resolver, "get_bundled_templates_path", return_value=None
        ), patch.object(resolver, "_attempt_github_download") as mock_download:
            mock_download.return_value = TemplateResolutionResult(
                source=None, success=False, message="All sources failed", fallback_attempted=True
            )

            result = resolver.resolve_templates_with_transparency()
            assert result.success is False
            assert result.source is None
            assert result.fallback_attempted is True
