#!/usr/bin/env python3

import tempfile
from pathlib import Path
from unittest.mock import patch
from typer.testing import CliRunner
from src.improved_sdd_cli import app
from src.services.template_resolver import TemplateResolver

def debug_template_download():
    runner = CliRunner()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Test bundled templates resolution
        resolver = TemplateResolver(temp_path)
        print(f"Script dir: {resolver.script_dir}")
        print(f"Script parent: {resolver.script_dir.parent}")
        bundled_path = resolver.get_bundled_templates_path()
        print(f"Bundled path: {bundled_path}")
        print(f"Bundled exists: {bundled_path.exists() if bundled_path else 'None'}")
        
        # Check workspace .sdd_templates
        workspace_templates = Path("c:/Users/Robert/Documents/Projects/improved-sdd/.sdd_templates")
        print(f"Workspace templates: {workspace_templates}")
        print(f"Workspace templates exists: {workspace_templates.exists()}")
        
        with patch("pathlib.Path.cwd", return_value=temp_path):
            with patch("src.improved_sdd_cli.console_manager.show_banner"):
                result = runner.invoke(
                    app,
                    ["init", "--app-type", "python-cli", "--ai-tools", "github-copilot", "--force"],
                )
                
                print(f"Exit code: {result.exit_code}")
                print(f"Stdout: {result.stdout}")

if __name__ == "__main__":
    debug_template_download()