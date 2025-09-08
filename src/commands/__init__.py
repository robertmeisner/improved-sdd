"""Commands module for CLI decomposition.

This module contains CLI command implementations including:
- init command for project initialization
- delete command for template removal
- check command for system verification

During migration, command handlers will be separated from main CLI file.
"""

# Module version for migration tracking
__version__ = "0.1.0-migration"

from .check import check_command
from .delete import delete_command

# Import commands as they are extracted:
from .init import init_command
