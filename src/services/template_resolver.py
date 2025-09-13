"""Template resolver service for handling template source resolution.

This module provides the TemplateResolver class which implements a priority-based
template resolution system: local templates > bundled templates > GitHub download.
It also supports merging local templates with downloaded ones to create complete sets.
"""

import asyncio
from pathlib import Path
from typing import Optional

from src.core.config import DEFAULT_GITHUB_BRANCH, DEFAULT_GITHUB_REPO, DOWNLOAD_TEMPLATES_DIR, LOCAL_TEMPLATES_DIR
from src.core.exceptions import GitHubAPIError, NetworkError, RateLimitError, TimeoutError, ValidationError
from src.core.models import MergedTemplateSource, TemplateResolutionResult, TemplateSource, TemplateSourceType

from .cache_manager import CacheManager
from .github_downloader import GitHubDownloader


def _get_console():
    """Lazy import and return rich console."""
    from rich.console import Console

    return Console()


def _get_panel():
    """Lazy import and return rich Panel."""
    from rich.panel import Panel

    return Panel


class TemplateResolver:
    """Handles template resolution with priority-based system:
    local templates > bundled templates > GitHub download."""

    def __init__(
        self,
        project_path: Path,
        offline: bool = False,
        force_download: bool = False,
        template_repo: Optional[str] = None,
    ):
        """Initialize the resolver for a specific project path.

        Args:
            project_path: The target project directory where templates will be installed
            offline: If True, disable GitHub downloads and use only local/bundled templates
            force_download: If True, bypass local templates and force GitHub download
            template_repo: Custom GitHub repository for templates (format: "owner/repo")
        """
        self.project_path = project_path
        self.script_dir = Path(__file__).parent
        self.offline = offline
        self.force_download = force_download
        self.template_repo = template_repo

        # Parse custom repository if provided
        if template_repo:
            self.github_downloader = GitHubDownloader.from_repo_string(template_repo)
        else:
            self.github_downloader = GitHubDownloader()

        self.cache_manager = CacheManager()

        # Clean up orphaned caches on startup
        self.cache_manager.cleanup_orphaned_caches()

    # Template structure constants
    REQUIRED_TEMPLATE_TYPES = {"chatmodes", "instructions", "prompts", "commands"}

    def get_available_template_files(self, templates_path: Path) -> dict[str, set[str]]:
        """Get all available template files organized by template type.

        Args:
            templates_path: Path to templates directory

        Returns:
            Dict mapping template types to sets of available filenames
            e.g., {'prompts': {'file1.prompt.md', 'file2.prompt.md'}, 'chatmodes': {'mode1.chatmode.md'}}
        """
        if not templates_path.exists() or not templates_path.is_dir():
            return {}

        available_files = {}
        for template_type in self.REQUIRED_TEMPLATE_TYPES:
            type_dir = templates_path / template_type
            if type_dir.exists() and type_dir.is_dir():
                # Get all .md files in this template type directory
                md_files = {f.name for f in type_dir.glob("*.md")}
                if md_files:  # Only include if there are actual files
                    available_files[template_type] = md_files
        return available_files

    def get_missing_template_files(self, templates_path: Path, reference_path: Path) -> dict[str, set[str]]:
        """Get template files that are missing compared to a reference template set.

        Args:
            templates_path: Path to templates directory to check
            reference_path: Path to reference templates (e.g., bundled or downloaded)

        Returns:
            Dict mapping template types to sets of missing filenames
        """
        available_files = self.get_available_template_files(templates_path)
        reference_files = self.get_available_template_files(reference_path)

        missing_files = {}
        for template_type, ref_files in reference_files.items():
            local_files = available_files.get(template_type, set())
            missing = ref_files - local_files
            if missing:
                missing_files[template_type] = missing

        # Also include entire template types that are missing locally
        for template_type in self.REQUIRED_TEMPLATE_TYPES:
            if template_type not in available_files and template_type in reference_files:
                missing_files[template_type] = reference_files[template_type]

        return missing_files

    def get_local_templates_path(self) -> Optional[Path]:
        """Check for local templates directory in project or parent directories.

        Returns:
            Path to local templates directory if found, None otherwise
        """
        # Check current project directory first
        local_path = self.project_path / LOCAL_TEMPLATES_DIR
        if local_path.exists() and local_path.is_dir():
            return local_path

        # Check parent directories up to filesystem root
        current_path = self.project_path.parent
        while current_path != current_path.parent:  # Stop at filesystem root
            local_path = current_path / LOCAL_TEMPLATES_DIR
            if local_path.exists() and local_path.is_dir():
                return local_path
            current_path = current_path.parent

        return None

    def get_bundled_templates_path(self) -> Optional[Path]:
        """Get path to bundled templates directory.

        Returns:
            Path to bundled templates if they exist, None otherwise
        """
        bundled_path = self.script_dir.parent / LOCAL_TEMPLATES_DIR
        if bundled_path.exists() and bundled_path.is_dir():
            return bundled_path
        return None

    def resolve_templates_source(self) -> Optional[Path]:
        """Resolve template source using priority system.

        Priority order:
        1. Local templates (project or parent directories)
        2. Bundled templates directory
        3. GitHub download to temporary cache

        Returns:
            Path to templates source, None if no source found
        """
        # Priority 1: Local templates
        local_path = self.get_local_templates_path()
        if local_path:
            return local_path

        # Priority 2: Bundled templates
        bundled_path = self.get_bundled_templates_path()
        if bundled_path:
            return bundled_path

        # Priority 3: GitHub download
        try:
            return self._download_github_templates()
        except (NetworkError, GitHubAPIError, TimeoutError, ValidationError) as e:
            _get_console().print(f"[yellow]⚠ Could not download templates from GitHub: {e}[/yellow]")
            return None
        except Exception as e:
            _get_console().print(f"[yellow]⚠ Unexpected error during GitHub download: {e}[/yellow]")
            return None

    def resolve_templates_with_transparency(self) -> TemplateResolutionResult:
        """Resolve template source with full transparency and logging, respecting CLI options.

        New behavior: If user has local templates, use those and download
        only the missing template types. This creates a union of local + downloaded templates.

        Returns:
            TemplateResolutionResult with detailed information about resolution
        """
        # Force download mode - skip local and bundled templates
        if self.force_download:
            if self.offline:
                _get_console().print("[red]✗ Cannot force download in offline mode[/red]")
                return TemplateResolutionResult(
                    source=None,
                    success=False,
                    message="Cannot force download in offline mode",
                    fallback_attempted=False,
                )

            _get_console().print("[blue]⬇ Force download mode - downloading from GitHub...[/blue]")
            return self._attempt_github_download()

        # Check for local templates and determine what's needed
        local_path = self.get_local_templates_path()
        if local_path:
            local_files = self.get_available_template_files(local_path)

            if not local_files:
                # Local templates exist but are empty - proceed with normal fallback
                pass
            else:
                # We have some local files - need to determine what's missing
                if self.offline:
                    # In offline mode, use whatever local files we have
                    total_local_files = sum(len(files) for files in local_files.values())
                    _get_console().print(
                        f"[cyan]ℹ Using {total_local_files} local template files in offline mode[/cyan]"
                    )

                    source = TemplateSource(
                        path=local_path,
                        source_type=TemplateSourceType.LOCAL,
                        size_bytes=self._get_directory_size(local_path),
                    )
                    return TemplateResolutionResult(
                        source=source,
                        success=True,
                        message=f"Using {total_local_files} local template files",
                        fallback_attempted=False,
                    )
                else:
                    # Online mode - merge with downloaded templates
                    _get_console().print(f"[cyan]ℹ Found local template files in {len(local_files)} categories[/cyan]")
                    for template_type, files in local_files.items():
                        _get_console().print(f"  {template_type}: {len(files)} files")

                    _get_console().print(
                        f"[blue]⬇ Downloading complete template set to merge with local files...[/blue]"
                    )
                    return self._attempt_file_level_merge(local_path, local_files)

        # No local templates - fall back to existing logic
        # Fallback to bundled templates
        bundled_path = self.get_bundled_templates_path()
        if bundled_path:
            source = TemplateSource(
                path=bundled_path,
                source_type=TemplateSourceType.BUNDLED,
                size_bytes=self._get_directory_size(bundled_path),
            )
            _get_console().print(f"[cyan]ℹ Using bundled templates from {bundled_path}[/cyan]")
            return TemplateResolutionResult(
                source=source,
                success=True,
                message=f"Using bundled templates from {bundled_path}",
                fallback_attempted=True,
            )

        # Offline mode - skip GitHub download
        if self.offline:
            _get_console().print("[yellow]⚠ Offline mode - skipping GitHub download[/yellow]")
            self._show_offline_instructions()
            return TemplateResolutionResult(
                source=None,
                success=False,
                message="No templates found in offline mode",
                fallback_attempted=True,
            )

        # Fallback to GitHub download
        repo_msg = f" from {self.template_repo}" if self.template_repo else ""
        _get_console().print(f"[blue]⬇ No local templates found, attempting GitHub download{repo_msg}...[/blue]")
        return self._attempt_github_download()

    def _attempt_file_level_merge(self, local_path: Path, local_files: dict[str, set[str]]) -> TemplateResolutionResult:
        """Attempt to create merged template source by downloading and merging at file level.

        Args:
            local_path: Path to local templates directory
            local_files: Dict of local template files by type

        Returns:
            TemplateResolutionResult with merged source or error
        """
        try:
            # Download complete templates to cache
            github_path = self._download_github_templates()
            if not github_path:
                _get_console().print("[yellow]⚠ Failed to download templates from GitHub[/yellow]")
                # Fall back to using only local templates
                source = TemplateSource(
                    path=local_path,
                    source_type=TemplateSourceType.LOCAL,
                    size_bytes=self._get_directory_size(local_path),
                )
                local_count = sum(len(files) for files in local_files.values())
                return TemplateResolutionResult(
                    source=source,
                    success=True,
                    message=f"Using {local_count} local template files only (download failed)",
                    fallback_attempted=True,
                )

            # Get downloaded template files
            downloaded_files = self.get_available_template_files(github_path)

            # Calculate merge statistics
            local_count = sum(len(files) for files in local_files.values())
            downloaded_count = sum(len(files) for files in downloaded_files.values())

            # Create merged source with file-level tracking
            merged_source = MergedTemplateSource(
                local_path=local_path,
                downloaded_path=github_path,
                local_files=local_files,
                downloaded_files=downloaded_files,
            )

            # Calculate unique files (local takes priority)
            all_files = merged_source.get_all_available_files()
            total_unique_files = sum(len(files) for files in all_files.values())

            success_msg = f"Merged {local_count} local files with {downloaded_count} downloaded files ({total_unique_files} unique files total)"
            _get_console().print(f"[green]✓ {success_msg}[/green]")

            # Show detailed breakdown
            for template_type in sorted(all_files.keys()):
                local_in_type = len(local_files.get(template_type, set()))
                downloaded_in_type = len(downloaded_files.get(template_type, set()))
                unique_in_type = len(all_files[template_type])
                _get_console().print(
                    f"  {template_type}: {local_in_type} local + {downloaded_in_type} downloaded = {unique_in_type} unique"
                )

            return TemplateResolutionResult(
                source=merged_source,
                success=True,
                message=success_msg,
                fallback_attempted=True,
            )

        except (NetworkError, GitHubAPIError, TimeoutError, ValidationError) as e:
            _get_console().print(f"[yellow]⚠ Could not download templates for merging: {e}[/yellow]")
            _get_console().print(f"[cyan]ℹ Proceeding with local templates only[/cyan]")

            # Fall back to using only local templates
            source = TemplateSource(
                path=local_path,
                source_type=TemplateSourceType.LOCAL,
                size_bytes=self._get_directory_size(local_path),
            )
            local_count = sum(len(files) for files in local_files.values())
            return TemplateResolutionResult(
                source=source,
                success=True,
                message=f"Using {local_count} local template files only (download failed: {e})",
                fallback_attempted=True,
            )
        except Exception as e:
            _get_console().print(f"[red]✗ Unexpected error during template merge: {e}[/red]")
            # Fall back to using only local templates
            source = TemplateSource(
                path=local_path,
                source_type=TemplateSourceType.LOCAL,
                size_bytes=self._get_directory_size(local_path),
            )
            local_count = sum(len(files) for files in local_files.values())
            return TemplateResolutionResult(
                source=source,
                success=True,
                message=f"Using {local_count} local template files due to merge error: {e}",
                fallback_attempted=True,
            )

    def _attempt_merged_resolution(
        self, local_path: Path, local_types: set[str], missing_types: set[str]
    ) -> TemplateResolutionResult:
        """Attempt to create merged template source by downloading missing types.

        Args:
            local_path: Path to local templates directory
            local_types: Set of template types available locally
            missing_types: Set of template types that need to be downloaded

        Returns:
            TemplateResolutionResult with merged source or error
        """
        try:
            # Download complete templates to cache
            github_path = self._download_github_templates()
            if not github_path:
                _get_console().print("[yellow]⚠ Failed to download templates from GitHub[/yellow]")
                # Fall back to using partial local templates
                source = TemplateSource(
                    path=local_path,
                    source_type=TemplateSourceType.LOCAL,
                    size_bytes=self._get_directory_size(local_path),
                )
                return TemplateResolutionResult(
                    source=source,
                    success=False,
                    message=f"Using partial local templates (missing: {', '.join(sorted(missing_types))})",
                    fallback_attempted=True,
                )

            # Verify downloaded templates have the missing types
            downloaded_types = self.get_available_template_types(github_path)
            available_from_download = missing_types.intersection(downloaded_types)
            still_missing = missing_types - available_from_download

            if still_missing:
                _get_console().print(
                    f"[yellow]⚠ Downloaded templates also missing: {', '.join(sorted(still_missing))}[/yellow]"
                )

            # Create merged source
            merged_source = MergedTemplateSource(
                local_path=local_path,
                downloaded_path=github_path,
                local_types=local_types,
                downloaded_types=available_from_download,
            )

            success_msg = f"Merged local templates ({', '.join(sorted(local_types))}) with downloaded ({', '.join(sorted(available_from_download))})"
            if still_missing:
                success_msg += f" - still missing: {', '.join(sorted(still_missing))}"

            _get_console().print(f"[green]✓ {success_msg}[/green]")

            return TemplateResolutionResult(
                source=merged_source,
                success=True,
                message=success_msg,
                fallback_attempted=True,
            )

        except (NetworkError, GitHubAPIError, TimeoutError, ValidationError) as e:
            _get_console().print(f"[yellow]⚠ Could not download missing templates: {e}[/yellow]")
            _get_console().print(f"[cyan]ℹ Proceeding with partial local templates[/cyan]")

            # Fall back to using partial local templates
            source = TemplateSource(
                path=local_path,
                source_type=TemplateSourceType.LOCAL,
                size_bytes=self._get_directory_size(local_path),
            )
            return TemplateResolutionResult(
                source=source,
                success=False,
                message=f"Using partial local templates (missing: {', '.join(sorted(missing_types))}) - download failed: {e}",
                fallback_attempted=True,
            )
        except Exception as e:
            _get_console().print(f"[red]✗ Unexpected error during template merge: {e}[/red]")
            # Fall back to using partial local templates
            source = TemplateSource(
                path=local_path,
                source_type=TemplateSourceType.LOCAL,
                size_bytes=self._get_directory_size(local_path),
            )
            return TemplateResolutionResult(
                source=source,
                success=False,
                message=f"Using partial local templates due to merge error: {e}",
                fallback_attempted=True,
            )

    def _attempt_github_download(self) -> TemplateResolutionResult:
        """Attempt to download templates from GitHub with error handling."""
        try:
            github_path = self._download_github_templates()
            if github_path:
                source = TemplateSource(
                    path=github_path,
                    source_type=TemplateSourceType.GITHUB,
                    size_bytes=self._get_directory_size(github_path),
                )
                repo_msg = f" from {self.template_repo}" if self.template_repo else ""
                _get_console().print(f"[green]✓ Downloaded templates from GitHub{repo_msg} to {github_path}[/green]")
                return TemplateResolutionResult(
                    source=source,
                    success=True,
                    message=f"Downloaded templates from GitHub{repo_msg}",
                    fallback_attempted=True,
                )
        except NetworkError as e:
            _get_console().print(f"[yellow]⚠ Network error during GitHub download: {e}[/yellow]")
            self._show_offline_instructions()
        except GitHubAPIError as e:
            if isinstance(e, RateLimitError):
                retry_msg = f" (retry after {e.retry_after}s)" if hasattr(e, "retry_after") and e.retry_after else ""
                _get_console().print(f"[yellow]⚠ GitHub API rate limit exceeded{retry_msg}[/yellow]")
            else:
                _get_console().print(f"[yellow]⚠ GitHub API error: {e}[/yellow]")
            self._show_offline_instructions()
        except TimeoutError as e:
            _get_console().print(f"[yellow]⚠ Download timeout: {e}[/yellow]")
            _get_console().print("[cyan]Tip: Try again with a better internet connection[/cyan]")
        except ValidationError as e:
            _get_console().print(f"[yellow]⚠ Template validation failed: {e}[/yellow]")
            _get_console().print("[cyan]Tip: The downloaded templates may be corrupted or invalid[/cyan]")
        except Exception as e:
            _get_console().print(f"[red]✗ Unexpected error during GitHub download: {e}[/red]")

        # All template sources failed
        _get_console().print("[red]✗ No templates available from any source[/red]")
        self._show_manual_setup_instructions()
        return TemplateResolutionResult(
            source=None,
            success=False,
            message="No templates found from any source (local, bundled, or GitHub)",
            fallback_attempted=True,
        )

    def _get_directory_size(self, path: Path) -> Optional[int]:
        """Calculate total size of directory in bytes.

        Args:
            path: Directory path to calculate size for

        Returns:
            Size in bytes, or None if calculation fails
        """
        try:
            total_size = 0
            for file_path in path.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            return total_size
        except (OSError, PermissionError):
            return None

    def has_local_templates(self) -> bool:
        """Check if local templates are available."""
        return self.get_local_templates_path() is not None

    def has_bundled_templates(self) -> bool:
        """Check if bundled templates are available."""
        return self.get_bundled_templates_path() is not None

    def _download_github_templates(self) -> Optional[Path]:
        """Download templates from GitHub to temporary cache.

        Returns:
            Path to cached templates if successful, None otherwise

        Raises:
            NetworkError: If network operation fails
            GitHubAPIError: If GitHub API request fails
            TimeoutError: If download times out
            ValidationError: If template validation fails
        """
        # Create cache directory using CacheManager
        cache_dir = self.cache_manager.create_cache_dir()

        try:
            # Download templates asynchronously
            async def download():
                return await self.github_downloader.download_templates(cache_dir)

            # Run async download
            if hasattr(asyncio, "run"):
                source = asyncio.run(download())
            else:
                # Fallback for older Python versions
                loop = asyncio.get_event_loop()
                source = loop.run_until_complete(download())

            return source.path if source else None

        except Exception:
            # Cleanup cache directory on failure
            self.cache_manager.cleanup_cache(cache_dir)
            raise

    def _show_offline_instructions(self) -> None:
        """Show instructions for working offline with local templates."""
        offline_instructions = (
            "[bold cyan]Working Offline[/bold cyan]\n\n"
            "To use templates without internet access:\n"
            f"1. Create a [bold]{LOCAL_TEMPLATES_DIR}[/bold] folder in your project directory\n"
            "2. Copy template files from the repository manually:\n"
            f"   [dim]https://github.com/{DEFAULT_GITHUB_REPO}/tree/{DEFAULT_GITHUB_BRANCH}/{DOWNLOAD_TEMPLATES_DIR}[/dim]\n"
            f"3. Or work from a directory that already has [bold]{LOCAL_TEMPLATES_DIR}[/bold]"
        )

        _get_console().print(
            _get_panel()(offline_instructions, title="Offline Mode", border_style="cyan", padding=(1, 2))
        )

    def _show_manual_setup_instructions(self) -> None:
        """Show comprehensive manual setup instructions when all sources fail."""
        manual_instructions = (
            "[bold red]Manual Template Setup Required[/bold red]\n\n"
            "All template sources failed. To proceed manually:\n\n"
            "[bold cyan]Option 1: Download Templates[/bold cyan]\n"
            "1. Visit: [dim]https://github.com/robertmeisner/improved-sdd[/dim]\n"
            "2. Download or clone the repository\n"
            f"3. Copy the [bold]templates/[/bold] folder to [bold]{LOCAL_TEMPLATES_DIR}/[/bold] in your project\n\n"
            "[bold cyan]Option 2: Create Basic Structure[/bold cyan]\n"
            f"1. Create [bold]{LOCAL_TEMPLATES_DIR}/[/bold] folder manually\n"
            "2. Add basic template files as needed\n\n"
            "[bold cyan]Option 3: Use Different Directory[/bold cyan]\n"
            "Run this command from a directory that already has templates"
        )

        _get_console().print(
            _get_panel()(manual_instructions, title="🔧 Manual Setup", border_style="red", padding=(1, 2))
        )
