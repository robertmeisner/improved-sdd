# Template File Analysis - Spec File References

## Summary
Found **28 references** to spec files across **6 template files** that need updating.

## File Reference Mapping

### 1. sddSpecDriven.chatmode.md (15 references)
| Line | Context | Current Reference | New Reference |
|------|---------|-------------------|---------------|
| 286 | Documentation sync | requirements.md and design.md | 02_requirements.md and 03_design.md |
| 294 | File creation | .specs/{feature_name}/feasibility.md | .specs/{feature_name}/01_feasibility.md |
| 314 | File creation | .specs/{feature_name}/requirements.md | .specs/{feature_name}/02_requirements.md |
| 316 | Document format | requirements.md document | 02_requirements.md document |
| 395 | File creation | .specs/{feature_name}/design.md | .specs/{feature_name}/03_design.md |
| 401 | Document creation | .specs/{feature_name}/design.md | .specs/{feature_name}/03_design.md |
| 442 | File creation | .specs/{feature_name}/tasks.md | .specs/{feature_name}/04_tasks.md |
| 445 | Implementation plan | .specs/{feature_name}/tasks.md | .specs/{feature_name}/04_tasks.md |
| 476 | Section reference | tasks.md | 04_tasks.md |
| 538 | User instruction | tasks.md file | 04_tasks.md file |
| 686 | Execution prereq | requirements.md, design.md and tasks.md | 02_requirements.md, 03_design.md and 04_tasks.md |
| 717 | Task tracking | tasks.md file | 04_tasks.md file |
| 719 | Task completion | tasks.md file | 04_tasks.md file |
| 905 | Spec structure | requirements.md and design.md | 02_requirements.md and 03_design.md |
| 964 | Documentation sync | requirements.md and design.md | 02_requirements.md and 03_design.md |

### 2. sddSpecDrivenSimple.chatmode.md (8 references)
| Line | Context | Current Reference | New Reference |
|------|---------|-------------------|---------------|
| 172 | File creation | .specs/{feature_name}/feasibility.md | .specs/{feature_name}/01_feasibility.md |
| 181 | File creation | .specs/{feature_name}/requirements.md | .specs/{feature_name}/02_requirements.md |
| 211 | File creation | .specs/{feature_name}/design.md | .specs/{feature_name}/03_design.md |
| 223 | File creation | .specs/{feature_name}/tasks.md | .specs/{feature_name}/04_tasks.md |
| 257 | File reading | requirements.md, design.md, tasks.md | 02_requirements.md, 03_design.md, 04_tasks.md |
| 300 | Directory structure | feasibility.md | 01_feasibility.md |
| 301 | Directory structure | requirements.md | 02_requirements.md |
| 302 | Directory structure | design.md | 03_design.md |
| 303 | Directory structure | tasks.md | 04_tasks.md |

### 3. gitlab-flow-pr.md (2 references)
| Line | Context | Current Reference | New Reference |
|------|---------|-------------------|---------------|
| 16 | Prerequisites | tasks.md | 04_tasks.md |
| 64 | Review checklist | tasks.md | 04_tasks.md |

### 4. gitlab-flow-workflow.md (4 references)
| Line | Context | Current Reference | New Reference |
|------|---------|-------------------|---------------|
| 37 | Commit workflow | feasibility.md | 01_feasibility.md |
| 38 | Commit workflow | requirements.md | 02_requirements.md |
| 39 | Commit workflow | design.md | 03_design.md |
| 40 | Commit workflow | tasks.md | 04_tasks.md |

### 5. sddSpecSync.prompt.md (6 references)
| Line | Context | Current Reference | New Reference |
|------|---------|-------------------|---------------|
| 10 | Sync task | requirements.md | 02_requirements.md |
| 11 | Sync task | design.md | 03_design.md |
| 12 | Sync task | tasks.md | 04_tasks.md |
| 22 | Update task | requirements.md | 02_requirements.md |
| 53 | File loading | requirements.md, design.md, tasks.md, feasibility.md | 02_requirements.md, 03_design.md, 04_tasks.md, 01_feasibility.md |
| 65 | Output files | requirements.md, design.md, and tasks.md | 02_requirements.md, 03_design.md, and 04_tasks.md |

### 6. sddTaskExecution.prompt.md (1 reference)
| Line | Context | Current Reference | New Reference |
|------|---------|-------------------|---------------|
| 25 | Documentation | requirements.md or design.md | 02_requirements.md or 03_design.md |

## File Categories for Update

### High Priority (P0) - Core Workflow Files
1. **sddSpecDriven.chatmode.md** - Main chatmode template (15 refs)
2. **sddSpecDrivenSimple.chatmode.md** - Simple chatmode template (8 refs)

### Medium Priority (P1) - Supporting Templates  
3. **sddSpecSync.prompt.md** - Spec synchronization prompt (6 refs)
4. **gitlab-flow-workflow.md** - GitLab Flow workflow (4 refs)

### Low Priority (P2) - Documentation
5. **gitlab-flow-pr.md** - PR template (2 refs)
6. **sddTaskExecution.prompt.md** - Task execution prompt (1 ref)

## Reference Patterns Identified

### Pattern 1: File Path References
- `.specs/{feature_name}/[filename].md`
- **Count**: 8 occurrences
- **Regex**: `\.specs/\{feature_name\}/(feasibility|requirements|design|tasks)\.md`

### Pattern 2: Direct File References
- `[filename].md` (without path)
- **Count**: 15 occurrences  
- **Regex**: `\b(feasibility|requirements|design|tasks)\.md\b`

### Pattern 3: Comma-separated File Lists
- `requirements.md, design.md and tasks.md`
- **Count**: 5 occurrences
- **Regex**: `(feasibility|requirements|design|tasks)\.md(?:,?\s+(?:and\s+)?(feasibility|requirements|design|tasks)\.md)*`

## Next Steps for Task 1.2
- Create comprehensive regex patterns based on identified patterns
- Test patterns against sample content
- Validate replacement accuracy