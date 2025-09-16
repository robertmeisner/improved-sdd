"""Data models and enums for CLI operations.

This module contains all the dataclasses and enums used throughout the CLI
for representing template sources, progress information, and resolution results.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union

# Pydantic imports for configuration models
from pydantic import BaseModel, Field


class TemplateSourceType(Enum):
    """Enumeration of template source types for transparency."""

    LOCAL = "local"
    BUNDLED = "bundled"
    GITHUB = "github"
    MERGED = "merged"


@dataclass
class ProgressInfo:
    """Progress information for download and extraction operations."""

    phase: str  # "download" or "extract"
    bytes_completed: int
    bytes_total: int
    percentage: float
    speed_bps: Optional[int] = None
    eta_seconds: Optional[int] = None

    @property
    def speed_mbps(self) -> Optional[float]:
        """Download speed in MB/s."""
        return self.speed_bps / (1024 * 1024) if self.speed_bps else None


@dataclass
class TemplateSource:
    """Represents a template source with location and type information."""

    path: Path
    source_type: TemplateSourceType
    size_bytes: Optional[int] = None

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.source_type.value} templates at {self.path}"


@dataclass
class MergedTemplateSource:
    """Represents a merged template source combining local and downloaded templates at file level."""

    local_path: Optional[Path]  # User's .sdd_templates directory
    downloaded_path: Path  # Cache directory with downloaded templates
    local_files: dict[str, set[str]]  # Template files found locally: {'prompts': {'file1.md', 'file2.md'}}
    downloaded_files: dict[str, set[str]]  # Template files downloaded: {'chatmodes': {'file3.md'}}
    source_type: TemplateSourceType = TemplateSourceType.MERGED

    def get_file_source(self, template_type: str, filename: str) -> Optional[Path]:
        """Get the source path for a specific template file.

        Args:
            template_type: Template type (e.g., 'prompts', 'chatmodes')
            filename: Template filename (e.g., 'sddCommitWorkflow.prompt.md')

        Returns:
            Path to the file source (local takes priority) or None if not found
        """
        # Check local first (priority)
        if template_type in self.local_files and filename in self.local_files[template_type] and self.local_path:
            return self.local_path / template_type / filename

        # Check downloaded
        if template_type in self.downloaded_files and filename in self.downloaded_files[template_type]:
            return self.downloaded_path / template_type / filename

        return None

    def get_all_available_files(self) -> dict[str, set[str]]:
        """Get all available template files from both sources (local + downloaded)."""
        all_files = {}

        # Add local files
        for template_type, files in self.local_files.items():
            if template_type not in all_files:
                all_files[template_type] = set()
            all_files[template_type].update(files)

        # Add downloaded files (but not if already in local - local takes priority)
        for template_type, files in self.downloaded_files.items():
            if template_type not in all_files:
                all_files[template_type] = set()
            # Only add downloaded files that aren't already available locally
            local_files_for_type = self.local_files.get(template_type, set())
            all_files[template_type].update(files - local_files_for_type)

        return all_files

    def __str__(self) -> str:
        """Human-readable string representation."""
        local_count = sum(len(files) for files in self.local_files.values())
        downloaded_count = sum(len(files) for files in self.downloaded_files.values())
        all_files = self.get_all_available_files()
        total_count = sum(len(files) for files in all_files.values())

        local_desc = f"{local_count} local files" if local_count else "no local files"
        downloaded_desc = f"{downloaded_count} downloaded files" if downloaded_count else "no downloaded files"
        return f"merged templates ({local_desc}, {downloaded_desc}, {total_count} total unique files)"


# AI Tool Configuration Models (Pydantic)

class ManagedFiles(BaseModel):
    """Managed files configuration for an AI tool.
    
    Defines which specific files an AI tool creates and manages,
    enabling precise file deletion that preserves manual files.
    """
    chatmodes: List[str] = Field(default_factory=list, description="Chat mode template files")
    instructions: List[str] = Field(default_factory=list, description="Instruction template files")
    prompts: List[str] = Field(default_factory=list, description="Prompt template files")
    commands: List[str] = Field(default_factory=list, description="Command template files")
    
    def get_all_files(self) -> List[str]:
        """Get all managed files across all categories."""
        return self.chatmodes + self.instructions + self.prompts + self.commands
    
    def get_files_by_type(self, file_type: str) -> List[str]:
        """Get managed files for a specific type.
        
        Args:
            file_type: Type of files to retrieve (chatmodes, instructions, prompts, commands)
            
        Returns:
            List of files for the specified type
        """
        return getattr(self, file_type, [])
    
    def has_files(self) -> bool:
        """Check if this tool manages any files."""
        return bool(self.get_all_files())


class FileExtensions(BaseModel):
    """File extensions configuration for an AI tool."""
    chatmodes: str = Field(description="File extension for chat modes")
    instructions: str = Field(description="File extension for instructions")
    prompts: str = Field(description="File extension for prompts")
    commands: str = Field(description="File extension for commands")


class KeywordReplacements(BaseModel):
    """Keyword replacement configuration for an AI tool."""
    model_config = {"extra": "allow"}  # Allow additional keyword replacements
    

class AIToolConfig(BaseModel):
    """AI tool configuration schema.
    
    Represents the complete configuration for an AI tool including
    metadata, file management, and template processing settings.
    """
    name: str = Field(description="Display name of the AI tool")
    description: str = Field(default="", description="Description of the AI tool")
    template_dir: str = Field(description="Directory name for templates")
    managed_files: ManagedFiles = Field(default_factory=ManagedFiles, description="Files managed by this tool")
    file_extensions: Optional[FileExtensions] = Field(default=None, description="File extensions for this tool")
    keywords: Optional[KeywordReplacements] = Field(default=None, description="Keyword replacements for templates")
    
    def get_managed_files_for_type(self, file_type: str) -> List[str]:
        """Get managed files for a specific type.
        
        Args:
            file_type: Type of files (chatmodes, instructions, prompts, commands)
            
        Returns:
            List of managed files for the specified type
        """
        return self.managed_files.get_files_by_type(file_type)
    
    def has_managed_files(self) -> bool:
        """Check if this tool has any managed files."""
        return self.managed_files.has_files()


class DeleteBehaviorConfig(BaseModel):
    """Delete command behavior configuration."""
    confirm_before_delete: bool = Field(default=True, description="Require confirmation before deletion")
    show_file_preview: bool = Field(default=True, description="Show preview of files to be deleted")
    group_by_ai_tool: bool = Field(default=True, description="Group files by AI tool in preview")


class CLIConfig(BaseModel):
    """CLI behavior configuration."""
    delete_behavior: DeleteBehaviorConfig = Field(default_factory=DeleteBehaviorConfig)


class PreferencesConfig(BaseModel):
    """User preferences configuration."""
    default_ai_tools: List[str] = Field(default=["github-copilot"], description="Default AI tools to use")
    template_source: str = Field(default="github", description="Default template source")


class SDDConfig(BaseModel):
    """Root configuration schema for SDD CLI.
    
    This is the complete configuration structure that can be defined
    in YAML files to customize CLI behavior and AI tool settings.
    """
    version: str = Field(default="1.0", description="Configuration schema version")
    ai_tools: Dict[str, AIToolConfig] = Field(default_factory=dict, description="AI tool configurations")
    cli: CLIConfig = Field(default_factory=CLIConfig, description="CLI behavior settings")
    preferences: PreferencesConfig = Field(default_factory=PreferencesConfig, description="User preferences")
    
    def get_ai_tool(self, tool_id: str) -> Optional[AIToolConfig]:
        """Get configuration for a specific AI tool.
        
        Args:
            tool_id: ID of the AI tool
            
        Returns:
            AI tool configuration or None if not found
        """
        return self.ai_tools.get(tool_id)
    
    def get_available_tools(self) -> List[str]:
        """Get list of available AI tool IDs."""
        return list(self.ai_tools.keys())
    
    def has_ai_tool(self, tool_id: str) -> bool:
        """Check if an AI tool is configured."""
        return tool_id in self.ai_tools


# Runtime AI Tool Representation (Dataclass)

@dataclass
class AITool:
    """Runtime representation of an AI tool.
    
    This dataclass provides a simple, immutable representation
    of an AI tool for use during CLI operations.
    """
    id: str
    name: str
    description: str
    template_dir: str
    managed_files: Dict[str, List[str]]  # Simplified dict for runtime use
    file_extensions: Optional[Dict[str, str]] = None
    keywords: Optional[Dict[str, str]] = None
    
    @classmethod
    def from_config(cls, tool_id: str, config: AIToolConfig) -> 'AITool':
        """Create AITool instance from configuration.
        
        Args:
            tool_id: ID of the AI tool
            config: AI tool configuration
            
        Returns:
            AITool instance
        """
        # Convert ManagedFiles to simple dict
        managed_files = {
            "chatmodes": config.managed_files.chatmodes,
            "instructions": config.managed_files.instructions,
            "prompts": config.managed_files.prompts,
            "commands": config.managed_files.commands,
        }
        
        # Convert Pydantic models to dicts for runtime use
        file_extensions = None
        if config.file_extensions:
            file_extensions = config.file_extensions.model_dump()
            
        keywords = None
        if config.keywords:
            keywords = config.keywords.model_dump()
        
        return cls(
            id=tool_id,
            name=config.name,
            description=config.description,
            template_dir=config.template_dir,
            managed_files=managed_files,
            file_extensions=file_extensions,
            keywords=keywords,
        )
    
    def get_managed_files(self, file_type: Optional[str] = None) -> Union[List[str], Dict[str, List[str]]]:
        """Get managed files for this tool.
        
        Args:
            file_type: Specific file type to get, or None for all
            
        Returns:
            List of files for specific type, or dict of all files by type
        """
        if file_type:
            return self.managed_files.get(file_type, [])
        return self.managed_files
    
    def has_managed_files(self, file_type: Optional[str] = None) -> bool:
        """Check if tool has managed files.
        
        Args:
            file_type: Specific file type to check, or None for any
            
        Returns:
            True if tool has managed files of specified type or any type
        """
        if file_type:
            return bool(self.managed_files.get(file_type))
        return any(files for files in self.managed_files.values())


@dataclass
class TemplateResolutionResult:
    """Tracks the result of template resolution with transparency information."""

    source: Optional[Union[TemplateSource, MergedTemplateSource]]
    success: bool
    message: str
    fallback_attempted: bool = False

    @property
    def is_local(self) -> bool:
        """Check if resolved source is local .sdd_templates."""
        return (
            self.source is not None
            and hasattr(self.source, "source_type")
            and self.source.source_type == TemplateSourceType.LOCAL
        )

    @property
    def is_bundled(self) -> bool:
        """Check if resolved source is bundled templates."""
        return (
            self.source is not None
            and hasattr(self.source, "source_type")
            and self.source.source_type == TemplateSourceType.BUNDLED
        )

    @property
    def is_github(self) -> bool:
        """Check if resolved source is GitHub download."""
        return (
            self.source is not None
            and hasattr(self.source, "source_type")
            and self.source.source_type == TemplateSourceType.GITHUB
        )

    @property
    def is_merged(self) -> bool:
        """Check if resolved source is merged local + downloaded."""
        return (
            self.source is not None
            and hasattr(self.source, "source_type")
            and self.source.source_type == TemplateSourceType.MERGED
        )
