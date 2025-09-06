# Improved-SDD Constitution

*Last updated: September 6, 2025*

## Project Vision
The Improved-SDD project provides a comprehensive Spec-Driven Development toolkit with customizable templates for chatmodes, instructions, and prompts, enabling teams to build software systematically through requirements-driven workflows.

## Core Principles

### I. Template-First Development
**Every workflow starts with structured templates**
- Chatmodes define AI assistant behavior patterns
- Instructions provide context-specific guidance
- Prompts enable repeatable, high-quality interactions
- Templates enforce consistency across projects and teams

### II. Spec-Driven Methodology (NON-NEGOTIABLE)
**Requirements → Design → Implementation → Validation**
- RED-GREEN-Refactor cycle strictly enforced
- Requirements must be testable and implemented
- Design must trace back to specific requirements
- Implementation must reflect actual vs planned state
- All three layers (requirements ↔ design ↔ code) stay synchronized

### III. Code Minimalism & Quality
**Maximum value with minimum code**
- Each line of code must justify its existence
- Maximum 400 lines per file, 5 public methods per class
- Prefer composition over complex inheritance
- No premature optimization or future-proofing
- Delete before add - always consider removing existing code

### IV. Multi-Platform Compatibility
**Support Windows, macOS, and Linux development**
- PowerShell scripts for Windows environments
- Bash scripts for Unix-like systems
- Python CLI tools for cross-platform functionality
- Template structures that work across all platforms

### V. AI Assistant Integration
**Built for modern AI-assisted development**
- Templates designed for Claude Code, GitHub Copilot, Gemini CLI
- Context-aware instructions and prompts
- Structured workflows that guide AI interactions
- Feedback loops between human and AI throughout development

### VI. Observability & Progress Tracking
**Transparent development process**
- Todo management for complex workflows
- Progress tracking through all phases
- Implementation status clearly documented
- Regular synchronization audits between specs and code

### VII. Security & Best Practices
**Security and quality by design**
- Path validation and input sanitization
- No secrets in templates or examples
- Security considerations in all workflows
- Regular dependency and vulnerability audits

## Implementation Standards

### Template Organization
```
templates/
├── chatmodes/          # AI assistant behavior definitions
├── instructions/       # Context-specific guidance
├── prompts/           # Reusable interaction patterns
└── commands/          # Command definitions for AI assistants
```

### Spec Directory Structure
```
specs/[###-feature]/
├── feasibility.md     # Initial assessment
├── requirements.md    # EARS format requirements
├── design.md         # Technical design
├── tasks.md          # Implementation checklist
├── contracts/        # API specifications
└── retrospective.md  # Post-implementation learnings
```

### Quality Gates

#### Phase 0: Feasibility Assessment
- [ ] Technical feasibility confirmed
- [ ] Effort estimate provided
- [ ] Major risks identified
- [ ] User approval obtained

#### Phase 1: Requirements Gate
- [ ] Requirements in EARS format
- [ ] Success metrics defined
- [ ] Out of scope explicitly listed
- [ ] User explicit approval

#### Phase 2: Design Gate
- [ ] Architecture addresses all requirements
- [ ] API contracts defined
- [ ] Security considerations documented
- [ ] User explicit approval

#### Phase 3: Implementation Gate
- [ ] All tasks trace to requirements
- [ ] Test strategy defined
- [ ] Rollback plan documented
- [ ] User explicit approval

#### Phase 4: Validation Gate
- [ ] All requirements acceptance criteria met
- [ ] Tests validate both design and requirements
- [ ] Implementation status accurately reflects reality
- [ ] Cross-spec dependencies verified

## Workflow Enforcement

### Mandatory User Approval Points
- After feasibility assessment completion
- After requirements document completion
- After design document completion
- After task list completion
- Major changes to any approved document

### Synchronization Rules
- **NEVER** implement code without corresponding design
- **NEVER** create design without requirements traceability
- **ALWAYS** update all three layers when making changes
- **MANDATORY** implementation status tracking in all docs

### Exception Handling
When constitutional principles conflict with project needs:
1. Document the conflict in complexity tracking
2. Provide justification for the exception
3. Identify simpler alternatives that were rejected
4. Get explicit approval from project stakeholders
5. Plan to refactor toward constitutional compliance

## Success Metrics
- Requirements traceability: 100%
- Implementation status accuracy: 100%
- User approval at each gate: Required
- Code quality metrics: Meet defined thresholds
- Template reusability: Cross-project validation
- AI assistant effectiveness: User feedback positive

## Evolution Process
This constitution evolves through:
1. Implementation feedback and learnings
2. Template effectiveness analysis
3. User experience improvements
4. Technology stack updates
5. Community contributions and suggestions

**Constitutional changes require:** Stakeholder review, impact analysis, template updates, and documentation revision.

---

*This constitution serves as the foundation for all Improved-SDD projects. It ensures quality, consistency, and successful outcomes while remaining flexible enough to adapt to project-specific needs.*