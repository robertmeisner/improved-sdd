---
mode: agent
---
# Project-Wide Commit Analysis & Execution Framework

## EXECUTION PROTOCOL - Follow These Steps Precisely

### 1. INITIAL ASSESSMENT
**IMMEDIATELY run these commands to gather data:**
```bash
git status --porcelain
git diff --stat
git diff --name-only
git ls-files --others --exclude-standard
```

**Analyze the output and:**
- Count total files changed, added, deleted
- Identify file types and categories
- Check for any obviously problematic files (large binaries, secrets, etc.)

### 2. DETAILED CHANGE ANALYSIS
**Run these commands to get comprehensive change details:**
```bash
git diff --cached --stat  # Staged changes
git diff --stat           # Unstaged changes
git diff --name-status    # File status summary
```

**For each modified file, determine:**
- **Source Code**: .py, .js, .ts, .java, .cpp, .c, .h, .cs files
- **Configuration**: .json, .yml, .yaml, .ini, .cfg, .env files
- **Documentation**: .md, .rst, .txt, README files
- **Tests**: Files in test/ directories or with test_ prefix
- **Dependencies**: requirements.txt, package.json, setup.py, etc.
- **Build/Generated**: Files in dist/, build/, __pycache__/, .next/, etc.

### 3. SECURITY & EXCLUSION SCAN
**Check for files that should NEVER be committed:**
```bash
# Check for large files (>50MB)
find . -type f -size +50M -not -path "./.git/*" 2>/dev/null || echo "No large files found"

# Check for potential secrets
git diff | grep -i "password\|secret\|key\|token" || echo "No obvious secrets found"

# Check for sensitive file patterns
git ls-files | grep -E "\.(pem|key|cert|env|local)$" || echo "No sensitive files found"
```

**Automatically exclude:**
- IDE files: .vscode/, .idea/, *.swp, *.swo
- OS files: .DS_Store, Thumbs.db, desktop.ini
- Temp files: *.tmp, *.temp, *.log (if not needed)
- Generated files: __pycache__/, *.pyc, node_modules/ (if auto-generated)

### 4. COMMIT GROUPING STRATEGY
**Analyze changes and create logical commit groups:**

**Group 1 - Core Functionality Changes:**
- Related feature implementations
- Bug fixes in the same module
- API changes and their tests

**Group 2 - Configuration & Setup:**
- Configuration file changes
- Environment setup changes
- Build tool configurations

**Group 3 - Documentation & Tests:**
- Documentation updates
- Test additions/improvements
- Code comment improvements

**Group 4 - Dependencies & Tools:**
- Package updates
- Tool configurations
- Development environment changes

### 5. EXECUTE COMMITS
**For each commit group, execute:**
```bash
# Stage files for this commit group
git add [specific files for this group]

# Create commit with proper message
git commit -m "type(scope): description

- Detailed change 1
- Detailed change 2
- Related changes"

# Verify commit
git show --stat HEAD
```

### 6. FINAL VALIDATION & PUSH
**Before pushing, validate:**
```bash
# Check commit history
git log --oneline -5

# Run tests if available
npm test || yarn test || python -m pytest || echo "No test runner found"

# Check for any remaining uncommitted changes
git status --porcelain

# Pull latest changes
git pull --rebase origin main

# Push commits
git push origin main
```

## RESPONSE FORMAT - What You Must Report

### 📋 EXECUTION SUMMARY
**Repository**: [actual repo name]
**Branch**: [current branch]
**Total Commits Created**: X
**Files Processed**: Y
**Push Status**: ✅ Success | ⚠️ Manual Review | ❌ Failed

### 🔍 ANALYSIS RESULTS
**Change Categories Found**:
- Source Code: X files
- Tests: Y files
- Configuration: Z files
- Documentation: W files

**Security Scan Results**:
- Large Files Detected: [list or "none"]
- Potential Secrets: [list or "none"]
- Files Excluded: [list or "none"]

### ✅ COMMITS EXECUTED
| Commit # | Type | Files | Message |
|----------|------|-------|---------|
| 1 | feat | src/*.py | Feature implementation |
| 2 | fix | tests/*.py | Bug fixes |
| 3 | docs | README.md | Documentation updates |

### ⚠️ ISSUES ENCOUNTERED
| Issue | Severity | Resolution |
|-------|----------|------------|
| Large file detected | 🔴 Critical | Excluded from commit |
| Test failures | 🟠 High | Manual review required |
| Merge conflicts | 🔴 Critical | Resolved with rebase |

### 🚫 FILES EXCLUDED FROM COMMITS
- **Automatically Excluded**: [list files that were skipped]
- **User Decisions**: [files excluded based on analysis]
- **Security Concerns**: [files with potential secrets]

### 📋 EXECUTION LOG
```
[Timestamp] Started analysis
[Timestamp] Found X modified files
[Timestamp] Created commit group 1: "feat: core functionality"
[Timestamp] Created commit group 2: "test: test improvements"
[Timestamp] Pushed to remote successfully
```

### 🧪 VALIDATION RESULTS
- [ ] Tests passed before push
- [ ] No merge conflicts during pull
- [ ] All commits follow conventional format
- [ ] No sensitive data in commits
- [ ] Branch is up to date with remote

### � EXECUTION METRICS
- **Analysis Time**: X seconds
- **Commits Created**: Y
- **Files Processed**: Z
- **Success Rate**: W%

### 📈 RECOMMENDATIONS
- [ ] Enable pre-commit hooks for future commits
- [ ] Set up automated testing in CI/CD
- [ ] Configure branch protection rules
- [ ] Add commit message templates

### 🏁 FINAL STATUS
- **Overall Success**: ✅ Complete | ⚠️ Partial | ❌ Failed
- **Next Steps**: [any follow-up actions needed]
- **Confidence Level**: X%
- **Review Required**: Yes/No

## CRITICAL EXECUTION RULES

### ⚠️ STOP AND ASK FOR HELP IF:
- You detect sensitive data (passwords, API keys, secrets)
- Large files (>100MB) are detected
- Tests are failing and you can't determine why
- Merge conflicts occur during pull
- You're unsure about file categorization

### ✅ ALWAYS DO THESE THINGS:
- Run `git status` before and after each commit
- Use conventional commit format: `type(scope): description`
- Test changes before committing (if tests exist)
- Pull latest changes before pushing
- Verify no sensitive data is being committed

### 🚫 NEVER DO THESE THINGS:
- Commit large binary files without checking .gitignore
- Push without pulling latest changes first
- Commit generated files (node_modules, __pycache__, etc.)
- Use generic commit messages like "update" or "fix"
- Commit sensitive configuration files (.env, secrets, etc.)

## EXAMPLE EXECUTION SCENARIO

**Scenario: Python project with feature changes and tests**

```bash
# Step 1: Initial assessment
git status --porcelain
git diff --stat

# Step 2: Analyze changes
# Found: 15 modified .py files, 3 new test files, 1 README update

# Step 3: Security scan
find . -type f -size +50M 2>/dev/null || echo "No large files"
git diff | grep -i "password\|secret" || echo "No secrets found"

# Step 4: Create commit groups
git add src/feature.py src/utils.py
git commit -m "feat: implement new feature

- Add feature implementation in src/feature.py
- Update utility functions in src/utils.py
- Maintain backward compatibility"

git add tests/test_feature.py tests/test_utils.py
git commit -m "test: add tests for new feature

- Add comprehensive unit tests
- Test edge cases and error conditions
- Achieve 95% test coverage"

git add README.md
git commit -m "docs: update README with new feature

- Document new feature usage
- Update API examples
- Add installation instructions"

# Step 5: Validate and push
npm test || python -m pytest || echo "No tests found"
git pull --rebase origin main
git push origin main
```

This framework ensures systematic, secure, and well-organized commits that follow best practices and maintain code quality.

- Modified database config
- Updated environment variables"

git add [docs]
git commit -m "docs: update README and API docs"
```

### 📋 Pre-Push Checklists
- [ ] All changes tested locally
- [ ] No sensitive data in commits
- [ ] Commit messages follow conventions
- [ ] Branch is up to date with remote
- [ ] CI/CD checks will pass
- [ ] Breaking changes documented

### 🧪 Validation Recommendations
- [ ] Run test suite before pushing
- [ ] Check for linting errors
- [ ] Verify build process works
- [ ] Test deployment if applicable
- [ ] Review changes with team if needed

### 📊 Commit Quality Score
- **Atomicity**: X/10 (how well changes are grouped)
- **Clarity**: X/10 (commit message quality)
- **Completeness**: X/10 (all related changes included)
- **Safety**: X/10 (no sensitive data, proper exclusions)
- **Overall Score**: X/10

### 📈 Improvement Priority
1. **Critical** (🔴): Security issues, large files, secrets
2. **High** (🟠): Breaking changes, missing tests
3. **Medium** (🟡): Commit message improvements, grouping
4. **Low** (🟢): Documentation, minor optimizations

### ✨ Enhancement Suggestions
- Implement pre-commit hooks for automatic checks
- Use conventional commit format consistently
- Set up automated testing before commits
- Configure .gitignore templates for project type
- Enable commit signing for security

```

This framework ensures systematic, secure, and well-organized commits that follow best practices and maintain code quality.
