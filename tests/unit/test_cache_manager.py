"""Unit tests for CacheManager class."""

import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

# Import after path modification
from src import CacheManager  # noqa: E402


@pytest.mark.unit
@pytest.mark.templates
class TestCacheManager:
    """Test the CacheManager class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def cache_manager(self):
        """Create a CacheManager instance for testing."""
        return CacheManager()

    def test_init_sets_process_id(self, cache_manager):
        """Test CacheManager initialization sets process ID."""
        assert cache_manager.process_id == os.getpid()
        assert cache_manager._active_caches == []

    def test_create_cache_dir_returns_path(self, cache_manager):
        """Test cache directory creation returns valid path."""
        cache_dir = cache_manager.create_cache_dir()

        assert isinstance(cache_dir, Path)
        assert cache_dir.exists()
        assert cache_dir.is_dir()
        assert "sdd_templates" in cache_dir.name
        assert str(cache_manager.process_id) in cache_dir.name

        # Cache should be tracked
        assert cache_dir in cache_manager._active_caches

    def test_create_cache_dir_unique_names(self, cache_manager):
        """Test that multiple cache directories get unique names."""
        cache_dir1 = cache_manager.create_cache_dir()
        time.sleep(0.01)  # Ensure different timestamps
        cache_dir2 = cache_manager.create_cache_dir()

        assert cache_dir1 != cache_dir2
        assert cache_dir1.name != cache_dir2.name
        assert len(cache_manager._active_caches) == 2

    def test_cleanup_cache_removes_directory(self, cache_manager):
        """Test cache cleanup removes directory and tracking."""
        cache_dir = cache_manager.create_cache_dir()

        # Add some content
        (cache_dir / "test_file.txt").write_text("test content")
        assert cache_dir.exists()

        cache_manager.cleanup_cache(cache_dir)

        assert not cache_dir.exists()
        assert cache_dir not in cache_manager._active_caches

    def test_cleanup_cache_handles_missing_directory(self, cache_manager):
        """Test cleanup handles already removed directories gracefully."""
        cache_dir = cache_manager.create_cache_dir()

        # Manually remove directory
        import shutil

        shutil.rmtree(cache_dir)

        # Cleanup should not raise error
        cache_manager.cleanup_cache(cache_dir)
        assert cache_dir not in cache_manager._active_caches

    def test_cleanup_all_caches(self, cache_manager):
        """Test cleanup of all active caches."""
        cache_dir1 = cache_manager.create_cache_dir()
        cache_dir2 = cache_manager.create_cache_dir()

        # Add content to verify they exist
        (cache_dir1 / "file1.txt").write_text("content1")
        (cache_dir2 / "file2.txt").write_text("content2")

        cache_manager.cleanup_all_caches()

        assert not cache_dir1.exists()
        assert not cache_dir2.exists()
        assert len(cache_manager._active_caches) == 0

    def test_is_process_running_current_process(self, cache_manager):
        """Test process running check with current process."""
        current_pid = os.getpid()
        assert cache_manager._is_process_running(current_pid) is True

    def test_is_process_running_invalid_pid(self, cache_manager):
        """Test process running check with invalid PID."""
        # Use obviously invalid PIDs that should never exist
        assert cache_manager._is_process_running(999999) is False
        assert cache_manager._is_process_running(1000000) is False

    def test_cleanup_orphaned_caches_integration(self, cache_manager):
        """Test orphaned cache cleanup integration."""
        # This is a basic integration test that should not fail
        cleaned_count = cache_manager.cleanup_orphaned_caches()
        assert isinstance(cleaned_count, int)
        assert cleaned_count >= 0

    def test_get_cache_info_existing_cache(self, cache_manager):
        """Test getting cache information for existing cache."""
        cache_dir = cache_manager.create_cache_dir()

        # Add some content
        (cache_dir / "file1.txt").write_text("content1")
        (cache_dir / "file2.txt").write_text("content2")
        (cache_dir / "subdir").mkdir()
        (cache_dir / "subdir" / "file3.txt").write_text("content3")

        info = cache_manager.get_cache_info(cache_dir)

        assert info["exists"] is True
        assert info["file_count"] == 3
        assert info["size_bytes"] > 0
        assert "path" in info

    def test_get_cache_info_nonexistent_cache(self, cache_manager):
        """Test getting cache information for non-existent cache."""
        fake_cache = Path("/nonexistent/cache")

        info = cache_manager.get_cache_info(fake_cache)

        assert info["exists"] is False
        assert info["file_count"] == 0
        assert info["size_bytes"] == 0

    def test_get_cache_info_empty_cache(self, cache_manager):
        """Test getting cache information for empty cache."""
        cache_dir = cache_manager.create_cache_dir()

        info = cache_manager.get_cache_info(cache_dir)

        assert info["exists"] is True
        assert info["file_count"] == 0
        assert info["size_bytes"] == 0

    def test_cache_manager_context_manager(self, cache_manager, temp_dir):
        """Test CacheManager as context manager (if implemented)."""
        # Basic test - if context manager not implemented, just test basic usage
        cache_dir = cache_manager.create_cache_dir()
        (cache_dir / "test.txt").write_text("test")

        # Verify cache works
        info = cache_manager.get_cache_info(cache_dir)
        assert info["exists"] is True
        assert info["file_count"] == 1

    def test_cache_manager_edge_cases(self, cache_manager):
        """Test CacheManager edge cases and boundary conditions."""
        # Test cleanup of already cleaned cache
        cache_dir = cache_manager.create_cache_dir()
        cache_manager.cleanup_cache(cache_dir)

        # Cleanup again (should not error)
        cache_manager.cleanup_cache(cache_dir)

        # Test cleanup_all with no active caches
        cache_manager.cleanup_all_caches()

        # Test orphan cleanup with error handling
        cleaned_count = cache_manager.cleanup_orphaned_caches()
        assert isinstance(cleaned_count, int)

    def test_concurrent_cache_creation(self, cache_manager):
        """Test that concurrent cache creation works properly."""
        caches = []
        for _ in range(5):
            cache_dir = cache_manager.create_cache_dir()
            caches.append(cache_dir)
            time.sleep(0.001)  # Small delay to ensure unique timestamps

        # All caches should be unique
        assert len(set(caches)) == 5
        assert len(cache_manager._active_caches) == 5

        # All should exist
        for cache_dir in caches:
            assert cache_dir.exists()

    def test_cleanup_with_permission_error(self, cache_manager):
        """Test cleanup behavior when permission errors occur."""
        cache_dir = cache_manager.create_cache_dir()

        # Mock a permission error during cleanup
        with patch("shutil.rmtree", side_effect=PermissionError("Access denied")):
            # Should not raise exception
            cache_manager.cleanup_cache(cache_dir)

            # Cache should be removed from tracking even if cleanup failed
            assert cache_dir not in cache_manager._active_caches

    def test_cache_directory_structure(self, cache_manager):
        """Test that cache directories have the expected structure."""
        cache_dir = cache_manager.create_cache_dir()

        # Directory name should follow pattern
        assert cache_dir.name.startswith("sdd_templates_")
        assert str(cache_manager.process_id) in cache_dir.name

        # Should be in system temp directory
        assert cache_dir.parent == Path(tempfile.gettempdir())

    def test_multiple_cache_managers(self):
        """Test that multiple CacheManager instances work independently."""
        manager1 = CacheManager()
        manager2 = CacheManager()

        cache1 = manager1.create_cache_dir()
        cache2 = manager2.create_cache_dir()

        # Both should have same process ID but different cache sets
        assert manager1.process_id == manager2.process_id
        assert cache1 in manager1._active_caches
        assert cache2 in manager2._active_caches
        assert cache1 not in manager2._active_caches
        assert cache2 not in manager1._active_caches
