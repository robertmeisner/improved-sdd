#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["typer", "rich"]
# ///

"""
Version Management Utility    repo_url = get_repository_url()
    console.print()
    console.print(Panel(
        f"[green]Tag v{version} will trigger:[/green]\n"
        f"• Automated PyPI publishing\n"
        f"• GitHub release creation\n"
        f"• Installation verification\n\n"
        f"[yellow]Monitor progress at:[/yellow]\n"
        f"{repo_url}/actions",
        title="Publishing Automation",
        border_style="green"
    ))ed-sdd

This tool provides semantic version management capabilities including:
- Current version display
- Version bumping (major, minor, patch)
- Dry-run mode for testing changes
- Git tag preparation instructions
- PyPI publishing workflow guidance
"""

import re
import subprocess
import sys
from enum import Enum
from pathlib import Path
from typing import Optional, Tuple

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
app = typer.Typer(
    name="bump-version",
    help="Manage package versioning for improved-sdd",
    rich_markup_mode="rich"
)

class VersionPart(str, Enum):
    """Version parts that can be bumped."""
    major = "major"
    minor = "minor"
    patch = "patch"

def get_repository_url() -> str:
    """Get GitHub repository URL from git remote."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True
        )
        remote_url = result.stdout.strip()
        
        # Convert to GitHub web URL format
        if remote_url.startswith("git@github.com:"):
            # SSH format: git@github.com:owner/repo.git
            repo_path = remote_url.replace("git@github.com:", "").replace(".git", "")
            return f"https://github.com/{repo_path}"
        elif remote_url.startswith("https://github.com/"):
            # HTTPS format: https://github.com/owner/repo.git
            return remote_url.replace(".git", "")
        else:
            # Fallback to default
            return "https://github.com/robertmeisner/improved-sdd"
    except Exception:
        # Fallback to default if git command fails
        return "https://github.com/robertmeisner/improved-sdd"

def show_banner():
    """Display tool banner."""
    banner = """
[bold cyan]Version Management Utility[/bold cyan]
[dim]Semantic version management for improved-sdd[/dim]
"""
    console.print(Panel(banner, border_style="cyan"))

def get_current_version() -> str:
    """Get current version from pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        console.print("[red]ERROR: pyproject.toml not found in current directory[/red]")
        console.print("[yellow]TIP: Run this command from the project root directory[/yellow]")
        raise typer.Exit(1)
    
    content = pyproject_path.read_text(encoding='utf-8')
    match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
    if not match:
        console.print("[red]ERROR: Could not find version in pyproject.toml[/red]")
        console.print("[yellow]TIP: Ensure version is set as: version = \"1.0.0\"[/yellow]")
        raise typer.Exit(1)
    return match.group(1)

def validate_version(version: str) -> bool:
    """Validate semantic version format."""
    pattern = r'^\d+\.\d+\.\d+(?:-[a-zA-Z0-9.-]+)?(?:\+[a-zA-Z0-9.-]+)?$'
    return bool(re.match(pattern, version))

def parse_version(version: str) -> Tuple[int, int, int, Optional[str], Optional[str]]:
    """Parse semantic version into components."""
    if not validate_version(version):
        console.print(f"[red]ERROR: Invalid version format: {version}[/red]")
        console.print("[yellow]TIP: Expected format: major.minor.patch[-prerelease][+build][/yellow]")
        raise typer.Exit(1)
    
    # Split on '+' for build metadata
    version_core, build = (version.split('+', 1) + [None])[:2]
    
    # Split on '-' for prerelease
    version_nums, prerelease = (version_core.split('-', 1) + [None])[:2]
    
    # Parse major.minor.patch
    try:
        major, minor, patch = map(int, version_nums.split('.'))
        return major, minor, patch, prerelease, build
    except ValueError:
        console.print(f"[red]ERROR: Invalid version format: {version}[/red]")
        raise typer.Exit(1)

def bump_version_part(version: str, part: VersionPart) -> str:
    """Bump specified version part."""
    major, minor, patch, prerelease, build = parse_version(version)
    
    if part == VersionPart.major:
        major += 1
        minor = 0
        patch = 0
    elif part == VersionPart.minor:
        minor += 1
        patch = 0
    elif part == VersionPart.patch:
        patch += 1
    
    # Remove prerelease and build metadata when bumping
    new_version = f"{major}.{minor}.{patch}"
    return new_version

def update_version_file(new_version: str) -> None:
    """Update version in pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text(encoding='utf-8')
    
    # More robust replacement pattern
    updated_content = re.sub(
        r'(version\s*=\s*)["\'][^"\']+["\']',
        rf'\1"{new_version}"',
        content
    )
    
    if updated_content == content:
        console.print("[red]ERROR: Could not update version in pyproject.toml[/red]")
        raise typer.Exit(1)
    
    pyproject_path.write_text(updated_content, encoding='utf-8')
    console.print(f"[green]SUCCESS: Updated version to {new_version}[/green]")

def show_next_steps(version: str) -> None:
    """Show next steps for release workflow."""
    steps_table = Table(title="Next Steps for Release", show_header=False, box=None)
    steps_table.add_column("Step", style="bold cyan", no_wrap=True)
    steps_table.add_column("Command", style="bright_blue")
    
    steps_table.add_row("1. Commit changes:", f"git add pyproject.toml")
    steps_table.add_row("", f"git commit -m \"chore: bump version to {version}\"")
    steps_table.add_row("2. Create git tag:", f"git tag v{version}")
    steps_table.add_row("3. Push changes:", f"git push origin main")
    steps_table.add_row("4. Push tag:", f"git push origin v{version}")
    steps_table.add_row("5. Monitor workflow:", "Check GitHub Actions for publishing status")
    
    console.print()
    console.print(steps_table)
    
    console.print()
    console.print(Panel(
        f"[green]🎉 Tag v{version} will trigger:[/green]\n"
        f"• Automated PyPI publishing\n"
        f"• GitHub release creation\n"
        f"• Installation verification\n\n"
        f"[yellow]📋 Monitor progress at:[/yellow]\n"
        f"https://github.com/robertmeisner/improved-sdd/actions",
        title="Publishing Automation",
        border_style="green"
    ))

@app.callback()
def main(
    version: bool = typer.Option(False, "--version", help="Show tool version")
):
    """Version management utility for improved-sdd."""
    if version:
        console.print("bump-version 1.0.0")
        raise typer.Exit()

@app.command()
def current():
    """Show current package version."""
    show_banner()
    
    try:
        version = get_current_version()
        major, minor, patch, prerelease, build = parse_version(version)
        
        version_table = Table(title="Current Version Information", show_header=False)
        version_table.add_column("Field", style="bold cyan")
        version_table.add_column("Value", style="bright_green")
        
        version_table.add_row("Current Version", f"[bold]{version}[/bold]")
        version_table.add_row("Major", str(major))
        version_table.add_row("Minor", str(minor))
        version_table.add_row("Patch", str(patch))
        
        if prerelease:
            version_table.add_row("Prerelease", prerelease)
        if build:
            version_table.add_row("Build", build)
        
        console.print(version_table)
        
        # Show what next versions would be
        console.print()
        next_table = Table(title="Available Version Bumps", show_header=True)
        next_table.add_column("Type", style="bold cyan")
        next_table.add_column("Next Version", style="bright_blue")
        next_table.add_column("Use Case", style="dim")
        
        next_major = bump_version_part(version, VersionPart.major)
        next_minor = bump_version_part(version, VersionPart.minor)
        next_patch = bump_version_part(version, VersionPart.patch)
        
        next_table.add_row("major", next_major, "Breaking changes")
        next_table.add_row("minor", next_minor, "New features")
        next_table.add_row("patch", next_patch, "Bug fixes")
        
        console.print(next_table)
        
    except Exception as e:
        console.print(f"[red]ERROR: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def bump(
    part: VersionPart = typer.Argument(help="Version part to bump"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would happen without making changes"),
    message: str = typer.Option("", "--message", "-m", help="Custom commit message")
):
    """Bump version part (major.minor.patch)."""
    show_banner()
    
    try:
        current_version = get_current_version()
        new_version = bump_version_part(current_version, part)
        
        console.print(f"[bold]Version Bump: {part.title()}[/bold]")
        console.print(f"Current: [red]{current_version}[/red] → New: [green]{new_version}[/green]")
        console.print()
        
        if dry_run:
            console.print("[yellow]🔍 DRY RUN MODE - No changes will be made[/yellow]")
            console.print()
            console.print("[dim]Would update pyproject.toml with:[/dim]")
            console.print(f"[dim]version = \"{new_version}\"[/dim]")
            console.print()
            show_next_steps(new_version)
        else:
            # Confirm the action
            confirm = typer.confirm(
                f"Update version from {current_version} to {new_version}?"
            )
            
            if not confirm:
                console.print("[yellow]Version bump cancelled[/yellow]")
                raise typer.Exit()
            
            # Update the version
            update_version_file(new_version)
            
            console.print()
            show_next_steps(new_version)
            
    except Exception as e:
        console.print(f"[red]ERROR: {e}[/red]")
        raise typer.Exit(1)

@app.command()
def validate(
    version_string: str = typer.Argument(help="Version string to validate")
):
    """Validate a version string format."""
    show_banner()
    
    console.print(f"[bold]Validating version: {version_string}[/bold]")
    console.print()
    
    if validate_version(version_string):
        major, minor, patch, prerelease, build = parse_version(version_string)
        
        console.print("[green]SUCCESS: Valid semantic version![/green]")
        console.print()
        
        components_table = Table(title="Version Components", show_header=False)
        components_table.add_column("Component", style="bold cyan")
        components_table.add_column("Value", style="bright_green")
        
        components_table.add_row("Major", str(major))
        components_table.add_row("Minor", str(minor))
        components_table.add_row("Patch", str(patch))
        
        if prerelease:
            components_table.add_row("Prerelease", prerelease)
        if build:
            components_table.add_row("Build", build)
        
        console.print(components_table)
    else:
        console.print("[red]ERROR: Invalid version format![/red]")
        console.print()
        console.print("[yellow]📋 Valid semantic version examples:[/yellow]")
        console.print("• 1.0.0")
        console.print("• 2.1.3")
        console.print("• 1.0.0-alpha.1")
        console.print("• 1.0.0-beta.2+20230101")
        console.print("• 1.2.3-rc.1+build.123")
        raise typer.Exit(1)

@app.command()
def info():
    """Show detailed information about version management."""
    show_banner()
    
    info_content = """
[bold cyan]Version Management Guide[/bold cyan]

[bold]Semantic Versioning (SemVer):[/bold]
• [green]MAJOR[/green]: Breaking changes (incompatible API changes)
• [yellow]MINOR[/yellow]: New features (backward-compatible functionality)
• [blue]PATCH[/blue]: Bug fixes (backward-compatible bug fixes)

[bold]Prerelease Versions:[/bold]
• [dim]alpha[/dim]: Early development phase
• [dim]beta[/dim]: Feature complete, testing phase  
• [dim]rc[/dim]: Release candidate

[bold]Publishing Workflow:[/bold]
1. [cyan]bump version[/cyan]: Update package version
2. [cyan]git tag[/cyan]: Create version tag (v1.2.3)
3. [cyan]git push[/cyan]: Push tag to trigger publishing
4. [cyan]automation[/cyan]: GitHub Actions handles PyPI publishing

[bold]Examples:[/bold]
• [green]bump major[/green] → 1.0.0 → 2.0.0 (breaking changes)
• [yellow]bump minor[/yellow] → 1.0.0 → 1.1.0 (new features)
• [blue]bump patch[/blue] → 1.0.0 → 1.0.1 (bug fixes)

[bold]Useful Commands:[/bold]
• [cyan]current[/cyan]: Show current version
• [cyan]bump patch --dry-run[/cyan]: Preview patch bump
• [cyan]validate 1.2.3[/cyan]: Validate version format
"""
    
    console.print(Panel(info_content, title="📚 Documentation", border_style="blue"))

if __name__ == "__main__":
    app()