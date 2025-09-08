"""Progress tracking utilities for Improved-SDD CLI.

This module provides centralized progress tracking operations using Rich library,
abstracting progress UI concerns from business logic.
"""

from typing import Callable, Optional

from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from ..core.models import ProgressInfo


class ProgressTracker:
    """Centralized progress tracking for the CLI application.

    This class provides a consistent interface for all progress operations,
    including download progress, extraction progress, and generic task progress.
    """

    def __init__(self, console: Optional[Console] = None):
        """Initialize progress tracker with Rich console."""
        self.console = console or Console()

    def create_download_progress(self) -> Progress:
        """Create a Rich Progress instance configured for download operations.

        Returns:
            Progress: Configured Progress instance with download-specific columns
        """
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=self.console,
        )

    def create_extraction_progress(self) -> Progress:
        """Create a Rich Progress instance configured for extraction operations.

        Returns:
            Progress: Configured Progress instance with extraction-specific columns
        """
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console,
        )

    def create_generic_progress(self) -> Progress:
        """Create a Rich Progress instance for generic task operations.

        Returns:
            Progress: Configured Progress instance with basic columns
        """
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=self.console,
        )

    def update_progress_from_info(self, progress: Progress, task_id: int, info: ProgressInfo) -> None:
        """Update progress task using ProgressInfo data.

        Args:
            progress: Progress instance to update
            task_id: Task ID within the progress instance
            info: ProgressInfo containing update data
        """
        # Create description from phase
        if info.phase:
            if info.phase.endswith("ing"):
                description = f"{info.phase.title()}..."
            else:
                description = f"{info.phase.title()}ing..."
        else:
            description = "Processing..."

        # Update based on the type of progress info
        if info.bytes_total > 0:
            # For download/file operations with size info
            progress.update(
                task_id,
                completed=info.bytes_completed,
                total=info.bytes_total,
                description=description,
            )
        else:
            # For indeterminate progress (bytes_total is 0)
            progress.update(
                task_id,
                description=description,
            )

    def create_callback_for_progress(self, progress: Progress, task_id: int) -> Callable[[ProgressInfo], None]:
        """Create a progress callback function for service layer operations.

        Args:
            progress: Progress instance to update
            task_id: Task ID within the progress instance

        Returns:
            Callback function that accepts ProgressInfo and updates the progress
        """

        def progress_callback(info: ProgressInfo) -> None:
            self.update_progress_from_info(progress, task_id, info)

        return progress_callback

    def run_with_progress(
        self,
        operation: Callable[[Callable[[ProgressInfo], None]], any],
        description: str = "Processing...",
        progress_type: str = "generic",
    ) -> any:
        """Run an operation with progress tracking.

        Args:
            operation: Function that accepts a progress callback and returns a result
            description: Initial description for the progress task
            progress_type: Type of progress ('download', 'extraction', 'generic')

        Returns:
            Result from the operation
        """
        # Choose appropriate progress based on type
        if progress_type == "download":
            progress_instance = self.create_download_progress()
        elif progress_type == "extraction":
            progress_instance = self.create_extraction_progress()
        else:
            progress_instance = self.create_generic_progress()

        with progress_instance as progress:
            task_id = progress.add_task(description, total=None)
            callback = self.create_callback_for_progress(progress, task_id)

            # Run the operation with the callback
            result = operation(callback)

            # Mark as completed
            progress.update(task_id, description="Complete!", completed=100, total=100)

            return result


# Global progress tracker instance
progress_tracker = ProgressTracker()
