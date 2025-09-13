"""Improved-SDD CLI package."""

# Import main components for external access
# Import core components
from .core.models import ProgressInfo, TemplateResolutionResult, TemplateSource, TemplateSourceType
from .improved_sdd_cli import app
from .services.cache_manager import CacheManager

# Import services for testing
from .services.file_tracker import FileTracker
from .services.github_downloader import GitHubDownloader
from .services.template_resolver import TemplateResolver

# Import utils for testing
from .utils import (
    check_github_copilot,
    check_tool,
    create_project_structure,
    customize_template_content,
    get_template_filename,
    load_gitlab_flow_file,
    offer_user_choice,
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
    "load_gitlab_flow_file",
    "offer_user_choice",
    "create_project_structure",
]
