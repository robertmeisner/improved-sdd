# Requirements Document: GitLab Flow Integration

## Introduction

The GitLab Flow Integration feature will enhance the sddSpecDriven workflow by providing **dynamic keyword integration** that embeds GitLab Flow commands and workflows directly into the main chatmode. This feature leverages the existing **keyword replacement system** in `src/core/config.py` to conditionally include GitLab Flow workflow steps in the core spec development process.

The integration uses **markdown files as variable values** approach, where GitLab Flow content is stored in separate markdown files in `templates/gitlab-flow/` directory with platform-specific placeholders. These markdown files are loaded dynamically by the keyword replacement system and embedded into the main chatmode during template installation.

**Current Implementation Status**: NOT IMPLEMENTED - New dynamic keyword feature using markdown files as variable values

## Success Metrics

- **Workflow Integration**: GitLab Flow steps seamlessly integrated into main chatmode workflow
- **Keyword Functionality**: 100% success rate for GitLab Flow keyword replacement during template installation
- **User Experience**: Users can enable/disable GitLab Flow with simple CLI flag without workflow disruption
- **Zero Breaking Changes**: Existing workflows continue unchanged when GitLab Flow not enabled
- **Dynamic Behavior**: GitLab Flow commands appear in workflow only when enabled

## Out of Scope

- **Automated Git Operations**: No automatic git command execution - keywords provide guidance only
- **Complex Branching Logic**: No advanced git flow patterns beyond basic GitLab Flow
- **Git State Management**: No git repository state validation or error handling
- **Multiple Git Workflows**: Only GitLab Flow support, no Git Flow or GitHub Flow variants
- **Git Authentication**: No git credential management or setup automation
- **Advanced Git Features**: No support for rebasing, cherry-picking, or complex merge strategies

## Requirements

### Requirement 1: GitLab Flow Configuration Extension [P0]

**User Story:** As a developer setting up a new project, I want GitLab Flow configuration integrated into the existing keyword system, so that I can enable GitLab Flow workflows through the same mechanism as AI tool configuration.

#### Acceptance Criteria

1. WHEN GitLab Flow config is added to `src/core/config.py` THEN it SHALL follow the same pattern as AI tool configuration
2. WHEN GitLab Flow is configured THEN it SHALL include `get_gitlab_flow_keywords()` method that loads content from markdown files
3. WHEN GitLab Flow keywords are generated THEN they SHALL load content from `templates/gitlab-flow/*.md` files
4. WHEN GitLab Flow config exists THEN it SHALL integrate with existing `customize_template_content()` function
5. WHEN GitLab Flow is disabled THEN keywords SHALL be replaced with empty strings

#### Test Scenarios
- Scenario 1: GitLab Flow config follows same structure as AI tool configs
- Scenario 2: Keywords are properly defined for all workflow steps
- Scenario 3: Platform-specific commands work correctly
- Scenario 4: Integration with existing keyword replacement system functions

**Implementation Status**: NOT IMPLEMENTED - GitLab Flow configuration needs to be added to config.py

### Requirement 2: Main Chatmode Integration [P0]

**User Story:** As a developer using the spec workflow, I want GitLab Flow steps integrated directly into the main chatmode, so that git workflow guidance appears naturally in the spec development process.

#### Acceptance Criteria

1. WHEN `sddSpecDriven.chatmode.md` is modified THEN it SHALL include GitLab Flow keywords at appropriate workflow points
2. WHEN GitLab Flow is enabled THEN keywords SHALL be replaced with git commands and guidance
3. WHEN GitLab Flow is disabled THEN keywords SHALL be replaced with empty content or neutral messages
4. WHEN workflow phases complete THEN GitLab Flow SHALL provide commit guidance
5. WHEN all phases are done THEN GitLab Flow SHALL provide PR creation guidance
6. **CRITICAL**: PR creation guidance SHALL only appear AFTER all implementation tasks are completed

#### Test Scenarios
- Scenario 1: GitLab Flow steps appear at correct points in spec workflow
- Scenario 2: Keywords are replaced appropriately based on enabled/disabled state
- Scenario 3: Workflow remains functional when GitLab Flow disabled
- Scenario 4: PR timing guidance prevents premature PR creation

**Implementation Status**: NOT IMPLEMENTED - Main chatmode file needs GitLab Flow keyword integration

### Requirement 3: CLI Flag Integration [P0]

**User Story:** As a developer initializing a project, I want to enable GitLab Flow through a CLI flag, so that the keyword replacement system includes GitLab Flow configuration during template installation.

#### Acceptance Criteria

1. WHEN `--gitlab-flow` flag is used with init command THEN GitLab Flow keywords SHALL be enabled for replacement
2. WHEN flag is not used THEN GitLab Flow keywords SHALL be disabled (replaced with empty content)
3. WHEN flag is used THEN CLI SHALL display confirmation of GitLab Flow enablement
4. WHEN templates are installed THEN GitLab Flow keyword replacement SHALL occur automatically
5. WHEN GitLab Flow is enabled THEN all necessary workflow guidance SHALL appear in chatmode

#### Test Scenarios
- Scenario 1: `init --gitlab-flow` enables GitLab Flow keyword replacement
- Scenario 2: `init` without flag disables GitLab Flow (empty replacements)
- Scenario 3: Template installation correctly handles GitLab Flow state
- Scenario 4: User feedback confirms GitLab Flow enablement status

**Implementation Status**: NOT IMPLEMENTED - CLI flag handling for GitLab Flow keyword state needed

### Requirement 4: Dynamic Workflow Keywords [P1]

**User Story:** As a developer following the spec workflow, I want dynamic GitLab Flow guidance that appears contextually in the workflow, so that I receive git commands and instructions at the right moments.

#### Acceptance Criteria

1. WHEN feasibility phase begins THEN `{GITLAB_FLOW_SETUP}` keyword SHALL load content from `gitlab-flow-setup.md` file
2. WHEN each phase completes THEN `{GITLAB_FLOW_COMMIT}` keyword SHALL load content from `gitlab-flow-commit.md` file
3. WHEN all phases complete THEN `{GITLAB_FLOW_PR}` keyword SHALL load content from `gitlab-flow-pr.md` file
4. WHEN GitLab Flow disabled THEN all keywords SHALL resolve to empty strings
5. WHEN markdown files are loaded THEN platform-specific placeholders like `{GIT_STATUS}`, `{BRANCH_CREATE}` SHALL be replaced with appropriate commands

#### Test Scenarios
- Scenario 1: Setup guidance appears before spec work begins
- Scenario 2: Commit guidance appears after each phase approval
- Scenario 3: PR guidance appears only after all implementation complete
- Scenario 4: Platform-specific commands work correctly

**Implementation Status**: NOT IMPLEMENTED - Dynamic workflow keywords need to be defined and implemented

### Requirement 5: Keyword Replacement System Extension [P1]

**User Story:** As a developer using the template system, I want GitLab Flow keywords to integrate seamlessly with the existing AI tool keyword replacement, so that I can use GitLab Flow alongside any AI tool configuration.

#### Acceptance Criteria

1. WHEN `customize_template_content()` processes templates THEN it SHALL handle GitLab Flow keywords by loading markdown files
2. WHEN both AI tool and GitLab Flow keywords exist THEN both SHALL be replaced correctly
3. WHEN GitLab Flow keywords are processed THEN existing AI tool functionality SHALL remain unchanged
4. WHEN markdown files are loaded THEN `load_gitlab_flow_file()` function SHALL handle platform-specific placeholder replacement
5. WHEN markdown files are missing THEN graceful fallback to empty content SHALL occur

#### Test Scenarios
- Scenario 1: GitLab Flow keywords integrate with existing keyword system
- Scenario 2: Multiple keyword types (AI + GitLab Flow) work together
- Scenario 3: No interference with existing AI tool keyword functionality
- Scenario 4: Conditional replacement based on GitLab Flow enablement

**Implementation Status**: NOT IMPLEMENTED - Extension of existing keyword replacement system needed

### Requirement 6: Platform-Specific Command Generation [P2]

**User Story:** As a developer on any platform (Windows/macOS/Linux), I want GitLab Flow commands tailored to my platform, so that I can copy and execute commands without modification.

#### Acceptance Criteria

1. WHEN platform is Windows THEN git commands SHALL use PowerShell syntax
2. WHEN platform is macOS/Linux THEN git commands SHALL use bash syntax
3. WHEN commands are generated THEN they SHALL include proper path separators for platform
4. WHEN branch names are generated THEN they SHALL be valid for all platforms
5. WHEN command chaining is used THEN platform-appropriate operators SHALL be used

#### Test Scenarios
- Scenario 1: Windows PowerShell commands work correctly
- Scenario 2: macOS/Linux bash commands work correctly
- Scenario 3: Path separators are platform-appropriate
- Scenario 4: Command chaining uses correct operators

**Implementation Status**: NOT IMPLEMENTED - Platform-specific command generation logic needed

### Requirement 7: GitLab Flow Markdown File Library [P2]

**User Story:** As a developer extending the system, I want a complete library of GitLab Flow markdown files, so that I can understand and maintain the GitLab Flow integration.

#### Acceptance Criteria

1. WHEN GitLab Flow markdown files are created THEN they SHALL cover all essential workflow steps in `templates/gitlab-flow/` directory
2. WHEN markdown files are created THEN they SHALL include platform-specific placeholders like `{GIT_STATUS}`, `{BRANCH_CREATE}`, `{COMMIT_CMD}`
3. WHEN new workflow steps are needed THEN new markdown files SHALL be easily added to the library
4. WHEN markdown files are used THEN they SHALL follow consistent naming conventions (gitlab-flow-*.md)
5. WHEN placeholders are replaced THEN content SHALL be informative and actionable for the target platform

#### Test Scenarios
- Scenario 1: All essential GitLab Flow steps have corresponding keywords
- Scenario 2: Keywords follow consistent naming patterns
- Scenario 3: Keyword content is actionable and clear
- Scenario 4: Keyword library is maintainable and extensible

**Implementation Status**: NOT IMPLEMENTED - Complete GitLab Flow keyword library needs definition

### Requirement 8: Terminal-Based Commit Workflow [P0]

**User Story:** As a developer following the spec workflow, I want the chatmode/agent to use terminal commands to commit changes after each task completion with my confirmation, so that my progress is properly tracked in git using terminal tools and follows GitLab Flow practices.

#### Acceptance Criteria

1. WHEN a task is completed THEN the chatmode SHALL prompt user for commit confirmation
2. WHEN user confirms commit THEN the agent SHALL use `run_in_terminal` tool to execute git add and commit commands
3. WHEN committing changes THEN commit messages SHALL follow conventional commit format with task reference
4. WHEN GitLab Flow is enabled THEN commit workflow SHALL include terminal-based branch management guidance
5. WHEN GitLab Flow is disabled THEN basic git commit SHALL still occur via terminal with user confirmation
6. WHEN commit fails THEN user SHALL receive terminal output and manual commit guidance

#### Test Scenarios
- Scenario 1: Task completion triggers commit confirmation prompt
- Scenario 2: User confirmation leads to terminal-executed git commit via `run_in_terminal`
- Scenario 3: Commit messages include task reference and follow conventional commit format
- Scenario 4: Terminal-based branch management guidance appears when GitLab Flow enabled
- Scenario 5: Error handling for failed commits shows terminal output and manual guidance

**Implementation Status**: PARTIALLY IMPLEMENTED - Terminal-based commit workflow needs integration in chatmode

### Requirement 10: Configuration System Improvements [P2]

**User Story:** As a developer maintaining the GitLab Flow integration, I want improved configuration system architecture, so that the codebase is more maintainable and consistent.

#### Acceptance Criteria

1. WHEN GitLab Flow default state is configured THEN it SHALL be consistent between config.py and CLI default values
2. WHEN template paths are constructed THEN they SHALL use configurable template directory instead of hardcoded paths
3. WHEN platform detection is needed THEN it SHALL use a reusable helper method
4. WHEN GitLab Flow config is exported THEN it SHALL be included in legacy exports for consistency
5. WHEN template validation is needed THEN validation methods SHALL be available

#### Test Scenarios
- Scenario 1: Default GitLab Flow state is consistent across config and CLI
- Scenario 2: Template paths use configurable directories
- Scenario 3: Platform detection helper method is reusable
- Scenario 4: GitLab Flow config is properly exported
- Scenario 5: Template validation methods work correctly

**Implementation Status**: IDENTIFIED - Configuration improvements needed for maintainability

### Requirement 11: Enhanced Error Handling and Validation [P2]

**User Story:** As a developer using GitLab Flow integration, I want robust error handling and validation, so that I receive clear feedback when configuration issues occur.

#### Acceptance Criteria

1. WHEN GitLab Flow templates are missing THEN validation methods SHALL detect and report missing files
2. WHEN template files are invalid THEN graceful error handling SHALL provide helpful messages
3. WHEN platform detection fails THEN fallback mechanisms SHALL provide default behavior
4. WHEN template loading fails THEN caching mechanisms SHALL prevent repeated failures
5. WHEN configuration is invalid THEN validation SHALL prevent runtime errors

#### Test Scenarios
- Scenario 1: Missing template file validation works correctly
- Scenario 2: Invalid template file error handling is graceful
- Scenario 3: Platform detection failures have fallbacks
- Scenario 4: Template loading failures are cached to prevent retries
- Scenario 5: Configuration validation prevents runtime errors

**Implementation Status**: IDENTIFIED - Enhanced error handling and validation needed

### Requirement 12: Platform Keywords Consistency [P2]

**User Story:** As a developer maintaining the GitLab Flow configuration, I want consistent keyword naming conventions across all platform-specific commands, so that the configuration is easier to understand and maintain.

#### Acceptance Criteria

1. WHEN platform-specific commands are defined THEN they SHALL use consistent bracket notation with other keywords
2. WHEN platform keywords are referenced THEN the naming SHALL be consistent (platform_keywords vs platform_commands)
3. WHEN new platform commands are added THEN they SHALL follow the established keyword pattern
4. WHEN platform commands are processed THEN the replacement logic SHALL handle consistent keyword format
5. WHEN platform keywords are validated THEN validation SHALL work with consistent naming

#### Test Scenarios
- Scenario 1: Platform commands use {GIT_STATUS} format instead of "GIT_STATUS"
- Scenario 2: Configuration section renamed to platform_keywords for clarity
- Scenario 3: Keyword replacement works with consistent bracket notation
- Scenario 4: New platform commands follow established pattern
- Scenario 5: Validation works with consistent keyword format

**Implementation Status**: IDENTIFIED - Platform keyword consistency improvements needed

### Requirement 13: GitLab Flow Template Optimization [P2]

**User Story:** As a developer using GitLab Flow integration, I want optimized template organization that avoids duplication, so that the chatmode is cleaner and more maintainable.

#### Acceptance Criteria

1. WHEN GitLab Flow commit guidance is needed THEN it SHALL be provided in a single dedicated section
2. WHEN chatmode templates are organized THEN GitLab Flow content SHALL be consolidated to avoid repetition
3. WHEN commit workflow is triggered THEN users SHALL be directed to the dedicated GitLab Flow section
4. WHEN GitLab Flow is disabled THEN the dedicated section SHALL be cleanly removed
5. WHEN template maintenance is needed THEN changes SHALL be made in one location only

#### Test Scenarios
- Scenario 1: Single GitLab Flow section provides all commit guidance
- Scenario 2: No duplication of gitlab-flow-commit.md content
- Scenario 3: Clean template organization with dedicated sections
- Scenario 4: Easy maintenance with single source of truth
- Scenario 5: Proper section removal when GitLab Flow disabled

**Implementation Status**: IDENTIFIED - Template organization optimization needed

### Requirement 9: Backward Compatibility [P1]

**User Story:** As a developer with existing projects, I want GitLab Flow integration to be completely backward compatible, so that my existing workflows continue unchanged when I don't use GitLab Flow.

#### Acceptance Criteria

1. WHEN GitLab Flow is not enabled THEN existing workflows SHALL function identically
2. WHEN templates are installed without `--gitlab-flow` THEN no GitLab Flow content SHALL appear
3. WHEN existing projects are updated THEN GitLab Flow SHALL be opt-in only
4. WHEN AI tool keywords are used THEN they SHALL work exactly as before
5. WHEN configuration is accessed THEN existing AI tools SHALL be unaffected

#### Test Scenarios
- Scenario 1: Existing workflows unchanged when GitLab Flow disabled
- Scenario 2: No GitLab Flow content without explicit enablement
- Scenario 3: AI tool functionality remains identical
- Scenario 4: Configuration access patterns unchanged

**Implementation Status**: NOT IMPLEMENTED - Backward compatibility validation needed
