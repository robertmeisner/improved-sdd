# Testing Guide for Improved-SDD CLI

This document describes the test suite for the improved-sdd CLI tool.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Test configuration and fixtures
├── unit/                    # Unit tests
│   ├── test_cli_commands.py # CLI command tests
│   └── test_core_functions.py # Core function tests
├── integration/             # Integration tests
│   └── test_workflows.py    # End-to-end workflow tests
└── fixtures/                # Test data and mock files
    ├── test_data.py         # Test constants and data
    ├── sample_chatmode.md   # Sample template files
    ├── sample_instruction.md
    ├── sample_prompt.md
    └── sample_command.md
```

## Running Tests

### Basic Test Commands

```bash
# Run all tests
python tasks.py test

# Run unit tests only
python tasks.py test-unit

# Run integration tests only
python tasks.py test-integration

# Run tests with coverage
python tasks.py test-cov

# Run tests in parallel (faster)
python tasks.py test-fast
```

### Direct pytest Commands

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_cli_commands.py

# Run specific test method
pytest tests/unit/test_cli_commands.py::TestInitCommand::test_init_help

# Run tests matching pattern
pytest -k "test_init"

# Run tests with specific markers
pytest -m "unit"
pytest -m "integration"
pytest -m "cli"
```

## Test Categories

### Unit Tests

**CLI Commands (`test_cli_commands.py`)**
- `TestInitCommand`: Tests for the `init` command
- `TestDeleteCommand`: Tests for the `delete` command  
- `TestCheckCommand`: Tests for the `check` command
- `TestMainApp`: Tests for main app behavior

**Core Functions (`test_core_functions.py`)**
- `TestFileTracker`: Tests for file tracking functionality
- `TestTemplateCustomization`: Tests for template customization
- `TestToolChecking`: Tests for tool availability checking

### Integration Tests

**Workflows (`test_workflows.py`)**
- `TestCompleteWorkflows`: End-to-end CLI workflows
- `TestProjectStructureCreation`: Project structure creation
- `TestFullSystemIntegration`: Full system integration tests

## Test Fixtures

The test suite includes comprehensive fixtures for mocking:

- **`runner`**: CLI test runner using typer.testing
- **`temp_dir`**: Temporary directory for test isolation
- **`temp_project_dir`**: Temporary project directory
- **`mock_templates_dir`**: Mock templates directory structure
- **`mock_script_location`**: Mock CLI script location
- **`sample_ai_tools`**: Sample AI tool configurations
- **`project_with_existing_files`**: Project with pre-existing files

## Test Data

Test data is organized in `tests/fixtures/test_data.py`:

- **AI Tools**: Sample configurations for testing
- **Template Content**: Sample templates with placeholders
- **User Inputs**: Mock user inputs for interactive commands
- **Tool Availability**: Mock scenarios for tool checking
- **Expected Structures**: Expected file structures after operations

## Test Markers

Tests are marked with the following categories:

- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.cli`: CLI command tests
- `@pytest.mark.templates`: Template operation tests
- `@pytest.mark.file_ops`: File operation tests
- `@pytest.mark.slow`: Slow-running tests

## Coverage

The test suite aims for high coverage of the CLI functionality:

- **CLI Commands**: All commands (init, delete, check) with various options
- **Core Classes**: FileTracker and helper functions
- **Template Processing**: Template customization and file generation
- **Error Handling**: Edge cases and error conditions
- **User Interaction**: Interactive prompts and confirmations

## Mock Strategy

Tests use comprehensive mocking to isolate functionality:

- **File System**: Mock file operations for safety
- **User Input**: Mock interactive prompts
- **Tool Availability**: Mock external tool checking
- **Template Location**: Mock template directory location

## Continuous Integration

The test suite is designed to run reliably in CI environments:

- No external dependencies required
- All file operations are isolated to temp directories
- Comprehensive mocking prevents side effects
- Clear test categorization allows selective running

## Development Workflow

### Adding New Tests

1. **Unit Tests**: Add to appropriate file in `tests/unit/`
2. **Integration Tests**: Add to `tests/integration/test_workflows.py`
3. **Test Data**: Add to `tests/fixtures/test_data.py`
4. **Fixtures**: Add to `tests/conftest.py`

### Test-Driven Development

1. Write failing test for new functionality
2. Implement minimal code to pass test
3. Refactor and improve
4. Ensure all tests pass

### Pre-commit Checks

Run the full check suite before committing:

```bash
python tasks.py check
```

This runs:
1. Code formatting (black, isort)
2. Linting (flake8, mypy)
3. All tests with coverage

## Debugging Tests

### Verbose Output

```bash
pytest -v                    # Verbose test names
pytest -s                    # Don't capture output
pytest --tb=short           # Short traceback format
pytest --tb=long            # Long traceback format
```

### Failed Tests Only

```bash
pytest --lf                 # Run last failed tests
pytest --ff                 # Run failed tests first
```

### Test Discovery

```bash
pytest --collect-only       # Show what tests would run
```

## Performance

- **Fast Tests**: Unit tests run in < 1 second
- **Parallel Execution**: Integration tests can run in parallel
- **Selective Running**: Use markers to run specific test categories
- **Coverage Caching**: Coverage data is cached for faster reruns