"""Centralized configuration management with migration compatibility.

This module provides a centralized location for all configuration constants
with a compatibility layer to ensure smooth migration from the monolithic CLI.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class AIToolConfig:
    """Configuration for an AI tool including templates and keywords."""

    name: str
    description: str
    template_dir: str
    file_extensions: Dict[str, str]
    keywords: Dict[str, str]


@dataclass
class AppTypeConfig:
    """Configuration for an application type."""

    description: str
    instruction_files: List[str]


class ConfigCompatibilityLayer:
    """Provides backward-compatible access to configuration during migration.

    This class enables gradual migration by providing the same interface as the
    original constants while allowing for future enhancements and validation.
    """

    def __init__(self):
        """Initialize configuration with original data structures."""
        # Define AI tools configuration
        self._ai_tools_data = {
            "github-copilot": {
                "name": "GitHub Copilot",
                "description": "GitHub Copilot in VS Code",
                "template_dir": "github",
                "file_extensions": {
                    "chatmodes": ".chatmode.md",
                    "instructions": ".instructions.md",
                    "prompts": ".prompt.md",
                    "commands": ".command.md",
                },
                "keywords": {
                    "{AI_ASSISTANT}": "GitHub Copilot",
                    "{AI_SHORTNAME}": "Copilot",
                    "{AI_COMMAND}": "Ctrl+Shift+P → 'Chat: Open Chat'",
                },
            },
            "claude": {
                "name": "Claude (Anthropic)",
                "description": "Claude Code or Claude API",
                "template_dir": "claude",
                "file_extensions": {
                    "chatmodes": ".claude.md",
                    "instructions": ".claude.md",
                    "prompts": ".claude.md",
                    "commands": ".claude.md",
                },
                "keywords": {
                    "{AI_ASSISTANT}": "Claude",
                    "{AI_SHORTNAME}": "Claude",
                    "{AI_COMMAND}": "Open Claude interface",
                },
            },
            "cursor": {
                "name": "Cursor AI",
                "description": "Cursor AI Editor",
                "template_dir": "cursor",
                "file_extensions": {
                    "chatmodes": ".cursor.md",
                    "instructions": ".cursor.md",
                    "prompts": ".cursor.md",
                    "commands": ".cursor.md",
                },
                "keywords": {
                    "{AI_ASSISTANT}": "Cursor AI",
                    "{AI_SHORTNAME}": "Cursor",
                    "{AI_COMMAND}": "Ctrl+K or Ctrl+L",
                },
            },
            "gemini": {
                "name": "Google Gemini",
                "description": "Google Gemini CLI or API",
                "template_dir": "gemini",
                "file_extensions": {
                    "chatmodes": ".gemini.md",
                    "instructions": ".gemini.md",
                    "prompts": ".gemini.md",
                    "commands": ".gemini.md",
                },
                "keywords": {
                    "{AI_ASSISTANT}": "Google Gemini",
                    "{AI_SHORTNAME}": "Gemini",
                    "{AI_COMMAND}": "Use Gemini CLI or API",
                },
            },
        }

        # Define app types configuration
        self._app_types_data = {
            "mcp-server": {
                "description": "MCP Server - Model Context Protocol server for AI integrations",
                "instruction_files": ["sddMcpServerDev", "mcpDev"],  # New naming, legacy naming
            },
            "python-cli": {
                "description": "Python CLI - Command-line application using typer and rich",
                "instruction_files": [
                    "sddPythonCliDev",
                    "CLIPythonDev",
                ],  # New naming, legacy naming
            },
        }

        # Define banner and tagline
        self._banner = r"""
. _   __  __ _____ _____    _____       _______ _____        _____ _____  _____
 | | |      |  __ \|  __ \ / __ \ \    / /  ___|  __ \      / ____|  __ \|  __ \
 | | | |\/| | |__) | |__) | |  | \ \  / /| |__ | |  | |____| (___ | |  | | |  | |
 | | | |  | |  ___/|  _  /| |  | |\ \/ / |  __|| |  | |_____\___ \| |  | | |  | |
 | | | |  | | |    | | \ \| |__| | \  /  | |___| |__| |     ____) | |__| | |__| |
 |_| |_|  | |_|    |_|  \_\\____/   \/   |_____|_____/     |_____/|_____/|_____/
"""

        self._tagline = "Spec-Driven Development for GitHub Copilot (soon more: Cursor, Claude, Gemini)"

    @property
    def AI_TOOLS(self) -> Dict[str, Dict]:
        """Get AI tools configuration maintaining original dictionary interface."""
        return self._ai_tools_data.copy()

    @property
    def APP_TYPES(self) -> Dict[str, Dict]:
        """Get app types configuration maintaining original dictionary interface."""
        return self._app_types_data.copy()

    @property
    def BANNER(self) -> str:
        """Get ASCII banner string."""
        return self._banner

    @property
    def TAGLINE(self) -> str:
        """Get application tagline."""
        return self._tagline

    def get_ai_tool_config(self, tool_id: str) -> AIToolConfig:
        """Get typed AI tool configuration.

        Args:
            tool_id: ID of the AI tool

        Returns:
            AIToolConfig instance

        Raises:
            KeyError: If tool_id is not found
        """
        if tool_id not in self._ai_tools_data:
            raise KeyError(f"AI tool '{tool_id}' not found")

        data = self._ai_tools_data[tool_id]
        return AIToolConfig(
            name=data["name"],
            description=data["description"],
            template_dir=data["template_dir"],
            file_extensions=data["file_extensions"].copy(),
            keywords=data["keywords"].copy(),
        )

    def get_app_type_config(self, app_type: str) -> AppTypeConfig:
        """Get typed app type configuration.

        Args:
            app_type: ID of the app type

        Returns:
            AppTypeConfig instance

        Raises:
            KeyError: If app_type is not found
        """
        if app_type not in self._app_types_data:
            raise KeyError(f"App type '{app_type}' not found")

        data = self._app_types_data[app_type]
        return AppTypeConfig(description=data["description"], instruction_files=data["instruction_files"].copy())

    def validate_ai_tool_id(self, tool_id: str) -> bool:
        """Validate if an AI tool ID exists.

        Args:
            tool_id: ID to validate

        Returns:
            True if tool exists
        """
        return tool_id in self._ai_tools_data

    def validate_app_type(self, app_type: str) -> bool:
        """Validate if an app type exists.

        Args:
            app_type: App type to validate

        Returns:
            True if app type exists
        """
        return app_type in self._app_types_data

    def get_available_ai_tools(self) -> List[str]:
        """Get list of available AI tool IDs."""
        return list(self._ai_tools_data.keys())

    def get_available_app_types(self) -> List[str]:
        """Get list of available app type IDs."""
        return list(self._app_types_data.keys())


# Global configuration instance for CLI application
config = ConfigCompatibilityLayer()

# Legacy exports for backward compatibility during migration
AI_TOOLS = config.AI_TOOLS
APP_TYPES = config.APP_TYPES
BANNER = config.BANNER
TAGLINE = config.TAGLINE
