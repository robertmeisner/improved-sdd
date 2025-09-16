"""AI Tool Manager for managed file resolution and tool registry.

This module provides the AIToolManager class that acts as the central registry
for AI tools and manages file resolution for precise deletion operations.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Union
import logging

from .models import AITool, AIToolConfig, SDDConfig
from .config import ConfigCompatibilityLayer


@dataclass
class ManagedFileResult:
    """Result of managed file resolution for an AI tool and app type."""
    
    tool_id: str
    tool_name: str
    app_type: str
    managed_files: Dict[str, List[str]]  # file_type -> list of files
    total_files: int
    
    def get_files_by_type(self, file_type: str) -> List[str]:
        """Get managed files for a specific type."""
        return self.managed_files.get(file_type, [])
    
    def get_all_files(self) -> List[str]:
        """Get all managed files across all types."""
        all_files = []
        for files in self.managed_files.values():
            all_files.extend(files)
        return all_files
    
    def has_files(self) -> bool:
        """Check if this tool manages any files for the app type."""
        return self.total_files > 0


@dataclass 
class ActiveToolsResult:
    """Result of active AI tools detection."""
    
    active_tools: List[str]
    source: str  # "config", "defaults", "user_selection"
    confidence: float  # 0.0 to 1.0
    fallback_applied: bool = False
    
    def get_tool_names(self, config: ConfigCompatibilityLayer) -> List[str]:
        """Get display names for active tools."""
        return [config.get_ai_tool_config(tool_id).name for tool_id in self.active_tools 
                if config.validate_ai_tool_id(tool_id)]


class AIToolManager:
    """Manager for AI tool registry and managed file resolution.
    
    This class provides the core functionality for:
    - Tool registry and discovery from configuration
    - Managed file resolution for specific AI tools and app types
    - Active tool detection from user configuration
    - File categorization and conflict detection
    """
    
    def __init__(self, config: ConfigCompatibilityLayer, logger: Optional[logging.Logger] = None):
        """Initialize AI tool manager.
        
        Args:
            config: Configuration compatibility layer
            logger: Optional logger instance
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self._tool_cache: Dict[str, AITool] = {}
        self._active_tools_cache: Optional[ActiveToolsResult] = None
    
    def get_available_tools(self) -> List[str]:
        """Get list of available AI tool IDs.
        
        Returns:
            List of AI tool IDs from configuration
        """
        try:
            return self.config.get_available_ai_tools()
        except Exception as e:
            self.logger.warning(f"Failed to get available tools: {e}")
            return []
    
    def get_tool_info(self, tool_id: str) -> Optional[AITool]:
        """Get AI tool information.
        
        Args:
            tool_id: ID of the AI tool
            
        Returns:
            AITool instance or None if not found
        """
        if tool_id in self._tool_cache:
            return self._tool_cache[tool_id]
        
        try:
            if not self.config.validate_ai_tool_id(tool_id):
                return None
                
            ai_tool = self.config.get_ai_tool_runtime(tool_id)
            self._tool_cache[tool_id] = ai_tool
            return ai_tool
            
        except Exception as e:
            self.logger.warning(f"Failed to get tool info for '{tool_id}': {e}")
            return None
    
    def get_managed_files_for_tool(self, tool_id: str, app_type: Optional[str] = None) -> ManagedFileResult:
        """Get managed files for a specific AI tool.
        
        Args:
            tool_id: ID of the AI tool
            app_type: Optional app type filter (currently not used in file filtering)
            
        Returns:
            ManagedFileResult with resolved files
        """
        tool = self.get_tool_info(tool_id)
        if not tool:
            return ManagedFileResult(
                tool_id=tool_id,
                tool_name="Unknown Tool",
                app_type=app_type or "unknown",
                managed_files={},
                total_files=0
            )
        
        # Get all managed files from the tool
        managed_files = tool.get_managed_files()
        
        # Count total files
        total_files = sum(len(files) for files in managed_files.values())
        
        return ManagedFileResult(
            tool_id=tool_id,
            tool_name=tool.name,
            app_type=app_type or "any",
            managed_files=managed_files,
            total_files=total_files
        )
    
    def get_managed_files_for_tools(self, tool_ids: List[str], app_type: Optional[str] = None) -> List[ManagedFileResult]:
        """Get managed files for multiple AI tools.
        
        Args:
            tool_ids: List of AI tool IDs
            app_type: Optional app type filter
            
        Returns:
            List of ManagedFileResult for each tool
        """
        results = []
        for tool_id in tool_ids:
            result = self.get_managed_files_for_tool(tool_id, app_type)
            results.append(result)
        
        return results
    
    def get_all_managed_files(self, tool_ids: List[str], app_type: Optional[str] = None) -> Dict[str, Set[str]]:
        """Get all managed files across multiple tools organized by file type.
        
        Args:
            tool_ids: List of AI tool IDs
            app_type: Optional app type filter
            
        Returns:
            Dictionary mapping file types to sets of managed files
        """
        all_files: Dict[str, Set[str]] = {
            "chatmodes": set(),
            "instructions": set(), 
            "prompts": set(),
            "commands": set()
        }
        
        for tool_id in tool_ids:
            result = self.get_managed_files_for_tool(tool_id, app_type)
            for file_type, files in result.managed_files.items():
                if file_type in all_files:
                    all_files[file_type].update(files)
        
        return all_files
    
    def detect_active_tools(self, project_root: Optional[Union[str, Path]] = None) -> ActiveToolsResult:
        """Detect currently active AI tools for the project.
        
        This method tries multiple sources in order of priority:
        1. Environment variables (SDD_AI_TOOLS)
        2. Project-specific state file (.sdd-state.json) 
        3. Local YAML configuration with user preferences
        4. Global configuration defaults
        5. Fallback to first available tool
        
        Args:
            project_root: Project root directory (defaults to current directory)
            
        Returns:
            ActiveToolsResult with detected active tools
        """
        if self._active_tools_cache:
            return self._active_tools_cache
        
        try:
            project_path = Path(project_root) if project_root else Path.cwd()
            
            # Method 1: Check environment variable (highest priority)
            env_tools = os.getenv("SDD_AI_TOOLS")
            if env_tools:
                try:
                    tools_list = [tool.strip() for tool in env_tools.split(",") if tool.strip()]
                    valid_tools = [tool for tool in tools_list if self.config.validate_ai_tool_id(tool)]
                    if valid_tools:
                        result = ActiveToolsResult(
                            active_tools=valid_tools,
                            source="environment",
                            confidence=1.0
                        )
                        self._active_tools_cache = result
                        return result
                except Exception as e:
                    self.logger.debug(f"Invalid SDD_AI_TOOLS environment variable: {e}")
            
            # Method 2: Check for project-specific state file from init command
            state_file = project_path / ".sdd-state.json"
            if state_file.exists():
                try:
                    import json
                    with open(state_file, 'r') as f:
                        state_data = json.load(f)
                    
                    if "selected_ai_tools" in state_data and state_data["selected_ai_tools"]:
                        tools_list = state_data["selected_ai_tools"]
                        valid_tools = [tool for tool in tools_list if self.config.validate_ai_tool_id(tool)]
                        if valid_tools:
                            result = ActiveToolsResult(
                                active_tools=valid_tools,
                                source="project_state",
                                confidence=0.95
                            )
                            self._active_tools_cache = result
                            return result
                except Exception as e:
                    self.logger.debug(f"Could not load project state file: {e}")
            
            # Method 3: Check for local YAML configuration with preferences
            try:
                yaml_config = self.config.load_yaml_config(str(project_path))
                if yaml_config and "preferences" in yaml_config:
                    prefs = yaml_config["preferences"]
                    if "default_ai_tools" in prefs and prefs["default_ai_tools"]:
                        active_tools = prefs["default_ai_tools"]
                        # Validate tools exist
                        valid_tools = [tool for tool in active_tools if self.config.validate_ai_tool_id(tool)]
                        if valid_tools:
                            result = ActiveToolsResult(
                                active_tools=valid_tools,
                                source="config",
                                confidence=0.9
                            )
                            self._active_tools_cache = result
                            return result
            except Exception as e:
                self.logger.debug(f"Could not load YAML config for active tools: {e}")
            
            # Method 4: Check for SDD configuration model defaults
            try:
                sdd_config = self.config.create_sdd_config_model(yaml_config if 'yaml_config' in locals() else None)
                default_tools = sdd_config.preferences.default_ai_tools
                if default_tools:
                    valid_tools = [tool for tool in default_tools if self.config.validate_ai_tool_id(tool)]
                    if valid_tools:
                        result = ActiveToolsResult(
                            active_tools=valid_tools,
                            source="defaults",
                            confidence=0.7,
                            fallback_applied=True
                        )
                        self._active_tools_cache = result
                        return result
            except Exception as e:
                self.logger.debug(f"Could not create SDD config model: {e}")
            
            # Method 5: Fallback to first available tool
            available_tools = self.get_available_tools()
            if available_tools:
                fallback_tool = available_tools[0]  # Usually "github-copilot"
                result = ActiveToolsResult(
                    active_tools=[fallback_tool],
                    source="defaults",
                    confidence=0.5,
                    fallback_applied=True
                )
                self._active_tools_cache = result
                return result
            
            # Method 6: No tools available
            return ActiveToolsResult(
                active_tools=[],
                source="none",
                confidence=0.0,
                fallback_applied=True
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to detect active tools: {e}")
            return ActiveToolsResult(
                active_tools=[],
                source="error",
                confidence=0.0,
                fallback_applied=True
            )
    
    def invalidate_cache(self):
        """Invalidate internal caches."""
        self._tool_cache.clear()
        self._active_tools_cache = None
    
    def set_active_tools(self, tool_ids: List[str], project_root: Optional[Union[str, Path]] = None, persist: bool = True) -> ActiveToolsResult:
        """Set the active AI tools for the project.
        
        Args:
            tool_ids: List of AI tool IDs to set as active
            project_root: Project root directory (defaults to current directory)  
            persist: Whether to persist selection to project state file
            
        Returns:
            ActiveToolsResult with the set active tools
            
        Raises:
            ValueError: If any tool IDs are invalid
        """
        # Validate all tool IDs
        invalid_tools = [tool_id for tool_id in tool_ids if not self.config.validate_ai_tool_id(tool_id)]
        if invalid_tools:
            raise ValueError(f"Invalid AI tool IDs: {invalid_tools}")
        
        # Create result
        result = ActiveToolsResult(
            active_tools=tool_ids,
            source="manual",
            confidence=1.0
        )
        
        # Update cache
        self._active_tools_cache = result
        
        # Persist to project state file if requested
        if persist:
            try:
                project_path = Path(project_root) if project_root else Path.cwd()
                state_file = project_path / ".sdd-state.json"
                
                # Load existing state or create new
                state_data = {}
                if state_file.exists():
                    import json
                    with open(state_file, 'r') as f:
                        state_data = json.load(f)
                
                # Update with new tool selection
                state_data["selected_ai_tools"] = tool_ids
                state_data["last_updated"] = self._get_current_timestamp()
                
                # Write state file
                import json
                with open(state_file, 'w') as f:
                    json.dump(state_data, f, indent=2)
                
                self.logger.debug(f"Persisted active tools to {state_file}: {tool_ids}")
                
            except Exception as e:
                self.logger.warning(f"Failed to persist active tools: {e}")
        
        return result
    
    def get_active_tools_for_app_type(self, app_type: str, project_root: Optional[Union[str, Path]] = None) -> List[str]:
        """Get currently active AI tools for a specific app type.
        
        This is a convenience method that combines active tool detection
        with app type filtering for use in delete commands.
        
        Args:
            app_type: The app type (e.g., "python-cli", "mcp-server")
            project_root: Project root directory (defaults to current directory)
            
        Returns:
            List of active AI tool IDs that support the given app type
        """
        active_result = self.detect_active_tools(project_root)
        active_tools = active_result.active_tools
        
        # Filter tools that have managed files for this app type
        compatible_tools = []
        for tool_id in active_tools:
            result = self.get_managed_files_for_tool(tool_id, app_type)
            if result.has_files():
                compatible_tools.append(tool_id)
        
        return compatible_tools
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def discover_tools_from_config(self, yaml_config: Optional[Dict] = None) -> List[str]:
        """Discover AI tools from configuration.
        
        Args:
            yaml_config: Optional YAML configuration dictionary
            
        Returns:
            List of discovered AI tool IDs
        """
        discovered_tools = []
        
        try:
            # Discover from hardcoded configuration
            discovered_tools.extend(self.get_available_tools())
            
            # Discover from YAML configuration
            if yaml_config and "ai_tools" in yaml_config:
                yaml_tools = list(yaml_config["ai_tools"].keys())
                discovered_tools.extend(yaml_tools)
            
            # Remove duplicates while preserving order
            unique_tools = []
            seen = set()
            for tool in discovered_tools:
                if tool not in seen:
                    unique_tools.append(tool)
                    seen.add(tool)
            
            self.logger.info(f"Discovered {len(unique_tools)} AI tools from configuration")
            return unique_tools
            
        except Exception as e:
            self.logger.warning(f"Failed to discover tools from config: {e}")
            return []
    
    def validate_tool_files(self, tool_id: str) -> Dict[str, List[str]]:
        """Validate managed files for an AI tool.
        
        Args:
            tool_id: ID of the AI tool
            
        Returns:
            Dictionary of validation issues by category
        """
        issues = {
            "missing_files": [],
            "invalid_patterns": [],
            "warnings": []
        }
        
        try:
            tool = self.get_tool_info(tool_id)
            if not tool:
                issues["missing_files"].append(f"Tool '{tool_id}' not found")
                return issues
            
            # Check if tool has any managed files
            if not tool.has_managed_files():
                issues["warnings"].append(f"Tool '{tool_id}' has no managed files defined")
            
            # Validate file patterns (basic validation)
            for file_type, files in tool.get_managed_files().items():
                for file_name in files:
                    if not file_name or not file_name.strip():
                        issues["invalid_patterns"].append(f"Empty filename in {file_type}")
                    elif not file_name.endswith(".md"):
                        issues["warnings"].append(f"Non-markdown file in {file_type}: {file_name}")
            
            return issues
            
        except Exception as e:
            issues["missing_files"].append(f"Validation failed for '{tool_id}': {e}")
            return issues
    
    def get_tools_summary(self) -> Dict[str, any]:
        """Get summary of all available tools and their managed files.
        
        Returns:
            Dictionary with tools summary information
        """
        try:
            available_tools = self.get_available_tools()
            active_tools = self.detect_active_tools()
            
            tools_info = {}
            total_managed_files = 0
            
            for tool_id in available_tools:
                tool = self.get_tool_info(tool_id)
                if tool:
                    managed_count = sum(len(files) for files in tool.get_managed_files().values())
                    total_managed_files += managed_count
                    
                    tools_info[tool_id] = {
                        "name": tool.name,
                        "description": tool.description,
                        "managed_files_count": managed_count,
                        "is_active": tool_id in active_tools.active_tools,
                        "has_files": tool.has_managed_files()
                    }
            
            return {
                "total_tools": len(available_tools),
                "active_tools": len(active_tools.active_tools),
                "total_managed_files": total_managed_files,
                "active_tools_source": active_tools.source,
                "tools": tools_info
            }
            
        except Exception as e:
            self.logger.warning(f"Failed to get tools summary: {e}")
            return {"error": str(e)}