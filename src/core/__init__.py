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
    AI_TOOLS,
    APP_TYPES,
    BANNER,
    DEFAULT_GITHUB_BRANCH,
    DEFAULT_GITHUB_REPO,
    DOWNLOAD_TEMPLATES_DIR,
    FALLBACK_GITHUB_BRANCHES,
    LOCAL_TEMPLATES_DIR,
    TAGLINE,
    AIToolConfig,
    AppTypeConfig,
    ConfigCompatibilityLayer,
    config,
)
from .container import ServiceContainer, container

# Import exceptions (available after Task 2.2)
from .exceptions import GitHubAPIError, NetworkError, RateLimitError, TemplateError, TimeoutError, ValidationError

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

# Import models and enums (available after Task 1.3)
from .models import (
    AITool,
    AIToolConfig as AIToolConfigModel,
    CLIConfig,
    DeleteBehaviorConfig,
    FileExtensions,
    KeywordReplacements,
    ManagedFiles,
    PreferencesConfig,
    ProgressInfo,
    SDDConfig,
    TemplateResolutionResult,
    TemplateSource,
    TemplateSourceType,
)

# Import AI Tool Manager (available after Task 2.2)
from .ai_tool_manager import AIToolManager, ManagedFileResult, ActiveToolsResult

# Import File Manager (available after Task 3.1)
from .file_manager import FileManager, FileConflict, FileDiscoveryResult

# Import User Interaction Handler (available after Task 3.2)
from .user_interaction_handler import UserInteractionHandler, UserChoice, ConflictResolution

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
    "LOCAL_TEMPLATES_DIR",
    "DOWNLOAD_TEMPLATES_DIR",
    "DEFAULT_GITHUB_REPO",
    "DEFAULT_GITHUB_BRANCH",
    "FALLBACK_GITHUB_BRANCHES",
    # Exceptions
    "TemplateError",
    "NetworkError",
    "GitHubAPIError",
    "RateLimitError",
    "TimeoutError",
    "ValidationError",
    # Models and enums
    "AITool",
    "AIToolConfigModel",
    "CLIConfig", 
    "DeleteBehaviorConfig",
    "FileExtensions",
    "KeywordReplacements",
    "ManagedFiles",
    "PreferencesConfig",
    "ProgressInfo",
    "SDDConfig",
    "TemplateResolutionResult",
    "TemplateSource",
    "TemplateSourceType",
    # AI Tool Manager
    "AIToolManager",
    "ManagedFileResult",
    "ActiveToolsResult",
    # File Manager
    "FileManager",
    "FileConflict",
    "FileDiscoveryResult",
    # User Interaction Handler
    "UserInteractionHandler",
    "UserChoice",
    "ConflictResolution",
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

# Populate APP_TYPES with instruction file names
APP_TYPES["python-cli"]["instructions"] = ["sddPythonCliDev.instructions.md"]
APP_TYPES["mcp-server"]["instructions"] = ["sddMcpServerDev.instructions.md"]
