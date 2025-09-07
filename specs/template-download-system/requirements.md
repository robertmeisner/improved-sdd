# Requirements Document

## Introduction

The T2. WHEN no `.sdd_templates` folder exists in current directory THEN CLI SHALL check for bundled `.sdd_templates` in CLI installation
3. WHEN no bundled `.sdd_templates` exist THEN CLI SHALL attempt to download templates from GitHub repository `robertmeisner/improved-sdd` from the `/templates` folderplate Download System will transform the improved-sdd CLI from using bundled local templates to a dynamic hybrid system that prioritizes local `.sdd_templates` folders and falls back to downloading templates from GitHub. This enhances user experience by providing always-fresh templates while maintaining offline capability.

**Current Implementation Status**: PARTIALLY IMPLEMENTED - Template resolution infrastructure complete with TemplateResolver class, priority-based resolution, CLI integration, and bundled template rename. Ready for GitHub integration.

## Success Metrics

- **Template Freshness**: 100% of users without local templates get latest templates when online
- **Offline Reliability**: 100% success rate with local `.sdd_templates` folder
- **Performance**: Template resolution < 5 seconds (including download)
- **User Experience**: Clear progress indicators and fallback messaging
- **Cache Efficiency**: Zero persistent cache footprint after completion

## Out of Scope

- **Template Authoring Tools**: No GUI for creating templates
- **Multi-Repository Support**: Only `robertmeisner/improved-sdd` repository
- **Template Versioning UI**: No version selection interface
- **Authentication**: No GitHub authentication support in initial version
- **Offline Template Management**: No commands to pre-download templates

## Requirements

### Requirement 1: Local Template Priority [P0]

**User Story:** As a developer with custom templates, I want my local `.sdd_templates` folder to take precedence over downloaded templates, so that I can customize and override default templates without interference.

#### Acceptance Criteria

1. WHEN `.sdd_templates` folder exists in current directory THEN CLI SHALL use templates from that folder exclusively
2. WHEN `.sdd_templates` folder contains partial templates THEN CLI SHALL only use available templates from local folder
3. WHEN local template is corrupted or invalid THEN CLI SHALL display clear error message and NOT fallback to download
4. WHEN `.sdd_templates` folder exists THEN CLI SHALL NEVER modify, overwrite, or delete any files within it

#### Test Scenarios
- Scenario 1: `.sdd_templates` exists with complete template set - uses local only, never modifies folder
- Scenario 2: `.sdd_templates` exists with partial templates - uses only available local templates
- Scenario 3: Empty `.sdd_templates` folder - shows "no templates found" error
- Scenario 4: User has modified templates in `.sdd_templates` - CLI respects all modifications

**Implementation Status**: PARTIALLY IMPLEMENTED - TemplateResolver class checks for local .sdd_templates and respects user folders. GitHub integration and bundled template rename still needed.

### Requirement 2: GitHub Template Download [P0]

**User Story:** As a user without local templates, I want the CLI to automatically download the latest templates from GitHub, so that I always have access to current templates without manual updates.

#### Acceptance Criteria

1. WHEN no `.sdd_templates` folder exists in current directory THEN CLI SHALL check for bundled `.sdd_templates` in CLI installation
2. WHEN no bundled `.sdd_templates` exist THEN CLI SHALL attempt to download templates from GitHub
2. WHEN downloading templates THEN CLI SHALL show progress indicator with download status
3. WHEN download completes THEN CLI SHALL extract templates to temporary cache directory
4. WHEN templates are successfully cached THEN CLI SHALL proceed with normal template installation
5. WHEN `.sdd_templates` folder exists THEN CLI SHALL NEVER download or modify it, regardless of CLI flags

#### Test Scenarios
- Scenario 1: No local templates, bundled templates exist - uses bundled templates
- Scenario 2: No local or bundled templates, successful download - downloads and uses GitHub templates
- Scenario 3: Network available, GitHub API accessible - shows download progress
- Scenario 4: Large template download - displays progress percentage and speed

**Implementation Status**: NOT IMPLEMENTED - No GitHub integration exists

### Requirement 3: Cache Management [P1]

**User Story:** As a system administrator, I want template downloads to be cleaned up automatically, so that the CLI doesn't accumulate cache files over time.

#### Acceptance Criteria

1. WHEN templates are downloaded THEN CLI SHALL create temporary cache directory outside of current working directory and all parent directories
2. WHEN template installation completes successfully AND templates were downloaded THEN CLI SHALL delete cache directory
3. WHEN CLI exits unexpectedly THEN cache cleanup SHALL occur on next CLI invocation
4. IF cache cleanup fails THEN CLI SHALL log warning but continue operation
5. WHEN caching templates THEN CLI SHALL use system temporary directory (e.g., /tmp, %TEMP%) and NEVER use `.sdd_templates` as cache location

#### Test Scenarios
- Scenario 1: Normal completion - cache directory removed after installation
- Scenario 2: CLI interrupted - cache cleaned on next run
- Scenario 3: Cleanup permission error - logs warning, continues operation

**Implementation Status**: NOT IMPLEMENTED - No caching mechanism exists

### Requirement 4: Network Error Handling [P1]

**User Story:** As a user in a restricted network environment, I want clear error messages when templates cannot be downloaded, so that I understand how to resolve the issue.

#### Acceptance Criteria

1. WHEN network is unavailable THEN CLI SHALL display "offline mode" message with local template instructions
2. WHEN GitHub API is unreachable THEN CLI SHALL show specific GitHub connectivity error
3. WHEN download times out THEN CLI SHALL provide timeout error with retry suggestion
4. WHEN rate limit is exceeded THEN CLI SHALL show rate limit message with wait time
5. WHEN all template sources fail (local invalid, no bundled, download failed) THEN CLI SHALL display comprehensive error with manual template setup instructions

#### Test Scenarios
- Scenario 1: No internet connection - shows offline instructions
- Scenario 2: GitHub API down - shows GitHub-specific error
- Scenario 3: Rate limit hit - shows wait time and retry suggestion
- Scenario 4: All sources fail - shows manual setup instructions

**Implementation Status**: NOT IMPLEMENTED - No network error handling exists

### Requirement 5: Template Source Transparency [P2]

**User Story:** As a user, I want to know where my templates are coming from (local vs downloaded), so that I can understand the CLI's behavior and troubleshoot issues.

#### Acceptance Criteria

1. WHEN using local templates THEN CLI SHALL display "Using local templates from .sdd_templates"
2. WHEN downloading templates THEN CLI SHALL display "Downloading templates from GitHub"
3. WHEN templates are cached THEN CLI SHALL display cache location and size
4. WHEN in verbose mode THEN CLI SHALL show detailed template source information

#### Test Scenarios
- Scenario 1: Local templates detected - shows local source message
- Scenario 2: Download in progress - shows GitHub source message
- Scenario 3: Verbose mode - shows detailed source and cache information

**Implementation Status**: IMPLEMENTED - TemplateResolver provides template source transparency with Rich console output showing resolution source (local/bundled/github placeholder).

### Requirement 6: Folder Structure Migration [P0]

**User Story:** As a developer maintaining the CLI, I want to rename the bundled `templates/` folder to `.sdd_templates` for consistency with user local folders, while maintaining the GitHub source repository structure with templates in `/templates` folder.

#### Acceptance Criteria

1. WHEN CLI is updated THEN bundled templates folder SHALL be renamed from `templates/` to `.sdd_templates/`
2. WHEN CLI looks for bundled templates THEN it SHALL check `.sdd_templates/` directory relative to script location
3. WHEN downloading from GitHub THEN CLI SHALL download from `/templates` folder in `robertmeisner/improved-sdd` repository
4. WHEN bundled templates are missing THEN CLI SHALL proceed with GitHub download attempt from `/templates` source folder
5. WHEN both local and bundled `.sdd_templates` exist THEN local SHALL take priority

#### Test Scenarios
- Scenario 1: Update from old version - CLI finds new `.sdd_templates/` folder
- Scenario 2: Fresh installation - CLI uses bundled `.sdd_templates/`
- Scenario 3: Local `.sdd_templates` present - takes priority over bundled

**Implementation Status**: IMPLEMENTED - Bundled templates directory renamed from templates/ to .sdd_templates/ and CLI code updated. Template resolution correctly uses .sdd_templates for bundled templates.

### Requirement 7: Template Validation [P2]

**User Story:** As a user, I want the CLI to validate downloaded templates before using them, so that corrupted or incomplete downloads don't cause installation failures.

#### Acceptance Criteria

1. WHEN templates are downloaded THEN CLI SHALL verify ZIP file integrity
2. WHEN templates are extracted THEN CLI SHALL check for required template structure
3. WHEN validation fails THEN CLI SHALL retry download once before showing error
4. WHEN templates are missing required files THEN CLI SHALL show specific missing file errors

#### Test Scenarios
- Scenario 1: Corrupted download - retries once then shows error
- Scenario 2: Incomplete template structure - shows missing file details
- Scenario 3: Valid templates - proceeds with installation

**Implementation Status**: NOT IMPLEMENTED - No validation exists

### Requirement 8: Configuration Options [P3]

**User Story:** As a power user, I want CLI options to control template download behavior, so that I can optimize the CLI for my specific environment and needs.

#### Acceptance Criteria

1. WHEN `--offline` flag is used THEN CLI SHALL only use local templates and skip download attempts
2. WHEN `--force-download` flag is used THEN CLI SHALL download templates to cache and use cached templates instead of local templates for current session
3. WHEN `--template-repo` option is provided THEN CLI SHALL download from specified repository to cache only
4. WHEN `--no-cleanup` flag is used THEN CLI SHALL preserve cache directory for debugging
5. WHEN any CLI flag is used THEN CLI SHALL NEVER modify existing `.sdd_templates` folders under any circumstances

#### Test Scenarios
- Scenario 1: `--offline` flag - skips all download attempts
- Scenario 2: `--force-download` - downloads to cache and uses cached templates instead of local
- Scenario 3: Custom repository - downloads from specified repo

**Implementation Status**: NOT IMPLEMENTED - No template-related CLI options exist