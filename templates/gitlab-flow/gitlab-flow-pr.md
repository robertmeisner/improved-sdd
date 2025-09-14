## Create Pull Request

**🚨 CRITICAL**: Only create PR after ALL implementation tasks are completed and tested!

### Prerequisites Verification

Before creating a pull request, ensure you have completed:

**✅ Specification Complete**:
- [ ] Feasibility assessment approved
- [ ] Requirements document approved
- [ ] Design document approved
- [ ] Implementation tasks approved

**✅ Implementation Complete**:
- [ ] ALL tasks in 04_tasks.md marked complete (✅)
- [ ] All code implementations finished
- [ ] Comprehensive testing completed
- [ ] Documentation updated
- [ ] No failing tests or linting errors

### Push and Create PR

Once implementation is complete, push your branch and create a pull request:

```bash
# Push feature branch and create pull request
{PUSH_PR}
```

### PR Guidelines

#### PR Title Format
```
Spec: {Feature Name}
```

**Examples**:
- `Spec: User Authentication`
- `Spec: Payment System Integration`
- `Spec: Data Migration Framework`

#### PR Description Template
```markdown
## Specification Summary

Brief summary of the feature specification and implementation.

## Implementation Highlights

- Key architectural decisions made
- Important implementation details
- Any trade-offs or compromises

## Testing Coverage

- [ ] Unit tests implemented
- [ ] Integration tests added
- [ ] Edge cases covered
- [ ] Performance requirements met

## Review Checklist

- [ ] All tasks in 04_tasks.md completed ✅
- [ ] Code follows project standards
- [ ] Documentation updated
- [ ] No breaking changes
- [ ] Security considerations addressed

## Deployment Notes

- Any special deployment considerations
- Database migrations required (if any)
- Configuration changes needed
```

### Manual PR Creation (Alternative)

If the automated command fails, create PR manually:

1. **Push branch**:
   ```bash
   git push -u origin feature/spec-{feature-name}
   ```

2. **Visit GitHub repository** and click "Compare & pull request"

3. **Fill in details**:
   - Title: `Spec: {Feature Name}`
   - Description: Use template above
   - Reviewers: Add relevant team members
   - Labels: Add appropriate labels (e.g., `spec`, `feature`)

### Review Process

**🔍 Review Focus Areas**:
- **Specification Quality**: Requirements complete and testable
- **Design Soundness**: Architecture decisions well-justified
- **Implementation Quality**: Code follows project standards
- **Test Coverage**: Comprehensive testing of all functionality
- **Documentation**: Clear and up-to-date documentation

**📋 Post-Review Actions**:
- Address reviewer feedback promptly
- Update code and documentation as needed
- Re-request review after changes
- Merge only after all approvals received

### Success Criteria

**✅ PR Ready for Merge When**:
- [ ] All implementation tasks completed
- [ ] All automated checks passing
- [ ] Required approvals received
- [ ] No unresolved review comments
- [ ] Documentation updated and accurate

**🎉 Congratulations!** Your specification-driven development cycle is complete!
