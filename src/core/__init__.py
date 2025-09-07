"""Core module for CLI decomposition.

This module contains foundational components including:
- Configuration management
- Exception hierarchy
- Data models and enums
- Service interfaces and protocols

During migration, this module will be gradually populated with extracted code.
"""

# Module version for migration tracking
__version__ = "0.1.0-migration"

# Import configuration (available after Task 2.1)
from .config import (
    AIToolConfig,
    AppTypeConfig,
    ConfigCompatibilityLayer,
    config,
    AI_TOOLS,
    APP_TYPES,
    BANNER,
    TAGLINE,
)

# Import exceptions (available after Task 2.2)
from .exceptions import (
    TemplateError,
    NetworkError,
    GitHubAPIError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)

# Import models and enums (available after Task 1.3)
from .models import (
    ProgressInfo,
    TemplateResolutionResult,
    TemplateSource,
    TemplateSourceType,
)

# Import protocols and container (available after Task 1.2)
from .interfaces import (
    CacheManagerProtocol,
    ConsoleProtocol,
    FileTrackerProtocol,
    GitHubDownloaderProtocol,
    ProgressTrackerProtocol,
    ServiceContainerProtocol,
    TemplateResolverProtocol,
)
from .container import ServiceContainer, container

# Import order for future modules:
# All modules have been imported

__all__ = [
    # Configuration
    "AIToolConfig",
    "AppTypeConfig",
    "ConfigCompatibilityLayer",
    "config",
    "AI_TOOLS",
    "APP_TYPES", 
    "BANNER",
    "TAGLINE",
    # Exceptions
    "TemplateError",
    "NetworkError",
    "GitHubAPIError", 
    "RateLimitError",
    "TimeoutError",
    "ValidationError",
    # Models and enums
    "ProgressInfo",
    "TemplateResolutionResult", 
    "TemplateSource",
    "TemplateSourceType",
    # Protocols
    "CacheManagerProtocol",
    "ConsoleProtocol", 
    "FileTrackerProtocol",
    "GitHubDownloaderProtocol",
    "ProgressTrackerProtocol",
    "ServiceContainerProtocol",
    "TemplateResolverProtocol",
    # Container
    "ServiceContainer",
    "container",
]