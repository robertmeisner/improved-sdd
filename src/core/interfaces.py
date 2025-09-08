"""Protocol definitions for service layer dependency injection.

This module defines the interfaces (protocols) that services must implement
to enable clean dependency injection and testing isolation.
"""

from pathlib import Path
from typing import Callable, Optional, Protocol, runtime_checkable

from .models import ProgressInfo, TemplateResolutionResult, TemplateSource


@runtime_checkable
class FileTrackerProtocol(Protocol):
    """Protocol for tracking file operations during installation."""

    def track_file_creation(self, filepath: Path) -> None:
        """Track a file that was created.

        Args:
            filepath: Path to the created file
        """
        ...

    def track_file_modification(self, filepath: Path) -> None:
        """Track a file that was modified.

        Args:
            filepath: Path to the modified file
        """
        ...

    def track_dir_creation(self, dirpath: Path) -> None:
        """Track a directory that was created.

        Args:
            dirpath: Path to the created directory
        """
        ...

    def get_summary(self) -> str:
        """Get a formatted summary of all tracked changes.

        Returns:
            Rich-formatted string with file operation summary
        """
        ...


@runtime_checkable
class CacheManagerProtocol(Protocol):
    """Protocol for managing temporary cache directories."""

    def create_cache_dir(self) -> Path:
        """Create a temporary cache directory.

        Returns:
            Path to the created cache directory

        Raises:
            OSError: If cache directory creation fails
        """
        ...

    def cleanup_cache(self, cache_dir: Path) -> None:
        """Clean up a specific cache directory.

        Args:
            cache_dir: Path to cache directory to cleanup
        """
        ...

    def cleanup_all_caches(self) -> None:
        """Clean up all tracked cache directories."""
        ...

    def cleanup_orphaned_caches(self) -> int:
        """Clean up orphaned cache directories from previous runs.

        Returns:
            Number of orphaned caches cleaned up
        """
        ...
        ...

    def get_cache_info(self, cache_dir: Path) -> dict:
        """Get information about a cache directory.

        Args:
            cache_dir: Path to cache directory

        Returns:
            Dictionary with cache directory info
        """
        ...


@runtime_checkable
class GitHubDownloaderProtocol(Protocol):
    """Protocol for downloading templates from GitHub."""

    async def download_templates(
        self, target_dir: Path, progress_callback: Optional[Callable[[ProgressInfo], None]] = None
    ) -> TemplateSource:
        """Download templates from GitHub repository.

        Args:
            target_dir: Directory to download templates to
            progress_callback: Optional callback for progress updates

        Returns:
            TemplateSource with download information

        Raises:
            GitHubAPIError: If GitHub API request fails
            NetworkError: If network operation fails
            TimeoutError: If download times out
        """
        ...


@runtime_checkable
class TemplateResolverProtocol(Protocol):
    """Protocol for resolving template sources with priority system."""

    def get_local_templates_path(self) -> Optional[Path]:
        """Check for local .sdd_templates directory.

        Returns:
            Path to local templates if found, None otherwise
        """
        ...

    def has_bundled_templates(self) -> bool:
        """Check if bundled templates are available.

        Returns:
            True if bundled templates exist
        """
        ...

    def resolve_templates_with_transparency(self) -> TemplateResolutionResult:
        """Resolve templates using priority system with detailed logging.

        Returns:
            TemplateResolutionResult with resolution details and transparency info
        """
        ...


class ConsoleProtocol(Protocol):
    """Protocol for console operations and Rich UI components."""

    def print(self, *args, **kwargs) -> None:
        """Print to console with Rich formatting support.

        Args:
            *args: Arguments to print
            **kwargs: Keyword arguments for Rich console.print()
        """
        ...

    def print_success(self, message: str) -> None:
        """Print a success message with green styling.

        Args:
            message: Success message to display
        """
        ...

    def print_warning(self, message: str) -> None:
        """Print a warning message with yellow styling.

        Args:
            message: Warning message to display
        """
        ...

    def print_error(self, message: str) -> None:
        """Print an error message with red styling.

        Args:
            message: Error message to display
        """
        ...

    def show_panel(self, content: str, title: str, style: str = "cyan") -> None:
        """Display content in a Rich panel.

        Args:
            content: Content to display in the panel
            title: Panel title
            style: Panel border style
        """
        ...

    def show_banner(self) -> None:
        """Display the application banner."""
        ...


class ProgressTrackerProtocol(Protocol):
    """Protocol for progress tracking and reporting."""

    def create_download_progress(self) -> object:
        """Create a progress tracker for downloads.

        Returns:
            Progress object for tracking download progress
        """
        ...

    def update_progress(self, progress: object, task_id: int, info: ProgressInfo) -> None:
        """Update progress tracker with new information.

        Args:
            progress: Progress tracker object
            task_id: ID of the task being tracked
            info: Progress information to update
        """
        ...


class ServiceContainerProtocol(Protocol):
    """Protocol for dependency injection container."""

    def register(self, interface: type, implementation: object) -> None:
        """Register a service implementation for an interface.

        Args:
            interface: Protocol interface type
            implementation: Service implementation instance
        """
        ...

    def get(self, interface: type) -> object:
        """Get a service implementation for an interface.

        Args:
            interface: Protocol interface type

        Returns:
            Service implementation instance

        Raises:
            KeyError: If interface is not registered
        """
        ...

    def has(self, interface: type) -> bool:
        """Check if an interface is registered.

        Args:
            interface: Protocol interface type

        Returns:
            True if interface is registered
        """
        ...
