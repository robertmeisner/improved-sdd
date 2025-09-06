"""Makefile-style commands for development tasks."""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: str, description: str = "") -> int:
    """Run a command and return the exit code."""
    if description:
        print(f"🔄 {description}")

    print(f"➤ {cmd}")
    result = subprocess.run(cmd, shell=True)

    if result.returncode == 0:
        print(f"✅ Command completed successfully")
    else:
        print(f"❌ Command failed with exit code {result.returncode}")

    return result.returncode


def test():
    """Run all tests."""
    return run_command("pytest", "Running all tests")


def test_unit():
    """Run unit tests only."""
    return run_command("pytest tests/unit", "Running unit tests")


def test_integration():
    """Run integration tests only."""
    return run_command("pytest tests/integration", "Running integration tests")


def test_cov():
    """Run tests with coverage."""
    return run_command("pytest --cov=src --cov-report=html --cov-report=term", "Running tests with coverage")


def test_fast():
    """Run tests in parallel (fast)."""
    return run_command("pytest -n auto", "Running tests in parallel")


def lint():
    """Run linting tools."""
    commands = [
        ("black --check src tests", "Checking code formatting with black"),
        ("isort --check-only src tests", "Checking import sorting with isort"),
        ("flake8 src tests", "Running flake8 linter"),
        ("mypy src", "Running mypy type checker"),
    ]

    for cmd, desc in commands:
        exit_code = run_command(cmd, desc)
        if exit_code != 0:
            return exit_code

    return 0


def format_code():
    """Format code with black and isort."""
    commands = [
        ("black src tests", "Formatting code with black"),
        ("isort src tests", "Sorting imports with isort"),
    ]

    for cmd, desc in commands:
        exit_code = run_command(cmd, desc)
        if exit_code != 0:
            return exit_code

    return 0


def clean():
    """Clean up generated files."""
    import shutil

    patterns = [
        "**/__pycache__",
        "**/*.pyc",
        "**/*.pyo",
        ".coverage",
        "htmlcov",
        ".pytest_cache",
        ".mypy_cache",
        "dist",
        "build",
        "*.egg-info",
    ]

    print("🧹 Cleaning up generated files...")

    for pattern in patterns:
        for path in Path(".").glob(pattern):
            if path.is_file():
                path.unlink()
                print(f"  🗑️  Removed file: {path}")
            elif path.is_dir():
                shutil.rmtree(path)
                print(f"  🗑️  Removed directory: {path}")

    print("✅ Cleanup completed")
    return 0


def install_dev():
    """Install development dependencies."""
    return run_command("pip install -e .[dev,test]", "Installing development dependencies")


def check():
    """Run all checks (lint + test)."""
    print("🔍 Running all checks...")

    # Format first
    exit_code = format_code()
    if exit_code != 0:
        return exit_code

    # Then lint
    exit_code = lint()
    if exit_code != 0:
        return exit_code

    # Finally test
    exit_code = test()
    if exit_code != 0:
        return exit_code

    print("🎉 All checks passed!")
    return 0


def help_command():
    """Show available commands."""
    commands = {
        "test": "Run all tests",
        "test-unit": "Run unit tests only",
        "test-integration": "Run integration tests only",
        "test-cov": "Run tests with coverage",
        "test-fast": "Run tests in parallel",
        "lint": "Run linting tools",
        "format": "Format code with black and isort",
        "clean": "Clean up generated files",
        "install-dev": "Install development dependencies",
        "check": "Run all checks (format + lint + test)",
        "help": "Show this help message",
    }

    print("Available commands:")
    print()
    for cmd, desc in commands.items():
        print(f"  {cmd:<15} {desc}")
    print()
    print("Usage: python tasks.py <command>")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        help_command()
        sys.exit(1)

    command = sys.argv[1].replace("-", "_")

    if command == "help":
        help_command()
        sys.exit(0)

    # Get the function by name
    func = globals().get(command)
    if func is None:
        print(f"❌ Unknown command: {sys.argv[1]}")
        print()
        help_command()
        sys.exit(1)

    try:
        exit_code = func()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        sys.exit(130)
