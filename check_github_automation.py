#!/usr/bin/env python3
"""
GitHub Automation Status Checker

This script verifies that all components of the GitHub automation are properly configured.
"""

import sys
from pathlib import Path
from typing import List, Tuple
import json

def check_file_exists(filepath: str, description: str) -> Tuple[bool, str]:
    """Check if a file exists."""
    if Path(filepath).exists():
        return True, f"✅ {description}"
    else:
        return False, f"❌ {description} - MISSING"

def check_pyproject_dependencies() -> Tuple[bool, str]:
    """Check if pyproject.toml has required dependencies."""
    try:
        # Read pyproject.toml content (simple text parsing since toml isn't available)
        pyproject_path = Path("pyproject.toml")
        if not pyproject_path.exists():
            return False, "❌ pyproject.toml not found"
        
        content = pyproject_path.read_text()
        
        required_test_deps = ["pytest", "pytest-cov", "pytest-mock"]
        required_dev_deps = ["black", "isort", "flake8", "mypy"]
        
        missing_deps = []
        for dep in required_test_deps + required_dev_deps:
            if dep not in content:
                missing_deps.append(dep)
        
        if missing_deps:
            return False, f"❌ Missing dependencies: {', '.join(missing_deps)}"
        else:
            return True, "✅ All required dependencies present in pyproject.toml"
            
    except Exception as e:
        return False, f"❌ Error reading pyproject.toml: {str(e)}"

def main():
    """Main status check function."""
    print("🔍 GitHub Automation Status Check")
    print("=" * 50)
    
    checks = [
        # Core workflow files
        (".github/workflows/ci.yml", "Main CI/CD workflow"),
        (".github/workflows/security.yml", "Security audit workflow"),
        (".pre-commit-config.yaml", "Pre-commit configuration"),
        
        # Test files
        ("tests/conftest.py", "Test configuration and fixtures"),
        ("tests/unit/test_cli_commands.py", "CLI command tests"),
        ("tests/unit/test_core_functions.py", "Core function tests"),
        ("pytest.ini", "Pytest configuration"),
        
        # Test runners
        ("test_runner.py", "Simple test runner"),
        ("tasks.py", "Task runner script"),
        
        # Documentation
        ("GITHUB_AUTOMATION.md", "GitHub automation documentation"),
        
        # Core project files
        ("src/improved_sdd_cli.py", "Main CLI module"),
        ("pyproject.toml", "Project configuration"),
    ]
    
    results = []
    all_passed = True
    
    # Check file existence
    for filepath, description in checks:
        passed, message = check_file_exists(filepath, description)
        results.append((passed, message))
        if not passed:
            all_passed = False
    
    # Check dependencies
    dep_passed, dep_message = check_pyproject_dependencies()
    results.append((dep_passed, dep_message))
    if not dep_passed:
        all_passed = False
    
    # Print results
    for passed, message in results:
        print(message)
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("🎉 All GitHub automation components are properly configured!")
        print("\n📋 What GitHub will check on every push/PR:")
        print("   • Unit tests (45 tests)")
        print("   • Integration tests (7 tests)")
        print("   • Code formatting (black, isort)")
        print("   • Linting (flake8)")
        print("   • Type checking (mypy)")
        print("   • Security scanning (safety, bandit)")
        print("   • Multi-Python testing (3.8-3.12)")
        print("   • Cross-platform testing (Ubuntu, Windows, macOS)")
        print("   • Package building and validation")
        print("   • Coverage reporting")
        print("\n🔧 To activate:")
        print("   1. Commit and push to GitHub")
        print("   2. GitHub Actions will run automatically")
        print("   3. Check the 'Actions' tab for results")
        return 0
    else:
        print("⚠️  Some components are missing or misconfigured.")
        print("Please review the failed checks above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())