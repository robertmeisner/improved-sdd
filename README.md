# improved-sdd

A GitHub Copilot Studio project with Improved Spec-Driven Development templates.

## App Type: Python CLI - Command-line application using typer and rich

This project is configured with custom templates for GitHub Copilot Studio development.

## Quick Start

1. Open in VS Code
2. Use GitHub Copilot with the templates in `.github/`
3. Follow the spec-driven development workflow
4. Reference `.github/instructions/` for app-specific guidance

## Development Setup

### Prerequisites

- Python 3.8+
- VS Code with Python extension

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   # Development dependencies are included in requirements.txt
   ```

### Linting and Code Quality

This project uses several tools to maintain code quality:

#### Automatic Linting (Pre-commit Hooks)

Install pre-commit hooks to automatically run linting on each commit:

```bash
pip install pre-commit
pre-commit install
```

Now linting will run automatically on each commit. You can also run it manually:

```bash
pre-commit run --all-files
```

#### Manual Linting

Run individual linting tools:

```bash
# Flake8 (style guide enforcement)
flake8 src/ --max-line-length=120

# Black (code formatting)
black src/

# isort (import sorting)
isort src/ --profile=black

# mypy (type checking)
mypy src/
```

#### VS Code Integration

The project includes VS Code settings (`.vscode/settings.json`) that:
- Enable automatic linting with flake8
- Format code with black on save
- Sort imports automatically
- Show a ruler at 120 characters

#### CI/CD

GitHub Actions will automatically run linting checks on:
- Push to main/develop branches
- Pull requests to main/develop branches

### Configuration Files

- `.flake8` - Flake8 linting configuration
- `pyproject.toml` - Project configuration (Black, isort, mypy)
- `.pre-commit-config.yaml` - Pre-commit hooks configuration
- `.vscode/settings.json` - VS Code workspace settings
- `.github/workflows/ci.yml` - GitHub Actions CI configuration

## Templates Available

- **Chatmodes**: `.github/chatmodes/` - AI behavior patterns
- **Instructions**: `.github/instructions/` - Context-specific guidance
- **Prompts**: `.github/prompts/` - Structured interactions

## Python CLI Development

This project is set up for Python CLI application development:

- Use typer for modern CLI framework
- Rich for beautiful terminal output
- Follow CLI best practices and UX patterns
- Include comprehensive help and error handling
- Support cross-platform compatibility

### Resources

- [Typer Documentation](https://typer.tiangolo.com/)
- [Rich Documentation](https://rich.readthedocs.io/)
- [CLI Guidelines](https://clig.dev/)
- [Python CLI Template](.github/instructions/python-cli-dev.instructions.md)
