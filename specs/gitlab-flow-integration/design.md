# Design Document: GitLab Flow Integration

## Overview

This design document outlines the implementation of GitLab Flow integration into the sddSpecDriven chatmode using **Dynamic Keyword Integration** approach.

The solution uses **keyword replacement system extension** to add git workflow management directly into the main chatmode without breaking existing templates or requiring complex configuration.

The implementation will extend the existing keyword replacement system in `src/core/config.py` and `src/utils.py` to include:
- **GitLab Flow configuration** - Following same pattern as AI tool configuration
- **Dynamic workflow keywords** - Conditionally replaced based on CLI flag
- **Main chatmode integration** - GitLab Flow steps embedded in core workflow
- **Platform-specific commands** - Windows PowerShell vs macOS/Linux bash syntax

**Key Design Principles**:
- ✅ **Leverage existing architecture** - Extend proven keyword replacement system
- ✅ **Zero breaking changes** - Existing functionality unchanged when GitLab Flow disabled
- ✅ **Core workflow integration** - GitLab Flow embedded in main chatmode file
- ✅ **Dynamic behavior** - CLI flag controls keyword replacement during installation
- ✅ **Platform awareness** - Commands tailored to user's operating system

**Current Implementation Status**: NOT IMPLEMENTED - Extension of existing keyword system

**Target Architecture**: GitLab Flow configuration will be added to config.py following AI tool patterns, with keywords embedded in the main sddSpecDriven.chatmode.md file.

## Architecture

### Dynamic Keyword Integration Architecture

The GitLab Flow integration extends the existing keyword replacement system to include GitLab Flow configuration and workflow keywords:

```
src/core/config.py
├── AI Tools Configuration (existing)
│   ├── github-copilot: {AI_ASSISTANT}, {AI_SHORTNAME}, {AI_COMMAND}
│   ├── claude: {AI_ASSISTANT}, {AI_SHORTNAME}, {AI_COMMAND}
│   └── cursor: {AI_ASSISTANT}, {AI_SHORTNAME}, {AI_COMMAND}
└── GitLab Flow Configuration (new)
    ├── gitlab_flow_enabled: boolean flag
    ├── workflow_keywords: {GITLAB_FLOW_SETUP}, {GITLAB_FLOW_COMMIT}, {GITLAB_FLOW_PR}
    └── platform_commands: Windows PowerShell vs macOS/Linux bash
```

### Integration Strategy

**Extend existing keyword replacement system**:

1. **Add GitLab Flow config** to `ConfigCompatibilityLayer` class in config.py
2. **Extend `customize_template_content()`** function in utils.py to handle GitLab Flow keywords
3. **Modify main chatmode** to include GitLab Flow keywords at appropriate workflow points
4. **CLI flag controls** GitLab Flow keyword enablement during template installation
5. **Platform detection** determines command syntax (PowerShell vs bash)

**Integration Flow**:
```mermaid
flowchart TD
    A[User runs: improved-sdd init --gitlab-flow] --> B[CLI sets gitlab_flow_enabled=true]
    B --> C[Template installation begins]
    C --> D[customize_template_content() processes chatmode]
    D --> E{GitLab Flow enabled?}
    E -->|Yes| F[Replace keywords with git commands]
    E -->|No| G[Replace keywords with empty content]
    F --> H[Install chatmode with GitLab Flow]
    G --> I[Install standard chatmode]
    H --> J[User sees GitLab Flow steps in workflow]
    I --> K[User sees standard workflow only]
```

### Keyword Replacement System Extension

**Current System (AI Tools)**:
```python
# In customize_template_content()
for keyword, replacement in tool_config["keywords"].items():
    customized_content = customized_content.replace(keyword, replacement)
```

**Extended System (AI Tools + GitLab Flow)**:
```python
# Extended to handle GitLab Flow keywords
def customize_template_content(content: str, ai_tool: str, gitlab_flow_enabled: bool = False) -> str:
    # Existing AI tool keyword replacement
    if ai_tool in AI_TOOLS:
        for keyword, replacement in AI_TOOLS[ai_tool]["keywords"].items():
            content = content.replace(keyword, replacement)

    # New GitLab Flow keyword replacement
    if gitlab_flow_enabled:
        gitlab_flow_config = config.get_gitlab_flow_config()
        for keyword, replacement in gitlab_flow_config["keywords"].items():
            content = content.replace(keyword, replacement)
    else:
        # Replace GitLab Flow keywords with empty content
        for keyword in GITLAB_FLOW_KEYWORDS:
            content = content.replace(keyword, "")

    return content
```

## Components and Interfaces

### 1. GitLab Flow Configuration Extension (config.py)

Extend the `ConfigCompatibilityLayer` class to include GitLab Flow configuration using markdown file references:

```python
class ConfigCompatibilityLayer:
    def __init__(self):
        # ... existing configuration ...

        # GitLab Flow configuration
        self._gitlab_flow_config = {
            "enabled": False,  # Default disabled
            "template_files": {
                "setup": "gitlab-flow-setup.md",
                "commit": "gitlab-flow-commit.md",
                "pr": "gitlab-flow-pr.md",
            },
            "keywords": {
                "{GITLAB_FLOW_SETUP}": "{{LOAD_FILE:gitlab-flow-setup.md}}",
                "{GITLAB_FLOW_COMMIT}": "{{LOAD_FILE:gitlab-flow-commit.md}}",
                "{GITLAB_FLOW_PR}": "{{LOAD_FILE:gitlab-flow-pr.md}}",
                "{GITLAB_FLOW_BRANCH_NAME}": "feature/spec-{spec-name}",
            },
            "platform_commands": {
                "windows": {
                    "git_status": "git status",
                    "branch_create": "git checkout -b {branch_name}",
                    "commit": "git add . ; git commit -m \"{message}\"",
                    "push_pr": "git push -u origin {branch_name} ; gh pr create",
                },
                "unix": {
                    "git_status": "git status",
                    "branch_create": "git checkout -b {branch_name}",
                    "commit": "git add . && git commit -m \"{message}\"",
                    "push_pr": "git push -u origin {branch_name} && gh pr create",
                }
            }
        }

    def get_gitlab_flow_config(self, enabled: bool = False) -> Dict[str, Any]:
        """Get GitLab Flow configuration with conditional keyword content."""
        config = self._gitlab_flow_config.copy()
        config["enabled"] = enabled

        if not enabled:
            # Replace all keywords with empty content when disabled
            config["keywords"] = {k: "" for k in config["keywords"].keys()}

        return config

    def get_gitlab_flow_keywords(self, enabled: bool = False, platform: str = "windows", template_dir: str = "") -> Dict[str, str]:
        """Get GitLab Flow keywords with content loaded from markdown files."""
        if not enabled:
            return {k: "" for k in self._gitlab_flow_config["keywords"].keys()}

        # Load markdown content and replace platform-specific commands
        keywords = {}
        commands = self._gitlab_flow_config["platform_commands"].get(
            platform, self._gitlab_flow_config["platform_commands"]["windows"]
        )

        for keyword, file_reference in self._gitlab_flow_config["keywords"].items():
            if file_reference.startswith("{{LOAD_FILE:"):
                filename = file_reference.replace("{{LOAD_FILE:", "").replace("}}", "")
                file_path = os.path.join(template_dir, "gitlab-flow", filename)

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Replace platform-specific command placeholders
                    for cmd_key, cmd_value in commands.items():
                        content = content.replace(f"{{{cmd_key.upper()}}}", cmd_value)

                    keywords[keyword] = content
                except FileNotFoundError:
                    keywords[keyword] = f"<!-- GitLab Flow file not found: {filename} -->"
            else:
                keywords[keyword] = file_reference

        return keywords
```

### GitLab Flow Template Files Structure

Create separate markdown files for clean separation of content:

```
templates/
├── gitlab-flow/
│   ├── gitlab-flow-setup.md           # Setup instructions with placeholders
│   ├── gitlab-flow-commit.md          # Commit guidance with placeholders
│   └── gitlab-flow-pr.md              # PR creation with placeholders
└── chatmodes/
    └── sddSpecDriven.chatmode.md       # Main chatmode with keywords
```

#### `templates/gitlab-flow/gitlab-flow-setup.md`:
```markdown
## GitLab Flow Setup

Before starting the spec, create a feature branch:

```bash
# Check repository status
{GIT_STATUS}

# Create feature branch (replace {spec-name} with your feature name)
{BRANCH_CREATE}
```

**Branch Naming Convention**: `feature/spec-{kebab-case-name}`

**Examples**:
- "User Authentication" → `feature/spec-user-authentication`
- "Payment System" → `feature/spec-payment-system`
```

#### `templates/gitlab-flow/gitlab-flow-commit.md`:
```markdown
## Commit Phase Progress

After completing and approving this phase:

```bash
{COMMIT}
```

**Commit Message Format**:
- Feasibility: "Add feasibility assessment for {feature-name}"
- Requirements: "Add requirements for {feature-name}"
- Design: "Add design for {feature-name}"
- Tasks: "Add implementation tasks for {feature-name}"
```

#### `templates/gitlab-flow/gitlab-flow-pr.md`:
```markdown
## Create Pull Request

**CRITICAL**: Only create PR after ALL implementation tasks are completed!

```bash
{PUSH_PR}
```

**PR Guidelines**:
- Title: "Spec: {Feature Name}"
- Description: Brief summary of the spec and implementation
- Review: Ensure all tasks in tasks.md are completed ✅

**Manual PR Creation**:
1. Push branch: `git push -u origin feature/spec-{feature-name}`
2. Visit GitHub and create PR from feature branch to main
3. Fill in title and description following guidelines above
```

### 2. Template Customization Extension (utils.py)

Extend the `customize_template_content()` function to handle GitLab Flow keywords with markdown file loading:

```python
def customize_template_content(content: str, ai_tool: str, gitlab_flow_enabled: bool = False, platform: str = "windows", template_dir: str = "") -> str:
    """Customize template content for AI tool and optionally GitLab Flow.

    Args:
        content: Template content to customize
        ai_tool: AI tool key for customization
        gitlab_flow_enabled: Whether to enable GitLab Flow keywords
        platform: Target platform (windows/unix)
        template_dir: Base template directory path

    Returns:
        str: Customized template content with replaced keywords
    """
    customized_content = content

    # Existing AI tool keyword replacement
    if ai_tool in AI_TOOLS:
        tool_config = AI_TOOLS[ai_tool]
        for keyword, replacement in tool_config["keywords"].items():
            customized_content = customized_content.replace(keyword, replacement)

    # New GitLab Flow keyword replacement using markdown files
    gitlab_flow_keywords = config.get_gitlab_flow_keywords(gitlab_flow_enabled, platform, template_dir)
    for keyword, replacement in gitlab_flow_keywords.items():
        customized_content = customized_content.replace(keyword, replacement)

    return customized_content

def load_gitlab_flow_file(filename: str, template_dir: str, platform_commands: Dict[str, str]) -> str:
    """Load GitLab Flow markdown file and replace command placeholders.

    Args:
        filename: Name of the markdown file to load
        template_dir: Base template directory
        platform_commands: Platform-specific command replacements

    Returns:
        str: Processed markdown content with platform commands
    """
    file_path = os.path.join(template_dir, "gitlab-flow", filename)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Replace platform-specific command placeholders
        for cmd_key, cmd_value in platform_commands.items():
            placeholder = f"{{{cmd_key.upper()}}}"
            content = content.replace(placeholder, cmd_value)

        return content
    except FileNotFoundError:
        return f"<!-- GitLab Flow file not found: {filename} -->"
    except Exception as e:
        return f"<!-- Error loading GitLab Flow file {filename}: {str(e)} -->"
```

### 3. Main Chatmode Integration (sddSpecDriven.chatmode.md)

Modify the main chatmode file to include GitLab Flow keywords at strategic points:

```markdown
# Feature Spec Creation Workflow

## Overview

You are helping guide the user through the process of transforming a rough idea into a detailed design document...

{GITLAB_FLOW_SETUP}

### 0. Feasibility Assessment

Before diving into requirements, conduct a brief feasibility check...

**After completing feasibility assessment:**
{GITLAB_FLOW_COMMIT}

### 1. Requirement Gathering

First, generate an initial set of requirements...

**After user approves requirements:**
{GITLAB_FLOW_COMMIT}

### 2. Create Feature Design Document

After the user approves the Requirements...

**After user approves design:**
{GITLAB_FLOW_COMMIT}

### 3. Create Task List

After the user approves the Design...

**After user approves tasks:**
{GITLAB_FLOW_COMMIT}

## Implementation Complete

**After ALL implementation tasks are finished:**
{GITLAB_FLOW_PR}
```

### 3.1. Terminal-Based Commit Workflow Integration

The chatmode will include terminal-based git workflow guidance that provides users with appropriate git commands after each task completion:

**Chatmode Workflow Extensions**:

```markdown
## Task Execution Instructions

Follow these instructions for user requests related to spec tasks...

### Executing Instructions

- Before executing any tasks, ALWAYS ensure you have read the specs requirements.md, design.md and tasks.md files...
- Once you complete the requested task, ALWAYS mark the checkbox as complete in the tasks.md file
- **TERMINAL-BASED COMMIT WORKFLOW**:
  1. After marking task complete, ask user: "Would you like me to commit these changes to git?"
  2. If user confirms (yes/y/proceed), use terminal to execute git workflow:
     - Use `run_in_terminal` tool to execute `git add .` to stage changes
     - Generate conventional commit message: "feat: Complete [Task X.Y] - [task description]"
     - Use `run_in_terminal` tool to execute `git commit -m "[commit message]"`
     - Display commit result to user
  3. If GitLab Flow enabled, provide branch management guidance via terminal commands
  4. If commit fails, provide manual commit guidance with terminal troubleshooting
- Once you complete the requested task, stop and let the user review
```

**Commit Message Generation**:
- Use conventional commit format: `<type>: Complete [Task X.Y] - <description>`
- Task type mapping: implementation → `feat:`, tests → `test:`, docs → `docs:`, config → `chore:`
- Examples:
  - `feat: Complete [Task 1.1] - Add get_gitlab_flow_keywords method`
  - `docs: Complete [Task 2.3] - Update requirements documentation`
  - `test: Complete [Task 3.2] - Add GitLab Flow integration tests`

**Platform-Specific Terminal Commands**:
- Agent uses `run_in_terminal` tool with platform-appropriate command chaining
- **Windows PowerShell**: `git add . ; git commit -m "message"`
- **Unix/macOS**: `git add . && git commit -m "message"`

### 4. CLI Integration (init.py)

Extend the init command to handle GitLab Flow flag and template directory:

```python
def init_project(
    # ... existing parameters ...
    gitlab_flow: bool = typer.Option(False, "--gitlab-flow", help="Enable GitLab Flow workflow integration"),
):
    """Initialize project with optional GitLab Flow integration."""

    # ... existing initialization logic ...

    # Detect platform for GitLab Flow commands
    platform = "windows" if os.name == "nt" else "unix"

    # Get template directory path for GitLab Flow files
    template_base_dir = get_template_base_directory()  # Existing function

    # Customize templates with GitLab Flow if enabled
    for template_file in template_files:
        content = read_template_file(template_file)
        customized_content = customize_template_content(
            content,
            ai_tool,
            gitlab_flow_enabled=gitlab_flow,
            platform=platform,
            template_dir=template_base_dir
        )
        write_customized_template(customized_content, output_path)

    if gitlab_flow:
        # Verify GitLab Flow template files exist
        gitlab_flow_dir = os.path.join(template_base_dir, "gitlab-flow")
        if os.path.exists(gitlab_flow_dir):
            console.print("[green]✓[/green] GitLab Flow integration enabled")
            console.print("  Git workflow commands integrated into chatmode")
            console.print(f"  GitLab Flow templates loaded from: {gitlab_flow_dir}")
        else:
            console.print("[yellow]⚠[/yellow] GitLab Flow enabled but template files not found")
            console.print(f"  Expected directory: {gitlab_flow_dir}")
    else:
        console.print("[blue]ℹ[/blue] GitLab Flow disabled (use --gitlab-flow to enable)")

def get_template_base_directory() -> str:
    """Get the base template directory path."""
    # Use existing template resolution logic
    return resolve_template_directory()  # Existing function
```

### Benefits of Using Markdown Files as Variables

1. **Separation of Concerns**: Content separated from configuration logic
2. **Easy Editing**: GitLab Flow content can be edited without touching Python code
3. **Version Control**: Markdown files tracked separately, easier to review changes
4. **Reusability**: Same markdown files could be used for documentation generation
5. **Maintainability**: Content updates don't require code changes
6. **Localization**: Easy to add different language versions of workflow files
7. **Testing**: Can test content independently of keyword replacement logic

### File Organization Benefits

```
templates/
├── gitlab-flow/                    # GitLab Flow content directory
│   ├── gitlab-flow-setup.md       # Branch setup instructions
│   ├── gitlab-flow-commit.md      # Commit guidance
│   ├── gitlab-flow-pr.md          # PR creation instructions
│   └── README.md                  # Documentation for GitLab Flow templates
├── chatmodes/
│   └── sddSpecDriven.chatmode.md  # Main chatmode with {GITLAB_FLOW_*} keywords
└── instructions/
    └── sddPythonCliDev.instructions.md
```

This approach provides:
- **Clean architecture**: Content files separate from logic
- **Platform flexibility**: Command placeholders replaced per platform
- **Easy maintenance**: Update workflow instructions without touching code
- **Graceful degradation**: Missing files show helpful comments instead of errors

## Data Models

### Configuration Schema

```yaml
# .sdd/config.yml (or environment variables)
gitlab_flow:
  enabled: true
  branch_prefix: "feature/spec-"
  auto_commit: true
  auto_pr: false  # Ask user first
  pr_template: "templates/specs-pr-template.md"
```

### Branch Naming Convention

```
Pattern: feature/spec-{kebab-case-name}
Examples:
- "User Authentication" → "feature/spec-user-authentication"
- "Payment Processing System" → "feature/spec-payment-processing-system"
- "API Rate Limiting" → "feature/spec-api-rate-limiting"
```

### File Structure

```
templates/
├── chatmodes/
│   ├── sddSpecDriven.chatmode.md          # Main chatmode (minimal changes)
│   ├── workflows/
│   │   └── gitlab-flow-hooks.md           # Git workflow logic (~100 lines)
│   └── includes/
│       ├── pre-workflow-git-check.md      # Pre-workflow validation (~15 lines)
│       ├── post-phase-git-commit.md       # Post-phase commits (~10 lines)
│       └── post-workflow-pr-create.md     # PR creation prompt (~15 lines)
└── utils/
    └── git-utils.md                       # Helper functions (~50 lines)
```

### Commit Message Templates

```
Feasibility: "Add feasibility assessment for {feature-name}"
Requirements: "Add requirements for {feature-name}"
Design: "Add design for {feature-name}"
Tasks: "Add implementation tasks for {feature-name}"
```

## API Contract

## API Contract

### CLI Extension

**New Command Option**:
```bash
improved-sdd init [PROJECT_NAME] --gitlab-flow
```

**Behavior**:
- Installs templates with GitLab Flow keywords enabled
- Integrates automatic commit workflow into chatmode instructions
- Embeds GitLab Flow guidance at appropriate workflow points
- Platform-specific git commands based on detected OS

### Terminal-Based Git Workflow API

**Post-Task Completion Workflow**:

```markdown
1. Agent marks task complete in tasks.md file
2. Agent asks user: "Would you like me to commit these changes to git? (y/n)"
3. If user confirms, agent uses `run_in_terminal` tool to execute git commands:
   - Execute: `git add .` (stage all changes)
   - Generate conventional commit message based on task type and description
   - Execute: `git commit -m "[generated message]"`
   - Display terminal output to user
4. If GitLab Flow enabled, agent provides terminal commands for branch management
5. Agent stops and waits for user review before proceeding
```

**Commit Message Generation Guidelines**:
- Format: `<type>: Complete [Task X.Y] - <description>`
- Type mapping:
  - Implementation/feature tasks → `feat:`
  - Test-related tasks → `test:`
  - Documentation tasks → `docs:`
  - Configuration/setup tasks → `chore:`
  - Bug fixes → `fix:`
- Keep under 50 characters for git best practices
- Example: `feat: Complete [Task 6.1] - post-task commit prompt`

**Platform-Specific Terminal Execution**:
- Agent detects platform and uses appropriate command syntax via `run_in_terminal`
- **Windows**: Uses `;` separator: `git add . ; git commit -m "message"`
- **Unix/macOS**: Uses `&&` separator: `git add . && git commit -m "message"`
- All git operations executed through terminal tools, no scripted automation
        ]
        separator = " && "

    full_command = separator.join(commands)
    return execute_shell_command(full_command)
```

### File Installation Contract

#### Standard Installation (existing)
```
project/
├── .github/
│   ├── chatmodes/
│   │   └── sddSpecDriven.chatmode.md      # Unchanged
│   ├── instructions/
│   │   └── sddPythonCliDev.instructions.md
│   └── prompts/
│       └── sddProjectAnalysis.prompt.md
```

#### With --gitlab-flow flag
```
project/
├── .github/
│   ├── chatmodes/
│   │   └── sddSpecDriven.chatmode.md      # Enhanced with GitLab Flow keywords and auto-commit
│   ├── instructions/
│   │   ├── sddPythonCliDev.instructions.md
│   │   └── sddGitlabFlow.instructions.md   # New file with git workflow guidance
│   └── prompts/
│       └── sddProjectAnalysis.prompt.md
├── templates/
│   └── gitlab-flow/                        # GitLab Flow markdown templates
│       ├── gitlab-flow-setup.md
│       ├── gitlab-flow-commit.md
│       └── gitlab-flow-pr.md
```

### User Experience Contract

1. **Enhanced Workflow**: Main chatmode includes GitLab Flow guidance and automatic commit prompts
2. **User Confirmation**: Every commit requires explicit user confirmation
3. **Smart Commit Messages**: Automatically generated conventional commit messages
4. **Platform Awareness**: Git commands tailored to Windows PowerShell or Unix bash
5. **Error Handling**: Manual guidance provided when automatic commits fail
6. **Branch Management**: GitLab Flow branch guidance when enabled

## State Management

### No State Management Required

Option A uses **static files and user choice** - no state management needed:

```markdown
# No complex state tracking required
# User manually follows workflow steps when desired
# Git commands provide state through standard git operations

# State is tracked through:
# 1. Git branch names (feature/spec-{name})
# 2. Git commit history (phase completion tracking)
# 3. File system (specs directory structure)
# 4. GitHub/GitLab PR status (remote tracking)
```

### User-Driven Workflow Recovery

```markdown
# If user gets interrupted:
# 1. Check current branch: git branch --show-current
# 2. Check spec progress: ls specs/{feature-name}/
# 3. Review commit history: git log --oneline
# 4. Continue from last completed phase
```

## Error Handling

### User-Friendly Documentation

Since Option A provides **reference documentation** rather than automation:

```markdown
# Error handling through clear documentation

# Git setup issues → workflows/gitlab-flow-setup.md provides:
- Prerequisites checklist
- Common setup problems and solutions
- Alternative approaches for different environments

# Workflow confusion → workflows/gitlab-flow-overview.md provides:
- Simple step-by-step process
- Visual examples
- When to use each workflow file

# Command failures → Each workflow file includes:
- Troubleshooting sections
- Alternative commands for different platforms
- Manual fallback options
```

### Self-Service Support

```markdown
# User has full control and can:
# 1. Skip git operations entirely (normal spec workflow)
# 2. Use only parts of GitLab Flow (just branch creation)
# 3. Modify commands for their specific setup
# 4. Reference documentation when needed
# 5. Ignore GitLab Flow files completely if desired
```

## Performance Considerations

### Efficient Terminal Operations

- **Command Batching**: Group git commands where possible
  ```bash
  git add . && git commit -m "message"  # Single terminal call
  ```

- **Conditional Execution**: Skip unnecessary git checks
  ```markdown
  # Only check git status if not already validated in current session
  IF git_validated != true: run_in_terminal: git status
  ```

- **Async Operations**: Use background processes for non-blocking operations
  ```markdown
  # Push and PR creation in background while user continues
  run_in_terminal: git push -u origin {branch} --background
  ```

### Minimal Resource Usage

- **No Persistent State**: Rely on git's native state tracking
- **No Caching**: Use git commands directly for current state
- **Terminal Reuse**: Leverage existing `run_in_terminal` infrastructure

## Security Considerations

### Input Sanitization for Git Commands

```markdown
# Sanitize feature names for branch creation
feature_name = sanitize_for_git_branch(user_input)
# Remove special characters, spaces, etc.

# Validate branch names before use
IF branch_name matches /^[a-zA-Z0-9\-_\/]+$/: CONTINUE
ELSE: Display error and ask for valid name
```

### Safe Command Construction

```markdown
# Use git-safe branch names
branch_name = f"feature/spec-{kebab_case(feature_name)}"

# Validate paths before git operations
IF path.startswith('specs/') AND path.contains('../') == False: CONTINUE
ELSE: ABORT with security warning
```

### Credential Security

- **No Credential Handling**: Rely on user's existing git config
- **Use System Git**: Leverage user's configured authentication
- **GitHub CLI Integration**: Use `gh` for authenticated operations

## Testing Strategy

### ChatMode Workflow Testing

- **Manual Testing**: Test modified chatmode workflow with real git repositories
- **Command Validation**: Verify git commands work across platforms (Windows/Linux/macOS)
- **Error Simulation**: Test error scenarios by simulating git command failures

### Integration Testing

- **Real Repository Testing**: Test against actual git repositories with various states
- **GitHub CLI Testing**: Test PR creation with `gh` CLI
- **Cross-Platform Testing**: Validate on Windows PowerShell, Linux bash, macOS zsh

## Rollback Strategy

### Simple Git-Based Rollback

```markdown
# Automated rollback using git commands
IF workflow fails or user cancels:
  - run_in_terminal: git checkout {original_branch}
  - userInput: "Delete feature branch {feature_branch}? (y/N)"
  - IF yes: run_in_terminal: git branch -D {feature_branch}

# Manual rollback instructions
Display: "To manually clean up:
1. git checkout main
2. git branch -D feature/spec-{feature_name}
3. rm -rf specs/{feature_name}/"
```

## Feature Flags

### Simple Configuration Control

```yaml
# In chatmode configuration or environment variable
GITLAB_FLOW_ENABLED=true
AUTO_COMMIT_ENABLED=true
AUTO_PR_ENABLED=false
STRICT_BRANCH_VALIDATION=true
```

## Monitoring & Observability

### Basic Logging

```markdown
# Log git operations for troubleshooting
LOG: "Git operation: git {command}"
LOG: "Git result: exit_code={code}, output={output}"
LOG: "Workflow phase: {phase} completed for {feature_name}"

# Error tracking
LOG: "Git error: {error_message} in phase {phase}"
LOG: "User decision: {user_choice} for {prompt}"
```

## Missing Components

### Implementation Requirements for Option A

1. **New CLI Flag**: Add `--gitlab-flow` option to `init` command
2. **Workflow Template Files**: Create 4 workflow documentation files
3. **Instructions File**: Create comprehensive GitLab Flow instructions
4. **Template Installation Logic**: Extend template copying to include workflow files
5. **Documentation Updates**: Update CLI help and README

### No Complex Components Needed

- ❌ No template engine (Jinja2)
- ❌ No state management system
- ❌ No automated git operations
- ❌ No complex error handling
- ❌ No environment configuration
- ❌ No modifications to existing chatmode files

### Simple Implementation Approach

- ✅ Add CLI flag handling in existing `init` command
- ✅ Create static markdown workflow files
- ✅ Extend existing template installation system
- ✅ Use existing file copying infrastructure
- ✅ Leverage existing CLI option handling patterns

## Future Development Phases

### Phase 1: Core Documentation Delivery (Current Scope)
- Create GitLab Flow workflow documentation files
- Add CLI flag for optional installation
- Provide self-service git workflow guidance
- Zero changes to existing chatmode files

### Phase 2: Enhanced User Experience (Optional Future)
- Interactive tutorials within workflow files
- Platform-specific command variations (Windows/Linux/macOS)
- Integration examples with different Git hosting providers
- Video tutorials and visual guides

### Phase 3: Community Contributions (Long-term)
- User-contributed workflow variations
- Team-specific GitLab Flow adaptations
- Integration with other project management tools
- Advanced branching strategy documentation

### Phase 4: Potential Automation (Major Version)
- If user demand is high, consider automated git operations
- Template engine approach for dynamic content
- CLI automation options for power users
- Integration with CI/CD pipeline templates

**Current Focus**: Phase 1 only - simple, effective, non-breaking solution
