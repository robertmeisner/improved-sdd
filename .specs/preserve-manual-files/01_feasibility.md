# Manual File Preservation Feasibility Assessment

## Feature Summary
Implement precise file deletion by defining exactly which files each AI tool creates, rather than deleting ALL files in directories. When users run `delete python-cli`, only delete files that were actually created by the CLI for the selected AI tools, preserving any manually created files like `xxx.chatmode.md`.

## Current Implementation Analysis

### Delete Command Current Problem
- **Location**: `src/commands/delete.py`
- **Current logic**: Uses directory globbing (`*.md`) - deletes ALL files
- **Problem**: No distinction between AI tool files vs manual files
- **Example issue**: Deletes manually created `xxx.chatmode.md` along with CLI-generated files

### AI Tool Configuration System
- **Location**: `src/core/config.py` 
- **Current structure**: Each AI tool defines file extensions and naming patterns
- **Available data**: Template directories, file extensions, keywords per AI tool
- **Missing piece**: Explicit file lists that each AI tool creates

## Technical Feasibility Assessment

### ✅ HIGH FEASIBILITY - Configuration-Based File Lists

**Recommended Approach: Explicit File Mapping Per AI Tool**

```python
# In config.py - extend existing AI_TOOLS configuration
AI_TOOLS = {
    "github-copilot": {
        "name": "GitHub Copilot",
        "template_dir": "github",
        "managed_files": {  # NEW: Define exact files this tool creates
            "chatmodes": [
                "sddSpecDriven.chatmode.md",
                "sddSpecDrivenSimple.chatmode.md", 
                "sddTesting.chatmode.md"
            ],
            "instructions": [
                "sddPythonCliDev.instructions.md",
                "sddMcpServerDev.instructions.md"
            ],
            "prompts": [
                "sddCommitWorkflow.prompt.md",
                "sddFileVerification.prompt.md",
                # ... etc
            ]
        }
    },
    "claude": {
        "name": "Claude",
        "managed_files": {
            "chatmodes": [
                "sddSpecDriven.claude.md",
                "sddSpecDrivenSimple.claude.md"
            ]
            # Different files than GitHub Copilot
        }
    }
}
```

**Delete Logic Update:**
1. User selects AI tools during CLI setup
2. Delete command only targets files from those specific AI tools
3. Manual files (not in any AI tool's managed_files list) are preserved

## Implementation Complexity: VERY SIMPLE

**Estimated Effort**: 2-4 hours
- Extend AI_TOOLS config with managed_files: 1 hour
- Update delete command to use file lists: 1 hour  
- Testing: 1-2 hours

## Benefits of This Approach

### ✅ **Precision**
- Only deletes files the CLI actually created
- Each AI tool manages its own file list
- Different tools can have different files

### ✅ **Simplicity** 
- No metadata parsing or manifest files needed
- Leverages existing configuration system
- Easy to understand and maintain

### ✅ **Flexibility**
- Easy to add new AI tools with their own file lists
- Per-tool customization of managed files
- Clear separation between tools

### ✅ **User Experience**
- Predictable behavior - only CLI files deleted
- Manual files always preserved
- Tool-specific deletion granularity

## Risk Assessment: MINIMAL

- **Technical risk**: NONE - Simple configuration change
- **Breaking changes**: NONE - Additive configuration
- **Performance**: NO IMPACT - Same file operations, just more precise
- **Maintenance**: REDUCED - Clear file ownership per tool

## Success Criteria

1. **Precision**: Only delete files that specific AI tools actually created
2. **Preservation**: Manual files like `xxx.chatmode.md` never deleted
3. **Tool-specific**: Different AI tools can have different file sets
4. **Maintainability**: Easy to add new tools or modify file lists

## Example Scenarios

### Scenario 1: GitHub Copilot User
```bash
improved-sdd delete python-cli  # User has github-copilot selected
# Only deletes: sddSpecDriven.chatmode.md, sddPythonCliDev.instructions.md, etc.
# Preserves: xxx.chatmode.md (manual file)
```

### Scenario 2: Claude User  
```bash
improved-sdd delete python-cli  # User has claude selected
# Only deletes: sddSpecDriven.claude.md, etc.
# Preserves: xxx.chatmode.md, sddSpecDriven.chatmode.md (GitHub Copilot files)
```

## Recommendation: PROCEED WITH CONFIGURATION-BASED APPROACH

This approach is:
- **Simple to implement** - Just configuration changes
- **Highly precise** - Explicit file control per AI tool
- **Future-proof** - Easy to extend for new AI tools
- **User-friendly** - Predictable and safe deletion behavior

**Next Steps**: Proceed to requirements gathering to define the exact file lists for each AI tool and user interaction patterns.