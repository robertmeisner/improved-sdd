# Pragmatic Codebase Testing & Fix Agent

## Objective
Test entire codebase, fix broken tests and code, use pragmatic approaches for quick results.

## Context
- **Project Structure**: Source code in `src/`, tests in `tests/` (or `test/`, `spec/`)
- **Focus**: Fix what's broken, skip perfection
- **Approach**: Results over process

## Execution Instructions

### 1. Discovery
Identify test framework and run discovery:
```bash
# Examples by language/framework
npm test -- --listTests          # Jest/Node
mvn test -Dtest=*                # Java/Maven
dotnet test --list-tests         # .NET
go test ./... -list              # Go
pytest --collect-only            # Python
rspec --dry-run                  # Ruby
```

### 2. Test Execution Priority
```bash
# Quick failure detection
[test-runner] --fail-fast        # Stop on first failure
[test-runner] --verbose           # Detailed output
[test-runner] --exclude=slow      # Skip slow tests

# Targeted testing
[test-runner] path/to/specific   # Specific module
[test-runner] --grep="pattern"   # Pattern matching
[test-runner] --tag=unit          # By category

# Coverage
[test-runner] --coverage          # With coverage report
```

### 3. Fix Priority
1. **Build errors** - Code won't compile/run
2. **Setup failures** - Dependencies/environment
3. **Assertion failures** - Logic issues  
4. **Flaky tests** - Timing/concurrency
5. **Coverage gaps** - Critical paths only

### 4. Common Fixes
- **Timeouts**: Increase limits or add async handling
- **Dependencies**: Check package versions, lock files
- **Paths**: Verify relative/absolute paths, working directory
- **Environment**: Check required env vars, config files
- **Cleanup**: Ensure proper teardown/resource disposal
- **Cache**: Clear test cache if behavior unexpected

## Required Output

### Summary
```
Tests: X → Y (passing/total)
Coverage: X% → Y%
Runtime: Xs → Ys
```

### Critical Fixes
For each fix:
- Test/file name
- Actual code change
- Verification passed

### Remaining Issues
- What needs manual intervention
- Why it can't be auto-fixed
- Suggested approach

### CI/CD Commands
```bash
# Minimal working command set for pipeline
[test-command]
[coverage-command]
```

## Response Constraints
- Show code fixes, not descriptions
- Provide executable commands
- Focus on results over process
- Use project's existing test framework