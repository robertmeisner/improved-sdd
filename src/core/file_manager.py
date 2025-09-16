"""File Manager for file discovery and conflict detection.

This module provides the FileManager class that handles:
- File discovery across project template directories
- Conflict detection between existing files and managed files
- Safe file categorization for deletion operations
- Safe file deletion with comprehensive error handling
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Union
import logging
import os
import stat

from .ai_tool_manager import AIToolManager, ManagedFileResult


class ConflictType(Enum):
    """Types of file conflicts that can occur."""
    
    MANAGED_FILE_EXISTS = "managed_file_exists"  # File exists and is managed by active tools
    MANUAL_FILE_EXISTS = "manual_file_exists"    # File exists but not managed by any tool
    NAME_CONFLICT = "name_conflict"              # File has same name as managed file


@dataclass
class FileConflict:
    """Represents a conflict between an existing file and managed files."""
    
    file_path: Path
    file_type: str  # "chatmodes", "instructions", "prompts", "commands"
    conflict_type: ConflictType
    managed_by_tools: List[str]  # AI tool IDs that manage this file
    file_size: int
    last_modified: Optional[str] = None
    
    @property
    def is_managed(self) -> bool:
        """Check if this file is managed by any AI tools."""
        return len(self.managed_by_tools) > 0
    
    @property
    def is_manual(self) -> bool:
        """Check if this is a manual (unmanaged) file."""
        return len(self.managed_by_tools) == 0
    
    def get_relative_path(self, project_root: Path) -> str:
        """Get relative path from project root."""
        try:
            return str(self.file_path.relative_to(project_root))
        except ValueError:
            return str(self.file_path)


@dataclass
class FileDiscoveryResult:
    """Result of file discovery operation."""
    
    discovered_files: List[Path]
    conflicts: List[FileConflict]
    files_by_type: Dict[str, List[Path]]
    managed_files_found: List[Path]
    manual_files_found: List[Path]
    total_files: int
    
    @property
    def has_conflicts(self) -> bool:
        """Check if any conflicts were found."""
        return len(self.conflicts) > 0
    
    @property
    def conflict_count(self) -> int:
        """Get total number of conflicts."""
        return len(self.conflicts)
    
    def get_conflicts_by_type(self, conflict_type: ConflictType) -> List[FileConflict]:
        """Get conflicts of a specific type."""
        return [conflict for conflict in self.conflicts if conflict.conflict_type == conflict_type]


@dataclass
class DeletionAttempt:
    """Result of a single file deletion attempt."""
    
    file_path: Path
    success: bool
    error_message: Optional[str] = None
    permission_denied: bool = False
    file_not_found: bool = False
    
    @property
    def failed(self) -> bool:
        """Check if deletion failed."""
        return not self.success


@dataclass
class DeleteResult:
    """Comprehensive result of delete operation."""
    
    deleted_files: List[Path]
    skipped_files: List[Path]
    failed_deletions: List[DeletionAttempt]
    total_conflicts: int
    total_files_processed: int
    
    @property
    def success_count(self) -> int:
        """Number of successfully deleted files."""
        return len(self.deleted_files)
    
    @property
    def skip_count(self) -> int:
        """Number of skipped files."""
        return len(self.skipped_files)
    
    @property
    def failure_count(self) -> int:
        """Number of failed deletions."""
        return len(self.failed_deletions)
    
    @property
    def total_processed(self) -> int:
        """Total number of files processed."""
        return self.success_count + self.skip_count + self.failure_count
    
    @property
    def success_rate(self) -> float:
        """Success rate as percentage."""
        if self.total_processed == 0:
            return 100.0
        return (self.success_count / self.total_processed) * 100.0


class FileManager:
    """Manager for file discovery and conflict detection.
    
    This class provides functionality for:
    - Discovering files in project template directories
    - Detecting conflicts between existing files and managed files
    - Categorizing files as managed vs manual
    - Supporting safe deletion operations
    """
    
    def __init__(self, ai_tool_manager: AIToolManager):
        """Initialize FileManager with AI tool manager.
        
        Args:
            ai_tool_manager: AIToolManager instance for getting managed file lists
        """
        self.ai_tool_manager = ai_tool_manager
        self.logger = logging.getLogger(__name__)
        
        # Standard template directory structure
        self.template_directories = {
            "chatmodes": ".github/chatmodes",
            "instructions": ".github/instructions", 
            "prompts": ".github/prompts",
            "commands": ".github/commands"
        }
        
        # File extensions to scan
        self.file_extensions = {".md"}
    
    def discover_files(self, project_root: Union[str, Path], 
                      active_tools: Optional[List[str]] = None,
                      app_type: Optional[str] = None) -> FileDiscoveryResult:
        """Discover files in project template directories.
        
        Args:
            project_root: Project root directory
            active_tools: List of active AI tool IDs (if None, auto-detect)
            app_type: Optional app type filter
            
        Returns:
            FileDiscoveryResult with discovered files and conflicts
        """
        project_path = Path(project_root)
        
        # Auto-detect active tools if not provided
        if active_tools is None:
            if app_type:
                active_tools = self.ai_tool_manager.get_active_tools_for_app_type(app_type, project_root)
            else:
                active_result = self.ai_tool_manager.detect_active_tools(project_root)
                active_tools = active_result.active_tools
        
        # Get managed files for active tools
        managed_files_map = self._build_managed_files_map(active_tools, app_type)
        
        # Discover actual files
        discovered_files = []
        files_by_type = {file_type: [] for file_type in self.template_directories.keys()}
        
        for file_type, dir_path in self.template_directories.items():
            type_path = project_path / dir_path
            if type_path.exists() and type_path.is_dir():
                for file_path in type_path.iterdir():
                    if file_path.is_file() and file_path.suffix in self.file_extensions:
                        discovered_files.append(file_path)
                        files_by_type[file_type].append(file_path)
        
        # Detect conflicts
        conflicts = self._detect_conflicts(discovered_files, managed_files_map, project_path)
        
        # Categorize files
        managed_files_found = []
        manual_files_found = []
        
        for conflict in conflicts:
            if conflict.is_managed:
                managed_files_found.append(conflict.file_path)
            else:
                manual_files_found.append(conflict.file_path)
        
        return FileDiscoveryResult(
            discovered_files=discovered_files,
            conflicts=conflicts,
            files_by_type=files_by_type,
            managed_files_found=managed_files_found,
            manual_files_found=manual_files_found,
            total_files=len(discovered_files)
        )
    
    def detect_conflicts_for_tools(self, project_root: Union[str, Path],
                                  tool_ids: List[str], 
                                  app_type: Optional[str] = None) -> List[FileConflict]:
        """Detect conflicts for specific AI tools.
        
        Args:
            project_root: Project root directory
            tool_ids: List of AI tool IDs to check
            app_type: Optional app type filter
            
        Returns:
            List of FileConflict objects
        """
        result = self.discover_files(project_root, tool_ids, app_type)
        return result.conflicts
    
    def get_managed_files_to_delete(self, project_root: Union[str, Path],
                                   tool_ids: List[str],
                                   app_type: Optional[str] = None) -> List[Path]:
        """Get list of managed files that can be safely deleted.
        
        Args:
            project_root: Project root directory
            tool_ids: List of AI tool IDs
            app_type: Optional app type filter
            
        Returns:
            List of file paths that are managed and can be deleted
        """
        result = self.discover_files(project_root, tool_ids, app_type)
        
        # Return only files that are managed by the specified tools
        managed_files = []
        for conflict in result.conflicts:
            if conflict.conflict_type == ConflictType.MANAGED_FILE_EXISTS:
                # Only include if managed by one of the specified tools
                if any(tool_id in tool_ids for tool_id in conflict.managed_by_tools):
                    managed_files.append(conflict.file_path)
        
        return managed_files
    
    def get_manual_files(self, project_root: Union[str, Path]) -> List[Path]:
        """Get list of manual (unmanaged) files that should be preserved.
        
        Args:
            project_root: Project root directory
            
        Returns:
            List of file paths that are manual and should be preserved
        """
        result = self.discover_files(project_root)
        return result.manual_files_found
    
    def _build_managed_files_map(self, tool_ids: List[str], 
                                app_type: Optional[str] = None) -> Dict[str, Set[str]]:
        """Build map of managed files by file type.
        
        Args:
            tool_ids: List of AI tool IDs
            app_type: Optional app type filter
            
        Returns:
            Dictionary mapping file types to sets of managed file names
        """
        managed_files_map = {file_type: set() for file_type in self.template_directories.keys()}
        
        for tool_id in tool_ids:
            try:
                result = self.ai_tool_manager.get_managed_files_for_tool(tool_id, app_type)
                for file_type, files in result.managed_files.items():
                    if file_type in managed_files_map:
                        managed_files_map[file_type].update(files)
            except Exception as e:
                self.logger.warning(f"Failed to get managed files for tool {tool_id}: {e}")
        
        return managed_files_map
    
    def _detect_conflicts(self, discovered_files: List[Path],
                         managed_files_map: Dict[str, Set[str]],
                         project_root: Path) -> List[FileConflict]:
        """Detect conflicts between discovered files and managed files.
        
        Args:
            discovered_files: List of discovered file paths
            managed_files_map: Map of file types to managed file names
            project_root: Project root directory
            
        Returns:
            List of FileConflict objects
        """
        conflicts = []
        
        for file_path in discovered_files:
            file_name = file_path.name
            file_type = self._get_file_type(file_path, project_root)
            
            if not file_type:
                continue
            
            # Check if this file is managed by any tools
            managed_by_tools = []
            if file_name in managed_files_map.get(file_type, set()):
                # Find which tools manage this file
                for tool_id in self.ai_tool_manager.get_available_tools():
                    try:
                        result = self.ai_tool_manager.get_managed_files_for_tool(tool_id)
                        tool_files = result.managed_files.get(file_type, [])
                        if file_name in tool_files:
                            managed_by_tools.append(tool_id)
                    except Exception:
                        continue
            
            # Determine conflict type
            if managed_by_tools:
                conflict_type = ConflictType.MANAGED_FILE_EXISTS
            else:
                conflict_type = ConflictType.MANUAL_FILE_EXISTS
            
            # Get file info
            try:
                file_size = file_path.stat().st_size
                last_modified = file_path.stat().st_mtime
                last_modified_str = str(last_modified)
            except Exception:
                file_size = 0
                last_modified_str = None
            
            conflict = FileConflict(
                file_path=file_path,
                file_type=file_type,
                conflict_type=conflict_type,
                managed_by_tools=managed_by_tools,
                file_size=file_size,
                last_modified=last_modified_str
            )
            
            conflicts.append(conflict)
        
        return conflicts
    
    def safe_delete_files(self, files_to_delete: List[Path], dry_run: bool = False) -> DeleteResult:
        """Safely delete files using the SafeFileDeletor.
        
        Args:
            files_to_delete: List of file paths to delete
            dry_run: If True, only simulate deletion
            
        Returns:
            DeleteResult with comprehensive deletion statistics
        """
        deletor = SafeFileDeletor()
        return deletor.delete_files(files_to_delete, dry_run)
    
    def _get_file_type(self, file_path: Path, project_root: Path) -> Optional[str]:
        """Determine the file type based on the file path.
        
        Args:
            file_path: Path to the file
            project_root: Project root directory
            
        Returns:
            File type string or None if not in a template directory
        """
        try:
            relative_path = file_path.relative_to(project_root)
            path_parts = relative_path.parts
            
            # Check if file is in one of our template directories
            for file_type, dir_path in self.template_directories.items():
                dir_parts = Path(dir_path).parts
                if len(path_parts) >= len(dir_parts):
                    if path_parts[:len(dir_parts)] == dir_parts:
                        return file_type
            
            return None
        except ValueError:
            return None


class SafeFileDeletor:
    """Result of a single file deletion attempt."""
    
class SafeFileDeletor:
    """Safe file deletion engine with comprehensive error handling."""
    
    def __init__(self):
        """Initialize safe file deletor."""
        self.logger = logging.getLogger(__name__)
    
    def delete_files(self, files_to_delete: List[Path], dry_run: bool = False) -> DeleteResult:
        """Safely delete a list of files with comprehensive error handling.
        
        Args:
            files_to_delete: List of file paths to delete
            dry_run: If True, only simulate deletion without actually deleting
            
        Returns:
            DeleteResult with comprehensive deletion statistics
        """
        deleted_files = []
        failed_deletions = []
        
        self.logger.info(f"Starting {'dry run' if dry_run else 'deletion'} of {len(files_to_delete)} files")
        
        for file_path in files_to_delete:
            attempt = self._delete_single_file(file_path, dry_run)
            
            if attempt.success:
                deleted_files.append(file_path)
                self.logger.info(f"{'Would delete' if dry_run else 'Deleted'}: {file_path}")
            else:
                failed_deletions.append(attempt)
                self.logger.error(f"Failed to delete {file_path}: {attempt.error_message}")
        
        result = DeleteResult(
            deleted_files=deleted_files,
            skipped_files=[],  # No skips in this method
            failed_deletions=failed_deletions,
            total_conflicts=0,  # Not applicable here
            total_files_processed=len(files_to_delete)
        )
        
        self.logger.info(
            f"Deletion {'simulation' if dry_run else 'operation'} complete: "
            f"{result.success_count} succeeded, {result.failure_count} failed"
        )
        
        return result
    
    def _delete_single_file(self, file_path: Path, dry_run: bool = False) -> DeletionAttempt:
        """Safely delete a single file with comprehensive error handling.
        
        Args:
            file_path: Path to file to delete
            dry_run: If True, only simulate deletion
            
        Returns:
            DeletionAttempt with result details
        """
        try:
            # Validate path
            if not self._validate_file_path(file_path):
                return DeletionAttempt(
                    file_path=file_path,
                    success=False,
                    error_message="Invalid file path - potential security risk"
                )
            
            # Check if file exists
            if not file_path.exists():
                return DeletionAttempt(
                    file_path=file_path,
                    success=False,
                    error_message="File does not exist",
                    file_not_found=True
                )
            
            # Check if it's actually a file (not directory)
            if not file_path.is_file():
                return DeletionAttempt(
                    file_path=file_path,
                    success=False,
                    error_message="Path is not a file"
                )
            
            # Check permissions
            if not self._check_file_permissions(file_path):
                return DeletionAttempt(
                    file_path=file_path,
                    success=False,
                    error_message="Insufficient permissions to delete file",
                    permission_denied=True
                )
            
            # Perform deletion (or simulate)
            if not dry_run:
                file_path.unlink()
            
            return DeletionAttempt(
                file_path=file_path,
                success=True
            )
            
        except PermissionError as e:
            return DeletionAttempt(
                file_path=file_path,
                success=False,
                error_message=f"Permission denied: {str(e)}",
                permission_denied=True
            )
        except FileNotFoundError as e:
            return DeletionAttempt(
                file_path=file_path,
                success=False,
                error_message=f"File not found: {str(e)}",
                file_not_found=True
            )
        except OSError as e:
            return DeletionAttempt(
                file_path=file_path,
                success=False,
                error_message=f"OS error: {str(e)}"
            )
        except Exception as e:
            return DeletionAttempt(
                file_path=file_path,
                success=False,
                error_message=f"Unexpected error: {str(e)}"
            )
    
    def _validate_file_path(self, file_path: Path) -> bool:
        """Validate file path for security.
        
        Args:
            file_path: Path to validate
            
        Returns:
            True if path is safe, False otherwise
        """
        try:
            # Convert to absolute path to resolve any relative components
            abs_path = file_path.resolve()
            
            # Check for directory traversal attempts
            if ".." in str(abs_path):
                return False
            
            # Path should exist within reasonable bounds (not system directories)
            path_str = str(abs_path).lower()
            
            # Block system directories on Windows
            system_dirs = ["c:\\windows", "c:\\program files", "c:\\system32"]
            for sys_dir in system_dirs:
                if path_str.startswith(sys_dir):
                    return False
            
            # Block system directories on Unix-like systems
            unix_dirs = ["/bin", "/sbin", "/usr/bin", "/usr/sbin", "/etc", "/boot"]
            for unix_dir in unix_dirs:
                if path_str.startswith(unix_dir):
                    return False
            
            return True
            
        except Exception:
            # If we can't resolve or validate the path, err on the side of caution
            return False
    
    def _check_file_permissions(self, file_path: Path) -> bool:
        """Check if we have permission to delete the file.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if we can delete the file, False otherwise
        """
        try:
            # Check if parent directory is writable
            parent = file_path.parent
            if not os.access(parent, os.W_OK):
                return False
            
            # Check if file is writable (or if we can change its permissions)
            if not os.access(file_path, os.W_OK):
                # Try to check if we can modify permissions
                try:
                    current_stat = file_path.stat()
                    # If file is read-only, we might still be able to delete it
                    # depending on directory permissions, so we'll allow it
                    return True
                except Exception:
                    return False
            
            return True
            
        except Exception:
            return False
