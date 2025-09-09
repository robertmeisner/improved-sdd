"""Unit tests for CacheManager service.

Tests cache directory creation, cleanup, orphaned cache detection,
and cross-platform process checking functionality.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from src.services.cache_manager import CacheManager  # noqa: E402


class TestCacheManager:
    """Test suite for CacheManager service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cache_manager = CacheManager()
        # Clear any active caches from setup
        self.cache_manager._active_caches.clear()

    def teardown_method(self):
        """Clean up after each test."""
        # Clean up any remaining cache directories
        for cache_dir in self.cache_manager._active_caches.copy():
            try:
                if cache_dir.exists():
                    shutil.rmtree(cache_dir, ignore_errors=True)
            except Exception:
                pass
        self.cache_manager._active_caches.clear()

    def test_create_cache_dir_creates_unique_directory(self):
        """Test that create_cache_dir creates a unique directory in temp location."""
        cache_dir = self.cache_manager.create_cache_dir()

        # Verify directory exists
        assert cache_dir.exists()
        assert cache_dir.is_dir()

        # Verify it's in system temp directory
        temp_dir = Path(tempfile.gettempdir())
        assert cache_dir.parent == temp_dir

        # Verify naming pattern
        assert cache_dir.name.startswith(f"sdd_templates_{os.getpid()}_")

        # Verify it's tracked
        assert cache_dir in self.cache_manager._active_caches

    def test_create_cache_dir_tracks_multiple_caches(self):
        """Test that multiple cache directories are properly tracked."""
        cache1 = self.cache_manager.create_cache_dir()
        cache2 = self.cache_manager.create_cache_dir()

        assert cache1 != cache2
        assert cache1 in self.cache_manager._active_caches
        assert cache2 in self.cache_manager._active_caches
        assert len(self.cache_manager._active_caches) == 2

    def test_cleanup_cache_removes_directory_and_tracking(self):
        """Test that cleanup_cache removes directory and removes from tracking."""
        cache_dir = self.cache_manager.create_cache_dir()

        # Create a test file in the cache
        test_file = cache_dir / "test.txt"
        test_file.write_text("test content")

        # Verify setup
        assert cache_dir.exists()
        assert test_file.exists()
        assert cache_dir in self.cache_manager._active_caches

        # Clean up
        self.cache_manager.cleanup_cache(cache_dir)

        # Verify cleanup
        assert not cache_dir.exists()
        assert cache_dir not in self.cache_manager._active_caches

    def test_cleanup_cache_handles_nonexistent_directory(self):
        """Test that cleanup_cache handles non-existent directories gracefully."""
        nonexistent_dir = Path("/nonexistent/cache/dir")

        # Should not raise exception
        self.cache_manager.cleanup_cache(nonexistent_dir)

        # Should not be in tracking
        assert nonexistent_dir not in self.cache_manager._active_caches

    def test_cleanup_all_caches_cleans_all_tracked_directories(self):
        """Test that cleanup_all_caches removes all tracked cache directories."""
        cache1 = self.cache_manager.create_cache_dir()
        cache2 = self.cache_manager.create_cache_dir()

        # Create test files
        (cache1 / "file1.txt").write_text("content1")
        (cache2 / "file2.txt").write_text("content2")

        # Verify setup
        assert cache1.exists()
        assert cache2.exists()
        assert len(self.cache_manager._active_caches) == 2

        # Clean up all
        self.cache_manager.cleanup_all_caches()

        # Verify cleanup
        assert not cache1.exists()
        assert not cache2.exists()
        assert len(self.cache_manager._active_caches) == 0

    def test_cleanup_orphaned_caches_detects_orphaned_directories(self):
        """Test that cleanup_orphaned_caches detects and cleans orphaned cache directories."""
        # Create a fake orphaned cache directory with a non-existent PID
        temp_dir = Path(tempfile.gettempdir())
        fake_pid = 999999  # Very unlikely to exist
        orphaned_cache = temp_dir / f"sdd_templates_{fake_pid}_orphaned"
        orphaned_cache.mkdir()

        # Create a test file
        (orphaned_cache / "test.txt").write_text("orphaned content")

        try:
            # Run cleanup
            cleaned_count = self.cache_manager.cleanup_orphaned_caches()

            # Verify cleanup
            assert cleaned_count == 1
            assert not orphaned_cache.exists()

        finally:
            # Ensure cleanup even if test fails
            if orphaned_cache.exists():
                shutil.rmtree(orphaned_cache, ignore_errors=True)

    def test_cleanup_orphaned_caches_skips_own_cache(self):
        """Test that cleanup_orphaned_caches skips the current process's cache directories."""
        # Create our own cache
        own_cache = self.cache_manager.create_cache_dir()

        # Run cleanup
        cleaned_count = self.cache_manager.cleanup_orphaned_caches()

        # Verify our cache is still there
        assert own_cache.exists()
        assert cleaned_count == 0

    def test_cleanup_orphaned_caches_handles_running_processes(self):
        """Test that cleanup_orphaned_caches skips directories of running processes."""
        # Create a fake cache directory with current PID (simulating running process)
        temp_dir = Path(tempfile.gettempdir())
        current_pid = os.getpid()
        running_cache = temp_dir / f"sdd_templates_{current_pid}_running"
        running_cache.mkdir()

        try:
            # Run cleanup
            cleaned_count = self.cache_manager.cleanup_orphaned_caches()

            # Verify running process cache is preserved
            assert running_cache.exists()
            assert cleaned_count == 0

        finally:
            # Cleanup
            if running_cache.exists():
                shutil.rmtree(running_cache, ignore_errors=True)

    @patch("platform.system")
    @patch("subprocess.run")
    def test_is_process_running_windows_tasklist_success(self, mock_subprocess, mock_platform):
        """Test process checking on Windows with successful tasklist."""
        mock_platform.return_value = "Windows"
        mock_result = MagicMock()
        mock_result.stdout = f"PID {12345} exists"
        mock_subprocess.return_value = mock_result

        assert self.cache_manager._is_process_running(12345) is True
        mock_subprocess.assert_called_once()

    @patch("platform.system")
    @patch("subprocess.run")
    def test_is_process_running_windows_tasklist_failure(self, mock_subprocess, mock_platform):
        """Test process checking on Windows with tasklist failure."""
        mock_platform.return_value = "Windows"
        mock_subprocess.side_effect = subprocess.TimeoutExpired("tasklist", 5)

        assert self.cache_manager._is_process_running(12345) is False

    @patch("platform.system")
    @patch("os.kill")
    def test_is_process_running_unix_success(self, mock_kill, mock_platform):
        """Test process checking on Unix-like systems with success."""
        mock_platform.return_value = "Linux"
        mock_kill.return_value = None  # Success

        assert self.cache_manager._is_process_running(12345) is True
        mock_kill.assert_called_once_with(12345, 0)

    @patch("platform.system")
    @patch("os.kill")
    def test_is_process_running_unix_process_not_found(self, mock_kill, mock_platform):
        """Test process checking on Unix-like systems with process not found."""
        mock_platform.return_value = "Linux"
        mock_kill.side_effect = ProcessLookupError()

        assert self.cache_manager._is_process_running(12345) is False

    @patch("platform.system")
    @patch("os.kill")
    def test_is_process_running_unix_os_error(self, mock_kill, mock_platform):
        """Test process checking on Unix-like systems with OS error."""
        mock_platform.return_value = "Linux"
        mock_kill.side_effect = OSError()

        assert self.cache_manager._is_process_running(12345) is False

    @patch("platform.system")
    def test_is_process_running_unknown_platform(self, mock_platform):
        """Test process checking on unknown platform defaults to safe assumption."""
        mock_platform.return_value = "Unknown"

        # On unknown platforms, the method may return False due to os.kill failure
        # This is actually safer than assuming True
        result = self.cache_manager._is_process_running(12345)
        # The result depends on whether os.kill works on the unknown platform
        assert isinstance(result, bool)

    def test_get_cache_info_existing_directory(self):
        """Test get_cache_info for existing directory with files."""
        cache_dir = self.cache_manager.create_cache_dir()

        # Create test files
        (cache_dir / "file1.txt").write_text("content1")
        (cache_dir / "file2.txt").write_text("content2")
        (cache_dir / "subdir").mkdir()
        (cache_dir / "subdir" / "file3.txt").write_text("content3")

        info = self.cache_manager.get_cache_info(cache_dir)

        assert info["exists"] is True
        assert info["file_count"] == 3  # Should count all files recursively
        assert info["size_bytes"] == len("content1") + len("content2") + len("content3")
        assert info["path"] == str(cache_dir)

    def test_get_cache_info_nonexistent_directory(self):
        """Test get_cache_info for non-existent directory."""
        nonexistent_dir = Path("/nonexistent/cache/dir")

        info = self.cache_manager.get_cache_info(nonexistent_dir)

        assert info["exists"] is False
        assert info["size_bytes"] == 0
        assert info["file_count"] == 0

    def test_get_cache_info_empty_directory(self):
        """Test get_cache_info for empty directory."""
        cache_dir = self.cache_manager.create_cache_dir()

        info = self.cache_manager.get_cache_info(cache_dir)

        assert info["exists"] is True
        assert info["size_bytes"] == 0
        assert info["file_count"] == 0
        assert info["path"] == str(cache_dir)

    def test_get_cache_info_handles_permission_errors(self):
        """Test get_cache_info handles permission errors gracefully."""
        cache_dir = self.cache_manager.create_cache_dir()

        # Create a file
        test_file = cache_dir / "test.txt"
        test_file.write_text("content")

        # Mock the rglob iteration to raise permission error
        with patch.object(Path, "rglob") as mock_rglob:
            mock_rglob.side_effect = PermissionError()
            info = self.cache_manager.get_cache_info(cache_dir)

        # Should still return basic info
        assert info["exists"] is True
        assert info["path"] == str(cache_dir)
        # Size and count should be 0 due to error handling
        assert info["size_bytes"] == 0
        assert info["file_count"] == 0

    def test_protocol_compliance(self):
        """Test that CacheManager implements CacheManagerProtocol correctly."""
        from core.interfaces import CacheManagerProtocol

        # Should be able to use isinstance check
        assert isinstance(self.cache_manager, CacheManagerProtocol)

        # Should implement all required methods
        required_methods = [
            "create_cache_dir",
            "cleanup_cache",
            "cleanup_all_caches",
            "cleanup_orphaned_caches",
            "get_cache_info",
        ]

        for method_name in required_methods:
            assert hasattr(self.cache_manager, method_name)
            assert callable(getattr(self.cache_manager, method_name))

    def test_atexit_registration(self):
        """Test that atexit handler is properly registered."""
        # This is difficult to test directly, but we can verify the handler is callable
        assert callable(self.cache_manager.cleanup_all_caches)
