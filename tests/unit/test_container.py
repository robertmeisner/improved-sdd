"""Tests for the dependency injection container."""

import tempfile
from pathlib import Path
from typing import Protocol
from unittest.mock import Mock

import pytest

from src.core.container import ServiceContainer, container
from src.core.interfaces import (
    CacheManagerProtocol,
    FileTrackerProtocol,
    GitHubDownloaderProtocol,
    TemplateResolverProtocol,
)


class TestServiceContainer:
    """Test dependency injection container functionality."""

    def test_container_initialization(self):
        """Test that container initializes with default services."""
        test_container = ServiceContainer()

        # Check that default services are registered
        assert test_container.has(FileTrackerProtocol)
        assert test_container.has(CacheManagerProtocol)
        assert test_container.has(GitHubDownloaderProtocol)

    def test_singleton_service_registration_and_retrieval(self):
        """Test singleton service registration and retrieval."""
        test_container = ServiceContainer()
        test_container.clear()  # Start fresh

        # Mock service implementation
        class MockService:
            def __init__(self):
                self.calls = 0

            def method(self):
                self.calls += 1
                return "called"

        # Register singleton factory
        test_container.register_singleton(object, lambda: MockService())

        # Get service multiple times
        service1 = test_container.get(object)
        service2 = test_container.get(object)

        # Should be the same instance (singleton)
        assert service1 is service2
        assert hasattr(service1, "calls")

    def test_service_registration_and_retrieval(self):
        """Test direct service registration and retrieval."""
        test_container = ServiceContainer()
        test_container.clear()  # Start fresh

        # Mock service instance
        mock_service = "test_service"

        # Register service directly
        test_container.register(str, mock_service)

        # Retrieve service
        retrieved = test_container.get(str)
        assert retrieved == mock_service

    def test_factory_registration_and_lazy_loading(self):
        """Test factory function registration with lazy loading."""
        test_container = ServiceContainer()
        test_container.clear()  # Start fresh

        call_count = 0

        def factory():
            nonlocal call_count
            call_count += 1
            return f"instance_{call_count}"

        # Register factory
        test_container.register(str, factory)

        # Factory not called yet
        assert call_count == 0

        # Get service - factory should be called
        service1 = test_container.get(str)
        assert call_count == 1
        assert service1 == "instance_1"

        # Get again - should get cached singleton
        service2 = test_container.get(str)
        assert call_count == 1  # Not called again
        assert service2 == "instance_1"
        assert service1 is service2

    def test_has_method(self):
        """Test has method for checking service registration."""
        test_container = ServiceContainer()
        test_container.clear()  # Start fresh

        # Should not have unregistered service
        assert not test_container.has(str)

        # Register service
        test_container.register(str, "test")

        # Should have registered service
        assert test_container.has(str)

    def test_get_unregistered_service_raises_error(self):
        """Test that getting unregistered service raises KeyError."""
        test_container = ServiceContainer()
        test_container.clear()  # Start fresh

        with pytest.raises(KeyError, match="Service object is not registered"):
            test_container.get(object)

    def test_clear_method(self):
        """Test clearing all registered services."""
        test_container = ServiceContainer()

        # Should have default services
        assert test_container.has(FileTrackerProtocol)

        # Clear all services
        test_container.clear()

        # Should not have any services
        assert not test_container.has(FileTrackerProtocol)
        assert not test_container.has(CacheManagerProtocol)

    def test_default_services_work(self):
        """Test that default services can be retrieved and work."""
        test_container = ServiceContainer()

        # Get FileTracker service
        file_tracker = test_container.get(FileTrackerProtocol)
        assert file_tracker is not None
        assert hasattr(file_tracker, "track_file_creation")

        # Get CacheManager service
        cache_manager = test_container.get(CacheManagerProtocol)
        assert cache_manager is not None
        assert hasattr(cache_manager, "create_cache_dir")

        # Get GitHubDownloader service
        github_downloader = test_container.get(GitHubDownloaderProtocol)
        assert github_downloader is not None
        assert hasattr(github_downloader, "download_templates")

    def test_singleton_behavior_with_default_services(self):
        """Test that default services behave as singletons."""
        test_container = ServiceContainer()

        # Get same service multiple times
        file_tracker1 = test_container.get(FileTrackerProtocol)
        file_tracker2 = test_container.get(FileTrackerProtocol)

        # Should be same instance
        assert file_tracker1 is file_tracker2

    def test_create_template_resolver_factory(self):
        """Test TemplateResolver factory method."""
        test_container = ServiceContainer()

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create resolver
            resolver = test_container.create_template_resolver(
                project_path=project_path, offline=True, force_download=False, template_repo="custom/repo"
            )

            assert resolver is not None
            assert hasattr(resolver, "resolve_templates_with_transparency")

            # Create another resolver - should be different instance
            resolver2 = test_container.create_template_resolver(project_path=project_path, offline=False)

            assert resolver2 is not None
            assert resolver is not resolver2  # Not singleton

    def test_global_container_instance(self):
        """Test that global container instance is available."""
        assert container is not None
        assert isinstance(container, ServiceContainer)

        # Should have default services
        assert container.has(FileTrackerProtocol)
        assert container.has(CacheManagerProtocol)
        assert container.has(GitHubDownloaderProtocol)

    def test_service_isolation(self):
        """Test that services are properly isolated."""
        test_container = ServiceContainer()

        # Get two different service types
        file_tracker = test_container.get(FileTrackerProtocol)
        cache_manager = test_container.get(CacheManagerProtocol)

        # Should be different instances
        assert file_tracker is not cache_manager
        assert type(file_tracker).__name__ == "FileTracker"
        assert type(cache_manager).__name__ == "CacheManager"

    def test_lazy_loading_performance(self):
        """Test that services are only created when requested."""
        test_container = ServiceContainer()
        test_container.clear()  # Start fresh

        creation_count = 0

        def expensive_factory():
            nonlocal creation_count
            creation_count += 1
            return f"expensive_service_{creation_count}"

        # Register factory
        test_container.register_singleton(str, expensive_factory)

        # Factory should not be called yet
        assert creation_count == 0

        # Only when we get the service should it be created
        service = test_container.get(str)
        assert creation_count == 1
        assert service == "expensive_service_1"

    def test_multiple_factory_types(self):
        """Test container can handle different factory patterns."""
        test_container = ServiceContainer()
        test_container.clear()  # Start fresh

        # Direct instance registration
        test_container.register(int, 42)

        # Factory function registration
        test_container.register(str, lambda: "factory_created")

        # Singleton factory registration
        test_container.register_singleton(float, lambda: 3.14)

        # Test retrieval
        assert test_container.get(int) == 42
        assert test_container.get(str) == "factory_created"
        assert test_container.get(float) == 3.14

        # Test singleton behavior
        float1 = test_container.get(float)
        float2 = test_container.get(float)
        assert float1 is float2

    def test_protocol_compliance(self):
        """Test that retrieved services implement expected protocols."""
        test_container = ServiceContainer()

        # Test FileTracker protocol compliance
        file_tracker = test_container.get(FileTrackerProtocol)
        assert hasattr(file_tracker, "track_file_creation")
        assert hasattr(file_tracker, "track_file_modification")
        assert hasattr(file_tracker, "track_dir_creation")
        assert hasattr(file_tracker, "get_summary")

        # Test CacheManager protocol compliance
        cache_manager = test_container.get(CacheManagerProtocol)
        assert hasattr(cache_manager, "create_cache_dir")
        assert hasattr(cache_manager, "cleanup_cache")
        assert hasattr(cache_manager, "cleanup_all_caches")
        assert hasattr(cache_manager, "cleanup_orphaned_caches")
        assert hasattr(cache_manager, "get_cache_info")

        # Test GitHubDownloader protocol compliance
        github_downloader = test_container.get(GitHubDownloaderProtocol)
        assert hasattr(github_downloader, "download_templates")

    def test_template_resolver_factory_parameters(self):
        """Test TemplateResolver factory accepts all required parameters."""
        test_container = ServiceContainer()

        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Test with all parameters
            resolver = test_container.create_template_resolver(
                project_path=project_path, offline=True, force_download=True, template_repo="owner/repo"
            )

            assert resolver is not None
            # Check that parameters were passed correctly
            assert resolver.project_path == project_path
            assert resolver.offline is True
            assert resolver.force_download is True
            assert resolver.template_repo == "owner/repo"

            # Test with minimal parameters
            resolver_minimal = test_container.create_template_resolver(project_path=project_path)

            assert resolver_minimal is not None
            assert resolver_minimal.project_path == project_path
            assert resolver_minimal.offline is False  # Default
            assert resolver_minimal.force_download is False  # Default
            assert resolver_minimal.template_repo is None  # Default
