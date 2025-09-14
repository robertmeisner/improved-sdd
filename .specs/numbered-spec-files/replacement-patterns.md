# Regex Replacement Patterns for Numbered Spec Files

## Pattern Categories

### 1. File Path References (Pattern A)
**Target**: `specs/{feature_name}/[filename].md`
**Count**: 8 occurrences

```regex
# Search Pattern
specs/\{feature_name\}/(feasibility|requirements|design|tasks)\.md

# Replacement Mapping
feasibility\.md -> 01_feasibility.md
requirements\.md -> 02_requirements.md  
design\.md -> 03_design.md
tasks\.md -> 04_tasks.md
```

**Specific Replacements**:
```regex
specs/\{feature_name\}/feasibility\.md → specs/{feature_name}/01_feasibility.md
specs/\{feature_name\}/requirements\.md → specs/{feature_name}/02_requirements.md
specs/\{feature_name\}/design\.md → specs/{feature_name}/03_design.md
specs/\{feature_name\}/tasks\.md → specs/{feature_name}/04_tasks.md
```

### 2. Direct File References (Pattern B)
**Target**: `[filename].md` (without path)
**Count**: 15 occurrences

```regex
# Search Pattern (with word boundaries to avoid partial matches)
\b(feasibility|requirements|design|tasks)\.md\b

# Replacement Mapping
\bfeasibility\.md\b -> 01_feasibility.md
\brequirements\.md\b -> 02_requirements.md
\bdesign\.md\b -> 03_design.md
\btasks\.md\b -> 04_tasks.md
```

### 3. Comma-Separated File Lists (Pattern C)
**Target**: Complex lists like `requirements.md, design.md and tasks.md`
**Count**: 5 occurrences

**Sub-patterns**:
```regex
# Pattern C1: Two files with "and"
\b(requirements|design)\.md and (design|tasks)\.md\b
→ 0X_$1.md and 0Y_$2.md

# Pattern C2: Three files with commas and "and" 
\brequirements\.md, design\.md and tasks\.md\b
→ 02_requirements.md, 03_design.md and 04_tasks.md

# Pattern C3: Four files (complete list)
\brequirements\.md, design\.md, tasks\.md, feasibility\.md\b
→ 02_requirements.md, 03_design.md, 04_tasks.md, 01_feasibility.md
```

## Comprehensive Replacement Script

### PowerShell Implementation
```powershell
# Define file mapping
$fileMapping = @{
    'feasibility' = '01_feasibility'
    'requirements' = '02_requirements'  
    'design' = '03_design'
    'tasks' = '04_tasks'
}

# Pattern A: File paths
foreach ($file in $fileMapping.Keys) {
    $oldPattern = "specs/\{feature_name\}/$file\.md"
    $newReplacement = "specs/{feature_name}/$($fileMapping[$file]).md"
    # Apply replacement
}

# Pattern B: Direct file references  
foreach ($file in $fileMapping.Keys) {
    $oldPattern = "\b$file\.md\b"
    $newReplacement = "$($fileMapping[$file]).md"
    # Apply replacement
}

# Pattern C: Complex lists (handle individually)
$complexPatterns = @(
    @{
        Pattern = '\brequirements\.md and design\.md\b'
        Replacement = '02_requirements.md and 03_design.md'
    },
    @{
        Pattern = '\brequirements\.md, design\.md and tasks\.md\b'  
        Replacement = '02_requirements.md, 03_design.md and 04_tasks.md'
    },
    @{
        Pattern = '\brequirements\.md, design\.md, tasks\.md, feasibility\.md\b'
        Replacement = '02_requirements.md, 03_design.md, 04_tasks.md, 01_feasibility.md'
    }
)
```

## Pattern Testing

### Test Cases
```markdown
# Test Input
Create `specs/{feature_name}/feasibility.md`:
The model MUST create a 'specs/{feature_name}/requirements.md' file
Read requirements.md, design.md, tasks.md
ALL tasks in tasks.md marked complete
requirements.md and design.md files
Load all existing spec files (requirements.md, design.md, tasks.md, feasibility.md if present)

# Expected Output  
Create `specs/{feature_name}/01_feasibility.md`:
The model MUST create a 'specs/{feature_name}/02_requirements.md' file
Read 02_requirements.md, 03_design.md, 04_tasks.md
ALL tasks in 04_tasks.md marked complete
02_requirements.md and 03_design.md files
Load all existing spec files (02_requirements.md, 03_design.md, 04_tasks.md, 01_feasibility.md if present)
```

### Validation Tests
1. **No False Positives**: Ensure patterns don't match unintended text
2. **Complete Coverage**: Verify all 28 identified references are handled
3. **Order Preservation**: Maintain correct sequential numbering in lists
4. **Context Preservation**: Keep surrounding text intact

## Edge Cases Handled

### 1. File Extensions
- Only match `.md` files, not other extensions
- Word boundaries prevent partial matches

### 2. List Ordering  
- Maintain logical order: feasibility → requirements → design → tasks
- Handle out-of-order lists appropriately

### 3. Context Sensitivity
- Preserve grammatical structure in sentences
- Maintain proper punctuation in lists

## Implementation Priority

### Phase 1: Simple Patterns (Low Risk)
1. Pattern A: File paths (8 refs)
2. Pattern B: Direct references (15 refs)

### Phase 2: Complex Patterns (Medium Risk)  
3. Pattern C: Lists and combinations (5 refs)

### Phase 3: Validation
- Test all patterns against real template files
- Verify no unintended changes
- Confirm all 28 references updated correctly