# CLI Decomposition Design Document

## Overview

This document outlines the architectural design for decomposing the monolithic `improved_sdd_cli.py` file into a modular, maintainable structure. The design follows a layered architecture with clear separation of concerns while preserving all existing functionality.

**Current Implementation Status**: NOT IMPLEMENTED - Design represents target architecture

## Architecture

### Architectural Principles

1. **Single Responsibility### Testing Strategy

### Baseline Testing Infrastructure
```python
# tools/baseline_testing.py
class BaselineTestSuite:
    """Captures behavioral snapshots for migration safety"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.snapshots: Dict[str, Any] = {}

    def capture_cli_behavior(self) -> None:
        """Capture complete CLI behavior before migration"""
        test_cases = [
            ["--help"],
            ["init", "--help"],
            ["delete", "--help"],
            ["check"],
            # Add comprehensive test scenarios
        ]

        for case in test_cases:
            result = self._run_cli_command(case)
            self.snapshots["_".join(case)] = {
                "command": case,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "execution_time_ms": result.execution_time
            }

        # Save snapshots
        with open(self.output_dir / "behavioral_baseline.json", "w") as f:
            json.dump(self.snapshots, f, indent=2)

    def compare_behavior(self, new_snapshots: Dict) -> ComparisonReport:
        """Compare current behavior against baseline"""
        differences = []

        for test_case, baseline in self.snapshots.items():
            if test_case not in new_snapshots:
                differences.append(f"Missing test case: {test_case}")
                continue

            current = new_snapshots[test_case]

            # Compare key behavioral aspects
            if baseline["exit_code"] != current["exit_code"]:
                differences.append(f"{test_case}: exit code changed")

            if not self._output_functionally_equivalent(baseline["stdout"], current["stdout"]):
                differences.append(f"{test_case}: output changed")

        return ComparisonReport(differences=differences, passed=len(differences) == 0)
```

### Unit Testinginciple**: Each module handles one specific concern
2. **Dependency Inversion**: High-level modules don't depend on low-level modules
3. **Interface Segregation**: Modules expose only the interfaces they need
4. **Open/Closed Principle**: Easy to extend without modifying existing code
5. **Minimal Coupling**: Modules interact through well-defined interfaces

### Layer Structure

```
┌─────────────────────────────────────┐
│           CLI Layer                 │
│  (commands/, improved_sdd_cli.py)   │
├─────────────────────────────────────┤
│           UI Layer                  │
│     (ui/console.py, progress.py)    │
├─────────────────────────────────────┤
│         Service Layer               │
│  (services/*, template operations)  │
├─────────────────────────────────────┤
│          Core Layer                 │
│   (core/*, models, exceptions)      │
└─────────────────────────────────────┘
```

## Components and Interfaces

### Core Layer (`src/core/`)

#### `core/config.py`
**Purpose**: Centralized configuration management with migration compatibility
```python
from typing import Dict, List
from dataclasses import dataclass

# Configuration classes
@dataclass
class AIToolConfig:
    name: str
    description: str
    template_dir: str
    file_extensions: Dict[str, str]
    keywords: Dict[str, str]

@dataclass
class AppTypeConfig:
    description: str
    instruction_files: List[str]

class ConfigCompatibilityLayer:
    """Provides backward-compatible access during migration"""

    def __init__(self):
        self._ai_tools = self._load_ai_tools()
        self._app_types = self._load_app_types()

    @property
    def AI_TOOLS(self) -> Dict:
        """Legacy format for backward compatibility"""
        return self._ai_tools

    @property
    def APP_TYPES(self) -> Dict:
        """Legacy format for backward compatibility"""
        return self._app_types

    def get_ai_tool_config(self, tool: str) -> AIToolConfig:
        """New interface for new code"""
        return AIToolConfig(**self.AI_TOOLS[tool])

    def get_app_type_config(self, app_type: str) -> AppTypeConfig:
        """New interface for new code"""
        return AppTypeConfig(**self.APP_TYPES[app_type])

    def validate_config(self) -> List[str]:
        """Validate configuration and return any issues"""
        issues = []
        for tool_id, config in self.AI_TOOLS.items():
            if not isinstance(config.get('name'), str):
                issues.append(f"AI tool {tool_id} missing valid name")
        return issues

# Global configuration instance
config = ConfigCompatibilityLayer()

# Legacy exports for backward compatibility
AI_TOOLS = config.AI_TOOLS
APP_TYPES = config.APP_TYPES
BANNER: str = "..."
TAGLINE: str = "..."
```

#### `core/exceptions.py`
**Purpose**: Centralized exception hierarchy with context preservation
```python
from typing import Optional, Dict, Any

class TemplateError(Exception):
    """Base exception for template operations with rich context"""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.context = context or {}
        self.operation = self.context.get('operation', 'unknown')
        self.file_path = self.context.get('file_path')
        self.timestamp = self.context.get('timestamp', time.time())

class NetworkError(TemplateError):
    """Network-related template errors"""
    pass

class GitHubAPIError(TemplateError):
    """GitHub API specific errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, context: Optional[Dict] = None):
        super().__init__(message, context)
        self.status_code = status_code

class RateLimitError(GitHubAPIError):
    """GitHub API rate limit errors"""
    def __init__(self, retry_after: Optional[int] = None, context: Optional[Dict] = None):
        super().__init__("GitHub API rate limit exceeded", context=context)
        self.retry_after = retry_after

class TimeoutError(NetworkError): ...
class ValidationError(TemplateError): ...
```

#### `core/interfaces.py`
**Purpose**: Service protocol definitions for dependency injection
```python
from typing import Protocol, Optional
from pathlib import Path

class FileTrackerProtocol(Protocol):
    def track_file_creation(self, filepath: Path) -> None: ...
    def track_file_modification(self, filepath: Path) -> None: ...
    def track_dir_creation(self, dirpath: Path) -> None: ...
    def get_summary(self) -> str: ...

class TemplateResolverProtocol(Protocol):
    def resolve_templates_with_transparency(self) -> TemplateResolutionResult: ...
    def get_local_templates_path(self) -> Optional[Path]: ...

class ConsoleProtocol(Protocol):
    def print_success(self, message: str) -> None: ...
    def print_error(self, message: str) -> None: ...
    def show_panel(self, content: str, title: str, style: str = "cyan") -> None: ...
```

#### `core/container.py`
**Purpose**: Dependency injection container for service management
```python
class ServiceContainer:
    """Dependency injection container for CLI services"""

    def __init__(self):
        self._services = {}
        self._configure_services()

    def get_file_tracker(self) -> FileTrackerProtocol:
        return self._services['file_tracker']

    def get_template_resolver(self, **kwargs) -> TemplateResolverProtocol:
        return self._create_template_resolver(**kwargs)

    def get_console_manager(self) -> ConsoleProtocol:
        return self._services['console_manager']

    def _configure_services(self) -> None:
        # Lazy initialization of services
        pass
```

#### `core/models.py`
**Purpose**: Data models and enums
```python
class TemplateSourceType(Enum): ...
@dataclass
class ProgressInfo: ...
@dataclass
class TemplateSource: ...
@dataclass
class TemplateResolutionResult: ...
```

### Service Layer (`src/services/`)

#### `services/file_tracker.py`
**Purpose**: Track file creation and modification during installation
```python
class FileTracker:
    def track_file_creation(self, filepath: Path) -> None
    def track_file_modification(self, filepath: Path) -> None
    def track_dir_creation(self, dirpath: Path) -> None
    def get_summary(self) -> str
```

#### `services/cache_manager.py`
**Purpose**: Manage temporary cache directories
```python
class CacheManager:
    def create_cache_dir(self) -> Path
    def cleanup_cache(self, cache_dir: Path) -> None
    def cleanup_all_caches(self) -> None
    def cleanup_orphaned_caches(self) -> int
    def get_cache_info(self, cache_dir: Path) -> dict
```

#### `services/github_downloader.py`
**Purpose**: Handle GitHub template downloads
```python
class GitHubDownloader:
    async def download_templates(
        self,
        target_dir: Path,
        progress_callback: Optional[Callable[[ProgressInfo], None]] = None
    ) -> TemplateSource

    def extract_templates(
        self,
        zip_path: Path,
        target_dir: Path,
        progress_callback: Optional[Callable[[ProgressInfo], None]] = None
    ) -> None
```

#### `services/template_resolver.py`
**Purpose**: Resolve template sources with priority system
```python
class TemplateResolver:
    def resolve_templates_source(self) -> Optional[Path]
    def resolve_templates_with_transparency(self) -> TemplateResolutionResult
    def get_local_templates_path(self) -> Optional[Path]
    def get_bundled_templates_path(self) -> Optional[Path]
    def has_local_templates(self) -> bool
    def has_bundled_templates(self) -> bool
```

### UI Layer (`src/ui/`)

#### `ui/console.py`
**Purpose**: Centralized console operations
```python
class ConsoleManager:
    def __init__(self):
        self.console = Console()

    def print_success(self, message: str) -> None
    def print_error(self, message: str) -> None
    def print_warning(self, message: str) -> None
    def print_info(self, message: str) -> None
    def show_panel(self, content: str, title: str, style: str = "cyan") -> None
    def show_banner(self) -> None

# Global instance
console_manager = ConsoleManager()
```

#### `ui/progress.py`
**Purpose**: Progress tracking utilities
```python
class ProgressTracker:
    def create_download_progress(self) -> Progress
    def create_extraction_progress(self) -> Progress
    def update_progress(self, progress: Progress, task_id: int, info: ProgressInfo) -> None
```

### Command Layer (`src/commands/`)

#### `commands/init.py`
**Purpose**: Initialize project with templates
```python
def init_command(
    project_name: str,
    app_type: str,
    ai_tools: str,
    ignore_agent_tools: bool,
    here: bool,
    force: bool,
    offline: bool,
    force_download: bool,
    template_repo: str
) -> None
```

#### `commands/delete.py`
**Purpose**: Delete installed templates
```python
def delete_command(
    app_type: str,
    force: bool
) -> None
```

#### `commands/check.py`
**Purpose**: Check system requirements
```python
def check_command() -> None
```

### Main Entry Point (`src/improved_sdd_cli.py`)

**Purpose**: CLI application setup and command routing
- Typer app configuration
- Command registration
- Global exception handling
- Shared utilities (tool checking, user prompts)

## Data Models

### Configuration Models
```python
@dataclass
class AIToolConfig:
    name: str
    description: str
    template_dir: str
    file_extensions: Dict[str, str]
    keywords: Dict[str, str]

@dataclass
class AppTypeConfig:
    description: str
    instruction_files: List[str]
```

### Template Models
```python
@dataclass
class ProgressInfo:
    phase: str
    bytes_completed: int
    bytes_total: int
    percentage: float
    speed_bps: Optional[int] = None
    eta_seconds: Optional[int] = None

@dataclass
class TemplateSource:
    path: Path
    source_type: TemplateSourceType
    size_bytes: Optional[int] = None

@dataclass
class TemplateResolutionResult:
    source: Optional[TemplateSource]
    success: bool
    message: str
    fallback_attempted: bool = False
```

## API Contract

### Service Dependencies
```python
# Dependency injection pattern
class InitCommandHandler:
    def __init__(
        self,
        template_resolver: TemplateResolver,
        file_tracker: FileTracker,
        console_manager: ConsoleManager,
        progress_tracker: ProgressTracker
    ):
        self.template_resolver = template_resolver
        self.file_tracker = file_tracker
        self.console_manager = console_manager
        self.progress_tracker = progress_tracker
```

### Interface Contracts
```python
# Template resolution interface
Protocol TemplateResolverProtocol:
    def resolve_templates_with_transparency(self) -> TemplateResolutionResult

# Console interface
Protocol ConsoleProtocol:
    def print_success(self, message: str) -> None
    def print_error(self, message: str) -> None
    def show_panel(self, content: str, title: str, style: str) -> None

# File tracking interface
Protocol FileTrackerProtocol:
    def track_file_creation(self, filepath: Path) -> None
    def get_summary(self) -> str
```

## State Management

### Module State Isolation
- **No shared mutable state** between modules
- **Immutable configuration** loaded once at startup
- **Service instances** passed via dependency injection
- **Stateless functions** where possible

### Lifecycle Management
```python
# Application lifecycle
def main():
    # 1. Load configuration
    config = load_config()

    # 2. Initialize services
    cache_manager = CacheManager()
    console_manager = ConsoleManager()

    # 3. Register cleanup handlers
    atexit.register(cache_manager.cleanup_all_caches)

    # 4. Start CLI app
    app()
```

## Error Handling

### Exception Hierarchy
```
Exception
└── TemplateError (base for all template operations)
    ├── NetworkError (network-related failures)
    │   ├── TimeoutError (request timeouts)
    │   └── GitHubAPIError (API failures)
    │       └── RateLimitError (rate limiting)
    └── ValidationError (data validation failures)
```

### Error Propagation Strategy
1. **Service Layer**: Raises specific exceptions with context
2. **Command Layer**: Catches service exceptions, logs details, converts to user-friendly messages
3. **CLI Layer**: Handles command exceptions, shows error UI, returns appropriate exit codes

### Error Context Preservation
```python
try:
    result = template_resolver.resolve_templates_with_transparency()
except GitHubAPIError as e:
    console_manager.print_error(f"GitHub API error: {e}")
    if e.status_code == 403:
        console_manager.print_info("Rate limit may be exceeded. Try --offline mode.")
    raise typer.Exit(1)
```

## Performance Considerations

### Import Optimization
- **Lazy imports** for heavy dependencies (httpx, zipfile)
- **Module-level imports** only for frequently used items
- **Function-level imports** for optional dependencies

### Memory Management
- **Streaming downloads** for large files
- **Temporary file cleanup** via context managers
- **Cache size limits** to prevent disk usage growth

### Startup Performance
```python
# Lazy import example
def download_templates(self, ...):
    import httpx  # Only import when needed
    ...

# Conditional imports
if sys.platform == "win32":
    import winreg
```

## Security Considerations

### Input Validation
- **Path traversal prevention** in template extraction
- **GitHub URL validation** for custom repositories
- **Command argument sanitization**

### File System Security
- **Safe temporary directory creation** outside project paths
- **Permission checks** before file operations
- **Atomic file operations** to prevent corruption

### Network Security
- **HTTPS-only downloads**
- **Certificate validation**
- **Timeout limits** on network requests
- **Rate limiting respect** for GitHub API

## Testing Strategy

### Unit Testing
```python
# Service layer tests
def test_file_tracker_creation():
    tracker = FileTracker()
    tracker.track_file_creation(Path("test.txt"))
    assert "test.txt" in tracker.get_summary()

# Mock external dependencies
@patch('httpx.AsyncClient')
def test_github_downloader(mock_client):
    downloader = GitHubDownloader()
    # Test with mocked HTTP responses
```

### Integration Testing
```python
# Command integration tests
def test_init_command_with_real_templates():
    # Test with actual template files
    result = runner.invoke(app, ["init", "test-project"])
    assert result.exit_code == 0
```

### Performance Testing
- **Startup time benchmarks**
- **Memory usage profiling**
- **Download speed validation**

## Rollback Strategy

### Phase-by-Phase Migration
1. **Phase 1**: Extract core models and exceptions
2. **Phase 2**: Extract service classes
3. **Phase 3**: Extract UI utilities
4. **Phase 4**: Extract command handlers
5. **Phase 5**: Clean up main file

### Rollback Points
- **After each phase**: All tests pass, functionality preserved
- **Git commits**: Each phase gets dedicated commit
- **Backup strategy**: Original file preserved until completion

### Validation at Each Step
```python
# Integration test suite runs after each extraction
def test_cli_behavior_unchanged():
    # Compare outputs before and after refactoring
    assert new_cli_output == original_cli_output
```

## Feature Flags

### Migration Control
```python
# Feature flags for gradual rollout
USE_MODULAR_SERVICES = os.getenv("SDD_USE_MODULAR", "true").lower() == "true"

if USE_MODULAR_SERVICES:
    from .services.template_resolver import TemplateResolver
else:
    # Legacy implementation
```

### Debugging Support
```python
DEBUG_IMPORTS = os.getenv("SDD_DEBUG_IMPORTS", "false").lower() == "true"

if DEBUG_IMPORTS:
    console.print(f"[dim]Loading module: {__name__}[/dim]")
```

## Monitoring & Observability

### Performance Monitoring
```python
# tools/performance_monitor.py
@dataclass
class PerformanceMetrics:
    startup_time_ms: float
    memory_usage_mb: float
    command_execution_time_ms: Dict[str, float]
    import_time_ms: Dict[str, float]

class PerformanceMonitor:
    def __init__(self):
        self.baseline: Optional[PerformanceMetrics] = None

    def establish_baseline(self) -> PerformanceMetrics:
        """Measure current performance before migration"""
        metrics = self._measure_performance()
        self.baseline = metrics
        return metrics

    def measure_current_performance(self) -> PerformanceMetrics:
        """Measure performance during/after migration"""
        return self._measure_performance()

    def compare_performance(self, current: PerformanceMetrics) -> PerformanceReport:
        """Generate performance comparison report"""
        if not self.baseline:
            raise ValueError("No baseline established")

        return PerformanceReport(
            startup_degradation_pct=self._calculate_degradation(
                self.baseline.startup_time_ms, current.startup_time_ms
            ),
            memory_increase_pct=self._calculate_degradation(
                self.baseline.memory_usage_mb, current.memory_usage_mb
            ),
            within_tolerance=self._check_tolerance(current)
        )
```

### Rollback Strategy
```python
# tools/rollback.py
class MigrationRollback:
    def __init__(self, checkpoint_dir: Path):
        self.checkpoint_dir = checkpoint_dir
        self.checkpoints: Dict[str, Path] = {}

    def create_checkpoint(self, phase: str) -> None:
        """Create rollback point before each major change"""
        checkpoint_path = self.checkpoint_dir / f"checkpoint_{phase}_{int(time.time())}"

        # Copy current state
        shutil.copytree("src/", checkpoint_path / "src")
        shutil.copytree("tests/", checkpoint_path / "tests")

        # Store performance baseline
        performance = PerformanceMonitor().measure_current_performance()
        with open(checkpoint_path / "performance.json", "w") as f:
            json.dump(asdict(performance), f)

        self.checkpoints[phase] = checkpoint_path
        console.print(f"[green]✓ Checkpoint created for phase: {phase}[/green]")

    def rollback_to_checkpoint(self, phase: str) -> None:
        """Restore to previous working state"""
        if phase not in self.checkpoints:
            raise ValueError(f"No checkpoint found for phase: {phase}")

        checkpoint_path = self.checkpoints[phase]

        # Restore files
        if Path("src").exists():
            shutil.rmtree("src")
        if Path("tests").exists():
            shutil.rmtree("tests")

        shutil.copytree(checkpoint_path / "src", "src")
        shutil.copytree(checkpoint_path / "tests", "tests")

        console.print(f"[yellow]⟲ Rolled back to checkpoint: {phase}[/yellow]")

    def validate_rollback(self, phase: str) -> bool:
        """Verify rollback was successful"""
        # Run basic tests to ensure rollback worked
        result = subprocess.run(["python", "-m", "pytest", "tests/"],
                              capture_output=True, text=True)
        return result.returncode == 0
```

### Error Tracking
- **CLI startup time** tracking
- **Memory usage** monitoring
- **Import time** measurements

### Error Tracking
```python
# Error context logging
logger.error(
    "Template resolution failed",
    extra={
        "source_type": resolution_result.source_type,
        "error_type": type(e).__name__,
        "fallback_attempted": resolution_result.fallback_attempted
    }
)
```

### Debug Information
```python
# Debug mode support
if os.getenv("SDD_DEBUG"):
    console.print(f"[dim]Module dependency graph: {get_dependency_info()}[/dim]")
```

## Missing Components

### Not Yet Implemented
- **Async/await support** throughout the service layer
- **Plugin architecture** for extending AI tool support
- **Configuration file support** (.sdd-config.json)
- **Advanced caching strategies** (content-based hashing)

### Future Development Phases

#### Phase 1: Core Extraction (Current Spec)
- Extract models, exceptions, and core services
- Maintain identical CLI behavior
- Establish testing infrastructure

#### Phase 2: Enhanced Architecture
- Add plugin system for AI tools
- Implement configuration files
- Add advanced caching

#### Phase 3: Performance Optimization
- Full async/await implementation
- Advanced lazy loading
- Memory optimization

#### Phase 4: Extensibility
- Plugin API for custom template sources
- Webhook support for template updates
- Advanced CLI features

## Migration Dependencies

### Internal Dependencies
- All existing tests must pass
- Performance benchmarks established
- Code coverage maintained above 80%

### External Dependencies
- No changes to `pyproject.toml` requirements
- Python 3.11+ compatibility maintained
- uv script functionality preserved

### Breaking Changes
- **None planned** - full backward compatibility required
- Internal API changes only (not user-facing)
- Import paths will change (internal only)
