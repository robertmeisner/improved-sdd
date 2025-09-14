# Spec Re-evaluation and Synchronization Request

Re-evaluate and synchronize the provided spec with the current project state using available analysis tools. Ensure all spec documents accurately reflect the actual implemented code and project structure.

## Spec Synchronization Requirements

Provide a comprehensive re-evaluation covering:

### 1. Spec-to-Code Alignment Analysis
- Compare requirements.md against actual implemented functionality
- Verify design.md matches current architecture and implementation
- Check tasks.md completion status and accuracy
- Identify discrepancies between spec and reality

### 2. Current Implementation Assessment
- Analyze existing codebase structure and patterns
- Document actual functionality that may not be in specs
- Identify implemented features missing from requirements
- Assess current code quality and architecture decisions

### 3. Requirements Synchronization
- Update requirements.md to reflect actual system capabilities
- Add missing user stories for implemented functionality
- Remove or mark obsolete requirements that are no longer relevant
- Ensure acceptance criteria match current behavior
- Logically validate requirements for consistency, completeness, and feasibility
- Update priority levels based on actual implementation status

### 4. Design Document Alignment
- Synchronize architecture section with current codebase structure
- Update component and interface descriptions to match implementation
- Verify data models reflect actual schemas/structures
- Update API contracts to match current endpoints
- Align security and performance considerations with implementation

### 5. Task Status and Completion
- Mark completed tasks based on actual implementation
- Identify partially completed tasks and document remaining work
- Add new tasks for functionality that exists but wasn't in original spec
- Update time estimates based on actual implementation complexity
- Document technical debt and improvement opportunities

### 6. Gap Analysis and Recommendations
- Identify missing functionality compared to original requirements
- Document unplanned features that were implemented
- Assess technical debt introduced during implementation
- Recommend next steps for full spec-code alignment
- Suggest improvements to prevent future desynchronization

## Instructions

1. **Start with Project Analysis**: Use available tools to analyze the current project structure and codebase
2. **Load Spec Files**: Read all existing spec files (requirements.md, design.md, tasks.md, feasibility.md if present)
3. **Compare and Contrast**: Systematically compare each spec section against actual implementation
4. **Update Spec Documents**: Modify spec files to accurately reflect current state
5. **Document Changes**: Clearly indicate what was updated and why
6. **Provide Recommendations**: Suggest actions to maintain spec-code synchronization going forward
7. If any mismatch between spec and reality is found, double down and check a wider scope because this might not be isolated.

## Output Format

Structure your response with:
- **Executive Summary**: High-level sync status and key findings
- **Detailed Analysis**: Section-by-section comparison and updates
- **Updated Spec Files**: Revised requirements.md, design.md, and tasks.md
- **Change Log**: What was modified and rationale
- **Recommendations**: Actions to prevent future desynchronization

Please ensure all updates reflect the **current actual state** of the code, not what it was planned to be. Remove any migration language and focus on documenting what exists now.
