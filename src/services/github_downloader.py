"""GitHub downloader service for template downloading with progress reporting.

This module provides the GitHubDownloader class which handles downloading
templates from GitHub repositories with comprehensive error handling,
progress reporting, and security validation.
"""

import shutil
import tempfile
import time
from pathlib import Path
from typing import Callable, Optional

# Lazy imports for heavy dependencies
try:
    import httpx

    HTTPX_AVAILABLE = True
except ImportError:
    httpx = None
    HTTPX_AVAILABLE = False

try:
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

    RICH_AVAILABLE = True
except ImportError:
    Console = None
    Progress = None
    SpinnerColumn = None
    TextColumn = None
    BarColumn = None
    DownloadColumn = None
    TransferSpeedColumn = None
    TimeRemainingColumn = None
    RICH_AVAILABLE = False

from src.core.exceptions import (
    GitHubAPIError,
    NetworkError,
    TemplateError,
    TimeoutError,
)
from src.core.interfaces import GitHubDownloaderProtocol
from src.core.models import ProgressInfo, TemplateSource, TemplateSourceType


class GitHubDownloader(GitHubDownloaderProtocol):
    """Handles downloading templates from GitHub repository with progress reporting."""

    def __init__(self, repo_owner: str = "robertmeisner", repo_name: str = "improved-sdd"):
        """Initialize GitHub downloader.

        Args:
            repo_owner: GitHub repository owner
            repo_name: GitHub repository name
        """
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.base_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"

    async def download_templates(
        self,
        target_dir: Path,
        progress_callback: Optional[Callable[[ProgressInfo], None]] = None,
        progress_instance: Optional[Progress] = None,
    ) -> TemplateSource:
        """Download templates from GitHub repository's /templates folder.

        Args:
            target_dir: Directory to download templates to
            progress_callback: Optional callback for detailed progress updates
            progress_instance: Optional Rich Progress instance from UI layer

        Returns:
            TemplateSource: Information about the downloaded templates

        Raises:
            GitHubAPIError: If GitHub API request fails
            NetworkError: If network operation fails
            TimeoutError: If download times out
        """
        if not HTTPX_AVAILABLE:
            raise TemplateError(
                "httpx library is required for GitHub downloads. Install with: pip install httpx"
            )

        if not RICH_AVAILABLE:
            raise TemplateError(
                "rich library is required for progress display. Install with: pip install rich"
            )

        console = Console()

        # Ensure target directory exists
        target_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Download repository archive
            archive_url = (
                f"https://github.com/{self.repo_owner}/{self.repo_name}/archive/refs/heads/main.zip"
            )

            # Setup progress tracking - use provided instance or create new one
            if progress_instance:
                # Use provided progress instance from UI layer
                progress = progress_instance
                download_task = progress.add_task("Downloading templates...", total=None)

                # Perform download
                temp_path = await self._download_with_progress(
                    progress, download_task, archive_url, progress_callback
                )

                # Extract templates
                progress.update(download_task, description="Validating and extracting templates...")
                self.extract_templates(temp_path, target_dir, progress_callback)

                # Cleanup and finalize
                try:
                    temp_path.unlink()
                except OSError:
                    pass  # Ignore cleanup errors

                total_size = sum(f.stat().st_size for f in target_dir.rglob("*") if f.is_file())
                progress.update(
                    download_task,
                    description="Download complete!",
                    completed=total_size,
                    total=total_size,
                )

                return TemplateSource(
                    path=target_dir, source_type=TemplateSourceType.GITHUB, size_bytes=total_size
                )
            else:
                # Create own progress instance (existing behavior)
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    DownloadColumn(),
                    TransferSpeedColumn(),
                    TimeRemainingColumn(),
                    console=console,
                ) as progress:
                    download_task = progress.add_task("Downloading templates...", total=None)

                    # Perform download
                    temp_path = await self._download_with_progress(
                        progress, download_task, archive_url, progress_callback
                    )

                    # Extract templates
                    progress.update(
                        download_task, description="Validating and extracting templates..."
                    )
                    self.extract_templates(temp_path, target_dir, progress_callback)

                    # Cleanup and finalize
                    try:
                        temp_path.unlink()
                    except OSError:
                        pass  # Ignore cleanup errors

                    total_size = sum(f.stat().st_size for f in target_dir.rglob("*") if f.is_file())
                    progress.update(
                        download_task,
                        description="Download complete!",
                        completed=total_size,
                        total=total_size,
                    )

                    return TemplateSource(
                        path=target_dir,
                        source_type=TemplateSourceType.GITHUB,
                        size_bytes=total_size,
                    )

        except httpx.TimeoutException:
            raise TimeoutError("Download timed out")
        except httpx.RequestError as e:
            raise NetworkError(f"Network error during download: {e}")
        except Exception as e:
            if isinstance(e, (TemplateError, NetworkError, GitHubAPIError, TimeoutError)):
                raise
            raise TemplateError(f"Unexpected error during template download: {e}")

    async def _download_with_progress(
        self,
        progress: Progress,
        download_task: int,
        archive_url: str,
        progress_callback: Optional[Callable[[ProgressInfo], None]] = None,
    ) -> Path:
        """Helper method to perform the actual download with progress tracking.

        Args:
            progress: Progress instance to update
            download_task: Task ID in progress instance
            archive_url: URL to download from
            progress_callback: Optional callback for progress updates

        Returns:
            Path to downloaded temporary file
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Use the streaming response directly from client.stream
            async with client.stream("GET", archive_url) as response:
                # Response.status_code is expected to be an int by tests/mocks
                if response.status_code != 200:
                    raise GitHubAPIError(
                        f"Failed to download repository: HTTP {response.status_code}",
                        response.status_code,
                    )

                # Get content length for progress tracking
                total_size = int(response.headers.get("content-length", 0))
                if total_size > 0:
                    progress.update(download_task, total=total_size)

                # Download to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_file:
                    temp_path = Path(temp_file.name)
                    downloaded = 0
                    start_time = time.time()

                    # Iterate over streamed bytes
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        temp_file.write(chunk)
                        downloaded += len(chunk)
                        progress.update(download_task, completed=downloaded)

                        # Enhanced progress callback
                        if progress_callback and total_size > 0:
                            elapsed_time = time.time() - start_time
                            if elapsed_time > 0:
                                speed_bps = int(downloaded / elapsed_time)
                                remaining_bytes = total_size - downloaded
                                eta_seconds = (
                                    int(remaining_bytes / speed_bps) if speed_bps > 0 else None
                                )
                            else:
                                speed_bps = None
                                eta_seconds = None

                            progress_info = ProgressInfo(
                                phase="download",
                                bytes_completed=downloaded,
                                bytes_total=total_size,
                                percentage=(downloaded / total_size) * 100,
                                speed_bps=speed_bps,
                                eta_seconds=eta_seconds,
                            )
                            progress_callback(progress_info)

                    return temp_path

    def extract_templates(
        self,
        zip_path: Path,
        target_dir: Path,
        progress_callback: Optional[Callable[[ProgressInfo], None]] = None,
    ) -> None:
        """Extract templates from ZIP archive with validation and security checks.

        Args:
            zip_path: Path to the downloaded ZIP file
            target_dir: Directory to extract templates to
            progress_callback: Optional callback for extraction progress updates

        Raises:
            TemplateError: If ZIP is invalid or templates are missing
        """
        # Step 1: ZIP integrity validation
        self._validate_zip_integrity(zip_path)
        # Step 2: Extract with path traversal protection
        extracted_files = self._extract_with_protection(zip_path, target_dir, progress_callback)

        # Convert extracted zip-relative names to template-relative paths for validation
        templates_prefix = f"{self.repo_name}-main/sdd_templates/"
        relative_files = [
            name[len(templates_prefix) :]
            for name in extracted_files
            if name.startswith(templates_prefix)
        ]

        # Step 3: Template structure validation (expects relative paths like 'chatmodes/..')
        self._validate_template_structure(target_dir, relative_files)

    def _validate_zip_integrity(self, zip_path: Path) -> None:
        """Validate ZIP file integrity before extraction.

        Args:
            zip_path: Path to ZIP file to validate

        Raises:
            TemplateError: If ZIP is corrupted or invalid
        """
        # Lazy import zipfile when needed
        import zipfile

        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                # Test ZIP integrity
                bad_file = zip_ref.testzip()
                if bad_file:
                    raise TemplateError(f"Corrupted ZIP file detected: {bad_file}")

                # Validate ZIP has content
                if not zip_ref.namelist():
                    raise TemplateError("ZIP file is empty")

                # Check for sdd_templates folder
                templates_prefix = f"{self.repo_name}-main/sdd_templates/"
                template_files = [
                    name for name in zip_ref.namelist() if name.startswith(templates_prefix)
                ]

                if not template_files:
                    raise TemplateError("No sdd_templates folder found in repository archive")

        except zipfile.BadZipFile:
            raise TemplateError("Downloaded file is not a valid ZIP archive")
        except Exception as e:
            if isinstance(e, TemplateError):
                raise
            raise TemplateError(f"Failed to validate ZIP file: {e}")

    def _extract_with_protection(
        self,
        zip_path: Path,
        target_dir: Path,
        progress_callback: Optional[Callable[[ProgressInfo], None]] = None,
    ) -> list[str]:
        """Extract ZIP contents with path traversal protection.

        Args:
            zip_path: Path to ZIP file
            target_dir: Target extraction directory
            progress_callback: Optional callback for extraction progress

        Returns:
            List of extracted file paths (including sdd_templates prefix)

        Raises:
            TemplateError: If extraction fails or path traversal detected
        """
        # Lazy import zipfile when needed
        import zipfile

        extracted_files = []

        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                templates_prefix = f"{self.repo_name}-main/sdd_templates/"
                template_files = [
                    name for name in zip_ref.namelist() if name.startswith(templates_prefix)
                ]

                # Calculate total extraction size for progress tracking
                total_files = len([f for f in template_files if not zip_ref.getinfo(f).is_dir()])
                extracted_count = 0

                for file_path in template_files:
                    # Remove prefix to get relative path
                    relative_path = file_path[len(templates_prefix) :]
                    if not relative_path:  # Skip the sdd_templates/ directory itself
                        continue

                    # Path traversal protection
                    safe_path = self._validate_safe_path(relative_path, target_dir)

                    # Extract file info
                    file_info = zip_ref.getinfo(file_path)

                    # Skip directories
                    if file_info.is_dir():
                        safe_path.mkdir(parents=True, exist_ok=True)
                        continue

                    # Create parent directories
                    safe_path.parent.mkdir(parents=True, exist_ok=True)

                    # Extract file content
                    with zip_ref.open(file_info) as source, open(safe_path, "wb") as target:
                        shutil.copyfileobj(source, target)

                    # Append original zip entry name (including sdd_templates prefix)
                    extracted_files.append(file_path)
                    extracted_count += 1

                    # Report extraction progress
                    if progress_callback and total_files > 0:
                        progress_info = ProgressInfo(
                            phase="extract",
                            bytes_completed=extracted_count,
                            bytes_total=total_files,
                            percentage=(extracted_count / total_files) * 100,
                        )
                        progress_callback(progress_info)

                return extracted_files

        except Exception as e:
            if isinstance(e, TemplateError):
                raise
            raise TemplateError(f"Failed to extract templates: {e}")

    def _validate_safe_path(self, relative_path: str, target_dir: Path) -> Path:
        """Validate that a path is safe and doesn't escape the target directory.

        Args:
            relative_path: Relative path from ZIP archive
            target_dir: Target extraction directory

        Returns:
            Validated absolute path

        Raises:
            TemplateError: If path traversal attempt detected
        """
        # Normalize path and resolve any .. or . components
        safe_path = (target_dir / relative_path).resolve()

        # Ensure the resolved path is within target directory
        try:
            safe_path.relative_to(target_dir.resolve())
        except ValueError:
            raise TemplateError(f"Path traversal attempt detected: {relative_path}")

        return safe_path

    def _validate_template_structure(self, target_dir: Path, extracted_files: list[str]) -> None:
        """Validate that extracted templates have expected structure.

        Args:
            target_dir: Directory containing extracted templates
            extracted_files: List of extracted file paths

        Raises:
            TemplateError: If template structure is invalid
        """
        if not extracted_files:
            raise TemplateError("No template files were extracted")

        # Check for expected template directories
        expected_dirs = {"chatmodes", "commands", "instructions", "prompts"}
        found_dirs = set()

        for file_path in extracted_files:
            # Get top-level directory
            parts = Path(file_path).parts
            if parts:
                found_dirs.add(parts[0])

        # Validate at least some expected directories exist
        if not found_dirs.intersection(expected_dirs):
            raise TemplateError(
                f"Invalid template structure. Expected directories: {', '.join(expected_dirs)}, "
                f"found: {', '.join(found_dirs) if found_dirs else 'none'}"
            )

        # Check for minimum file count
        if len(extracted_files) < 3:
            raise TemplateError(
                f"Too few template files extracted: {len(extracted_files)}. Expected at least 3 files."
            )

        # Validate file sizes (basic check for empty files)
        empty_files = []
        for file_path in extracted_files:
            full_path = target_dir / file_path
            if full_path.is_file() and full_path.stat().st_size == 0:
                empty_files.append(file_path)

        if len(empty_files) > len(extracted_files) // 2:  # More than half are empty
            raise TemplateError(
                f"Too many empty template files detected: {len(empty_files)}/{len(extracted_files)}"
            )
