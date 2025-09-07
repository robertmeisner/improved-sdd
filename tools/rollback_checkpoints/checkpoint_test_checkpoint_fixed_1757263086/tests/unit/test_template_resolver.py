"""Unit tests for TemplateResolver class."""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

# Import after path modification
from improved_sdd_cli import (  # noqa: E402
    CacheManager,
    GitHubAPIError,
    GitHubDownloader,
    NetworkError,
    TemplateResolutionResult,
    TemplateResolver,
    TemplateSource,
    TemplateSourceType,
    TimeoutError,
    ValidationError,
)


@pytest.mark.unit
@pytest.mark.templates
class TestTemplateResolver:
    """Test the TemplateResolver class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def mock_local_templates_dir(self, temp_dir):
        """Create a mock local .sdd_templates directory."""
        templates_dir = temp_dir / ".sdd_templates"
        templates_dir.mkdir()

        # Create template subdirectories
        github_dir = templates_dir / "github"
        github_dir.mkdir()

        # Create sample template files
        chatmodes_dir = github_dir / "chatmodes"
        chatmodes_dir.mkdir()
        (chatmodes_dir / "sample.chatmode.md").write_text("# Sample chatmode")

        instructions_dir = github_dir / "instructions"
        instructions_dir.mkdir()
        (instructions_dir / "sample.instructions.md").write_text("# Sample instructions")

        return templates_dir

    @pytest.fixture
    def mock_bundled_templates_dir(self, temp_dir):
        """Create a mock bundled .sdd_templates directory."""
        # Simulate CLI installation directory
        cli_dir = temp_dir / "cli_install"
        cli_dir.mkdir()
        templates_dir = cli_dir / ".sdd_templates"
        templates_dir.mkdir()

        # Create template subdirectories
        github_dir = templates_dir / "github"
        github_dir.mkdir()

        # Create sample template files
        chatmodes_dir = github_dir / "chatmodes"
        chatmodes_dir.mkdir()
        (chatmodes_dir / "bundled.chatmode.md").write_text("# Bundled chatmode")

        return templates_dir

    @pytest.fixture
    def resolver(self, temp_dir):
        """Create a TemplateResolver instance for testing."""
        return TemplateResolver(temp_dir)

    def test_init_default_options(self, temp_dir):
        """Test TemplateResolver initialization with default options."""
        resolver = TemplateResolver(temp_dir)

        assert resolver.project_path == temp_dir
        assert resolver.offline is False
        assert resolver.force_download is False
        assert resolver.template_repo is None
        assert isinstance(resolver.cache_manager, CacheManager)
        assert isinstance(resolver.github_downloader, GitHubDownloader)

    def test_init_with_custom_options(self, temp_dir):
        """Test TemplateResolver initialization with custom options."""
        resolver = TemplateResolver(temp_dir, offline=True, force_download=False, template_repo="custom/repo")

        assert resolver.project_path == temp_dir
        assert resolver.offline is True
        assert resolver.force_download is False
        assert resolver.template_repo == "custom/repo"

    def test_init_with_conflicting_options(self, temp_dir):
        """Test TemplateResolver initialization with conflicting options."""
        # This should not raise an error at init, but should be handled during resolution
        resolver = TemplateResolver(temp_dir, offline=True, force_download=True)

        assert resolver.offline is True
        assert resolver.force_download is True

    def test_get_local_templates_path_exists(self, temp_dir, mock_local_templates_dir):
        """Test getting local templates path when it exists."""
        resolver = TemplateResolver(temp_dir)

        result = resolver.get_local_templates_path()

        assert result == mock_local_templates_dir
        assert result.exists()

    def test_get_local_templates_path_not_exists(self, temp_dir):
        """Test getting local templates path when it doesn't exist."""
        resolver = TemplateResolver(temp_dir)

        result = resolver.get_local_templates_path()

        assert result is None

    def test_get_local_templates_path_empty_dir(self, temp_dir):
        """Test getting local templates path when directory is empty."""
        templates_dir = temp_dir / ".sdd_templates"
        templates_dir.mkdir()

        resolver = TemplateResolver(temp_dir)
        result = resolver.get_local_templates_path()

        # Should return the path even if empty - the resolver just checks existence
        assert result == templates_dir

    def test_get_bundled_templates_path_exists(self, temp_dir, mock_bundled_templates_dir):
        """Test getting bundled templates path when it exists."""
        # Mock the script_dir to point to our test CLI location
        resolver = TemplateResolver(temp_dir)
        resolver.script_dir = mock_bundled_templates_dir.parent / "src"

        result = resolver.get_bundled_templates_path()

        assert result == mock_bundled_templates_dir

    def test_get_bundled_templates_path_not_exists(self, temp_dir):
        """Test getting bundled templates path when it doesn't exist."""
        resolver = TemplateResolver(temp_dir)
        # Set script_dir to a location without templates
        resolver.script_dir = temp_dir / "no_templates"

        result = resolver.get_bundled_templates_path()

        assert result is None

    def test_resolve_templates_local_priority(self, temp_dir, mock_local_templates_dir):
        """Test template resolution prioritizes local templates."""
        resolver = TemplateResolver(temp_dir)

        with patch.object(resolver, "get_bundled_templates_path", return_value=Path("/fake/bundled")):
            result = resolver.resolve_templates_with_transparency()

        assert result.success is True
        assert result.source.source_type == TemplateSourceType.LOCAL
        assert result.source.path == mock_local_templates_dir
        assert result.fallback_attempted is False
        assert "Using local templates" in result.message

    def test_resolve_templates_bundled_fallback(self, temp_dir, mock_bundled_templates_dir):
        """Test template resolution falls back to bundled templates."""
        resolver = TemplateResolver(temp_dir)
        # Set script_dir to enable bundled templates
        resolver.script_dir = mock_bundled_templates_dir.parent / "src"

        result = resolver.resolve_templates_with_transparency()

        assert result.success is True
        assert result.source.source_type == TemplateSourceType.BUNDLED
        assert result.source.path == mock_bundled_templates_dir
        assert result.fallback_attempted is True
        assert "Using bundled templates" in result.message

    def test_resolve_templates_force_download_mode(self, temp_dir, mock_local_templates_dir):
        """Test template resolution with force download bypassing local templates."""
        resolver = TemplateResolver(temp_dir, force_download=True)

        with patch.object(resolver, "_attempt_github_download") as mock_download:
            mock_download.return_value = TemplateResolutionResult(
                source=TemplateSource(
                    path=Path("/cache/templates"), source_type=TemplateSourceType.GITHUB, size_bytes=1024
                ),
                success=True,
                message="Downloaded from GitHub",
                fallback_attempted=True,
            )

            result = resolver.resolve_templates_with_transparency()

        mock_download.assert_called_once()
        assert result.success is True
        assert result.source.source_type == TemplateSourceType.GITHUB

    def test_resolve_templates_offline_mode(self, temp_dir, mock_local_templates_dir):
        """Test template resolution in offline mode with local templates."""
        resolver = TemplateResolver(temp_dir, offline=True)

        result = resolver.resolve_templates_with_transparency()

        assert result.success is True
        assert result.source.source_type == TemplateSourceType.LOCAL
        # Should not attempt GitHub download in offline mode

    def test_resolve_templates_offline_mode_no_local(self, temp_dir):
        """Test template resolution in offline mode without local templates."""
        resolver = TemplateResolver(temp_dir, offline=True)

        with patch.object(resolver, "get_bundled_templates_path", return_value=None):
            result = resolver.resolve_templates_with_transparency()

        assert result.success is False
        assert result.source is None
        assert "offline mode" in result.message.lower()

    def test_resolve_templates_conflicting_options(self, temp_dir):
        """Test template resolution with conflicting offline and force_download options."""
        resolver = TemplateResolver(temp_dir, offline=True, force_download=True)

        result = resolver.resolve_templates_with_transparency()

        assert result.success is False
        assert "Cannot force download in offline mode" in result.message

    @patch("improved_sdd_cli.console.print")
    def test_resolve_templates_never_modifies_local_templates(self, mock_print, temp_dir, mock_local_templates_dir):
        """Test that template resolution never modifies user's .sdd_templates folder."""
        # Record initial state
        initial_files = list(mock_local_templates_dir.rglob("*"))
        initial_content = {}
        for file_path in initial_files:
            if file_path.is_file():
                initial_content[file_path] = file_path.read_text()

        resolver = TemplateResolver(temp_dir)

        # Try various resolution scenarios
        result1 = resolver.resolve_templates_with_transparency()

        # Force download mode (should not touch local templates)
        resolver_force = TemplateResolver(temp_dir, force_download=True)
        with patch.object(resolver_force, "_attempt_github_download") as mock_download:
            mock_download.return_value = TemplateResolutionResult(
                source=None, success=False, message="Download failed", fallback_attempted=True
            )
            result2 = resolver_force.resolve_templates_with_transparency()

        # Verify no modifications to local templates
        final_files = list(mock_local_templates_dir.rglob("*"))
        final_content = {}
        for file_path in final_files:
            if file_path.is_file():
                final_content[file_path] = file_path.read_text()

        assert set(initial_files) == set(final_files)
        assert initial_content == final_content

    def test_github_download_attempt_success(self, temp_dir):
        """Test successful GitHub download attempt."""
        resolver = TemplateResolver(temp_dir)

        mock_path = Path("/cache/downloaded")
        with patch.object(resolver, "_download_github_templates", return_value=mock_path):
            with patch.object(resolver, "_get_directory_size", return_value=2048):
                result = resolver._attempt_github_download()

        assert result.success is True
        assert result.source.source_type == TemplateSourceType.GITHUB
        assert result.source.path == mock_path
        assert result.source.size_bytes == 2048

    def test_github_download_attempt_network_error(self, temp_dir):
        """Test GitHub download attempt with network error."""
        resolver = TemplateResolver(temp_dir)

        with patch.object(resolver, "_download_github_templates", side_effect=NetworkError("Connection failed")):
            result = resolver._attempt_github_download()

        assert result.success is False
        assert result.source is None

    def test_github_download_attempt_api_error(self, temp_dir):
        """Test GitHub download attempt with API error."""
        resolver = TemplateResolver(temp_dir)

        with patch.object(resolver, "_download_github_templates", side_effect=GitHubAPIError("API Error", 404)):
            result = resolver._attempt_github_download()

        assert result.success is False
        assert result.source is None

    def test_github_download_attempt_timeout_error(self, temp_dir):
        """Test GitHub download attempt with timeout error."""
        resolver = TemplateResolver(temp_dir)

        with patch.object(resolver, "_download_github_templates", side_effect=TimeoutError("Download timeout")):
            result = resolver._attempt_github_download()

        assert result.success is False
        assert result.source is None

    def test_github_download_attempt_validation_error(self, temp_dir):
        """Test GitHub download attempt with validation error."""
        resolver = TemplateResolver(temp_dir)

        with patch.object(resolver, "_download_github_templates", side_effect=ValidationError("Invalid templates")):
            result = resolver._attempt_github_download()

        assert result.success is False
        assert result.source is None

    def test_custom_repository_configuration(self, temp_dir):
        """Test TemplateResolver with custom repository configuration."""
        resolver = TemplateResolver(temp_dir, template_repo="custom/repo")

        # Verify the GitHub downloader was configured with custom repo
        assert resolver.github_downloader.repo_owner == "custom"
        assert resolver.github_downloader.repo_name == "repo"

    def test_invalid_repository_format_handling(self, temp_dir):
        """Test TemplateResolver handles invalid repository format gracefully."""
        # This should raise an error during initialization because repo_parts[1] doesn't exist
        with pytest.raises(IndexError):
            TemplateResolver(temp_dir, template_repo="invalid-format")

    def test_directory_size_calculation(self, temp_dir, mock_local_templates_dir):
        """Test directory size calculation utility method."""
        resolver = TemplateResolver(temp_dir)

        size = resolver._get_directory_size(mock_local_templates_dir)

        assert isinstance(size, int)
        assert size > 0  # Should have some content from fixtures

    def test_directory_size_nonexistent_path(self, temp_dir):
        """Test directory size calculation for nonexistent path."""
        resolver = TemplateResolver(temp_dir)

        size = resolver._get_directory_size(Path("/nonexistent/path"))

        assert size == 0

    @patch("improved_sdd_cli.console.print")
    def test_template_resolution_transparency_logging(self, mock_print, temp_dir, mock_local_templates_dir):
        """Test that template resolution provides transparency logging."""
        resolver = TemplateResolver(temp_dir)

        result = resolver.resolve_templates_with_transparency()

        # Verify console output was called for transparency
        mock_print.assert_called()

        # Check that appropriate messages were logged
        printed_messages = [call.args[0] for call in mock_print.call_args_list]
        assert any("Using local templates" in str(msg) for msg in printed_messages)

    def test_cache_integration(self, temp_dir):
        """Test that TemplateResolver properly integrates with CacheManager."""
        resolver = TemplateResolver(temp_dir)

        # Verify cache manager is initialized
        assert isinstance(resolver.cache_manager, CacheManager)

        # Test that cache is used in download workflow
        mock_cache_dir = Path("/cache/test")
        with patch.object(resolver.cache_manager, "create_cache_dir", return_value=mock_cache_dir):
            with patch.object(resolver.github_downloader, "download_templates") as mock_download:
                # Mock successful download
                mock_download.return_value = TemplateSource(
                    path=mock_cache_dir, source_type=TemplateSourceType.GITHUB, size_bytes=1024
                )

                result = resolver._download_github_templates()

                # Verify cache directory was requested
                resolver.cache_manager.create_cache_dir.assert_called_once()
                mock_download.assert_called_once_with(mock_cache_dir)

    def test_template_source_priority_order(self, temp_dir):
        """Test that template source priority follows the correct order."""
        resolver = TemplateResolver(temp_dir)

        # Mock all possible sources
        with patch.object(resolver, "get_local_templates_path", return_value=Path("/local")):
            with patch.object(resolver, "get_bundled_templates_path", return_value=Path("/bundled")):
                with patch.object(resolver, "_get_directory_size", return_value=100):
                    result = resolver.resolve_templates_with_transparency()

        # Should prioritize local templates
        assert result.source.source_type == TemplateSourceType.LOCAL
        assert result.fallback_attempted is False

    def test_template_resolution_error_scenarios(self, temp_dir):
        """Test various error scenarios in template resolution."""
        resolver = TemplateResolver(temp_dir)

        # No templates available anywhere
        with patch.object(resolver, "get_local_templates_path", return_value=None):
            with patch.object(resolver, "get_bundled_templates_path", return_value=None):
                with patch.object(resolver, "_attempt_github_download") as mock_download:
                    mock_download.return_value = TemplateResolutionResult(
                        source=None, success=False, message="All sources failed", fallback_attempted=True
                    )

                    result = resolver.resolve_templates_with_transparency()

        assert result.success is False
        assert result.source is None
        assert result.fallback_attempted is True
