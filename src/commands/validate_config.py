"""Configuration validation command for SDD CLI.

This command provides comprehensive validation of sdd-config.yaml files
with detailed reporting and troubleshooting guidance.
"""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

try:
    # Development/editable install: direct imports from src
    from core.config import ConfigurationLoader, ConfigurationValidator
    from core.exceptions import ValidationError
except (ImportError, ModuleNotFoundError):
    # Production install: relative imports  
    from ..core.config import ConfigurationLoader, ConfigurationValidator
    from ..core.exceptions import ValidationError

console = Console()


def validate_config_command(
    config_path: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c", 
        help="Path to specific config file to validate. Defaults to .sdd_templates/sdd-config.yaml"
    ),
    project_root: Optional[Path] = typer.Option(
        None,
        "--project-root",
        "-p",
        help="Project root directory. Defaults to current directory"
    ),
    show_details: bool = typer.Option(
        False,
        "--details",
        "-d",
        help="Show detailed validation information"
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q", 
        help="Only show errors, suppress warnings and info"
    )
) -> None:
    """Validate SDD configuration files with comprehensive reporting.
    
    This command validates YAML configuration files for syntax, schema compliance,
    and logical consistency. It provides detailed feedback about issues and 
    suggestions for resolution.
    
    Examples:
        improved-sdd validate-config                    # Validate default config
        improved-sdd validate-config --details          # Show detailed validation info
        improved-sdd validate-config -c custom.yaml    # Validate specific file
        improved-sdd validate-config --quiet            # Only show errors
    """
    
    if not quiet:
        console.print(Panel(
            "[bold cyan]SDD Configuration Validation[/bold cyan]\n"
            "Comprehensive validation of sdd-config.yaml files",
            border_style="cyan"
        ))
    
    # Determine paths
    if project_root is None:
        project_root = Path.cwd()
    
    if config_path is None:
        config_path = project_root / ".sdd_templates" / "sdd-config.yaml"
    
    # Validate configuration
    try:
        result = _validate_configuration(config_path, project_root, show_details, quiet)
        
        if result["success"]:
            if not quiet:
                _show_success_summary(result)
            sys.exit(0)
        else:
            _show_failure_summary(result, quiet)
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]Unexpected error during validation: {e}[/red]")
        if show_details:
            import traceback
            console.print("[dim]" + traceback.format_exc() + "[/dim]")
        sys.exit(1)


def _validate_configuration(config_path: Path, project_root: Path, show_details: bool, quiet: bool) -> dict:
    """Perform comprehensive configuration validation."""
    
    # Initialize validator and loader
    validator = ConfigurationValidator()
    loader = ConfigurationLoader()
    
    validation_results = {
        "success": True,
        "config_path": config_path,
        "validation_result": None,
        "hierarchy_result": None,
        "conflicts": [],
        "recommendations": []
    }
    
    if not quiet:
        console.print(f"[blue]Validating configuration at:[/blue] {config_path}")
    
    # Check if file exists
    if not config_path.exists():
        if not quiet:
            console.print(f"[yellow]Local config not found at {config_path}[/yellow]")
            console.print("[blue]Testing configuration hierarchy fallback...[/blue]")
        
        # Test configuration hierarchy
        try:
            hierarchy_config = loader.load_configuration_hierarchy(project_root)
            validation_results["hierarchy_result"] = hierarchy_config
            
            if hierarchy_config:
                if not quiet:
                    console.print("[green]✓ Successfully loaded configuration from hierarchy[/green]")
                _add_recommendation(validation_results, 
                    "Consider creating a local configuration file for project-specific customization",
                    f"Create {config_path} to override default settings")
            else:
                validation_results["success"] = False
                console.print("[red]✗ No configuration available from any source[/red]")
                _add_recommendation(validation_results, 
                    "Create a local configuration file",
                    f"Create {config_path} with basic configuration structure")
                
        except Exception as e:
            validation_results["success"] = False
            console.print(f"[red]✗ Configuration hierarchy loading failed: {e}[/red]")
            
        return validation_results
    
    # Validate specific file
    try:
        content = config_path.read_text(encoding='utf-8')
        result = validator.validate_config(content, str(config_path))
        validation_results["validation_result"] = result
        
        if not quiet:
            _show_validation_details(result, show_details)
        
        # Check for conflicts using configuration manager
        if result.valid and result.parsed_content:
            conflicts = loader.detect_configuration_conflicts(result.parsed_content)
            validation_results["conflicts"] = conflicts
            
            if conflicts and not quiet:
                _show_conflicts(conflicts)
        
        # Determine overall success
        validation_results["success"] = result.valid and len(validation_results["conflicts"]) == 0
        
        # Add recommendations
        _generate_recommendations(validation_results, result)
        
    except Exception as e:
        validation_results["success"] = False
        console.print(f"[red]✗ Failed to validate {config_path}: {e}[/red]")
        
    return validation_results


def _show_validation_details(result, show_details: bool) -> None:
    """Display validation result details."""
    
    # Overall status
    if result.valid:
        if result.has_warnings():
            console.print("[yellow]⚠ Configuration valid with warnings[/yellow]")
        else:
            console.print("[green]✓ Configuration is valid[/green]")
    else:
        console.print("[red]✗ Configuration has errors[/red]")
    
    # Show summary
    console.print(f"[dim]Status: {result.summary()}[/dim]")
    
    # Show errors
    if result.has_errors():
        console.print("\n[red bold]Errors:[/red bold]")
        for error in result.errors:
            console.print(f"  [red]• {error}[/red]")
    
    # Show warnings by category
    if result.has_warnings():
        console.print("\n[yellow bold]Warnings:[/yellow bold]")
        
        if show_details:
            # Group warnings by category
            categories = ["syntax", "schema", "duplicate", "empty", "pattern"]
            for category in categories:
                cat_warnings = result.get_warnings_by_category(category)
                if cat_warnings:
                    console.print(f"\n[yellow]  {category.title()} Issues:[/yellow]")
                    for warning in cat_warnings:
                        console.print(f"    [yellow]• {warning}[/yellow]")
        else:
            # Show all warnings together
            for warning in result.warnings:
                console.print(f"  [yellow]• {warning}[/yellow]")
    
    # Show schema validation status
    if show_details and hasattr(result, 'schema_valid'):
        if result.schema_valid:
            console.print("\n[green]✓ Pydantic schema validation passed[/green]")
        elif result.schema_valid is False:
            console.print("\n[yellow]⚠ Pydantic schema validation failed (see warnings above)[/yellow]")
        else:
            console.print("\n[blue]ℹ Pydantic not available for schema validation[/blue]")


def _show_conflicts(conflicts: list) -> None:
    """Display configuration conflicts."""
    
    console.print("\n[red bold]Configuration Conflicts:[/red bold]")
    for conflict in conflicts:
        console.print(f"  [red]• {conflict}[/red]")


def _add_recommendation(results: dict, title: str, description: str) -> None:
    """Add a recommendation to the results."""
    results["recommendations"].append({
        "title": title,
        "description": description
    })


def _generate_recommendations(results: dict, validation_result) -> None:
    """Generate helpful recommendations based on validation results."""
    
    if not validation_result.valid:
        _add_recommendation(results,
            "Fix configuration errors",
            "Resolve all syntax and structural errors before proceeding")
    
    if validation_result.has_warnings():
        duplicate_warnings = validation_result.get_warnings_by_category("duplicate")
        empty_warnings = validation_result.get_warnings_by_category("empty")
        pattern_warnings = validation_result.get_warnings_by_category("pattern")
        
        if duplicate_warnings:
            _add_recommendation(results,
                "Resolve duplicate file entries",
                "Remove duplicate files from AI tool managed_files lists to avoid conflicts")
        
        if empty_warnings:
            _add_recommendation(results,
                "Review empty file lists",
                "Consider adding files to empty managed_files categories or removing unused tools")
        
        if pattern_warnings:
            _add_recommendation(results,
                "Fix file naming patterns",
                "Ensure all managed files follow valid naming conventions")
    
    if results["conflicts"]:
        _add_recommendation(results,
            "Resolve AI tool file conflicts",
            "Ensure each file is managed by only one AI tool to prevent deletion conflicts")
    
    # Always add this helpful recommendation
    _add_recommendation(results,
        "Review the configuration documentation",
        "Check the GitHub repository for configuration examples and best practices")


def _show_success_summary(results: dict) -> None:
    """Show success summary with recommendations."""
    
    console.print("\n[green bold]✓ Configuration Validation Successful[/green bold]")
    
    if results["recommendations"]:
        console.print("\n[blue bold]Recommendations:[/blue bold]")
        for rec in results["recommendations"]:
            console.print(f"  [blue]• {rec['title']}[/blue]")
            console.print(f"    [dim]{rec['description']}[/dim]")


def _show_failure_summary(results: dict, quiet: bool) -> None:
    """Show failure summary with troubleshooting guidance."""
    
    if not quiet:
        console.print("\n[red bold]✗ Configuration Validation Failed[/red bold]")
        
        # Show troubleshooting guide
        troubleshooting = Panel(
            "[bold]Troubleshooting Guide:[/bold]\n\n"
            "1. [cyan]Check YAML syntax[/cyan] - Ensure proper indentation and quotes\n"
            "2. [cyan]Validate structure[/cyan] - Verify all required fields are present\n"
            "3. [cyan]Review file lists[/cyan] - Check for duplicates and valid patterns\n"
            "4. [cyan]Test with defaults[/cyan] - Remove local config to test with defaults\n"
            "5. [cyan]Check examples[/cyan] - Review GitHub repository for configuration examples",
            title="Troubleshooting",
            border_style="yellow"
        )
        console.print(troubleshooting)
        
        if results["recommendations"]:
            console.print("\n[red bold]Immediate Actions:[/red bold]")
            for rec in results["recommendations"]:
                console.print(f"  [red]• {rec['title']}[/red]")
                console.print(f"    [dim]{rec['description']}[/dim]")