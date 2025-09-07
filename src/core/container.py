"""Dependency injection container for CLI services.

This module provides a simple dependency injection container that enables
clean separation of concerns and easier testing through service registration
and resolution.
"""
from typing import Any, Dict, Type, TypeVar

from .interfaces import ServiceContainerProtocol

T = TypeVar('T')


class ServiceContainer:
    """Simple dependency injection container for service management.
    
    Provides service registration and resolution with type safety through protocols.
    Supports singleton pattern for shared service instances.
    """

    def __init__(self):
        """Initialize empty service container."""
        self._services: Dict[Type, Any] = {}
        self._singletons: Dict[Type, Any] = {}

    def register(self, interface: Type[T], implementation: T) -> None:
        """Register a service implementation for an interface.
        
        Args:
            interface: Protocol interface type
            implementation: Service implementation instance
        """
        self._services[interface] = implementation

    def register_singleton(self, interface: Type[T], implementation: T) -> None:
        """Register a singleton service implementation.
        
        Args:
            interface: Protocol interface type  
            implementation: Service implementation instance
        """
        self._services[interface] = implementation
        self._singletons[interface] = implementation

    def get(self, interface: Type[T]) -> T:
        """Get a service implementation for an interface.
        
        Args:
            interface: Protocol interface type
            
        Returns:
            Service implementation instance
            
        Raises:
            KeyError: If interface is not registered
        """
        if interface not in self._services:
            raise KeyError(f"Service {interface.__name__} is not registered")
        
        # Return singleton instance if registered as singleton
        if interface in self._singletons:
            return self._singletons[interface]
            
        return self._services[interface]

    def has(self, interface: Type[T]) -> bool:
        """Check if an interface is registered.
        
        Args:
            interface: Protocol interface type
            
        Returns:
            True if interface is registered
        """
        return interface in self._services

    def clear(self) -> None:
        """Clear all registered services."""
        self._services.clear()
        self._singletons.clear()


# Global service container instance for CLI application
container = ServiceContainer()