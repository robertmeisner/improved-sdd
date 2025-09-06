---
applyTo: '**'
---
# Python CLI Development Instructions

## Overview
This template provides guidance for developing Python CLI applications using modern best practices, focusing on typer + rich for beautiful, interactive command-line interfaces.

## Core Stack
- **CLI Framework**: [Typer](https://typer.tiangolo.com/) - Modern Python CLI framework
- **UI/Display**: [Rich](https://rich.readthedocs.io/) - Rich text and beautiful formatting
- **Progress**: Rich Progress for long-running operations
- **Configuration**: Typer options and arguments
- **Packaging**: uv script or standalone package

## Project Structure
```
project/
├── src/
│   ├── __init__.py
│   ├── main.py              # Entry point with typer.Typer()
│   ├── commands/            # Command modules
│   │   ├── __init__.py
│   │   ├── init.py         # init command
│   │   ├── config.py       # config command
│       └── ...
│   ├── core/               # Core business logic
│   │   ├── __init__.py
│   │   ├── models.py       # Data models
│   │   ├── utils.py        # Utilities
│       └── ...
│   └── ui/                 # UI components
│       ├── __init__.py
│       ├── console.py      # Rich console setup
│       ├── progress.py     # Progress tracking
│       ├── prompts.py      # Interactive prompts
│       └── ...
├── tests/
├── pyproject.toml          # Project configuration
├── README.md
└── ...
```

## Implementation Guidelines

### 1. Main CLI Setup
```python
#!/usr/bin/env python3
import typer
from rich.console import Console
from rich.panel import Panel

console = Console()
app = typer.Typer(
    name="your-cli",
    help="Your CLI description",
    rich_markup_mode="rich"
)

def show_banner():
    banner = """
Your ASCII Art Banner Here
"""
    console.print(Panel(banner, border_style="cyan"))

@app.callback()
def main(
    version: bool = typer.Option(False, "--version", help="Show version")
):
    if version:
        console.print("v1.0.0")
        raise typer.Exit()

if __name__ == "__main__":
    app()
```

### 2. Rich UI Components
```python
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.tree import Tree

# Console setup
console = Console()

# Progress tracking
def show_progress():
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Processing...", total=None)
        # Your work here

# Tables for data display
def show_table(data):
    table = Table(title="Results")
    table.add_column("Name", style="cyan")
    table.add_column("Value", style="green")

    for item in data:
        table.add_row(item.name, item.value)

    console.print(table)
```

### 3. Interactive Prompts
```python
import typer
from rich.prompt import Prompt, Confirm
from rich.console import Console

def get_user_input():
    name = Prompt.ask("Enter your name")
    confirm = Confirm.ask("Are you sure?")

    choice = typer.prompt(
        "Select option",
        type=typer.Choice(["dev", "prod", "test"])
    )
    return name, confirm, choice
```

### 4. Error Handling
```python
from rich.console import Console
import typer

console = Console()

def handle_error(error: Exception, context: str = ""):
    console.print(f"[red]Error{' in ' + context if context else ''}:[/red] {str(error)}")
    raise typer.Exit(1)

try:
    # Your code here
    pass
except Exception as e:
    handle_error(e, "initialization")
```

### 5. Configuration Management
```python
from pathlib import Path
from typing import Optional
import json
import typer

def get_config_path() -> Path:
    """Get configuration file path."""
    config_dir = Path.home() / ".config" / "your-cli"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "config.json"

def load_config() -> dict:
    """Load configuration from file."""
    config_path = get_config_path()
    if config_path.exists():
        return json.loads(config_path.read_text())
    return {}

def save_config(config: dict):
    """Save configuration to file."""
    config_path = get_config_path()
    config_path.write_text(json.dumps(config, indent=2))
```

### 6. File Operations with Tracking
```python
from pathlib import Path
from rich.console import Console

class FileTracker:
    def __init__(self):
        self.created = []
        self.modified = []

    def create_file(self, path: Path, content: str):
        if path.exists():
            self.modified.append(str(path))
        else:
            self.created.append(str(path))

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def summary(self) -> str:
        lines = []
        if self.created:
            lines.append(f"Created: {', '.join(self.created)}")
        if self.modified:
            lines.append(f"Modified: {', '.join(self.modified)}")
        return "\n".join(lines)
```

## Command Patterns

### 1. Simple Command
```python
@app.command()
def hello(
    name: str = typer.Argument(..., help="Name to greet"),
    count: int = typer.Option(1, help="Number of greetings")
):
    """Say hello to someone."""
    for _ in range(count):
        console.print(f"Hello [bold blue]{name}[/bold blue]!")
```

### 2. Complex Command with Subcommands
```python
# Create sub-app
config_app = typer.Typer(name="config", help="Configuration management")
app.add_typer(config_app)

@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Configuration key"),
    value: str = typer.Argument(..., help="Configuration value")
):
    """Set a configuration value."""
    config = load_config()
    config[key] = value
    save_config(config)
    console.print(f"Set {key} = {value}")

@config_app.command("get")
def config_get(
    key: str = typer.Argument(..., help="Configuration key")
):
    """Get a configuration value."""
    config = load_config()
    if key in config:
        console.print(f"{key} = {config[key]}")
    else:
        console.print(f"[yellow]Key '{key}' not found[/yellow]")
```

### 3. Interactive Command
```python
@app.command()
def init(
    name: Optional[str] = typer.Option(None, help="Project name"),
    template: str = typer.Option("basic", help="Template to use")
):
    """Initialize a new project."""
    if not name:
        name = Prompt.ask("Enter project name")

    console.print(f"Creating project: [bold blue]{name}[/bold blue]")

    # Show progress
    with Progress() as progress:
        task = progress.add_task("Setting up...", total=100)

        # Create project structure
        progress.update(task, advance=25, description="Creating directories...")
        # ... directory creation code

        progress.update(task, advance=50, description="Installing templates...")
        # ... template installation code

        progress.update(task, advance=25, description="Finalizing...")
        # ... finalization code

    console.print("[green]✓ Project created successfully![/green]")
```

## Testing Guidelines

### 1. CLI Testing with Typer
```python
from typer.testing import CliRunner
import pytest

runner = CliRunner()

def test_hello_command():
    result = runner.invoke(app, ["hello", "World"])
    assert result.exit_code == 0
    assert "Hello World" in result.output

def test_config_set():
    result = runner.invoke(app, ["config", "set", "key", "value"])
    assert result.exit_code == 0
    assert "Set key = value" in result.output
```

### 2. Rich Output Testing
```python
from rich.console import Console
from io import StringIO

def test_rich_output():
    string_io = StringIO()
    console = Console(file=string_io, width=80)

    console.print("[bold]Test[/bold]")
    output = string_io.getvalue()

    # Test markup was processed
    assert "Test" in output
```

## Packaging and Distribution

### 1. uv Script (Single File)
```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "typer",
#     "rich",
# ]
# ///

# Your CLI code here
```

### 2. Package Structure (pyproject.toml)
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "your-cli"
version = "1.0.0"
description = "Your CLI description"
dependencies = [
    "typer",
    "rich",
]

[project.scripts]
your-cli = "your_cli.main:app"
```

## Best Practices

### 1. User Experience
- **Clear help text**: Every command and option should have helpful descriptions
- **Progress feedback**: Show progress for long-running operations
- **Confirmation prompts**: Ask before destructive operations
- **Colorful output**: Use Rich styling to make output readable
- **Error handling**: Provide clear, actionable error messages

### 2. Code Organization
- **Single responsibility**: Each command does one thing well
- **Modular design**: Separate commands, logic, and UI
- **Type hints**: Use type annotations throughout
- **Documentation**: Document all functions and classes

### 3. Performance
- **Lazy imports**: Import heavy modules only when needed
- **Async operations**: Use async for I/O-bound tasks
- **Caching**: Cache expensive computations
- **Early validation**: Validate inputs before processing

### 4. Compatibility
- **Python versions**: Support Python 3.11+
- **Cross-platform**: Test on Windows, macOS, Linux
- **Dependencies**: Minimize external dependencies
- **Graceful degradation**: Handle missing optional tools

## Example: Complete Mini CLI

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["typer", "rich"]
# ///

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import track
from pathlib import Path

console = Console()
app = typer.Typer(help="Example CLI with typer and rich")

@app.command()
def create(
    name: str = typer.Argument(..., help="Project name"),
    template: str = typer.Option("basic", help="Template type")
):
    """Create a new project."""
    console.print(f"Creating project: [bold blue]{name}[/bold blue]")

    project_path = Path(name)
    if project_path.exists():
        console.print("[red]Project already exists![/red]")
        raise typer.Exit(1)

    # Simulate work with progress
    for step in track(["Creating directories", "Installing templates", "Setting up config"],
                      description="Setting up project..."):
        # Simulate work
        import time
        time.sleep(0.5)

    project_path.mkdir()
    (project_path / "README.md").write_text(f"# {name}\n\nCreated with example CLI")

    console.print(Panel(
        f"[green]✓ Project '{name}' created successfully![/green]\n\n"
        f"Next steps:\n"
        f"1. cd {name}\n"
        f"2. Start developing!",
        title="Success",
        border_style="green"
    ))

if __name__ == "__main__":
    app()
```

## Resources

- [Typer Documentation](https://typer.tiangolo.com/)
- [Rich Documentation](https://rich.readthedocs.io/)
- [Click Documentation](https://click.palletsprojects.com/) (Typer is built on Click)
- [Python CLI Best Practices](https://clig.dev/)
- [uv Scripts](https://docs.astral.sh/uv/guides/scripts/)

## Common Patterns

### Confirmation Before Destructive Actions
```python
from rich.prompt import Confirm

@app.command()
def delete(path: str):
    """Delete a file or directory."""
    if not Confirm.ask(f"Are you sure you want to delete {path}?"):
        console.print("Cancelled")
        raise typer.Exit()

    # Perform deletion
    console.print(f"[red]Deleted {path}[/red]")
```

### Environment Variable Integration
```python
import os
from typing import Optional

@app.command()
def deploy(
    env: Optional[str] = typer.Option(
        None,
        envvar="DEPLOY_ENV",
        help="Deployment environment"
    )
):
    """Deploy application."""
    if not env:
        env = typer.prompt("Enter environment")

    console.print(f"Deploying to: [bold]{env}[/bold]")
```

This template provides a comprehensive foundation for building professional Python CLI applications with modern tools and best practices.
