# Improved-SDD CLI Usage

## Installation

### Option 1: Using pip (recommended for regular use)
```bash
# Install dependencies
pip install -r requirements.txt

# Run the CLI
python src/improved_sdd_cli.py --help
python src/improved_sdd_cli.py init
python src/improved_sdd_cli.py init --app-type mcp-server
python src/improved_sdd_cli.py init my-project --new-dir
```

### Option 2: Using uv (for development)
```bash
# Run directly with uv (no installation needed)
uvx src/improved_sdd_cli.py init
uv run src/improved_sdd_cli.py init
```

## Commands

- `init` - Install Improved-SDD templates for GitHub Copilot Studio
- `check` - Check that all required tools are installed
- `delete` - Delete a project directory with confirmation

### GitLab Flow Integration

The `init` command supports GitLab Flow integration through CLI flags:

- `--gitlab-flow` - Enable GitLab Flow workflow guidance (default)
- `--no-gitlab-flow` - Disable GitLab Flow integration

## Common Usage

```bash
# Install in current directory with GitLab Flow (default)
python src/improved_sdd_cli.py init

# Create new project directory with GitLab Flow
python src/improved_sdd_cli.py init my-project --new-dir

# Initialize without GitLab Flow integration
python src/improved_sdd_cli.py init my-project --no-gitlab-flow

# Skip confirmation prompts
python src/improved_sdd_cli.py init --force

# Specify app type with GitLab Flow
python src/improved_sdd_cli.py init --app-type python-cli --gitlab-flow

# Check project status
python src/improved_sdd_cli.py check my-project

# Delete project with confirmation
python src/improved_sdd_cli.py delete my-project
```

## GitLab Flow Integration Details

### What is GitLab Flow?

GitLab Flow integration provides automatic workflow guidance during spec-driven development:

- **Branch Management**: Automatic feature branch creation guidance
- **Commit Workflow**: Structured commit prompts after each spec phase
- **PR Timing**: Prevents premature PR creation before implementation completion
- **Platform Commands**: Windows PowerShell vs Unix/macOS bash syntax

### How It Works

1. **Dynamic Keywords**: GitLab Flow content loaded from markdown files
2. **Conditional Replacement**: Keywords replaced based on `--gitlab-flow` flag
3. **Platform Detection**: Commands automatically adapted to your OS
4. **Workflow Integration**: Git guidance appears at natural workflow points

### Example: Enabling GitLab Flow

```bash
# Initialize project with GitLab Flow
python src/improved_sdd_cli.py init user-auth-feature --gitlab-flow

# This will:
# 1. Install templates with GitLab Flow keywords enabled
# 2. Show branch setup guidance in chatmode
# 3. Provide commit prompts after each spec phase
# 4. Include PR creation guidance after implementation
```

### Example: Disabling GitLab Flow

```bash
# Initialize project without GitLab Flow
python src/improved_sdd_cli.py init user-auth-feature --no-gitlab-flow

# This will:
# 1. Install templates with GitLab Flow keywords disabled
# 2. Show standard spec workflow without git guidance
# 3. No automatic commit or PR prompts
```

### GitLab Flow Workflow Steps

1. **Setup Phase**: Repository validation and feature branch creation
2. **Feasibility Phase**: Commit feasibility assessment
3. **Requirements Phase**: Commit approved requirements
4. **Design Phase**: Commit approved design
5. **Tasks Phase**: Commit implementation task list
6. **Implementation Phase**: Commit after completing each task
7. **PR Creation**: Create pull request when all tasks complete

### Platform-Specific Commands

GitLab Flow automatically detects your platform and provides appropriate commands:

**Windows (PowerShell)**:
```powershell
git status
git checkout -b feature/spec-user-auth
git add .; git commit -m "Add requirements for user-auth"
```

**Unix/macOS (Bash)**:
```bash
git status
git checkout -b feature/spec-user-auth
git add . && git commit -m "Add requirements for user-auth"
```

## Version Management Utility

The version management utility (`tools/bump_version.py`) provides professional semantic version management for releases.

### Basic Usage

```bash
# Show current version and available bumps
python tools/bump_version.py current

# Bump version with dry-run preview
python tools/bump_version.py bump patch --dry-run
python tools/bump_version.py bump minor --dry-run  
python tools/bump_version.py bump major --dry-run

# Actually bump the version
python tools/bump_version.py bump patch

# Validate version format
python tools/bump_version.py validate 1.2.3-alpha.1

# Show documentation and examples
python tools/bump_version.py info
```

### Release Workflow

The tool provides step-by-step guidance for the complete release workflow:

1. **Bump Version**: Update version in `pyproject.toml`
2. **Commit Changes**: Git commit with version bump
3. **Create Tag**: Git tag with version (triggers PyPI publishing)
4. **Push Changes**: Push commits and tags to trigger automation

**Example workflow**:
```bash
# 1. Bump version
python tools/bump_version.py bump patch

# 2. Follow the provided instructions:
git add pyproject.toml
git commit -m "chore: bump version to 0.1.4"
git tag v0.1.4
git push origin main
git push origin v0.1.4

# 3. Monitor at: https://github.com/robertmeisner/improved-sdd/actions
```

### Features

- **Semantic Versioning**: Full SemVer support with prerelease/build metadata
- **Rich UI**: Beautiful terminal output with tables and color coding
- **Dry Run Mode**: Preview changes before applying them
- **Validation**: Verify version formats before using them
- **Error Handling**: Clear error messages with helpful tips
- **Next Steps**: Automated Git workflow guidance
- **PyPI Integration**: Direct integration with publishing automation
