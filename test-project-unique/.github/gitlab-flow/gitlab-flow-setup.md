# GitLab Flow Setup Agent Instructions

**CRITICAL**: Execute these commands BEFORE starting any spec development workflow.

## MANDATORY PRE-WORKFLOW SETUP

### Step 1: Repository Status Verification

**EXECUTE IMMEDIATELY:**
```bash
git status
```

**THEN EXECUTE:**
```bash
git checkout master ; git pull origin master
```

**VERIFY OUTPUT**: Ensure repository is clean and up-to-date before proceeding.

### Step 2: Create Feature Branch

**EXECUTE THIS COMMAND** (replace `{kebab-case-name}` with actual feature name):
```bash
git checkout -b feature/spec-{kebab-case-name}
```

## BRANCH NAMING REQUIREMENTS

**Format**: `feature/spec-{kebab-case-name}`

**Agent Translation Examples**:
- "User Authentication" → `feature/spec-user-authentication`
- "Payment System" → `feature/spec-payment-system` 
- "Data Migration" → `feature/spec-data-migration`
- "API Integration" → `feature/spec-api-integration`

## VALIDATION CHECKLIST

**AGENT MUST VERIFY** before proceeding to spec development:

### ✅ Required Conditions
- [ ] `git status` shows clean working directory
- [ ] Currently on master/main branch  
- [ ] Latest changes pulled from origin
- [ ] Feature branch created successfully
- [ ] Branch name follows exact naming convention

### ✅ Terminal Command Verification
**RUN THIS TO CONFIRM SETUP:**
```bash
git branch --show-current
```
**Expected Output**: `feature/spec-{your-feature-name}`

## ERROR HANDLING

**If git checkout fails:**
1. Run `git status` to check for uncommitted changes
2. Commit or stash changes: `git stash`
3. Retry checkout command
4. Report any errors to user

**If branch already exists:**
1. Switch to existing branch: `git checkout feature/spec-{name}`
2. Ensure it's up to date: `git pull origin master`
3. Continue with spec development

## NEXT ACTION

**AFTER SUCCESSFUL SETUP**: Begin feasibility assessment phase and commit each spec phase as completed.

**WORKFLOW BENEFITS**: Feature isolation, incremental safety, team collaboration, easy rollback.
