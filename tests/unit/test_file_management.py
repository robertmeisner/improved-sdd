"""Unit tests for file management and conflict detection system.

This module tests the FileManager class, conflict detection logic,
file discovery functionality, and related data classes.
"""

import os
import stat
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch
from datetime import datetime

import pytest

from src.core.file_manager import (
    FileManager,
    FileConflict,
    ConflictType,
    FileDiscoveryResult,
    DeletionAttempt,
    DeleteResult,
    SafeFileDeletor
)
from src.core.ai_tool_manager import AIToolManager, ManagedFileResult


class TestFileConflict:
    """Test FileConflict dataclass functionality."""
    
    def test_file_conflict_creation(self):
        """Test creating a FileConflict instance."""
        file_path = Path("/test/file.md")
        conflict = FileConflict(
            file_path=file_path,
            file_type="chatmodes",
            conflict_type=ConflictType.MANAGED_FILE_EXISTS,
            managed_by_tools=["github-copilot"],
            file_size=1024,
            last_modified="1234567890"
        )
        
        assert conflict.file_path == file_path
        assert conflict.file_type == "chatmodes"
        assert conflict.conflict_type == ConflictType.MANAGED_FILE_EXISTS
        assert conflict.managed_by_tools == ["github-copilot"]
        assert conflict.file_size == 1024
        assert conflict.last_modified == "1234567890"
    
    def test_is_managed_property(self):
        """Test is_managed property logic."""
        # Managed file
        managed_conflict = FileConflict(
            file_path=Path("/test/file.md"),
            file_type="chatmodes",
            conflict_type=ConflictType.MANAGED_FILE_EXISTS,
            managed_by_tools=["github-copilot"],
            file_size=1024
        )
        assert managed_conflict.is_managed is True
        
        # Manual file
        manual_conflict = FileConflict(
            file_path=Path("/test/file.md"),
            file_type="chatmodes", 
            conflict_type=ConflictType.MANUAL_FILE_EXISTS,
            managed_by_tools=[],
            file_size=1024
        )
        assert manual_conflict.is_managed is False
    
    def test_is_manual_property(self):
        """Test is_manual property logic."""
        # Manual file
        manual_conflict = FileConflict(
            file_path=Path("/test/file.md"),
            file_type="chatmodes",
            conflict_type=ConflictType.MANUAL_FILE_EXISTS,
            managed_by_tools=[],
            file_size=1024
        )
        assert manual_conflict.is_manual is True
        
        # Managed file
        managed_conflict = FileConflict(
            file_path=Path("/test/file.md"),
            file_type="chatmodes",
            conflict_type=ConflictType.MANAGED_FILE_EXISTS, 
            managed_by_tools=["github-copilot"],
            file_size=1024
        )
        assert managed_conflict.is_manual is False
    
    def test_get_relative_path(self):
        """Test relative path calculation."""
        project_root = Path("/project")
        file_path = Path("/project/.github/chatmodes/test.md")
        
        conflict = FileConflict(
            file_path=file_path,
            file_type="chatmodes",
            conflict_type=ConflictType.MANAGED_FILE_EXISTS,
            managed_by_tools=["github-copilot"],
            file_size=1024
        )
        
        relative_path = conflict.get_relative_path(project_root)
        # Normalize path separators for cross-platform compatibility
        expected_path = ".github/chatmodes/test.md"
        assert relative_path == expected_path or relative_path == expected_path.replace("/", "\\")
    
    def test_get_relative_path_outside_project(self):
        """Test relative path for file outside project root."""
        project_root = Path("/project")
        file_path = Path("/outside/test.md")
        
        conflict = FileConflict(
            file_path=file_path,
            file_type="chatmodes",
            conflict_type=ConflictType.MANUAL_FILE_EXISTS,
            managed_by_tools=[],
            file_size=1024
        )
        
        relative_path = conflict.get_relative_path(project_root)
        # Normalize path separators for cross-platform compatibility
        expected_path = "/outside/test.md"
        assert relative_path == expected_path or relative_path == expected_path.replace("/", "\\")


class TestFileDiscoveryResult:
    """Test FileDiscoveryResult dataclass functionality."""
    
    def test_file_discovery_result_creation(self):
        """Test creating a FileDiscoveryResult instance."""
        files = [Path("/test/file1.md"), Path("/test/file2.md")]
        conflicts = [
            FileConflict(
                file_path=Path("/test/file1.md"),
                file_type="chatmodes",
                conflict_type=ConflictType.MANAGED_FILE_EXISTS,
                managed_by_tools=["github-copilot"],
                file_size=1024
            )
        ]
        files_by_type = {"chatmodes": [Path("/test/file1.md")]}
        
        result = FileDiscoveryResult(
            discovered_files=files,
            conflicts=conflicts,
            files_by_type=files_by_type,
            managed_files_found=[Path("/test/file1.md")],
            manual_files_found=[Path("/test/file2.md")],
            total_files=2
        )
        
        assert result.discovered_files == files
        assert result.conflicts == conflicts
        assert result.files_by_type == files_by_type
        assert result.total_files == 2
    
    def test_has_conflicts_property(self):
        """Test has_conflicts property."""
        # With conflicts
        result_with_conflicts = FileDiscoveryResult(
            discovered_files=[],
            conflicts=[Mock()],
            files_by_type={},
            managed_files_found=[],
            manual_files_found=[],
            total_files=0
        )
        assert result_with_conflicts.has_conflicts is True
        
        # Without conflicts
        result_no_conflicts = FileDiscoveryResult(
            discovered_files=[],
            conflicts=[],
            files_by_type={},
            managed_files_found=[],
            manual_files_found=[],
            total_files=0
        )
        assert result_no_conflicts.has_conflicts is False
    
    def test_conflict_count_property(self):
        """Test conflict_count property."""
        conflicts = [Mock(), Mock(), Mock()]
        result = FileDiscoveryResult(
            discovered_files=[],
            conflicts=conflicts,
            files_by_type={},
            managed_files_found=[],
            manual_files_found=[],
            total_files=0
        )
        assert result.conflict_count == 3
    
    def test_get_conflicts_by_type(self):
        """Test filtering conflicts by type."""
        managed_conflict = FileConflict(
            file_path=Path("/test/managed.md"),
            file_type="chatmodes",
            conflict_type=ConflictType.MANAGED_FILE_EXISTS,
            managed_by_tools=["github-copilot"],
            file_size=1024
        )
        manual_conflict = FileConflict(
            file_path=Path("/test/manual.md"),
            file_type="chatmodes",
            conflict_type=ConflictType.MANUAL_FILE_EXISTS,
            managed_by_tools=[],
            file_size=1024
        )
        
        result = FileDiscoveryResult(
            discovered_files=[],
            conflicts=[managed_conflict, manual_conflict],
            files_by_type={},
            managed_files_found=[],
            manual_files_found=[],
            total_files=0
        )
        
        managed_conflicts = result.get_conflicts_by_type(ConflictType.MANAGED_FILE_EXISTS)
        manual_conflicts = result.get_conflicts_by_type(ConflictType.MANUAL_FILE_EXISTS)
        
        assert len(managed_conflicts) == 1
        assert len(manual_conflicts) == 1
        assert managed_conflicts[0] == managed_conflict
        assert manual_conflicts[0] == manual_conflict


class TestDeletionAttempt:
    """Test DeletionAttempt dataclass functionality."""
    
    def test_deletion_attempt_success(self):
        """Test successful deletion attempt."""
        attempt = DeletionAttempt(
            file_path=Path("/test/file.md"),
            success=True
        )
        
        assert attempt.file_path == Path("/test/file.md")
        assert attempt.success is True
        assert attempt.failed is False
        assert attempt.error_message is None
        assert attempt.permission_denied is False
        assert attempt.file_not_found is False
    
    def test_deletion_attempt_failure(self):
        """Test failed deletion attempt."""
        attempt = DeletionAttempt(
            file_path=Path("/test/file.md"),
            success=False,
            error_message="Permission denied",
            permission_denied=True
        )
        
        assert attempt.success is False
        assert attempt.failed is True
        assert attempt.error_message == "Permission denied"
        assert attempt.permission_denied is True


class TestDeleteResult:
    """Test DeleteResult dataclass functionality."""
    
    def test_delete_result_creation(self):
        """Test creating a DeleteResult instance."""
        deleted_files = [Path("/test/file1.md")]
        skipped_files = [Path("/test/file2.md")]
        failed_deletions = [
            DeletionAttempt(
                file_path=Path("/test/file3.md"),
                success=False,
                error_message="Permission denied"
            )
        ]
        
        result = DeleteResult(
            deleted_files=deleted_files,
            skipped_files=skipped_files,
            failed_deletions=failed_deletions,
            total_conflicts=3,
            total_files_processed=3
        )
        
        assert result.deleted_files == deleted_files
        assert result.skipped_files == skipped_files
        assert result.failed_deletions == failed_deletions
        assert result.total_conflicts == 3
        assert result.total_files_processed == 3
    
    def test_success_count_property(self):
        """Test success_count property."""
        result = DeleteResult(
            deleted_files=[Path("/test/file1.md"), Path("/test/file2.md")],
            skipped_files=[],
            failed_deletions=[],
            total_conflicts=2,
            total_files_processed=2
        )
        assert result.success_count == 2
    
    def test_skip_count_property(self):
        """Test skip_count property."""
        result = DeleteResult(
            deleted_files=[],
            skipped_files=[Path("/test/file1.md"), Path("/test/file2.md")],
            failed_deletions=[],
            total_conflicts=2,
            total_files_processed=2
        )
        assert result.skip_count == 2
    
    def test_failure_count_property(self):
        """Test failure_count property."""
        failed_attempts = [
            DeletionAttempt(Path("/test/file1.md"), False),
            DeletionAttempt(Path("/test/file2.md"), False)
        ]
        result = DeleteResult(
            deleted_files=[],
            skipped_files=[],
            failed_deletions=failed_attempts,
            total_conflicts=2,
            total_files_processed=2
        )
        assert result.failure_count == 2
    
    def test_success_rate_property(self):
        """Test success_rate calculation."""
        result = DeleteResult(
            deleted_files=[Path("/test/file1.md")],
            skipped_files=[Path("/test/file2.md")],
            failed_deletions=[DeletionAttempt(Path("/test/file3.md"), False)],
            total_conflicts=3,
            total_files_processed=3
        )
        # 1 successful out of 3 processed = 33.33%
        assert abs(result.success_rate - 33.33) < 0.01
    
    def test_success_rate_zero_processed(self):
        """Test success_rate with zero processed files."""
        result = DeleteResult(
            deleted_files=[],
            skipped_files=[],
            failed_deletions=[],
            total_conflicts=0,
            total_files_processed=0
        )
        # According to implementation, zero processed files returns 100.0
        assert result.success_rate == 100.0


class TestFileManager:
    """Test FileManager class functionality."""
    
    @pytest.fixture
    def mock_ai_tool_manager(self):
        """Create a mock AIToolManager."""
        manager = Mock(spec=AIToolManager)
        manager.get_available_tools.return_value = ["github-copilot", "claude"]
        return manager
    
    @pytest.fixture
    def file_manager(self, mock_ai_tool_manager):
        """Create a FileManager instance with mocked dependencies."""
        return FileManager(mock_ai_tool_manager)
    
    def test_file_manager_initialization(self, mock_ai_tool_manager):
        """Test FileManager initialization."""
        file_manager = FileManager(mock_ai_tool_manager)
        
        assert file_manager.ai_tool_manager == mock_ai_tool_manager
        assert file_manager.logger is not None
        assert "chatmodes" in file_manager.template_directories
        assert "instructions" in file_manager.template_directories
        assert "prompts" in file_manager.template_directories
        assert "commands" in file_manager.template_directories
        assert ".md" in file_manager.file_extensions
    
    def test_get_file_type(self, file_manager):
        """Test _get_file_type method."""
        project_root = Path("/project")
        
        # Test chatmodes file
        chatmodes_file = Path("/project/.github/chatmodes/test.md")
        file_type = file_manager._get_file_type(chatmodes_file, project_root)
        assert file_type == "chatmodes"
        
        # Test instructions file
        instructions_file = Path("/project/.github/instructions/test.md")
        file_type = file_manager._get_file_type(instructions_file, project_root)
        assert file_type == "instructions"
        
        # Test file outside template directories
        other_file = Path("/project/README.md")
        file_type = file_manager._get_file_type(other_file, project_root)
        assert file_type is None
        
        # Test file outside project root
        external_file = Path("/outside/test.md")
        file_type = file_manager._get_file_type(external_file, project_root)
        assert file_type is None
    
    def test_build_managed_files_map(self, file_manager):
        """Test _build_managed_files_map method."""
        # Setup mock AI tool manager
        file_manager.ai_tool_manager.get_managed_files_for_tool.return_value = ManagedFileResult(
            tool_id="github-copilot",
            tool_name="GitHub Copilot",
            app_type="python-cli",
            managed_files={
                "chatmodes": ["copilot.chatmode.md"],
                "instructions": ["copilot.instructions.md"]
            },
            total_files=2
        )
        
        result = file_manager._build_managed_files_map(["github-copilot"])
        
        assert "chatmodes" in result
        assert "instructions" in result
        assert "copilot.chatmode.md" in result["chatmodes"]
        assert "copilot.instructions.md" in result["instructions"]
    
    def test_build_managed_files_map_with_error(self, file_manager):
        """Test _build_managed_files_map handling errors."""
        # Setup mock to raise exception
        file_manager.ai_tool_manager.get_managed_files_for_tool.side_effect = Exception("Test error")
        
        result = file_manager._build_managed_files_map(["github-copilot"])
        
        # Should return empty sets for all file types
        for file_type in file_manager.template_directories.keys():
            assert file_type in result
            assert len(result[file_type]) == 0
    
    def test_discover_files_simple(self, file_manager):
        """Test discover_files method with simplified mocking."""
        project_root = Path("/project")
        
        # Mock the AI tool manager behavior
        file_manager.ai_tool_manager.detect_active_tools.return_value.active_tools = ["github-copilot"]
        file_manager.ai_tool_manager.get_managed_files_for_tool.return_value = ManagedFileResult(
            tool_id="github-copilot",
            tool_name="GitHub Copilot",
            app_type="python-cli",
            managed_files={"chatmodes": ["test.md"]},
            total_files=1
        )
        
        # Test with a non-existent project root to avoid complex file system mocking
        with patch('pathlib.Path.exists', return_value=False):
            result = file_manager.discover_files(project_root)
            
            # Should return empty result when directories don't exist
            assert len(result.discovered_files) == 0
            assert result.total_files == 0
            assert len(result.conflicts) == 0
    
    def test_detect_conflicts_for_tools(self, file_manager):
        """Test detect_conflicts_for_tools method."""
        project_root = Path("/project")
        tool_ids = ["github-copilot"]
        
        # Mock discover_files to return a result with conflicts
        expected_conflicts = [
            FileConflict(
                file_path=Path("/project/.github/chatmodes/test.md"),
                file_type="chatmodes",
                conflict_type=ConflictType.MANAGED_FILE_EXISTS,
                managed_by_tools=["github-copilot"],
                file_size=1024
            )
        ]
        
        with patch.object(file_manager, 'discover_files') as mock_discover:
            mock_result = Mock(spec=FileDiscoveryResult)
            mock_result.conflicts = expected_conflicts
            mock_discover.return_value = mock_result
            
            conflicts = file_manager.detect_conflicts_for_tools(project_root, tool_ids)
            
            assert conflicts == expected_conflicts
            mock_discover.assert_called_once_with(project_root, tool_ids, None)
    
    def test_get_managed_files_to_delete(self, file_manager):
        """Test get_managed_files_to_delete method."""
        project_root = Path("/project")
        tool_ids = ["github-copilot"]
        
        # Mock conflicts with mixed types
        conflicts = [
            FileConflict(
                file_path=Path("/project/.github/chatmodes/managed.md"),
                file_type="chatmodes",
                conflict_type=ConflictType.MANAGED_FILE_EXISTS,
                managed_by_tools=["github-copilot"],
                file_size=1024
            ),
            FileConflict(
                file_path=Path("/project/.github/chatmodes/manual.md"),
                file_type="chatmodes",
                conflict_type=ConflictType.MANUAL_FILE_EXISTS,
                managed_by_tools=[],
                file_size=1024
            )
        ]
        
        with patch.object(file_manager, 'discover_files') as mock_discover:
            mock_result = Mock(spec=FileDiscoveryResult)
            mock_result.conflicts = conflicts
            mock_discover.return_value = mock_result
            
            managed_files = file_manager.get_managed_files_to_delete(project_root, tool_ids)
            
            # Should only return managed files
            assert len(managed_files) == 1
            assert managed_files[0] == Path("/project/.github/chatmodes/managed.md")
    
    def test_get_manual_files(self, file_manager):
        """Test get_manual_files method."""
        project_root = Path("/project")
        
        manual_files = [
            Path("/project/.github/chatmodes/manual1.md"),
            Path("/project/.github/chatmodes/manual2.md")
        ]
        
        with patch.object(file_manager, 'discover_files') as mock_discover:
            mock_result = Mock(spec=FileDiscoveryResult)
            mock_result.manual_files_found = manual_files
            mock_discover.return_value = mock_result
            
            result = file_manager.get_manual_files(project_root)
            
            assert result == manual_files
            mock_discover.assert_called_once_with(project_root)


class TestSafeFileDeletor:
    """Test SafeFileDeletor class functionality."""
    
    @pytest.fixture
    def safe_deletor(self):
        """Create a SafeFileDeletor instance."""
        return SafeFileDeletor()
    
    def test_safe_deletor_initialization(self, safe_deletor):
        """Test SafeFileDeletor initialization."""
        assert safe_deletor.logger is not None
    
    def test_delete_files_dry_run(self, safe_deletor):
        """Test delete_files in dry run mode."""
        # Create temporary files for the test
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            file1 = temp_path / "file1.md"
            file2 = temp_path / "file2.md"
            
            # Create actual files for dry run test
            file1.write_text("# Test file 1")
            file2.write_text("# Test file 2")
            
            files = [file1, file2]
            
            result = safe_deletor.delete_files(files, dry_run=True)
            
            # In dry run mode, files should be simulated as deleted
            assert len(result.deleted_files) == 2
            assert len(result.failed_deletions) == 0
            assert result.success_count == 2
            
            # Files should still exist after dry run
            assert file1.exists()
            assert file2.exists()
    
    def test_delete_files_actual_nonexistent(self, safe_deletor):
        """Test delete_files with non-existent files."""
        files = [Path("/test/nonexistent1.md"), Path("/test/nonexistent2.md")]
        
        result = safe_deletor.delete_files(files, dry_run=False)
        
        # Non-existent files should result in failures
        assert len(result.deleted_files) == 0
        assert len(result.failed_deletions) == 2
        assert result.failure_count == 2
        for attempt in result.failed_deletions:
            assert attempt.file_not_found is True


class TestFileManagerIntegration:
    """Integration tests for FileManager with real filesystem operations."""
    
    def test_file_discovery_integration(self):
        """Test file discovery with temporary filesystem."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create test directory structure
            chatmodes_dir = project_root / ".github" / "chatmodes"
            chatmodes_dir.mkdir(parents=True)
            
            # Create test files
            test_file = chatmodes_dir / "test.md"
            test_file.write_text("# Test chatmode")
            
            # Create FileManager with mocked AIToolManager
            mock_ai_tool_manager = Mock(spec=AIToolManager)
            mock_ai_tool_manager.detect_active_tools.return_value.active_tools = ["github-copilot"]
            mock_ai_tool_manager.get_managed_files_for_tool.return_value = ManagedFileResult(
                tool_id="github-copilot",
                tool_name="GitHub Copilot",
                app_type="python-cli",
                managed_files={"chatmodes": ["test.md"]},
                total_files=1
            )
            mock_ai_tool_manager.get_available_tools.return_value = ["github-copilot"]
            
            file_manager = FileManager(mock_ai_tool_manager)
            
            # Test file discovery
            result = file_manager.discover_files(project_root)
            
            assert len(result.discovered_files) == 1
            assert result.discovered_files[0] == test_file
            assert len(result.conflicts) == 1
            assert result.conflicts[0].conflict_type == ConflictType.MANAGED_FILE_EXISTS
            assert result.conflicts[0].managed_by_tools == ["github-copilot"]
    
    def test_safe_file_deletion_integration(self):
        """Test safe file deletion with temporary filesystem."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            # Create test file
            test_file = project_root / "test.md"
            test_file.write_text("# Test file")
            
            # Test file deletion
            deletor = SafeFileDeletor()
            result = deletor.delete_files([test_file], dry_run=False)
            
            assert result.success_count == 1
            assert not test_file.exists()