"""Template resolver service for handling template source resolution.

This module provides the TemplateResolver class which implements a priority-based
template resolution system: local .sdd_templates > bundled templates > GitHub download.
"""

import asyncio
from pathlib import Path
from typing import Optional

from src.core.exceptions import GitHubAPIError, NetworkError, RateLimitError, TimeoutError, ValidationError
from src.core.models import TemplateResolutionResult, TemplateSource, TemplateSourceType

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
    local .sdd_templates > bundled templates > GitHub download."""

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
            repo_parts = template_repo.split("/")
            self.github_downloader = GitHubDownloader(repo_owner=repo_parts[0], repo_name=repo_parts[1])
        else:
            self.github_downloader = GitHubDownloader()

        self.cache_manager = CacheManager()

        # Clean up orphaned caches on startup
        self.cache_manager.cleanup_orphaned_caches()

    def get_local_templates_path(self) -> Optional[Path]:
        """Check for local .sdd_templates directory in project or parent directories.

        Returns:
            Path to local .sdd_templates if found, None otherwise
        """
        # Check current project directory first
        local_path = self.project_path / ".sdd_templates"
        if local_path.exists() and local_path.is_dir():
            return local_path

        # Check parent directories up to filesystem root
        current_path = self.project_path.parent
        while current_path != current_path.parent:  # Stop at filesystem root
            local_path = current_path / ".sdd_templates"
            if local_path.exists() and local_path.is_dir():
                return local_path
            current_path = current_path.parent

        return None

    def get_bundled_templates_path(self) -> Optional[Path]:
        """Get path to bundled templates directory.

        Returns:
            Path to bundled templates if they exist, None otherwise
        """
        bundled_path = self.script_dir.parent / ".sdd_templates"
        if bundled_path.exists() and bundled_path.is_dir():
            return bundled_path
        return None

    def resolve_templates_source(self) -> Optional[Path]:
        """Resolve template source using priority system.

        Priority order:
        1. Local .sdd_templates (project or parent directories)
        2. Bundled templates directory
        3. GitHub download to temporary cache

        Returns:
            Path to templates source, None if no source found
        """
        # Priority 1: Local .sdd_templates
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

        # Check local .sdd_templates first (unless force download)
        local_path = self.get_local_templates_path()
        if local_path:
            source = TemplateSource(
                path=local_path,
                source_type=TemplateSourceType.LOCAL,
                size_bytes=self._get_directory_size(local_path),
            )
            _get_console().print(f"[green]✓ Using local templates from {local_path}[/green]")
            return TemplateResolutionResult(
                source=source,
                success=True,
                message=f"Using local templates from {local_path}",
                fallback_attempted=False,
            )

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
            _get_console().print("[cyan]💡 Try again with a better internet connection[/cyan]")
        except ValidationError as e:
            _get_console().print(f"[yellow]⚠ Template validation failed: {e}[/yellow]")
            _get_console().print("[cyan]💡 The downloaded templates may be corrupted or invalid[/cyan]")
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
        """Check if local .sdd_templates are available."""
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
            "1. Create a [bold].sdd_templates[/bold] folder in your project directory\n"
            "2. Copy template files from the repository manually:\n"
            "   [dim]https://github.com/robertmeisner/improved-sdd/tree/main/templates[/dim]\n"
            "3. Or work from a directory that already has [bold].sdd_templates[/bold]"
        )

        _get_console().print(
            _get_panel()(offline_instructions, title="💡 Offline Mode", border_style="cyan", padding=(1, 2))
        )

    def _show_manual_setup_instructions(self) -> None:
        """Show comprehensive manual setup instructions when all sources fail."""
        manual_instructions = (
            "[bold red]Manual Template Setup Required[/bold red]\n\n"
            "All template sources failed. To proceed manually:\n\n"
            "[bold cyan]Option 1: Download Templates[/bold cyan]\n"
            "1. Visit: [dim]https://github.com/robertmeisner/improved-sdd[/dim]\n"
            "2. Download or clone the repository\n"
            "3. Copy the [bold]templates/[/bold] folder to [bold].sdd_templates/[/bold] in your project\n\n"
            "[bold cyan]Option 2: Create Basic Structure[/bold cyan]\n"
            "1. Create [bold].sdd_templates/[/bold] folder manually\n"
            "2. Add basic template files as needed\n\n"
            "[bold cyan]Option 3: Use Different Directory[/bold cyan]\n"
            "Run this command from a directory that already has templates"
        )

        _get_console().print(
            _get_panel()(manual_instructions, title="🔧 Manual Setup", border_style="red", padding=(1, 2))
        )
