# Improved-SDD

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)

A GitHub Copilot Studio project with Improved Spec-Driven Development templates for building high-quality Python CLI applications.

## Features

- **Spec-Driven Development**: Structured approach to software development with comprehensive specifications
- **GitLab Flow Integration**: Built-in workflow guidance with automatic commit prompts and PR creation
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
# Initialize a new project with GitLab Flow (default)
python src/improved_sdd_cli.py init <project-name>

# Initialize without GitLab Flow integration
python src/improved_sdd_cli.py init <project-name> --no-gitlab-flow

# Delete a project (with confirmation)
python src/improved_sdd_cli.py delete <project-name>

# Check project configuration
python src/improved_sdd_cli.py check <project-name>

# Get help
python src/improved_sdd_cli.py --help
```

### Development Workflow

1. Create a specification in `specs/`
2. Use the CLI to initialize your project structure
3. Develop following the spec-driven approach
4. Commit changes (linting runs automatically)

### GitLab Flow Integration

The improved-sdd CLI includes built-in GitLab Flow support that provides workflow guidance during spec development:

#### **Automatic Workflow Integration**
- **Setup Guidance**: Branch creation and repository validation before starting specs
- **Phase Commit Prompts**: Commit guidance after completing each spec phase (feasibility, requirements, design, tasks)
- **PR Creation**: Step-by-step PR creation guidance after implementation completion
- **Platform-Specific Commands**: Windows PowerShell vs Unix/macOS bash command syntax

#### **How It Works**

GitLab Flow uses a **dynamic keyword integration** approach:

1. **Markdown Files as Variables**: GitLab Flow content stored in `templates/gitlab-flow/*.md` files
2. **Keyword Replacement**: Keywords like `{GITLAB_FLOW_SETUP}`, `{GITLAB_FLOW_COMMIT}`, `{GITLAB_FLOW_PR}` in chatmode files
3. **Conditional Loading**: Keywords replaced with GitLab Flow content when enabled, empty when disabled
4. **Platform Detection**: Commands automatically adjusted for Windows vs Unix systems

#### **CLI Flag Control**

```bash
# Enable GitLab Flow (default behavior)
python src/improved_sdd_cli.py init my-project --gitlab-flow

# Disable GitLab Flow
python src/improved_sdd_cli.py init my-project --no-gitlab-flow
```

#### **Example Workflow**

1. **Project Initialization**: `improved-sdd init my-feature --gitlab-flow`
2. **Branch Setup**: Follow GitLab Flow setup guidance in chatmode
3. **Spec Development**: Complete feasibility → requirements → design → tasks
4. **Automatic Commits**: Commit after each phase using provided guidance
5. **Implementation**: Execute tasks with commit prompts between tasks
6. **PR Creation**: Create pull request when all implementation complete

#### **GitLab Flow Templates**

The system includes three core templates:

- **`gitlab-flow-setup.md`**: Repository validation and branch creation
- **`gitlab-flow-commit.md`**: Phase completion commit guidance with conventional commit format
- **`gitlab-flow-pr.md`**: PR creation with timing safeguards and templates

#### **Benefits**

- ✅ **Integrated Workflow**: Git operations embedded naturally in spec development
- ✅ **Zero Breaking Changes**: Existing workflows unchanged when disabled
- ✅ **Platform Agnostic**: Works on Windows, macOS, and Linux
- ✅ **Flexible Control**: Easy to enable/disable via CLI flag
- ✅ **Best Practices**: Conventional commits and proper PR timing

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
│   ├── chatmodes/         # AI behavior patterns
│   ├── instructions/      # Development guidance
│   ├── prompts/           # Structured AI prompts
│   └── gitlab-flow/       # GitLab Flow workflow templates
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
- **GitLab Flow**: Workflow templates for git operations and branch management

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
