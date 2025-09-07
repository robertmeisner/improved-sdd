"""Services module for CLI decomposition.

This module contains business logic services including:
- FileTracker for file operation tracking
- CacheManager for temporary directory management
- GitHubDownloader for template downloading
- TemplateResolver for template source resolution

During migration, services will be extracted following protocol-based patterns.
"""

# Module version for migration tracking
__version__ = "0.1.0-migration"

# Import order will be established as services are extracted:
# from .file_tracker import FileTracker
# from .cache_manager import CacheManager
# from .github_downloader import GitHubDownloader
# from .template_resolver import TemplateResolver