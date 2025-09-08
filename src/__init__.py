"""Improved-SDD CLI package."""

# Import main components for external access
from .improved_sdd_cli import app

# Import services for testing
from .services.file_tracker import FileTracker
from .services.cache_manager import CacheManager
from .services.github_downloader import GitHubDownloader
from .services.template_resolver import TemplateResolver

# Import core components
from .core.models import (
    ProgressInfo,
    TemplateResolutionResult,
    TemplateSource,
    TemplateSourceType,
)

# Import utils for testing
from .utils import (
    check_github_copilot,
    check_tool,
    customize_template_content,
    get_template_filename,
    offer_user_choice,
    create_project_structure,
)

__all__ = [
    "app",
    "FileTracker",
    "CacheManager", 
    "GitHubDownloader",
    "TemplateResolver",
    "ProgressInfo",
    "TemplateResolutionResult",
    "TemplateSource",
    "TemplateSourceType",
    "check_github_copilot",
    "check_tool",
    "customize_template_content",
    "get_template_filename",
    "offer_user_choice",
    "create_project_structure",
]