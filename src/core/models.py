"""Data models and enums for CLI operations.

This module contains all the dataclasses and enums used throughout the CLI
for representing template sources, progress information, and resolution results.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Union


class TemplateSourceType(Enum):
    """Enumeration of template source types for transparency."""

    LOCAL = "local"
    BUNDLED = "bundled"
    GITHUB = "github"
    MERGED = "merged"


@dataclass
class ProgressInfo:
    """Progress information for download and extraction operations."""

    phase: str  # "download" or "extract"
    bytes_completed: int
    bytes_total: int
    percentage: float
    speed_bps: Optional[int] = None
    eta_seconds: Optional[int] = None

    @property
    def speed_mbps(self) -> Optional[float]:
        """Download speed in MB/s."""
        return self.speed_bps / (1024 * 1024) if self.speed_bps else None


@dataclass
class TemplateSource:
    """Represents a template source with location and type information."""

    path: Path
    source_type: TemplateSourceType
    size_bytes: Optional[int] = None

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.source_type.value} templates at {self.path}"


@dataclass
class MergedTemplateSource:
    """Represents a merged template source combining local and downloaded templates at file level."""

    local_path: Optional[Path]  # User's .sdd_templates directory
    downloaded_path: Path  # Cache directory with downloaded templates
    local_files: dict[str, set[str]]  # Template files found locally: {'prompts': {'file1.md', 'file2.md'}}
    downloaded_files: dict[str, set[str]]  # Template files downloaded: {'chatmodes': {'file3.md'}}
    source_type: TemplateSourceType = TemplateSourceType.MERGED

    def get_file_source(self, template_type: str, filename: str) -> Optional[Path]:
        """Get the source path for a specific template file.

        Args:
            template_type: Template type (e.g., 'prompts', 'chatmodes')
            filename: Template filename (e.g., 'sddCommitWorkflow.prompt.md')

        Returns:
            Path to the file source (local takes priority) or None if not found
        """
        # Check local first (priority)
        if template_type in self.local_files and filename in self.local_files[template_type] and self.local_path:
            return self.local_path / template_type / filename

        # Check downloaded
        if template_type in self.downloaded_files and filename in self.downloaded_files[template_type]:
            return self.downloaded_path / template_type / filename

        return None

    def get_all_available_files(self) -> dict[str, set[str]]:
        """Get all available template files from both sources (local + downloaded)."""
        all_files = {}

        # Add local files
        for template_type, files in self.local_files.items():
            if template_type not in all_files:
                all_files[template_type] = set()
            all_files[template_type].update(files)

        # Add downloaded files (but not if already in local - local takes priority)
        for template_type, files in self.downloaded_files.items():
            if template_type not in all_files:
                all_files[template_type] = set()
            # Only add downloaded files that aren't already available locally
            local_files_for_type = self.local_files.get(template_type, set())
            all_files[template_type].update(files - local_files_for_type)

        return all_files

    def __str__(self) -> str:
        """Human-readable string representation."""
        local_count = sum(len(files) for files in self.local_files.values())
        downloaded_count = sum(len(files) for files in self.downloaded_files.values())
        all_files = self.get_all_available_files()
        total_count = sum(len(files) for files in all_files.values())

        local_desc = f"{local_count} local files" if local_count else "no local files"
        downloaded_desc = f"{downloaded_count} downloaded files" if downloaded_count else "no downloaded files"
        return f"merged templates ({local_desc}, {downloaded_desc}, {total_count} total unique files)"


@dataclass
class TemplateResolutionResult:
    """Tracks the result of template resolution with transparency information."""

    source: Optional[Union[TemplateSource, MergedTemplateSource]]
    success: bool
    message: str
    fallback_attempted: bool = False

    @property
    def is_local(self) -> bool:
        """Check if resolved source is local .sdd_templates."""
        return (
            self.source is not None
            and hasattr(self.source, "source_type")
            and self.source.source_type == TemplateSourceType.LOCAL
        )

    @property
    def is_bundled(self) -> bool:
        """Check if resolved source is bundled templates."""
        return (
            self.source is not None
            and hasattr(self.source, "source_type")
            and self.source.source_type == TemplateSourceType.BUNDLED
        )

    @property
    def is_github(self) -> bool:
        """Check if resolved source is GitHub download."""
        return (
            self.source is not None
            and hasattr(self.source, "source_type")
            and self.source.source_type == TemplateSourceType.GITHUB
        )

    @property
    def is_merged(self) -> bool:
        """Check if resolved source is merged local + downloaded."""
        return (
            self.source is not None
            and hasattr(self.source, "source_type")
            and self.source.source_type == TemplateSourceType.MERGED
        )
