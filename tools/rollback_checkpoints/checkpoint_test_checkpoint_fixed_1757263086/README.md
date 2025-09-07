# Improved-SDD

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)

A GitHub Copilot Studio project with Improved Spec-Driven Development templates for building high-quality Python CLI applications.

## Features

- **Spec-Driven Development**: Structured approach to software development with comprehensive specifications
- **Python CLI Framework**: Built with Typer and Rich for modern, beautiful command-line interfaces
- **Automated Code Quality**: Pre-commit hooks with Flake8, Black, isort, and mypy
- **GitHub Copilot Integration**: Custom templates and instructions for AI-assisted development
- **CI/CD Ready**: GitHub Actions workflow for automated testing and linting
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd improved-sdd
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up development environment**
   ```bash
   pip install pre-commit
   pre-commit install
   ```

4. **Open in VS Code** and start developing with GitHub Copilot using the provided templates

## Usage

### CLI Commands

The project includes a CLI tool for managing spec-driven development projects:

```bash
# Initialize a new project
python src/improved_sdd_cli.py init <project-name>

# Delete a project (with confirmation)
python src/improved_sdd_cli.py delete <project-name>

# Get help
python src/improved_sdd_cli.py --help
```

### Development Workflow

1. Create a specification in `specs/`
2. Use the CLI to initialize your project structure
3. Develop following the spec-driven approach
4. Commit changes (linting runs automatically)

## Development Setup

### Prerequisites

- Python 3.8 or higher
- VS Code with Python extension
- Git

### Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install pre-commit hooks:
   ```bash
   pip install pre-commit
   pre-commit install
   ```

### Code Quality Tools

This project uses comprehensive linting and formatting tools:

#### Automatic Linting (Pre-commit Hooks)

Pre-commit hooks run automatically on each commit. Install them with:

```bash
pre-commit install
```

Run manually on all files:
```bash
pre-commit run --all-files
```

#### Manual Tools

```bash
# Style guide enforcement
flake8 src/ --max-line-length=120

# Code formatting
black src/

# Import sorting
isort src/ --profile=black

# Type checking
mypy src/
```

#### VS Code Integration

The project includes optimized VS Code settings for:
- Real-time linting with Flake8
- Automatic formatting with Black on save
- Import sorting
- 120-character line ruler

#### CI/CD

GitHub Actions automatically runs quality checks on:
- Pushes to main/develop branches
- Pull requests

## Project Structure

```
improved-sdd/
├── src/                    # Source code
├── specs/                  # Project specifications
├── templates/              # Development templates
├── memory/                 # Project memory and constitution
├── .github/                # GitHub templates and workflows
├── requirements.txt        # Python dependencies
├── pyproject.toml         # Project configuration
├── .pre-commit-config.yaml # Pre-commit hooks
└── .flake8                # Linting configuration
```

## Templates Available

- **Chatmodes**: AI behavior patterns for different development scenarios
- **Instructions**: Context-specific development guidance
- **Prompts**: Structured prompts for AI interactions

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes and ensure tests pass
4. Commit with pre-commit hooks: `git commit -m "Add your feature"`
5. Push to your branch: `git push origin feature/your-feature`
6. Create a Pull Request

### Development Guidelines

- Follow the spec-driven development approach
- Write clear, documented code
- Use type hints for better code quality
- Run pre-commit hooks before committing
- Update specifications for new features

## Resources

- [Typer Documentation](https://typer.tiangolo.com/)
- [Rich Documentation](https://rich.readthedocs.io/)
- [CLI Guidelines](https://clig.dev/)
- [Python CLI Development Guide](.github/instructions/python-cli-development.md)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
