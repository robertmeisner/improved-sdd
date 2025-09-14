"""Depenfrom typing import Any, Dict, Optional, Type, TypeVar

from .interfaces import (
    CacheManagerProtocol,
    FileTrackerProtocol,
    GitHubDownloaderProtocol,
    TemplateResolverProtocol,
)ection container for CLI services.

This module provides a dependency injection container that enables
clean separation of concerns, lazy loading, and easier testing through
service registration and resolution.
"""

from pathlib import Path
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union

from .interfaces import CacheManagerProtocol, FileTrackerProtocol, GitHubDownloaderProtocol, TemplateResolverProtocol

T = TypeVar("T")


class ServiceContainer:
    """Dependency injection container for service management.

    Provides service registration and resolution with type safety through protocols.
    Supports singleton pattern for shared service instances and lazy loading
    through factory functions.
    """

    def __init__(self):
        """Initialize service container and register default services."""
        self._services: Dict[Type, Any] = {}
        self._singletons: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}
        self._initialize_default_services()

    def register(self, interface: Type[T], implementation: Union[T, Callable[[], T]]) -> None:
        """Register a service implementation for an interface.

        Args:
            interface: Protocol interface type
            implementation: Service implementation instance or factory function
        """
        import inspect

        # Check if it's a callable that takes no arguments - likely a factory
        if callable(implementation):
            try:
                sig = inspect.signature(implementation)
                # If it's a callable with no required parameters, treat as factory
                if len(sig.parameters) == 0:
                    self._factories[interface] = implementation
                    return
            except (ValueError, TypeError):
                # If we can't inspect, assume it's an instance
                pass

        # Default to treating as an instance
        self._services[interface] = implementation

    def register_singleton(self, interface: Type[T], factory: Callable[[], T]) -> None:
        """Register a singleton service with lazy initialization.

        Args:
            interface: Protocol interface type
            factory: Factory function that creates the service instance
        """
        self._factories[interface] = factory

    def get(self, interface: Type[T]) -> T:
        """Get a service implementation for an interface.

        Args:
            interface: Protocol interface type

        Returns:
            Service implementation instance

        Raises:
            KeyError: If interface is not registered
        """
        # Check if we have a singleton instance already created
        if interface in self._singletons:
            return self._singletons[interface]

        # Check if we have a factory for lazy initialization
        if interface in self._factories:
            instance = self._factories[interface]()
            # Cache as singleton for future calls
            self._singletons[interface] = instance
            return instance

        # Check if we have a direct service registration
        if interface in self._services:
            return self._services[interface]

        raise KeyError(f"Service {interface.__name__} is not registered")

    def has(self, interface: Type[T]) -> bool:
        """Check if an interface is registered.

        Args:
            interface: Protocol interface type

        Returns:
            True if interface is registered
        """
        return interface in self._services or interface in self._factories or interface in self._singletons

    def clear(self) -> None:
        """Clear all registered services."""
        self._services.clear()
        self._singletons.clear()
        self._factories.clear()

    def create_template_resolver(
        self,
        project_path: Path,
        offline: bool = False,
        force_download: bool = False,
        template_repo: Optional[str] = None,
    ) -> TemplateResolverProtocol:
        """Factory method to create TemplateResolver with project context.

        Note: TemplateResolver currently creates its own dependencies internally.
        This should be refactored in a future iteration for proper DI.

        Args:
            project_path: Path to the project directory
            offline: Whether to operate in offline mode
            force_download: Whether to force download from GitHub
            template_repo: Custom template repository URL

        Returns:
            Configured TemplateResolver instance
        """
        # Import here to avoid circular imports
        from services.template_resolver import TemplateResolver

        return TemplateResolver(
            project_path=project_path,
            offline=offline,
            force_download=force_download,
            template_repo=template_repo,
        )

    def _initialize_default_services(self) -> None:
        """Initialize default service registrations with lazy loading."""
        # Register singleton services with lazy initialization
        self.register_singleton(FileTrackerProtocol, self._create_file_tracker)
        self.register_singleton(CacheManagerProtocol, self._create_cache_manager)
        self.register_singleton(GitHubDownloaderProtocol, self._create_github_downloader)

    def _create_file_tracker(self) -> FileTrackerProtocol:
        """Create FileTracker instance."""
        from services.file_tracker import FileTracker

        return FileTracker()

    def _create_cache_manager(self) -> CacheManagerProtocol:
        """Create CacheManager instance."""
        from services.cache_manager import CacheManager

        return CacheManager()

    def _create_github_downloader(self) -> GitHubDownloaderProtocol:
        """Create GitHubDownloader instance with default configuration."""
        from services.github_downloader import GitHubDownloader

        return GitHubDownloader()


# Global service container instance for CLI application
container = ServiceContainer()
