# Pull Request Creation Agent Instructions

**🚨 CRITICAL**: Execute ONLY after ALL implementation tasks are completed and tested!

## MANDATORY PRE-PR VERIFICATION

**AGENT MUST VERIFY** before creating PR:

### Step 1: Specification Completion Check
**EXECUTE THIS VERIFICATION:**
```bash
# Verify all spec documents exist and are complete
ls .specs/{feature-name}/ | findstr /R "01_feasibility.md 02_requirements.md 03_design.md 04_tasks.md"
```

### Step 2: Implementation Status Check
**VERIFY ALL TASKS MARKED COMPLETE:**
- Check that ALL `[ ]` in 04_tasks.md are changed to `[x]`
- Confirm no `[-]` (in-progress) tasks remain
- Validate all code implementations finished

### Step 3: Testing Verification
**EXECUTE TESTING COMMANDS:**
```bash
# Run all tests to ensure passing
pytest tests/ -v
```

## PR CREATION COMMANDS

### Primary Method: Automated PR Creation
**EXECUTE THIS COMMAND** (replace `{feature-name}` with actual name):
```bash
git push -u origin feature/spec-{feature-name} ; gh pr create --title "Spec: {Feature Name}" --body "Implementation of {feature-name} specification"
```

### Fallback Method: Manual Push + GitHub UI
**IF AUTOMATED METHOD FAILS:**
```bash
git push -u origin feature/spec-{feature-name}
```
**THEN INSTRUCT USER**: "Visit GitHub repository and click 'Compare & pull request'"

## PR CONFIGURATION REQUIREMENTS

### Title Format (EXACT)
```
Spec: {Feature Name}
```

**Agent Translation Examples**:
- feature/spec-user-authentication → `Spec: User Authentication`
- feature/spec-payment-system → `Spec: Payment System`

### PR Description Template (USE THIS EXACT FORMAT)
```markdown
## Specification Summary

Implementation of {feature-name} following specification-driven development process.

## Implementation Highlights

- Completed feasibility assessment and requirements analysis
- Implemented design with {key-architecture-decisions}
- All tasks in 04_tasks.md completed successfully

## Testing Coverage

- [x] Unit tests implemented and passing
- [x] Integration tests added where applicable
- [x] Edge cases covered in test scenarios
- [x] All automated checks passing

## Review Checklist

- [x] All tasks in 04_tasks.md completed ✅
- [x] Code follows project standards
- [x] Documentation updated and synchronized
- [x] No breaking changes introduced
- [x] Security considerations addressed

## Deployment Notes

{deployment-considerations-if-any}
```

## ERROR HANDLING

**If `gh pr create` fails:**
1. **EXECUTE**: `gh auth status` to check GitHub CLI authentication
2. **IF NOT AUTHENTICATED**: Instruct user to run `gh auth login`
3. **RETRY**: PR creation command after authentication
4. **FALLBACK**: Use manual push method above

**If push fails:**
1. **EXECUTE**: `git status` to check for uncommitted changes
2. **COMMIT REMAINING**: `git add . ; git commit -m "feat: Final cleanup before PR"`
3. **RETRY**: Push command

## POST-PR ACTIONS

**AGENT MUST COMMUNICATE TO USER:**
1. "✅ Pull request created successfully"
2. "🔗 PR URL: {generated-url}"
3. "📋 Next: Wait for code review and address any feedback"
4. "🎉 Specification-driven development cycle complete!"

## VERIFICATION COMMANDS

**CONFIRM PR CREATION:**
```bash
gh pr list --head feature/spec-{feature-name}
```

**Expected Output**: Should show the created PR with "Spec: {Feature Name}" title
