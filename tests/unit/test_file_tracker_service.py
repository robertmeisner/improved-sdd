"""Unit tests for FileTracker service.

Tests the extracted FileTracker service to ensure it works correctly
in isolation and implements the FileTrackerProtocol properly.
"""

import os
import sys
from pathlib import Path

import pytest

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from src.core.interfaces import FileTrackerProtocol
from src.services.file_tracker import FileTracker


class TestFileTracker:
    """Test the FileTracker service implementation."""

    def test_filetracker_implements_protocol(self):
        """Test that FileTracker properly implements FileTrackerProtocol."""
        tracker = FileTracker()
        assert isinstance(tracker, FileTrackerProtocol)

    def test_initialization(self):
        """Test FileTracker initializes with empty lists."""
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
        assert len(tracker.modified_files) == 0
        assert len(tracker.created_dirs) == 0

    def test_track_file_modification(self):
        """Test tracking file modification."""
        tracker = FileTracker()
        test_path = Path("test/file.txt")

        tracker.track_file_modification(test_path)

        assert str(test_path) in tracker.modified_files
        assert len(tracker.modified_files) == 1
        assert len(tracker.created_files) == 0
        assert len(tracker.created_dirs) == 0

    def test_track_dir_creation(self):
        """Test tracking directory creation."""
        tracker = FileTracker()
        test_path = Path("test/dir")

        tracker.track_dir_creation(test_path)

        assert str(test_path) in tracker.created_dirs
        assert len(tracker.created_dirs) == 1
        assert len(tracker.created_files) == 0
        assert len(tracker.modified_files) == 0

    def test_get_summary_empty(self):
        """Test summary generation with no tracked files."""
        tracker = FileTracker()
        summary = tracker.get_summary()

        assert "No files were created or modified" in summary

    def test_get_summary_with_files(self):
        """Test summary generation with tracked files."""
        tracker = FileTracker()
        tracker.track_dir_creation(Path("test_dir"))
        tracker.track_file_creation(Path("test/file.txt"))
        tracker.track_file_modification(Path("existing/file.txt"))

        summary = tracker.get_summary()

        assert "Directories Created:" in summary
        assert "test_dir" in summary
        assert "Files Created:" in summary
        # Convert to match platform path separators
        assert str(Path("test/file.txt")) in summary
        assert "Files Modified:" in summary
        assert str(Path("existing/file.txt")) in summary
        assert "Total: 1 directories, 1 files created, 1 files modified" in summary

    def test_group_files_by_type(self):
        """Test file grouping by type based on directory structure."""
        tracker = FileTracker()
        files = [
            "test/chatmodes/sample.md",
            "test/instructions/guide.md",
            "test/prompts/template.md",
            "test/commands/cmd.md",
            "test/other/file.txt",
        ]

        groups = tracker._group_files_by_type(files)

        assert "Chatmodes" in groups
        assert "Instructions" in groups
        assert "Prompts" in groups
        assert "Commands" in groups
        assert "Other" in groups
        assert "test/chatmodes/sample.md" in groups["Chatmodes"]
        assert "test/instructions/guide.md" in groups["Instructions"]
        assert "test/prompts/template.md" in groups["Prompts"]
        assert "test/commands/cmd.md" in groups["Commands"]
        assert "test/other/file.txt" in groups["Other"]

    def test_group_files_removes_empty_groups(self):
        """Test that empty groups are removed from file grouping."""
        tracker = FileTracker()
        files = ["test/chatmodes/sample.md"]

        groups = tracker._group_files_by_type(files)

        assert "Chatmodes" in groups
        assert "Instructions" not in groups
        assert "Prompts" not in groups
        assert "Commands" not in groups

    def test_multiple_operations(self):
        """Test multiple file operations are tracked correctly."""
        tracker = FileTracker()

        # Track multiple operations
        tracker.track_dir_creation(Path("dir1"))
        tracker.track_dir_creation(Path("dir2"))
        tracker.track_file_creation(Path("file1.txt"))
        tracker.track_file_creation(Path("file2.txt"))
        tracker.track_file_modification(Path("existing1.txt"))
        tracker.track_file_modification(Path("existing2.txt"))

        assert len(tracker.created_dirs) == 2
        assert len(tracker.created_files) == 2
        assert len(tracker.modified_files) == 2

        summary = tracker.get_summary()
        assert "Total: 2 directories, 2 files created, 2 files modified" in summary
