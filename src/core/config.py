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
                "{GITLAB_FLOW_WORKFLOW}": "gitlab-flow-workflow.md",
                "{GITLAB_FLOW_PR}": "gitlab-flow-pr.md",
            },
            "platform_keywords": {
                "windows": {
                    "{GIT_STATUS}": "git status",
                    "{BRANCH_CREATE}": "git checkout -b feature/spec-{spec-name}",
                    "{COMMIT}": 'git add . ; git commit -m "{message}"',
                    "{PUSH_PR}": 'git push -u origin feature/spec-{spec-name} ; gh pr create --title "Spec: {spec-name}" --body "Implementation of {spec-name} specification"',
                    "{AUTO_COMMIT}": 'git add . ; git commit -m "{commit-message}"',
                },
                "unix": {
                    "{GIT_STATUS}": "git status",
                    "{BRANCH_CREATE}": "git checkout -b feature/spec-{spec-name}",
                    "{COMMIT}": 'git add . && git commit -m "{message}"',
                    "{PUSH_PR}": 'git push -u origin feature/spec-{spec-name} && gh pr create --title "Spec: {spec-name}" --body "Implementation of {spec-name} specification"',
                    "{AUTO_COMMIT}": 'git add . ; git commit -m "{commit-message}"',
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

        # GitLab Flow template cache for performance
        self._gitlab_flow_cache = {
            "last_template_dir": None,
            "cached_content": {},
            "cache_valid": False
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

    def validate_gitlab_flow_templates(self, template_dir: str = "") -> Dict[str, Any]:
        """Validate that all required GitLab Flow template files exist.
        
        Args:
            template_dir: Base template directory path
            
        Returns:
            Dictionary with validation results including status, missing files, and recommendations
        """
        validation_result = {
            "valid": True,
            "missing_files": [],
            "existing_files": [],
            "recommendations": [],
            "template_dir": template_dir or "Not specified"
        }
        
        if not template_dir:
            validation_result["valid"] = False
            validation_result["recommendations"].append("Template directory not specified - provide template_dir parameter")
            return validation_result
        
        # Check each required template file
        gitlab_flow_dir = Path(template_dir) / self._gitlab_flow_config["template_dir"]
        
        for keyword, filename in self._gitlab_flow_config["template_file_mapping"].items():
            file_path = gitlab_flow_dir / filename
            
            if file_path.exists() and file_path.is_file():
                validation_result["existing_files"].append({
                    "keyword": keyword,
                    "filename": filename,
                    "path": str(file_path),
                    "size_bytes": file_path.stat().st_size
                })
            else:
                validation_result["valid"] = False
                validation_result["missing_files"].append({
                    "keyword": keyword,
                    "filename": filename,
                    "expected_path": str(file_path)
                })
        
        # Add recommendations based on validation results
        if validation_result["missing_files"]:
            validation_result["recommendations"].append(f"Create missing template files in {gitlab_flow_dir}")
            validation_result["recommendations"].append("Run 'improved-sdd init --force-download' to re-download templates")
        
        if not gitlab_flow_dir.exists():
            validation_result["recommendations"].append(f"Create GitLab Flow template directory: {gitlab_flow_dir}")
        
        return validation_result

    def _detect_platform_keywords(self, platform: str = "windows") -> Dict[str, str]:
        """Helper method to detect platform-specific git keywords.
        
        Args:
            platform: Target platform ("windows" or "unix")
            
        Returns:
            Dictionary of platform-specific git keywords
        """
        if platform.lower() == "windows":
            return {
                "{GIT_STATUS}": "git status",
                "{BRANCH_CREATE}": "git checkout -b feature/spec-{spec-name}",
                "{COMMIT}": "git add . ; git commit -m \"feat: Add {phase} for {feature-name}\"",
                "{PUSH_PR}": "git push -u origin feature/spec-{feature-name} ; gh pr create --title \"Spec: {feature-name}\" --body \"Implementation of {feature-name} specification\""
            }
        else:  # Unix/Linux/macOS
            return {
                "{GIT_STATUS}": "git status",
                "{BRANCH_CREATE}": "git checkout -b feature/spec-{spec-name}",
                "{COMMIT}": "git add . && git commit -m \"feat: Add {phase} for {feature-name}\"",
                "{PUSH_PR}": "git push -u origin feature/spec-{feature-name} && gh pr create --title \"Spec: {feature-name}\" --body \"Implementation of {feature-name} specification\""
            }

    def get_gitlab_flow_keywords(
        self, enabled: bool = False, platform: str = "windows", template_dir: str = ""
    ) -> Dict[str, str]:
        """Get GitLab Flow keywords populated with content from markdown files.
        
        Args:
            enabled: Whether GitLab Flow is enabled
            platform: Target platform for commands ("windows" or "unix")
            template_dir: Base template directory path
            
        Returns:
            Dictionary of GitLab Flow keywords with content
        """
        if not enabled:
            # Return empty content when GitLab Flow is disabled
            return {keyword: "" for keyword in self._gitlab_flow_config["template_file_mapping"].keys()}
        
        # Check cache validity
        cache_key = f"{template_dir}_{platform}"
        if (self._gitlab_flow_cache["cache_valid"] and 
            self._gitlab_flow_cache["last_template_dir"] == template_dir and
            cache_key in self._gitlab_flow_cache["cached_content"]):
            return self._gitlab_flow_cache["cached_content"][cache_key].copy()
        
        # Get platform-specific keywords using helper method
        platform_keywords = self._detect_platform_keywords(platform)
        
        # Load and populate keywords with markdown file content
        keywords = {}
        
        for keyword, filename in self._gitlab_flow_config["template_file_mapping"].items():
            try:
                # Use configurable template directory
                template_path = Path(template_dir) / self._gitlab_flow_config["template_dir"] / filename if template_dir else None
                
                if template_path and template_path.exists():
                    with open(template_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    # Replace platform-specific keyword placeholders
                    for cmd_key, cmd_value in platform_keywords.items():
                        content = content.replace(cmd_key, cmd_value)
                    
                    keywords[keyword] = content
                else:
                    # Enhanced error message with actionable guidance
                    missing_path = str(template_path) if template_path else "undefined"
                    keywords[keyword] = f"""<!-- GitLab Flow Template Missing -->

**GitLab Flow template not found: {filename}**

Expected location: `{missing_path}`

**Troubleshooting:**
1. Run `improved-sdd init --force-download` to re-download templates
2. Check that GitLab Flow templates are properly installed
3. Verify template directory path is correct

**Alternative:** Use manual git commands for your workflow
"""
            except (IOError, OSError, UnicodeDecodeError) as e:
                # Enhanced error message with specific error details
                keywords[keyword] = f"""<!-- GitLab Flow Template Error -->

**Error loading GitLab Flow template: {filename}**

Error details: {str(e)}

**Troubleshooting:**
1. Check file permissions for template directory
2. Verify file encoding is UTF-8
3. Run `improved-sdd init --force-download` to re-download templates
4. Contact support if issue persists

**Fallback:** Use manual git commands for your workflow
"""
        
        # Cache the results for performance
        self._gitlab_flow_cache["cached_content"][cache_key] = keywords.copy()
        self._gitlab_flow_cache["last_template_dir"] = template_dir
        self._gitlab_flow_cache["cache_valid"] = True
        
        return keywords
    
    def invalidate_gitlab_flow_cache(self) -> None:
        """Invalidate the GitLab Flow template cache.
        
        Use this method when template files have been updated and cache needs refresh.
        """
        self._gitlab_flow_cache["cached_content"].clear()
        self._gitlab_flow_cache["cache_valid"] = False
        self._gitlab_flow_cache["last_template_dir"] = None


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
