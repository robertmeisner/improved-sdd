#!/usr/bin/env python3
"""Test runner script for improved-sdd CLI tests."""

import sys
import subprocess
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and print the result."""
    if description:
        print(f"\n{'='*60}")
        print(f"🔄 {description}")
        print(f"{'='*60}")
    
    print(f"➤ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    
    if result.returncode == 0:
        print(f"✅ {description or 'Command'} completed successfully")
    else:
        print(f"❌ {description or 'Command'} failed with exit code {result.returncode}")
    
    return result.returncode


def main():
    """Main test runner."""
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
    else:
        test_type = "all"
    
    base_cmd = [sys.executable, "-m", "pytest"]
    
    if test_type == "unit":
        cmd = base_cmd + ["tests/unit/", "-v"]
        return run_command(cmd, "Running unit tests")
    
    elif test_type == "integration":
        cmd = base_cmd + ["tests/integration/test_simple_integration.py", "-v"]
        return run_command(cmd, "Running integration tests")
    
    elif test_type == "coverage":
        cmd = base_cmd + [
            "tests/unit/", 
            "tests/integration/test_simple_integration.py",
            "--cov=src", 
            "--cov-report=term-missing",
            "--cov-report=html"
        ]
        return run_command(cmd, "Running tests with coverage")
    
    elif test_type == "fast":
        cmd = base_cmd + [
            "tests/unit/", 
            "tests/integration/test_simple_integration.py",
            "-v", 
            "-x"  # Stop on first failure
        ]
        return run_command(cmd, "Running fast tests (stop on failure)")
    
    elif test_type == "all":
        cmd = base_cmd + [
            "tests/unit/", 
            "tests/integration/test_simple_integration.py",
            "-v"
        ]
        return run_command(cmd, "Running all working tests")
    
    elif test_type == "help":
        print("""
Test Runner for improved-sdd CLI

Usage: python test_runner.py [test_type]

Test types:
  unit        Run unit tests only
  integration Run integration tests only
  coverage    Run tests with coverage report
  fast        Run tests quickly (stop on first failure)
  all         Run all working tests (default)
  help        Show this help message

Examples:
  python test_runner.py unit
  python test_runner.py coverage
  python test_runner.py
""")
        return 0
    
    else:
        print(f"❌ Unknown test type: {test_type}")
        print("Run 'python test_runner.py help' for usage information")
        return 1


if __name__ == "__main__":
    sys.exit(main())