# Constitution Update Checklist

*Use this checklist when updating the constitution to ensure all dependent files are updated*

## When to Update the Constitution

- New core principles are discovered through project experience
- Quality gates need modification based on learnings
- Template structures change significantly
- New AI assistant integrations are added
- Workflow processes are enhanced or modified

## Templates to Update

### When adding/modifying ANY article:
- [ ] `/templates/chatmodes/*.md` - Update mode behavior if workflow changes
- [ ] `/templates/instructions/*.md` - Update context instructions if principles change
- [ ] `/templates/prompts/*.md` - Update prompt patterns if quality gates change
- [ ] `/templates/commands/*.md` - Update command definitions if workflow changes
- [ ] `/scripts/*.ps1` - Update PowerShell scripts if process changes
- [ ] `/src/improved_sdd_cli.py` - Update CLI if initialization changes

### Specific Update Categories

#### Quality Gate Changes:
- [ ] Update all chatmode templates with new quality criteria
- [ ] Modify executeTask.prompt.md with new validation steps
- [ ] Update doubleCheck.prompt.md with new quality measures
- [ ] Revise constitution check sections in all templates

#### Workflow Process Changes:
- [ ] Update specMode.chatmode.md workflow definition
- [ ] Modify task execution prompts and instructions
- [ ] Update script logic to match new workflow steps
- [ ] Revise CLI tool to support new process

#### Template Structure Changes:
- [ ] Update all template files to match new structure
- [ ] Modify CLI tool template creation logic
- [ ] Update documentation and examples
- [ ] Verify cross-platform compatibility

#### AI Assistant Integration Changes:
- [ ] Update chatmode templates for new AI capabilities
- [ ] Modify instruction templates for new AI features
- [ ] Update prompt templates for improved AI interactions
- [ ] Test with target AI assistants

## Verification Steps

### After Constitution Updates:
1. [ ] Review all template files for consistency
2. [ ] Test CLI tool initialization process
3. [ ] Verify script functionality on target platforms
4. [ ] Validate with actual AI assistant workflows
5. [ ] Update version numbers and timestamps
6. [ ] Create changelog entry documenting changes

### Cross-Reference Validation:
- [ ] Constitution principles align with template content
- [ ] Quality gates are consistently implemented
- [ ] Workflow steps match across all files
- [ ] Error handling follows constitutional guidelines
- [ ] Security principles are uniformly applied

## Impact Assessment

### Before Making Changes:
- [ ] Identify all files that reference the changing principle
- [ ] Assess impact on existing projects using the constitution
- [ ] Plan migration strategy for existing implementations
- [ ] Consider backward compatibility requirements

### After Making Changes:
- [ ] Test with representative project scenarios
- [ ] Validate AI assistant integration still works
- [ ] Verify all scripts execute successfully
- [ ] Confirm template generation produces correct output
- [ ] Update any dependent documentation

## Communication Plan

### Internal Updates:
- [ ] Update project README with constitutional changes
- [ ] Document rationale for changes in commit messages
- [ ] Create migration guide if breaking changes exist
- [ ] Update any training materials or examples

### External Communication:
- [ ] Notify teams using Improved-SDD of changes
- [ ] Provide upgrade guidance for existing projects
- [ ] Update any public documentation or tutorials
- [ ] Consider deprecation timeline for changed features

## Quality Assurance

### Pre-Release Validation:
- [ ] Full end-to-end test of spec-driven development workflow
- [ ] Multi-platform testing (Windows, macOS, Linux)
- [ ] AI assistant integration testing (Claude, Copilot, Gemini)
- [ ] Template generation and customization testing
- [ ] Script execution and error handling validation

### Post-Release Monitoring:
- [ ] Collect user feedback on constitutional changes
- [ ] Monitor for issues or confusion with new processes
- [ ] Track effectiveness of quality gate modifications
- [ ] Document lessons learned for future updates

---

*This checklist ensures constitutional changes are implemented consistently across all project components while maintaining quality and compatibility.*