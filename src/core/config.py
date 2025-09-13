"""Centralized configuration management with migration compatibility.

This module provides a centralized location for all configuration constants
with a compatibility layer to ensure smooth migration from the monolithic CLI.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


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
        # Template directory names
        self._template_dirs = {
            "local_templates": ".sdd_templates",  # User's local templates directory
            "download_templates": "templates",  # Downloaded templates directory (includes chatmodes, instructions, prompts, commands, gitlab-flow)
        }

        # GitHub repository configuration
        self._github_config = {
            "default_repo": "robertmeisner/improved-sdd",  # Default repository for templates
            "default_branch": "master",  # Default branch to download from
            "fallback_branches": ["main", "master"],  # Branches to try if default fails
        }

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

        # Define GitLab Flow configuration following AI tools pattern
        self._gitlab_flow_config = {
            "name": "GitLab Flow Integration",
            "description": "GitLab Flow workflow guidance with platform-specific git commands",
            "template_dir": "gitlab-flow",
            "enabled": True,  # Default enabled to match CLI
            "template_files": {
                "setup": "gitlab-flow-setup.md",
                "commit": "gitlab-flow-commit.md",
                "pr": "gitlab-flow-pr.md",
            },
            "template_file_mapping": {
                "{GITLAB_FLOW_SETUP}": "gitlab-flow-setup.md",
                "{GITLAB_FLOW_COMMIT}": "gitlab-flow-commit.md",
                "{GITLAB_FLOW_PR}": "gitlab-flow-pr.md",
            },
            "keywords": {
                "{GITLAB_FLOW_SETUP}": "",  # Will be loaded from markdown files
                "{GITLAB_FLOW_COMMIT}": "",  # Will be loaded from markdown files
                "{GITLAB_FLOW_PR}": "",  # Will be loaded from markdown files
            },
            "platform_commands": {
                "windows": {
                    "GIT_STATUS": "git status",
                    "BRANCH_CREATE": "git checkout -b feature/spec-{spec-name}",
                    "COMMIT": 'git add . ; git commit -m "{message}"',
                    "PUSH_PR": 'git push -u origin feature/spec-{spec-name} ; gh pr create --title "Spec: {spec-name}" --body "Implementation of {spec-name} specification"',
                    "AUTO_COMMIT": 'git add . ; git commit -m "{commit-message}"',
                },
                "unix": {
                    "GIT_STATUS": "git status",
                    "BRANCH_CREATE": "git checkout -b feature/spec-{spec-name}",
                    "COMMIT": 'git add . && git commit -m "{message}"',
                    "PUSH_PR": 'git push -u origin feature/spec-{spec-name} && gh pr create --title "Spec: {spec-name}" --body "Implementation of {spec-name} specification"',
                    "AUTO_COMMIT": 'git add . && git commit -m "{commit-message}"',
                },
            },
            "commit_types": {
                "feat": "New feature implementation",
                "docs": "Documentation updates",
                "test": "Test implementation",
                "fix": "Bug fix",
                "refactor": "Code refactoring",
                "style": "Code style improvements",
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

    @property
    def LOCAL_TEMPLATES_DIR(self) -> str:
        """Get local templates directory name (.sdd_templates)."""
        return self._template_dirs["local_templates"]

    @property
    def DOWNLOAD_TEMPLATES_DIR(self) -> str:
        """Get download templates directory name (templates)."""
        return self._template_dirs["download_templates"]

    @property
    def DEFAULT_GITHUB_REPO(self) -> str:
        """Get default GitHub repository for templates."""
        return self._github_config["default_repo"]

    @property
    def DEFAULT_GITHUB_BRANCH(self) -> str:
        """Get default GitHub branch for templates."""
        return self._github_config["default_branch"]

    @property
    def GITLAB_FLOW_CONFIG(self) -> Dict[str, Any]:
        """Get GitLab Flow configuration following AI tools pattern."""
        return self._gitlab_flow_config.copy()

    def get_gitlab_flow_config(self) -> Dict[str, Any]:
        """Get GitLab Flow configuration with current state."""
        config = self._gitlab_flow_config.copy()
        return config

    @property
    def FALLBACK_GITHUB_BRANCHES(self) -> List[str]:
        """Get list of fallback branches to try if default fails."""
        return self._github_config["fallback_branches"].copy()

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

    def get_github_repo_config(self, custom_repo: Optional[str] = None) -> Dict[str, str]:
        """Get GitHub repository configuration.

        Args:
            custom_repo: Optional custom repository in 'owner/repo' format

        Returns:
            Dict with 'repo' and 'branch' keys
        """
        if custom_repo:
            return {"repo": custom_repo, "branch": self._github_config["default_branch"]}
        return {"repo": self._github_config["default_repo"], "branch": self._github_config["default_branch"]}

    def validate_github_repo_format(self, repo: str) -> bool:
        """Validate GitHub repository format.

        Args:
            repo: Repository string to validate

        Returns:
            True if format is valid (owner/repo)
        """
        if not repo or not isinstance(repo, str):
            return False
        return "/" in repo and len(repo.split("/")) == 2 and all(part.strip() for part in repo.split("/"))

    def _detect_platform_commands(self, platform: str = "windows") -> Dict[str, str]:
        """Helper method to detect platform-specific git commands.
        
        Args:
            platform: Target platform ("windows" or "unix")
            
        Returns:
            Dictionary of platform-specific git commands
        """
        if platform.lower() == "windows":
            return {
                "GIT_STATUS": "git status",
                "BRANCH_CREATE": "git checkout -b feature/spec-{spec-name}",
                "COMMIT": "git add . ; git commit -m \"feat: Add {phase} for {feature-name}\"",
                "PUSH_PR": "git push -u origin feature/spec-{feature-name} ; gh pr create --title \"Spec: {feature-name}\" --body \"Implementation of {feature-name} specification\""
            }
        else:  # Unix/Linux/macOS
            return {
                "GIT_STATUS": "git status",
                "BRANCH_CREATE": "git checkout -b feature/spec-{spec-name}",
                "COMMIT": "git add . && git commit -m \"feat: Add {phase} for {feature-name}\"",
                "PUSH_PR": "git push -u origin feature/spec-{feature-name} && gh pr create --title \"Spec: {feature-name}\" --body \"Implementation of {feature-name} specification\""
            }

    def get_gitlab_flow_keywords(
        self, enabled: bool = False, platform: str = "windows", template_dir: str = ""
    ) -> Dict[str, str]:
        """Get GitLab Flow keywords with content loaded from markdown files.

        Args:
            enabled: Whether GitLab Flow is enabled
            platform: Target platform (windows/unix) for command syntax
            template_dir: Base template directory path

        Returns:
            Dict mapping GitLab Flow keywords to their content
        """
        if not enabled:
            # Return empty content for all GitLab Flow keywords when disabled
            return {keyword: "" for keyword in self._gitlab_flow_config["template_file_mapping"].keys()}

        # Detect platform if not specified
        if platform == "auto":
            platform = "windows" if os.name == "nt" else "unix"

        # Get platform-specific commands using helper method
        commands = self._detect_platform_commands(platform)

        # Load markdown content and replace platform-specific placeholders
        keywords = {}
        for keyword, filename in self._gitlab_flow_config["template_file_mapping"].items():
            # Use configurable template directory
            file_path = Path(template_dir) / self._gitlab_flow_config["template_dir"] / filename if template_dir else None

            if file_path and file_path.exists():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Replace platform-specific command placeholders
                    for cmd_key, cmd_value in commands.items():
                        content = content.replace(f"{{{cmd_key}}}", cmd_value)

                    keywords[keyword] = content
                except (IOError, OSError) as e:
                    # Graceful fallback for file reading errors
                    keywords[keyword] = f"<!-- GitLab Flow file error: {filename} - {str(e)} -->"
            else:
                # Graceful fallback for missing files
                keywords[keyword] = f"<!-- GitLab Flow file not found: {filename} -->"

        return keywords


# Global configuration instance for CLI application
config = ConfigCompatibilityLayer()

# Legacy exports for backward compatibility during migration
AI_TOOLS = config.AI_TOOLS
APP_TYPES = config.APP_TYPES
BANNER = config.BANNER
TAGLINE = config.TAGLINE
LOCAL_TEMPLATES_DIR = config.LOCAL_TEMPLATES_DIR
DOWNLOAD_TEMPLATES_DIR = config.DOWNLOAD_TEMPLATES_DIR
DEFAULT_GITHUB_REPO = config.DEFAULT_GITHUB_REPO
DEFAULT_GITHUB_BRANCH = config.DEFAULT_GITHUB_BRANCH
FALLBACK_GITHUB_BRANCHES = config.FALLBACK_GITHUB_BRANCHES
GITLAB_FLOW_CONFIG = config._gitlab_flow_config
