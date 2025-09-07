"""Data models and enums for CLI operations.

This module contains all the dataclasses and enums used throughout the CLI
for representing template sources, progress information, and resolution results.
"""
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class TemplateSourceType(Enum):
    """Enumeration of template source types for transparency."""

    LOCAL = "local"
    BUNDLED = "bundled"
    GITHUB = "github"


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
class TemplateResolutionResult:
    """Tracks the result of template resolution with transparency information."""

    source: Optional[TemplateSource]
    success: bool
    message: str
    fallback_attempted: bool = False

    @property
    def is_local(self) -> bool:
        """Check if resolved source is local .sdd_templates."""
        return self.source is not None and self.source.source_type == TemplateSourceType.LOCAL

    @property
    def is_bundled(self) -> bool:
        """Check if resolved source is bundled templates."""
        return self.source is not None and self.source.source_type == TemplateSourceType.BUNDLED

    @property
    def is_github(self) -> bool:
        """Check if resolved source is GitHub download."""
        return self.source is not None and self.source.source_type == TemplateSourceType.GITHUB