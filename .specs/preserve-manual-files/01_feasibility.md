# Manual File Preservation Feasibility Assessment

## Feature Summary
Implement a mechanism to prevent deletion of manually created files (like `.github\chatmodes\xxx.chatmode.md`) when using the `delete` command. Currently, the CLI deletes ALL files in specific directories without distinguishing between CLI-created and manually-created files.

## Current Implementation Analysis

### Delete Command Current Behavior
- **Location**: `src/commands/delete.py`
- **Logic**: Uses simple directory globbing (`*.md`) to find all files in target directories
- **Problem**: No distinction between CLI-created vs manually-created files
- **Affected directories**: `.github/chatmodes/`, `.github/instructions/`, `.github/prompts/`, `.github/commands/`

### File Tracking System Status
- **FileTracker Service**: Exists and tracks file creation/modification during CLI operations
- **Tracking scope**: Only during CLI execution session (not persistent)
- **Storage**: In-memory only, lost after CLI execution completes
- **Current usage**: Generate summary reports for user feedback

### Configuration System
- **Template definitions**: Well-defined in `src/core/config.py`
- **AI tool templates**: Each tool has specific file extensions and naming patterns
- **App type templates**: Specific instruction files for each app type

## Technical Feasibility Assessment

### ✅ HIGH FEASIBILITY

**1. File Metadata Approach**
- **Concept**: Store CLI creation metadata in file headers/comments
- **Implementation**: Add standardized metadata comments to CLI-generated files
- **Detection**: Parse file headers to identify CLI-created files
- **Effort**: LOW - Simple string operations
- **Risk**: LOW - Non-intrusive, backward compatible

**2. Manifest File Approach** 
- **Concept**: Maintain `.sdd-manifest.json` file tracking CLI-created files
- **Implementation**: Update manifest during `init`, read during `delete`
- **Detection**: Check manifest for file presence before deletion
- **Effort**: MEDIUM - JSON file management
- **Risk**: LOW - Isolated to single tracking file

**3. Enhanced Configuration Approach**
- **Concept**: Extend existing config to define CLI-managed file patterns
- **Implementation**: Add file pattern matching to config system
- **Detection**: Compare files against known CLI template patterns
- **Effort**: LOW - Leverage existing config infrastructure
- **Risk**: LOW - Builds on proven configuration system

### ⚠️ MEDIUM FEASIBILITY

**4. Database/SQLite Approach**
- **Concept**: Local SQLite database tracking file operations
- **Implementation**: Store file creation records with timestamps
- **Detection**: Query database before deletion
- **Effort**: HIGH - Database setup, migration, maintenance
- **Risk**: MEDIUM - Additional dependency, complexity

### ❌ LOW FEASIBILITY

**5. File System Attributes Approach**
- **Concept**: Use OS-specific file attributes/extended attributes
- **Implementation**: Set custom attributes on CLI-created files
- **Detection**: Read file attributes during deletion
- **Effort**: HIGH - Platform-specific implementations
- **Risk**: HIGH - Windows/Linux compatibility issues

## Recommended Solution: File Metadata + Manifest Hybrid

### Primary: File Metadata Headers
```markdown
<!-- 
SDD-CLI-GENERATED: true
SDD-VERSION: 1.0.0
SDD-CREATED: 2025-09-15T10:30:00Z
SDD-APP-TYPE: python-cli
SDD-AI-TOOL: github-copilot
SDD-TEMPLATE: sddSpecDriven.chatmode.md
-->
```

### Fallback: Manifest File
```json
{
  "version": "1.0.0",
  "created": "2025-09-15T10:30:00Z",
  "files": {
    ".github/chatmodes/sddSpecDriven.chatmode.md": {
      "created": "2025-09-15T10:30:00Z",
      "app_type": "python-cli",
      "ai_tool": "github-copilot",
      "template": "sddSpecDriven.chatmode.md"
    }
  }
}
```

## Implementation Complexity: SIMPLE

**Estimated Effort**: 1-2 days
- File metadata parsing: 4 hours
- Manifest file management: 4 hours
- Delete command modification: 2 hours
- Testing: 4 hours

## Risk Assessment: LOW

### Technical Risks
- **Backward compatibility**: LOW - Optional metadata, graceful fallback
- **Performance impact**: MINIMAL - Only affects delete operations
- **File corruption**: NONE - Read-only operations for detection

### User Experience Risks
- **Workflow disruption**: NONE - Preserves current CLI behavior for existing files
- **Migration complexity**: NONE - Automatic detection of CLI-generated files

## Success Criteria

1. **Preservation**: Manual files like `xxx.chatmode.md` are never deleted
2. **Identification**: CLI can accurately identify its own created files
3. **Backward Compatibility**: Existing installations work without changes
4. **Performance**: No noticeable impact on CLI operations
5. **Maintainability**: Solution integrates cleanly with existing codebase

## Alternative Approaches

### Manual Exclusion List
- **User maintains**: `.sdd-exclude` file with protected files
- **Pros**: Simple, user-controlled
- **Cons**: Manual maintenance burden, easy to forget

### Interactive Confirmation
- **Enhanced prompts**: Show each file with source information before deletion
- **Pros**: User maintains full control
- **Cons**: Verbose for large projects, interrupts automation

## Recommendation: PROCEED

The file metadata + manifest hybrid approach provides:
- **High reliability** through dual tracking mechanisms
- **Low implementation complexity** leveraging existing infrastructure
- **Excellent backward compatibility** with optional metadata
- **Future extensibility** for additional file management features

**Next Steps**: Proceed to requirements gathering phase to define specific implementation details and user stories.