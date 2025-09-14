#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["typer", "rich", "httpx"]
# ///

"""
PyPI Publishing Setup Verification Tool

This script verifies that the PyPI publishing automation is properly configured.
It checks GitHub repository settings, secrets, environments, and workflow configuration.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

import httpx
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()
app = typer.Typer(help="Verify PyPI publishing automation setup")

# Configuration constants
REQUIRED_SECRETS = ["TEST_PYPI_API_TOKEN", "PYPI_API_TOKEN"]
REQUIRED_ENVIRONMENTS = ["testpypi", "pypi"]
WORKFLOW_FILE = ".github/workflows/publish.yml"

class SetupVerifier:
    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.repo_owner = None
        self.repo_name = None
        self.headers = {}
        
        if self.github_token:
            self.headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }

    def detect_repository(self) -> bool:
        """Detect GitHub repository from git remote."""
        try:
            import subprocess
            result = subprocess.run(
                ["git", "remote", "get-url", "origin"],
                capture_output=True,
                text=True,
                check=True
            )
            
            remote_url = result.stdout.strip()
            
            # Parse GitHub URL
            if "github.com" in remote_url:
                if remote_url.startswith("git@"):
                    # SSH format: git@github.com:owner/repo.git
                    parts = remote_url.split(":")[-1].replace(".git", "").split("/")
                elif remote_url.startswith("https://"):
                    # HTTPS format: https://github.com/owner/repo.git
                    parts = remote_url.split("/")[-2:]
                    parts[-1] = parts[-1].replace(".git", "")
                else:
                    return False
                
                if len(parts) >= 2:
                    self.repo_owner = parts[-2]
                    self.repo_name = parts[-1]
                    return True
            
            return False
        except Exception:
            return False

    def check_workflow_file(self) -> Dict[str, bool]:
        """Check if workflow file exists and has required configuration."""
        results = {
            "file_exists": False,
            "has_testpypi_job": False,
            "has_pypi_job": False,
            "has_required_triggers": False,
            "has_environments": False,
            "has_ci_dependencies": False
        }
        
        workflow_path = Path(WORKFLOW_FILE)
        if not workflow_path.exists():
            return results
        
        results["file_exists"] = True
        
        try:
            content = workflow_path.read_text(encoding='utf-8')
            
            # Check for required jobs
            if "publish-testpypi:" in content:
                results["has_testpypi_job"] = True
            if "publish-pypi:" in content:
                results["has_pypi_job"] = True
            
            # Check for triggers
            if "push:" in content and "tags:" in content and "workflow_dispatch:" in content:
                results["has_required_triggers"] = True
            
            # Check for environment references
            if "environment: testpypi" in content and "environment: pypi" in content:
                results["has_environments"] = True
            
            # Check for CI workflow dependencies
            if ("lewagon/wait-on-check-action" in content and 
                "check-name: 'Test Suite'" in content and 
                "check-name: 'Security Audit'" in content):
                results["has_ci_dependencies"] = True
                
        except Exception as e:
            console.print(f"[red]Error reading workflow file: {e}[/red]")
        
        return results

    async def check_github_secrets(self) -> Dict[str, bool]:
        """Check if required GitHub secrets are configured."""
        results = {secret: False for secret in REQUIRED_SECRETS}
        
        if not self.github_token or not self.repo_owner or not self.repo_name:
            return results
        
        try:
            async with httpx.AsyncClient() as client:
                url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/actions/secrets"
                response = await client.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    secrets_data = response.json()
                    secret_names = [secret["name"] for secret in secrets_data.get("secrets", [])]
                    
                    for secret in REQUIRED_SECRETS:
                        results[secret] = secret in secret_names
                
        except Exception as e:
            console.print(f"[red]Error checking GitHub secrets: {e}[/red]")
        
        return results

    async def check_github_environments(self) -> Dict[str, Dict]:
        """Check if required GitHub environments are configured."""
        results = {env: {"exists": False, "url": None} for env in REQUIRED_ENVIRONMENTS}
        
        if not self.github_token or not self.repo_owner or not self.repo_name:
            return results
        
        try:
            async with httpx.AsyncClient() as client:
                url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/environments"
                response = await client.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    environments_data = response.json()
                    
                    for env_data in environments_data.get("environments", []):
                        env_name = env_data["name"]
                        if env_name in REQUIRED_ENVIRONMENTS:
                            results[env_name]["exists"] = True
                            results[env_name]["url"] = env_data.get("url")
                
        except Exception as e:
            console.print(f"[red]Error checking GitHub environments: {e}[/red]")
        
        return results

    def check_local_configuration(self) -> Dict[str, bool]:
        """Check local project configuration."""
        results = {
            "pyproject_toml": False,
            "proper_version": False,
            "package_name": False,
            "git_repository": False
        }
        
        # Check pyproject.toml
        pyproject_path = Path("pyproject.toml")
        if pyproject_path.exists():
            results["pyproject_toml"] = True
            
            try:
                # Try tomllib first (Python 3.11+), then fallback to tomli
                try:
                    import tomllib
                    with open(pyproject_path, "rb") as f:
                        data = tomllib.load(f)
                except ImportError:
                    # Fallback for older Python versions
                    try:
                        import tomli as tomllib
                        with open(pyproject_path, "rb") as f:
                            data = tomllib.load(f)
                    except ImportError:
                        # Final fallback - skip TOML parsing
                        return results
                
                project = data.get("project", {})
                if "name" in project:
                    results["package_name"] = True
                if "version" in project:
                    version = project["version"]
                    # Basic semantic version check
                    if len(version.split(".")) >= 3:
                        results["proper_version"] = True
                        
            except Exception:
                pass
        
        # Check if we're in a git repository
        if Path(".git").exists():
            results["git_repository"] = True
        
        return results

@app.command()
def verify(
    github_token: Optional[str] = typer.Option(
        None, 
        "--token", 
        help="GitHub token for API access (or set GITHUB_TOKEN env var)",
        envvar="GITHUB_TOKEN"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):
    """Verify PyPI publishing automation setup."""
    
    console.print(Panel.fit(
        "[bold blue]PyPI Publishing Setup Verification[/bold blue]",
        border_style="blue"
    ))
    
    verifier = SetupVerifier(github_token)
    
    # Detect repository
    if not verifier.detect_repository():
        console.print("[red]⚠️  Could not detect GitHub repository from git remote[/red]")
        console.print("Make sure you're in a git repository with GitHub remote configured")
        if not github_token:
            console.print("[yellow]Note: Some checks require a GitHub token[/yellow]")
    else:
        console.print(f"[green]✓ Detected repository: {verifier.repo_owner}/{verifier.repo_name}[/green]")
    
    # Check local configuration
    console.print("\n[bold]Local Configuration[/bold]")
    local_results = verifier.check_local_configuration()
    
    for check, passed in local_results.items():
        status = "✓" if passed else "✗"
        color = "green" if passed else "red"
        check_name = check.replace("_", " ").title()
        console.print(f"[{color}]{status} {check_name}[/{color}]")
    
    # Check workflow file
    console.print("\n[bold]Workflow Configuration[/bold]")
    workflow_results = verifier.check_workflow_file()
    
    # Define better display names for workflow checks
    workflow_check_names = {
        "file_exists": "Workflow File Exists",
        "has_testpypi_job": "TestPyPI Publishing Job",
        "has_pypi_job": "PyPI Publishing Job", 
        "has_required_triggers": "Required Triggers (Push/Tags/Manual)",
        "has_environments": "Environment References",
        "has_ci_dependencies": "CI Workflow Dependencies"
    }
    
    for check, passed in workflow_results.items():
        status = "✓" if passed else "✗"
        color = "green" if passed else "red"
        check_name = workflow_check_names.get(check, check.replace("_", " ").title())
        console.print(f"[{color}]{status} {check_name}[/{color}]")
    
    # Check GitHub configuration (if token available)
    if github_token and verifier.repo_owner and verifier.repo_name:
        console.print("\n[bold]GitHub Configuration[/bold]")
        
        # Run async checks
        import asyncio
        
        async def run_github_checks():
            secrets_results = await verifier.check_github_secrets()
            environments_results = await verifier.check_github_environments()
            return secrets_results, environments_results
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Checking GitHub configuration...", total=None)
            secrets_results, environments_results = asyncio.run(run_github_checks())
        
        # Display secrets results
        console.print("\n[bold cyan]Repository Secrets[/bold cyan]")
        for secret, exists in secrets_results.items():
            status = "✓" if exists else "✗"
            color = "green" if exists else "red"
            console.print(f"[{color}]{status} {secret}[/{color}]")
        
        # Display environments results
        console.print("\n[bold cyan]Environments[/bold cyan]")
        for env, data in environments_results.items():
            status = "✓" if data["exists"] else "✗"
            color = "green" if data["exists"] else "red"
            url_info = f" ({data['url']})" if data["url"] else ""
            console.print(f"[{color}]{status} {env}{url_info}[/{color}]")
    
    else:
        console.print("\n[yellow]⚠️  GitHub configuration checks skipped[/yellow]")
        console.print("Provide a GitHub token with repo permissions to check secrets and environments")
        console.print("Set GITHUB_TOKEN environment variable or use --token option")
    
    # Summary
    console.print("\n[bold]Setup Summary[/bold]")
    
    all_local_passed = all(local_results.values())
    all_workflow_passed = all(workflow_results.values())
    
    if github_token and verifier.repo_owner and verifier.repo_name:
        all_secrets_passed = all(secrets_results.values())
        all_environments_passed = all(data["exists"] for data in environments_results.values())
        
        overall_status = all([
            all_local_passed,
            all_workflow_passed, 
            all_secrets_passed,
            all_environments_passed
        ])
    else:
        overall_status = all_local_passed and all_workflow_passed
    
    if overall_status:
        console.print("[green]🎉 All checks passed! Publishing automation is ready.[/green]")
    else:
        console.print("[red]❌ Some checks failed. Review the setup guide.[/red]")
        console.print("See docs/pypi-setup-guide.md for detailed setup instructions")
    
    return 0 if overall_status else 1

@app.command()
def info():
    """Display information about the setup verification tool."""
    
    table = Table(title="Setup Verification Checks")
    table.add_column("Category", style="cyan")
    table.add_column("Check", style="white")
    table.add_column("Description", style="dim")
    
    checks = [
        ("Local", "Pyproject TOML", "Project configuration file exists"),
        ("Local", "Proper Version", "Semantic version format (x.y.z)"),
        ("Local", "Package Name", "Package name defined in project config"),
        ("Local", "Git Repository", "Project is in a Git repository"),
        ("Workflow", "File Exists", "GitHub Actions workflow file exists"),
        ("Workflow", "TestPyPI Job", "TestPyPI publishing job configured"),
        ("Workflow", "PyPI Job", "PyPI publishing job configured"),
        ("Workflow", "Required Triggers", "Push, tags, and manual triggers"),
        ("Workflow", "Environments", "Environment references configured"),
        ("GitHub", "TEST_PYPI_API_TOKEN", "TestPyPI API token secret"),
        ("GitHub", "PYPI_API_TOKEN", "PyPI API token secret"),
        ("GitHub", "testpypi Environment", "TestPyPI deployment environment"),
        ("GitHub", "pypi Environment", "PyPI deployment environment"),
    ]
    
    for category, check, description in checks:
        table.add_row(category, check, description)
    
    console.print(table)
    
    console.print("\n[bold]Usage Examples[/bold]")
    console.print("• Basic verification: [cyan]python tools/verify-setup.py verify[/cyan]")
    console.print("• With GitHub token: [cyan]python tools/verify-setup.py verify --token YOUR_TOKEN[/cyan]")
    console.print("• Using environment: [cyan]GITHUB_TOKEN=xxx python tools/verify-setup.py verify[/cyan]")

if __name__ == "__main__":
    app()