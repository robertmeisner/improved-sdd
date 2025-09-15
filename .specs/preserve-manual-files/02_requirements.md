# Manual File Preservation Requirements

## Introduction

This feature implements precise file deletion by defining exactly which files each AI tool creates, ensuring manual files are never accidentally deleted during CLI cleanup operations.

**Current Implementation Status**: NOT IMPLEMENTED - Delete command currently uses directory globbing which deletes all files regardless of origin.

## Success Metrics

- **Precision Rate**: 100% - Only CLI-generated files are deleted, zero manual files affected
- **User Confidence**: High - Users can safely create custom files knowing they won't be deleted
- **Maintenance Effort**: Low - File lists are easy to update and maintain per AI tool

## Out of Scope

- Tracking file modification history or creation timestamps
- Complex metadata systems or manifest files
- Rollback or recovery of accidentally deleted files
- Cross-platform file attribute management

## Requirements

### Requirement 1: AI Tool Specific File Management [P0]

**User Story:** As a developer using multiple AI tools, I want the delete command to only remove files created by my selected AI tools, so that my manually created files are preserved.

#### Acceptance Criteria

1. WHEN user runs `delete python-cli` THEN CLI SHALL only delete files defined in the user's currently selected AI tools' managed file lists for the python-cli app type
2. WHEN user runs `delete mcp-server` THEN CLI SHALL only delete files defined in the user's currently selected AI tools' managed file lists for the mcp-server app type
3. WHEN user has GitHub Copilot selected THEN CLI SHALL only delete GitHub Copilot specific files for the specified app type (e.g., sddPythonCliDev.instructions.md for python-cli)
4. WHEN user has Claude selected THEN CLI SHALL only delete Claude specific files for the specified app type (e.g., sddPythonCliDev.claude.md for python-cli)
5. WHEN user has multiple AI tools selected THEN CLI SHALL delete files from all selected tools' managed lists for the specified app type
6. WHEN user runs delete command THEN CLI SHALL determine active AI tools from user's configuration or previous init selections

#### Test Scenarios
- Scenario 1: GitHub Copilot user with manual xxx.chatmode.md file - only CLI files deleted
- Scenario 2: Claude user with existing GitHub Copilot files - only Claude files deleted
- Scenario 3: Multi-tool user - files from all selected tools deleted, manual files preserved

**Implementation Status**: NOT IMPLEMENTED - Current delete logic uses directory globbing for all .md files

### Requirement 2: Configuration-Based File Lists [P0]

**User Story:** As a system administrator, I want each AI tool to define exactly which files it manages, so that file deletion is predictable and maintainable.

#### Acceptance Criteria

1. WHEN new AI tool is added THEN it SHALL define its complete managed file list in configuration
2. WHEN AI tool configuration is updated THEN file lists SHALL be easily modifiable without code changes
3. WHEN file list is queried THEN system SHALL return exact files for each AI tool by category
4. IF AI tool has no managed files defined THEN delete command SHALL skip that tool safely

#### Test Scenarios
- Scenario 1: Add new AI tool with file list - deletion works correctly
- Scenario 2: Modify existing tool's file list - changes take effect immediately
- Scenario 3: Tool with empty file list - graceful handling without errors

**Implementation Status**: PARTIALLY IMPLEMENTED - AI_TOOLS config exists but lacks managed_files structure

### Requirement 3: Safe Manual File Preservation [P0]

**User Story:** As a developer, I want to create custom template files (like xxx.chatmode.md) without worrying they'll be deleted, so that I can extend the CLI safely.

#### Acceptance Criteria

1. WHEN file exists but is not in any AI tool's managed list THEN CLI SHALL never delete it
2. WHEN user creates files with any naming convention THEN they SHALL be preserved unless explicitly managed
3. WHEN delete operation runs THEN CLI SHALL show which files will be deleted before deletion
4. WHEN file exists with same name as managed file THEN CLI SHALL always prompt user for action
5. WHEN file conflict prompt is shown THEN CLI SHALL offer options to skip, delete, or preview file before deciding
6. WHEN user chooses to preserve conflicted file THEN CLI SHALL skip deletion and continue with other files

#### Test Scenarios
- Scenario 1: Custom xxx.chatmode.md exists - preserved during deletion (not in managed lists)
- Scenario 2: User creates custom-tool.instructions.md - preserved always (not in managed lists)
- Scenario 3: Preview shows only managed files will be deleted
- Scenario 4: File exists with same name as managed file - user always prompted for action
- Scenario 5: User chooses to preserve conflict file - deletion skipped, other files processed
- Scenario 6: User chooses to delete conflict file - file deleted as requested

**Implementation Status**: NOT IMPLEMENTED - No protection mechanism for manual files exists

### Requirement 4: Multi-Tool Environment Support [P1]

**User Story:** As a developer using multiple AI tools, I want each tool's files to be managed independently, so that I can use different tools without conflicts.

#### Acceptance Criteria

1. WHEN multiple AI tools are installed THEN each SHALL manage its own distinct file set
2. WHEN user switches AI tools THEN previous tool's files SHALL remain unless explicitly deleted
3. WHEN file conflicts exist THEN CLI SHALL handle gracefully with clear messaging
4. WHEN tool-specific deletion runs THEN only that tool's files SHALL be affected

#### Test Scenarios
- Scenario 1: GitHub Copilot and Claude both installed - independent file management
- Scenario 2: Switch from Copilot to Claude - Copilot files remain until deleted
- Scenario 3: Delete specific tool - only that tool's files removed

**Implementation Status**: NOT IMPLEMENTED - Current system doesn't distinguish between AI tool files

### Requirement 5: Enhanced Delete Command Interface [P1]

**User Story:** As a developer, I want clear feedback about what files will be deleted and from which AI tools, so that I can make informed decisions.

#### Acceptance Criteria

1. WHEN delete command runs THEN CLI SHALL show files grouped by AI tool
2. WHEN multiple AI tools are present THEN CLI SHALL indicate source tool for each file  
3. WHEN no files are found for selected tools THEN CLI SHALL display helpful message
4. WHEN user confirms deletion THEN CLI SHALL report success/failure per file with tool context

#### Test Scenarios
- Scenario 1: Files from multiple tools - clearly labeled by source
- Scenario 2: No managed files found - helpful "no files to delete" message
- Scenario 3: Deletion report shows which tool each file belonged to

**Implementation Status**: NOT IMPLEMENTED - Current delete shows generic file lists

### Requirement 7: General YAML Configuration System [P1]

**User Story:** As a developer, I want to customize CLI behavior, AI tool settings, and managed files through YAML configuration files, so that I can override defaults and extend functionality without modifying code.

#### Acceptance Criteria

1. WHEN user creates custom config THEN CLI SHALL read `/.sdd_templates/sdd-config.yaml` as local override
2. WHEN local config file does not exist THEN CLI SHALL load default config from GitHub `/templates/sdd-config.yaml` without saving to project
3. WHEN both local and remote configs exist THEN local config SHALL take precedence over remote config for matching sections
4. WHEN YAML config is loaded THEN it SHALL merge with or override the hardcoded configuration
5. WHEN config is invalid THEN CLI SHALL log warnings but continue with default configuration
6. WHEN new AI tool is added via YAML THEN it SHALL be available for selection and deletion
7. WHEN configuration system is extended THEN new sections SHALL be easily added without breaking existing functionality

#### YAML Configuration Format
```yaml
# sdd-config.yaml - General configuration for SDD CLI
version: "1.0"

# AI Tool Configuration
ai_tools:
  github-copilot:
    name: "GitHub Copilot"
    description: "GitHub's AI pair programmer"
    template_dir: "github"
    managed_files:
      chatmodes:
        - "sddSpecDriven.chatmode.md"
        - "sddSpecDrivenSimple.chatmode.md"
        - "sddTesting.chatmode.md"
      instructions:
        - "sddPythonCliDev.instructions.md"
        - "sddMcpServerDev.instructions.md"
      prompts:
        - "sddCommitWorkflow.prompt.md"
        - "sddFileVerification.prompt.md"
        - "sddProjectAnalysis.prompt.md"
        - "sddSpecSync.prompt.md"
        - "sddTaskExecution.prompt.md"
        - "sddTaskVerification.prompt.md"
        - "sddTestAll.prompt.md"
      commands: []
      
  claude:
    name: "Anthropic Claude"
    description: "Anthropic's AI assistant"
    template_dir: "claude"
    managed_files:
      chatmodes:
        - "sddSpecDriven.claude.md"
        - "sddSpecDrivenSimple.claude.md"
        - "sddTesting.claude.md"
      instructions:
        - "sddPythonCliDev.claude.md"
        - "sddMcpServerDev.claude.md"
      prompts:
        - "sddCommitWorkflow.claude.md"
        - "sddFileVerification.claude.md"
        - "sddProjectAnalysis.claude.md"
        - "sddSpecSync.claude.md"
        - "sddTaskExecution.claude.md"
        - "sddTaskVerification.claude.md"
        - "sddTestAll.claude.md"
      commands: []

  # Custom user-defined AI tool
  custom-ai:
    name: "Custom AI Tool"
    description: "User's custom AI configuration"
    template_dir: "custom"
    managed_files:
      chatmodes:
        - "myCustom.chatmode.md"
      instructions:
        - "myCustom.instructions.md"
      prompts: []
      commands: []

# CLI Behavior Configuration (extensible for future features)
cli:
  delete_behavior:
    confirm_before_delete: true
    show_file_preview: true
    group_by_ai_tool: true
  
  # Future: Other CLI behaviors
  # logging:
  #   level: "info"
  #   file: "sdd-cli.log"
  # performance:
  #   cache_templates: true
  #   parallel_downloads: 3

# User Preferences (extensible)
preferences:
  default_ai_tools: ["github-copilot"]
  template_source: "github"
  
  # Future: Other preferences
  # editor: "vscode"
  # auto_update: true
  # analytics: false
```

#### Test Scenarios
- Scenario 1: No local config - CLI loads from GitHub templates without saving locally
- Scenario 2: User creates local override - local config takes precedence for matching sections
- Scenario 3: User adds custom AI tool via local YAML - tool appears in CLI options and managed files work
- Scenario 4: Invalid YAML format - CLI warns but continues with defaults
- Scenario 5: Missing local config and GitHub unavailable - CLI falls back to hardcoded configuration
- Scenario 6: User customizes CLI behavior settings - delete confirmation, preview, etc. work as configured
- Scenario 7: Future extension - new config sections added without breaking existing functionality

**Implementation Status**: NOT IMPLEMENTED - No general YAML configuration system exists

### Requirement 6: Configuration Validation [P2]

**User Story:** As a system administrator, I want the CLI to validate AI tool file configurations, so that misconfigurations are caught early.

#### Acceptance Criteria

1. WHEN CLI starts THEN it SHALL validate all AI tool managed file lists
2. WHEN invalid file patterns exist THEN CLI SHALL warn but continue operation
3. WHEN file list is empty THEN CLI SHALL log warning for that AI tool
4. WHEN duplicate files exist across tools THEN CLI SHALL warn about conflicts

#### Test Scenarios
- Scenario 1: Invalid file pattern in config - warning logged but CLI works
- Scenario 2: Empty file list for tool - warning but graceful handling
- Scenario 3: Same file claimed by two tools - conflict warning shown

**Implementation Status**: NOT IMPLEMENTED - No validation exists for managed file lists