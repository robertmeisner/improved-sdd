"""Centralized configuration management with migration compatibility.

This module provides a centralized location for all configuration constants
with a compatibility layer to ensure smooth migration from the monolithic CLI.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
import logging

# YAML support for configuration loading
try:
    import yaml
except ImportError:
    yaml = None

# Optional dependency for GitHub API access  
try:
    import httpx
except ImportError:
    httpx = None

# Type checking imports to avoid circular imports
if TYPE_CHECKING:
    from .models import AITool, AIToolConfig, SDDConfig


class YAMLConfigurationError(Exception):
    """Base exception for YAML configuration errors."""
    pass


class InvalidYAMLError(YAMLConfigurationError):
    """Invalid YAML syntax in configuration file."""
    pass


class MissingConfigError(YAMLConfigurationError):
    """Required configuration is missing."""
    pass


class ConfigurationLoader:
    """Base class for configuration loading with hierarchy support."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def load_local_config(self, project_root: Union[str, Path]) -> Dict[str, Any]:
        """Load configuration from local .sdd_templates/sdd-config.yaml.
        
        Args:
            project_root: Root directory of the project
            
        Returns:
            Dictionary containing local configuration or empty dict
        """
        if yaml is None:
            self.logger.warning("PyYAML not installed, skipping YAML configuration loading")
            return {}
            
        project_path = Path(project_root) if isinstance(project_root, str) else project_root
        config_path = project_path / ".sdd_templates" / "sdd-config.yaml"
        
        if not config_path.exists():
            self.logger.debug(f"Local config file not found: {config_path}")
            return {}
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content.strip():
                    self.logger.warning(f"Empty YAML configuration file: {config_path}")
                    return {}
                    
                config = yaml.safe_load(content)
                if config is None:
                    return {}
                    
                self.logger.info(f"Loaded local configuration from {config_path}")
                return config
                
        except yaml.YAMLError as e:
            self.logger.error(f"Invalid YAML in {config_path}: {e}")
            raise InvalidYAMLError(f"Invalid YAML syntax in {config_path}: {e}")
        except (IOError, OSError) as e:
            self.logger.error(f"Error reading config file {config_path}: {e}")
            return {}
    
    def load_remote_config(self, github_repo: str = "robertmeisner/improved-sdd", 
                          branch: str = "master") -> Dict[str, Any]:
        """Load configuration from GitHub repository.
        
        Args:
            github_repo: GitHub repository in 'owner/repo' format
            branch: Branch to load from
            
        Returns:
            Dictionary containing remote configuration or empty dict
        """
        if yaml is None or httpx is None:
            self.logger.warning("PyYAML or httpx not available, skipping remote config loading")
            return {}
            
        url = f"https://raw.githubusercontent.com/{github_repo}/{branch}/templates/sdd-config.yaml"
        
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(url)
                response.raise_for_status()
                
                content = response.text
                if not content.strip():
                    self.logger.warning(f"Empty remote configuration from {url}")
                    return {}
                    
                config = yaml.safe_load(content)
                if config is None:
                    return {}
                    
                self.logger.info(f"Loaded remote configuration from {url}")
                return config
                
        except httpx.RequestError as e:
            self.logger.warning(f"Failed to fetch remote config from {url}: {e}")
            return {}
        except yaml.YAMLError as e:
            self.logger.error(f"Invalid YAML in remote config {url}: {e}")
            raise InvalidYAMLError(f"Invalid YAML syntax in remote config: {e}")
    
    def deep_merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced deep merge configuration dictionaries with override taking precedence.
        
        Handles complex data types including lists, sets, and nested structures.
        
        Args:
            base: Base configuration dictionary
            override: Override configuration dictionary
            
        Returns:
            Merged configuration dictionary
        """
        if not isinstance(override, dict):
            return base if isinstance(base, dict) else override
        if not isinstance(base, dict):
            return override
            
        result = base.copy()
        
        for key, value in override.items():
            if key in result:
                base_value = result[key]
                
                # Handle nested dictionaries
                if isinstance(base_value, dict) and isinstance(value, dict):
                    result[key] = self.deep_merge_configs(base_value, value)
                # Handle lists - override completely (don't merge arrays)
                elif isinstance(base_value, list) and isinstance(value, list):
                    result[key] = value.copy()
                # Handle other types - override takes precedence
                else:
                    result[key] = value
            else:
                # New key from override
                if isinstance(value, dict):
                    result[key] = value.copy()
                elif isinstance(value, list):
                    result[key] = value.copy()
                else:
                    result[key] = value
                
        return result
    
    def validate_yaml_syntax(self, content: str, source: str = "configuration") -> Dict[str, Any]:
        """Validate YAML syntax and return parsed content with validation results.
        
        Args:
            content: YAML content string
            source: Source description for error messages
            
        Returns:
            Dictionary containing parsed content and validation info
            
        Raises:
            InvalidYAMLError: If YAML syntax is invalid
        """
        validation_result = {
            "valid": True,
            "parsed_content": {},
            "warnings": [],
            "errors": []
        }
        
        if not content or not content.strip():
            validation_result["warnings"].append(f"Empty {source}")
            return validation_result
            
        try:
            parsed = yaml.safe_load(content)
            if parsed is None:
                validation_result["warnings"].append(f"Empty or null content in {source}")
                return validation_result
                
            validation_result["parsed_content"] = parsed
            
            # Basic structure validation
            if isinstance(parsed, dict):
                # Check for required version field
                if "version" not in parsed:
                    validation_result["warnings"].append("Missing 'version' field in configuration")
                
                # Validate AI tools structure
                if "ai_tools" in parsed:
                    self._validate_ai_tools_structure(parsed["ai_tools"], validation_result)
                
                # Validate CLI configuration structure
                if "cli" in parsed:
                    self._validate_cli_structure(parsed["cli"], validation_result)
                    
            else:
                validation_result["warnings"].append(f"Configuration should be a dictionary, got {type(parsed)}")
                
        except yaml.YAMLError as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Invalid YAML syntax in {source}: {e}")
            raise InvalidYAMLError(f"Invalid YAML syntax in {source}: {e}")
        except Exception as e:
            validation_result["warnings"].append(f"Unexpected error validating {source}: {e}")
            
        return validation_result
    
    def _validate_ai_tools_structure(self, ai_tools: Any, validation_result: Dict[str, Any]) -> None:
        """Validate AI tools configuration structure.
        
        Args:
            ai_tools: AI tools configuration to validate
            validation_result: Validation result dictionary to update
        """
        if not isinstance(ai_tools, dict):
            validation_result["warnings"].append("AI tools configuration should be a dictionary")
            return
            
        for tool_id, tool_config in ai_tools.items():
            if not isinstance(tool_config, dict):
                validation_result["warnings"].append(f"AI tool '{tool_id}' configuration should be a dictionary")
                continue
                
            # Check for managed_files structure
            if "managed_files" in tool_config:
                managed_files = tool_config["managed_files"]
                if not isinstance(managed_files, dict):
                    validation_result["warnings"].append(f"AI tool '{tool_id}' managed_files should be a dictionary")
                else:
                    # Validate managed files categories
                    expected_categories = ["chatmodes", "instructions", "prompts", "commands"]
                    for category in managed_files:
                        if category not in expected_categories:
                            validation_result["warnings"].append(f"AI tool '{tool_id}' has unknown managed_files category: {category}")
                        elif not isinstance(managed_files[category], list):
                            validation_result["warnings"].append(f"AI tool '{tool_id}' managed_files.{category} should be a list")
                        else:
                            # Check for empty lists
                            if not managed_files[category]:
                                validation_result["warnings"].append(f"AI tool '{tool_id}' managed_files.{category} is empty")
                            # Check for duplicate files within category
                            file_list = managed_files[category]
                            if len(file_list) != len(set(file_list)):
                                validation_result["warnings"].append(f"AI tool '{tool_id}' managed_files.{category} contains duplicates")
    
    def _validate_cli_structure(self, cli_config: Any, validation_result: Dict[str, Any]) -> None:
        """Validate CLI configuration structure.
        
        Args:
            cli_config: CLI configuration to validate
            validation_result: Validation result dictionary to update
        """
        if not isinstance(cli_config, dict):
            validation_result["warnings"].append("CLI configuration should be a dictionary")
            return
            
        # Validate delete_behavior if present
        if "delete_behavior" in cli_config:
            delete_behavior = cli_config["delete_behavior"]
            if not isinstance(delete_behavior, dict):
                validation_result["warnings"].append("CLI delete_behavior should be a dictionary")
            else:
                # Check boolean fields
                boolean_fields = ["confirm_before_delete", "show_file_preview", "group_by_ai_tool"]
                for field in boolean_fields:
                    if field in delete_behavior and not isinstance(delete_behavior[field], bool):
                        validation_result["warnings"].append(f"CLI delete_behavior.{field} should be a boolean")
    
    def detect_configuration_conflicts(self, config: Dict[str, Any]) -> List[str]:
        """Detect potential conflicts in configuration.
        
        Args:
            config: Configuration dictionary to analyze
            
        Returns:
            List of conflict descriptions
        """
        conflicts = []
        
        if "ai_tools" not in config:
            return conflicts
            
        ai_tools = config["ai_tools"]
        if not isinstance(ai_tools, dict):
            return conflicts
            
        # Check for file conflicts across AI tools
        all_files = {}  # filename -> list of tools that claim it
        
        for tool_id, tool_config in ai_tools.items():
            if not isinstance(tool_config, dict) or "managed_files" not in tool_config:
                continue
                
            managed_files = tool_config["managed_files"]
            if not isinstance(managed_files, dict):
                continue
                
            for category, file_list in managed_files.items():
                if not isinstance(file_list, list):
                    continue
                    
                for filename in file_list:
                    if filename not in all_files:
                        all_files[filename] = []
                    all_files[filename].append(f"{tool_id}:{category}")
        
        # Report conflicts
        for filename, claiming_tools in all_files.items():
            if len(claiming_tools) > 1:
                conflicts.append(f"File '{filename}' claimed by multiple tools: {', '.join(claiming_tools)}")
                
        return conflicts
    
    def load_configuration_hierarchy(self, project_root: Union[str, Path] = ".", 
                                   github_repo: str = "robertmeisner/improved-sdd",
                                   branch: str = "master") -> Dict[str, Any]:
        """Load configuration using hierarchy: local override → GitHub remote → hardcoded defaults.
        
        Args:
            project_root: Root directory of the project
            github_repo: GitHub repository for remote config
            branch: Branch to load remote config from
            
        Returns:
            Merged configuration dictionary
        """
        # Start with empty config (hardcoded defaults will be applied by ConfigCompatibilityLayer)
        config = {}
        
        # Load remote configuration first (lower priority)
        try:
            remote_config = self.load_remote_config(github_repo, branch)
            if remote_config:
                config = self.deep_merge_configs(config, remote_config)
                self.logger.debug("Applied remote configuration")
        except Exception as e:
            self.logger.warning(f"Error loading remote configuration: {e}")
        
        # Load local configuration last (highest priority)
        try:
            local_config = self.load_local_config(project_root)
            if local_config:
                config = self.deep_merge_configs(config, local_config)
                self.logger.debug("Applied local configuration override")
        except Exception as e:
            self.logger.warning(f"Error loading local configuration: {e}")
        
        return config


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
        """Initialize configuration with original data structures and YAML loading capability."""
        
        # Initialize logger for configuration loading
        self.logger = logging.getLogger(__name__)
        
        # Initialize YAML configuration loader
        self._config_loader = ConfigurationLoader(self.logger)
        
        # Cache for loaded YAML configuration
        self._yaml_config_cache = {}
        self._yaml_cache_valid = False
        self._last_project_root = None
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
    
    # AI Tool Configuration Model Conversion Methods
    
    def get_ai_tool_config_model(self, tool_id: str) -> 'AIToolConfig':
        """Get AI tool configuration as Pydantic model.
        
        Args:
            tool_id: ID of the AI tool
            
        Returns:
            AIToolConfig instance
            
        Raises:
            KeyError: If tool_id is not found
        """
        from .models import AIToolConfig, ManagedFiles, FileExtensions, KeywordReplacements
        
        if tool_id not in self._ai_tools_data:
            raise KeyError(f"AI tool '{tool_id}' not found")
        
        data = self._ai_tools_data[tool_id]
        
        # Create ManagedFiles (currently empty, will be populated from YAML config)
        managed_files = ManagedFiles()
        
        # Create FileExtensions if present
        file_extensions = None
        if "file_extensions" in data:
            file_extensions = FileExtensions(**data["file_extensions"])
        
        # Create KeywordReplacements if present  
        keywords = None
        if "keywords" in data:
            keywords = KeywordReplacements(**data["keywords"])
        
        return AIToolConfig(
            name=data["name"],
            description=data.get("description", ""),
            template_dir=data["template_dir"],
            managed_files=managed_files,
            file_extensions=file_extensions,
            keywords=keywords,
        )
    
    def get_ai_tool_runtime(self, tool_id: str) -> 'AITool':
        """Get AI tool as runtime dataclass.
        
        Args:
            tool_id: ID of the AI tool
            
        Returns:
            AITool instance
            
        Raises:
            KeyError: If tool_id is not found
        """
        from .models import AITool
        
        config_model = self.get_ai_tool_config_model(tool_id)
        return AITool.from_config(tool_id, config_model)
    
    def get_all_ai_tools_config_models(self) -> Dict[str, 'AIToolConfig']:
        """Get all AI tools as Pydantic configuration models.
        
        Returns:
            Dictionary mapping tool IDs to AIToolConfig instances
        """
        return {tool_id: self.get_ai_tool_config_model(tool_id) for tool_id in self._ai_tools_data.keys()}
    
    def get_all_ai_tools_runtime(self) -> List['AITool']:
        """Get all AI tools as runtime dataclasses.
        
        Returns:
            List of AITool instances
        """
        return [self.get_ai_tool_runtime(tool_id) for tool_id in self._ai_tools_data.keys()]
    
    def create_sdd_config_model(self, yaml_config: Optional[Dict[str, Any]] = None) -> 'SDDConfig':
        """Create complete SDD configuration model.
        
        Args:
            yaml_config: Optional YAML configuration to merge
            
        Returns:
            SDDConfig instance with all AI tools and settings
        """
        from .models import SDDConfig, AIToolConfig, CLIConfig, PreferencesConfig
        
        # Start with default config
        ai_tools = self.get_all_ai_tools_config_models()
        
        # If YAML config provided, merge/override AI tools
        if yaml_config and "ai_tools" in yaml_config:
            yaml_ai_tools = yaml_config["ai_tools"]
            for tool_id, tool_config in yaml_ai_tools.items():
                if isinstance(tool_config, dict):
                    try:
                        ai_tools[tool_id] = AIToolConfig(**tool_config)
                    except Exception as e:
                        # Log validation error but continue
                        self.logger.warning(f"Invalid AI tool config for '{tool_id}': {e}")
        
        # Create CLI and preferences config from YAML if present
        cli_config = CLIConfig()
        if yaml_config and "cli" in yaml_config:
            try:
                cli_config = CLIConfig(**yaml_config["cli"])
            except Exception as e:
                self.logger.warning(f"Invalid CLI config: {e}")
        
        preferences_config = PreferencesConfig()
        if yaml_config and "preferences" in yaml_config:
            try:
                preferences_config = PreferencesConfig(**yaml_config["preferences"])
            except Exception as e:
                self.logger.warning(f"Invalid preferences config: {e}")
        
        return SDDConfig(
            version=yaml_config.get("version", "1.0") if yaml_config else "1.0",
            ai_tools=ai_tools,
            cli=cli_config,
            preferences=preferences_config,
        )
    
    def create_ai_tool_manager(self, logger: Optional[logging.Logger] = None) -> 'AIToolManager':
        """Create AIToolManager instance with this configuration.
        
        Args:
            logger: Optional logger instance
            
        Returns:
            AIToolManager instance
        """
        from .ai_tool_manager import AIToolManager
        return AIToolManager(self, logger)

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
    
    # YAML Configuration Methods
    
    def load_yaml_config(self, project_root: Union[str, Path] = ".", 
                        github_repo: Optional[str] = None,
                        branch: Optional[str] = None, 
                        force_reload: bool = False) -> Dict[str, Any]:
        """Load YAML configuration using hierarchy: local override → GitHub remote → hardcoded defaults.
        
        Args:
            project_root: Root directory of the project
            github_repo: GitHub repository for remote config (uses default if None)
            branch: Branch to load remote config from (uses default if None)
            force_reload: Force reload even if cache is valid
            
        Returns:
            Merged configuration dictionary
        """
        project_path = Path(project_root) if isinstance(project_root, str) else project_root
        
        # Check cache validity
        if (not force_reload and 
            self._yaml_cache_valid and 
            self._last_project_root == str(project_path) and 
            self._yaml_config_cache):
            return self._yaml_config_cache.copy()
        
        # Use defaults if not provided
        repo = github_repo or self._github_config["default_repo"]
        branch_name = branch or self._github_config["default_branch"]
        
        # Load configuration hierarchy
        try:
            config = self._config_loader.load_configuration_hierarchy(
                project_root=project_path,
                github_repo=repo,
                branch=branch_name
            )
            
            # Cache the results
            self._yaml_config_cache = config.copy()
            self._yaml_cache_valid = True
            self._last_project_root = str(project_path)
            
            return config
            
        except Exception as e:
            self.logger.error(f"Error loading YAML configuration: {e}")
            return {}
    
    def get_merged_ai_tools_config(self, project_root: Union[str, Path] = ".") -> Dict[str, Dict]:
        """Get AI tools configuration merged with YAML overrides.
        
        Args:
            project_root: Root directory of the project
            
        Returns:
            AI tools configuration with YAML overrides applied
        """
        # Start with hardcoded AI tools
        base_config = self._ai_tools_data.copy()
        
        # Load YAML configuration
        yaml_config = self.load_yaml_config(project_root)
        
        # Merge YAML AI tools if present
        if "ai_tools" in yaml_config and isinstance(yaml_config["ai_tools"], dict):
            base_config = self._config_loader.deep_merge_configs(base_config, yaml_config["ai_tools"])
            self.logger.debug("Applied YAML AI tools configuration overrides")
        
        return base_config
    
    def get_yaml_managed_files(self, tool_id: str, project_root: Union[str, Path] = ".") -> Dict[str, List[str]]:
        """Get managed files for an AI tool from YAML configuration.
        
        Args:
            tool_id: ID of the AI tool
            project_root: Root directory of the project
            
        Returns:
            Dictionary with managed files by category (chatmodes, instructions, prompts, commands)
        """
        ai_tools_config = self.get_merged_ai_tools_config(project_root)
        
        if tool_id not in ai_tools_config:
            self.logger.warning(f"AI tool '{tool_id}' not found in configuration")
            return {"chatmodes": [], "instructions": [], "prompts": [], "commands": []}
        
        tool_config = ai_tools_config[tool_id]
        managed_files = tool_config.get("managed_files", {})
        
        # Ensure all categories exist with empty lists as defaults
        return {
            "chatmodes": managed_files.get("chatmodes", []),
            "instructions": managed_files.get("instructions", []),
            "prompts": managed_files.get("prompts", []),
            "commands": managed_files.get("commands", [])
        }
    
    def get_cli_behavior_config(self, project_root: Union[str, Path] = ".") -> Dict[str, Any]:
        """Get CLI behavior configuration from YAML with defaults.
        
        Args:
            project_root: Root directory of the project
            
        Returns:
            CLI behavior configuration dictionary
        """
        yaml_config = self.load_yaml_config(project_root)
        
        # Default CLI behavior configuration
        default_config = {
            "delete_behavior": {
                "confirm_before_delete": True,
                "show_file_preview": True,
                "group_by_ai_tool": True
            }
        }
        
        # Merge with YAML CLI configuration if present
        if "cli" in yaml_config and isinstance(yaml_config["cli"], dict):
            return self._config_loader.deep_merge_configs(default_config, yaml_config["cli"])
        
        return default_config
    
    def get_user_preferences(self, project_root: Union[str, Path] = ".") -> Dict[str, Any]:
        """Get user preferences from YAML with defaults.
        
        Args:
            project_root: Root directory of the project
            
        Returns:
            User preferences configuration dictionary
        """
        yaml_config = self.load_yaml_config(project_root)
        
        # Default preferences
        default_preferences = {
            "default_ai_tools": ["github-copilot"],
            "template_source": "github"
        }
        
        # Merge with YAML preferences if present
        if "preferences" in yaml_config and isinstance(yaml_config["preferences"], dict):
            return self._config_loader.deep_merge_configs(default_preferences, yaml_config["preferences"])
        
        return default_preferences
    
    def invalidate_yaml_cache(self) -> None:
        """Invalidate the YAML configuration cache.
        
        Use this method when configuration files have been updated and cache needs refresh.
        """
        self._yaml_config_cache.clear()
        self._yaml_cache_valid = False
        self._last_project_root = None
        self.logger.debug("YAML configuration cache invalidated")
    
    def validate_yaml_config(self, project_root: Union[str, Path] = ".") -> Dict[str, Any]:
        """Validate YAML configuration and return validation results.
        
        Args:
            project_root: Root directory of the project
            
        Returns:
            Dictionary containing validation results
        """
        validation_result = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "config_found": False,
            "sources": []
        }
        
        try:
            # Check if local config exists
            project_path = Path(project_root) if isinstance(project_root, str) else project_root
            local_config_path = project_path / ".sdd_templates" / "sdd-config.yaml"
            
            if local_config_path.exists():
                validation_result["config_found"] = True
                validation_result["sources"].append(f"Local: {local_config_path}")
            
            # Attempt to load configuration
            config = self.load_yaml_config(project_root)
            
            if config:
                validation_result["config_found"] = True
                
                # Validate AI tools structure
                if "ai_tools" in config:
                    for tool_id, tool_config in config["ai_tools"].items():
                        if not isinstance(tool_config, dict):
                            validation_result["warnings"].append(f"AI tool '{tool_id}' configuration is not a dictionary")
                            continue
                            
                        # Check for managed_files structure
                        if "managed_files" in tool_config:
                            managed_files = tool_config["managed_files"]
                            if not isinstance(managed_files, dict):
                                validation_result["warnings"].append(f"AI tool '{tool_id}' managed_files is not a dictionary")
                            else:
                                for category in ["chatmodes", "instructions", "prompts", "commands"]:
                                    if category in managed_files and not isinstance(managed_files[category], list):
                                        validation_result["warnings"].append(f"AI tool '{tool_id}' managed_files.{category} is not a list")
            
        except InvalidYAMLError as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Invalid YAML syntax: {e}")
        except Exception as e:
            validation_result["warnings"].append(f"Error during validation: {e}")
        
        return validation_result
    
    # YAML Configuration Methods
    
    def load_yaml_config(self, project_root: Union[str, Path] = ".", 
                        github_repo: Optional[str] = None,
                        branch: Optional[str] = None, 
                        force_reload: bool = False) -> Dict[str, Any]:
        """Load YAML configuration using hierarchy: local override → GitHub remote → hardcoded defaults.
        
        Args:
            project_root: Root directory of the project
            github_repo: GitHub repository for remote config (uses default if None)
            branch: Branch to load remote config from (uses default if None)
            force_reload: Force reload even if cache is valid
            
        Returns:
            Merged configuration dictionary
        """
        project_path = Path(project_root) if isinstance(project_root, str) else project_root
        
        # Check cache validity
        if (not force_reload and 
            self._yaml_cache_valid and 
            self._last_project_root == str(project_path) and 
            self._yaml_config_cache):
            return self._yaml_config_cache.copy()
        
        # Use defaults if not provided
        repo = github_repo or self._github_config["default_repo"]
        branch_name = branch or self._github_config["default_branch"]
        
        # Load configuration hierarchy
        try:
            config = self._config_loader.load_configuration_hierarchy(
                project_root=project_path,
                github_repo=repo,
                branch=branch_name
            )
            
            # Cache the results
            self._yaml_config_cache = config.copy()
            self._yaml_cache_valid = True
            self._last_project_root = str(project_path)
            
            return config
            
        except Exception as e:
            self.logger.error(f"Error loading YAML configuration: {e}")
            return {}
    
    def get_merged_ai_tools_config(self, project_root: Union[str, Path] = ".") -> Dict[str, Dict]:
        """Get AI tools configuration merged with YAML overrides.
        
        Args:
            project_root: Root directory of the project
            
        Returns:
            AI tools configuration with YAML overrides applied
        """
        # Start with hardcoded AI tools
        base_config = self._ai_tools_data.copy()
        
        # Load YAML configuration
        yaml_config = self.load_yaml_config(project_root)
        
        # Merge YAML AI tools if present
        if "ai_tools" in yaml_config and isinstance(yaml_config["ai_tools"], dict):
            base_config = self._config_loader.deep_merge_configs(base_config, yaml_config["ai_tools"])
            self.logger.debug("Applied YAML AI tools configuration overrides")
        
        return base_config
    
    def get_yaml_managed_files(self, tool_id: str, project_root: Union[str, Path] = ".") -> Dict[str, List[str]]:
        """Get managed files for an AI tool from YAML configuration.
        
        Args:
            tool_id: ID of the AI tool
            project_root: Root directory of the project
            
        Returns:
            Dictionary with managed files by category (chatmodes, instructions, prompts, commands)
        """
        ai_tools_config = self.get_merged_ai_tools_config(project_root)
        
        if tool_id not in ai_tools_config:
            self.logger.warning(f"AI tool '{tool_id}' not found in configuration")
            return {"chatmodes": [], "instructions": [], "prompts": [], "commands": []}
        
        tool_config = ai_tools_config[tool_id]
        managed_files = tool_config.get("managed_files", {})
        
        # Ensure all categories exist with empty lists as defaults
        return {
            "chatmodes": managed_files.get("chatmodes", []),
            "instructions": managed_files.get("instructions", []),
            "prompts": managed_files.get("prompts", []),
            "commands": managed_files.get("commands", [])
        }
    
    def get_cli_behavior_config(self, project_root: Union[str, Path] = ".") -> Dict[str, Any]:
        """Get CLI behavior configuration from YAML with defaults.
        
        Args:
            project_root: Root directory of the project
            
        Returns:
            CLI behavior configuration dictionary
        """
        yaml_config = self.load_yaml_config(project_root)
        
        # Default CLI behavior configuration
        default_config = {
            "delete_behavior": {
                "confirm_before_delete": True,
                "show_file_preview": True,
                "group_by_ai_tool": True
            }
        }
        
        # Merge with YAML CLI configuration if present
        if "cli" in yaml_config and isinstance(yaml_config["cli"], dict):
            return self._config_loader.deep_merge_configs(default_config, yaml_config["cli"])
        
        return default_config
    
    def get_user_preferences(self, project_root: Union[str, Path] = ".") -> Dict[str, Any]:
        """Get user preferences from YAML with defaults.
        
        Args:
            project_root: Root directory of the project
            
        Returns:
            User preferences configuration dictionary
        """
        yaml_config = self.load_yaml_config(project_root)
        
        # Default preferences
        default_preferences = {
            "default_ai_tools": ["github-copilot"],
            "template_source": "github"
        }
        
        # Merge with YAML preferences if present
        if "preferences" in yaml_config and isinstance(yaml_config["preferences"], dict):
            return self._config_loader.deep_merge_configs(default_preferences, yaml_config["preferences"])
        
        return default_preferences
    
    def invalidate_yaml_cache(self) -> None:
        """Invalidate the YAML configuration cache.
        
        Use this method when configuration files have been updated and cache needs refresh.
        """
        self._yaml_config_cache.clear()
        self._yaml_cache_valid = False
        self._last_project_root = None
        self.logger.debug("YAML configuration cache invalidated")
    
    def validate_yaml_config(self, project_root: Union[str, Path] = ".") -> Dict[str, Any]:
        """Validate YAML configuration and return validation results.
        
        Args:
            project_root: Root directory of the project
            
        Returns:
            Dictionary containing validation results
        """
        validation_result = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "config_found": False,
            "sources": []
        }
        
        try:
            # Check if local config exists
            project_path = Path(project_root) if isinstance(project_root, str) else project_root
            local_config_path = project_path / ".sdd_templates" / "sdd-config.yaml"
            
            if local_config_path.exists():
                validation_result["config_found"] = True
                validation_result["sources"].append(f"Local: {local_config_path}")
            
            # Attempt to load configuration
            config = self.load_yaml_config(project_root)
            
            if config:
                validation_result["config_found"] = True
                
                # Validate AI tools structure
                if "ai_tools" in config:
                    for tool_id, tool_config in config["ai_tools"].items():
                        if not isinstance(tool_config, dict):
                            validation_result["warnings"].append(f"AI tool '{tool_id}' configuration is not a dictionary")
                            continue
                            
                        # Check for managed_files structure
                        if "managed_files" in tool_config:
                            managed_files = tool_config["managed_files"]
                            if not isinstance(managed_files, dict):
                                validation_result["warnings"].append(f"AI tool '{tool_id}' managed_files is not a dictionary")
                            else:
                                for category in ["chatmodes", "instructions", "prompts", "commands"]:
                                    if category in managed_files and not isinstance(managed_files[category], list):
                                        validation_result["warnings"].append(f"AI tool '{tool_id}' managed_files.{category} is not a list")
            
        except InvalidYAMLError as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Invalid YAML syntax: {e}")
        except Exception as e:
            validation_result["warnings"].append(f"Error during validation: {e}")
        
        return validation_result
    
    # Enhanced Configuration Management Methods
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about current cache state.
        
        Returns:
            Dictionary containing cache information and statistics
        """
        return {
            "yaml_cache": {
                "valid": self._yaml_cache_valid,
                "project_root": self._last_project_root,
                "entries": len(self._yaml_config_cache),
                "size_bytes": len(str(self._yaml_config_cache))
            },
            "gitlab_flow_cache": {
                "valid": self._gitlab_flow_cache["cache_valid"],
                "last_template_dir": self._gitlab_flow_cache["last_template_dir"],
                "entries": len(self._gitlab_flow_cache["cached_content"])
            }
        }
    
    def clear_all_caches(self) -> None:
        """Clear all configuration caches."""
        self.invalidate_yaml_cache()
        self.invalidate_gitlab_flow_cache()
        self.logger.info("All configuration caches cleared")
    
    def validate_and_load_config(self, project_root: Union[str, Path] = ".") -> Dict[str, Any]:
        """Load configuration with comprehensive validation and conflict detection.
        
        Args:
            project_root: Root directory of the project
            
        Returns:
            Dictionary containing validation results and loaded configuration
        """
        project_path = Path(project_root) if isinstance(project_root, str) else project_root
        
        result = {
            "valid": True,
            "config": {},
            "validation": {
                "warnings": [],
                "errors": [],
                "conflicts": []
            },
            "sources": [],
            "cache_used": False
        }
        
        try:
            # Check cache first
            if (self._yaml_cache_valid and 
                self._last_project_root == str(project_path) and 
                self._yaml_config_cache):
                result["config"] = self._yaml_config_cache.copy()
                result["cache_used"] = True
                result["sources"].append("Cache")
                self.logger.debug("Configuration loaded from cache")
            else:
                # Load with validation
                config = self.load_yaml_config(project_path)
                result["config"] = config
                
                if config:
                    # Detect conflicts
                    conflicts = self._config_loader.detect_configuration_conflicts(config)
                    result["validation"]["conflicts"] = conflicts
                    
                    if conflicts:
                        self.logger.warning(f"Configuration conflicts detected: {len(conflicts)} issues")
                        for conflict in conflicts:
                            self.logger.warning(f"  - {conflict}")
                
                # Determine sources
                local_config_path = project_path / ".sdd_templates" / "sdd-config.yaml"
                if local_config_path.exists():
                    result["sources"].append(f"Local: {local_config_path}")
                result["sources"].append("Remote: GitHub templates (attempted)")
                result["sources"].append("Hardcoded defaults")
            
        except InvalidYAMLError as e:
            result["valid"] = False
            result["validation"]["errors"].append(str(e))
        except Exception as e:
            result["validation"]["warnings"].append(f"Configuration loading error: {e}")
            
        return result
    
    def get_comprehensive_validation(self, project_root: Union[str, Path] = ".") -> Dict[str, Any]:
        """Get comprehensive validation report for configuration.
        
        Args:
            project_root: Root directory of the project
            
        Returns:
            Detailed validation report
        """
        project_path = Path(project_root) if isinstance(project_root, str) else project_root
        
        validation = {
            "overall_status": "valid",
            "summary": {
                "total_warnings": 0,
                "total_errors": 0,
                "total_conflicts": 0
            },
            "details": {
                "yaml_syntax": {"valid": True, "issues": []},
                "structure": {"valid": True, "issues": []},
                "conflicts": {"detected": False, "issues": []},
                "cache": {"info": self.get_cache_info()}
            },
            "recommendations": []
        }
        
        try:
            # Load and validate configuration
            config_result = self.validate_and_load_config(project_path)
            
            # Aggregate results
            validation["summary"]["total_warnings"] = len(config_result["validation"]["warnings"])
            validation["summary"]["total_errors"] = len(config_result["validation"]["errors"])
            validation["summary"]["total_conflicts"] = len(config_result["validation"]["conflicts"])
            
            # Set overall status
            if config_result["validation"]["errors"]:
                validation["overall_status"] = "invalid"
            elif config_result["validation"]["warnings"] or config_result["validation"]["conflicts"]:
                validation["overall_status"] = "warnings"
            
            # Populate details
            validation["details"]["structure"]["issues"] = config_result["validation"]["warnings"]
            validation["details"]["conflicts"]["issues"] = config_result["validation"]["conflicts"]
            validation["details"]["conflicts"]["detected"] = len(config_result["validation"]["conflicts"]) > 0
            
            if config_result["validation"]["errors"]:
                validation["details"]["yaml_syntax"]["valid"] = False
                validation["details"]["yaml_syntax"]["issues"] = config_result["validation"]["errors"]
            
            # Generate recommendations
            if validation["summary"]["total_conflicts"] > 0:
                validation["recommendations"].append("Resolve file conflicts between AI tools")
            
            if validation["summary"]["total_warnings"] > 0:
                validation["recommendations"].append("Review and fix configuration warnings")
                
            if not config_result["cache_used"]:
                validation["recommendations"].append("Configuration will be cached for better performance")
                
        except Exception as e:
            validation["overall_status"] = "error"
            validation["details"]["structure"]["issues"].append(f"Validation error: {e}")
            
        return validation


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
