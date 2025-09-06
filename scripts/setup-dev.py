#!/usr/bin/env python3
"""
Development setup script for improved-sdd project.
This script helps set up the development environment with all linting tools.
"""

import subprocess
import sys
from pathlib import Path


def run_command(command: str, description: str) -> bool:
    """Run a command and return success status."""
    print(f"🔧 {description}...")
    try:
        subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: ")
        print(e.stderr)
        return False


def main():
    """Set up the development environment."""
    print("🚀 Setting up improved-sdd development environment...\n")

    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)

    success_count = 0
    total_steps = 0

    # Install dependencies
    total_steps += 1
    if run_command("pip install -r requirements.txt", "Installing dependencies"):
        success_count += 1

    # Install pre-commit hooks
    total_steps += 1
    if run_command("pre-commit install", "Installing pre-commit hooks"):
        success_count += 1

    # Run initial linting check
    total_steps += 1
    if run_command("pre-commit run --all-files", "Running initial linting check"):
        success_count += 1

    print(f"\n📊 Setup complete: {success_count}/{total_steps} steps successful")

    if success_count == total_steps:
        print("🎉 Development environment is ready!")
        print("\nNext steps:")
        print("1. Open the project in VS Code")
        print("2. Start coding - linting will run automatically on save")
        print("3. Use 'git commit' - pre-commit hooks will run automatically")
    else:
        print("⚠️  Some steps failed. Please check the output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
