"""UI module for CLI decomposition.

This module contains user interface components including:
- Console management for Rich console operations
- Progress tracking utilities for download/operation progress
- Banner and display formatting

During migration, UI components will be abstracted from business logic.
"""

# Module version for migration tracking
__version__ = "0.1.0-migration"

# Import console management components
from .console import ConsoleManager, console_manager

# Import progress tracking components
from .progress import ProgressTracker, progress_tracker
