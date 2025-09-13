#!/usr/bin/env python3
"""Debug script to check GitLab Flow templates in downloaded content."""

import tempfile
import zipfile
from pathlib import Path
import requests
from rich.console import Console

console = Console()

def check_gitlab_templates():
    """Download and check for gitlab-flow templates."""
    
    # Download the feature branch
    url = "https://github.com/robertmeisner/improved-sdd/archive/refs/heads/feature/spec-gitlab-flow-integration.zip"
    
    console.print(f"[blue]Downloading from:[/blue] {url}")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        zip_path = temp_path / "templates.zip"
        
        # Download
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_bytes = 0
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                total_bytes += len(chunk)
        
        console.print(f"[green]Downloaded {total_bytes} bytes[/green]")
        
        # Extract and examine
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # List all files
            all_files = zip_ref.namelist()
            console.print(f"[blue]Total files in ZIP:[/blue] {len(all_files)}")
            
            # Find templates directory
            template_files = [f for f in all_files if '/templates/' in f]
            console.print(f"[blue]Template files:[/blue] {len(template_files)}")
            
            # Find gitlab-flow specifically
            gitlab_files = [f for f in all_files if 'gitlab' in f.lower()]
            console.print(f"[blue]GitLab-related files:[/blue] {len(gitlab_files)}")
            
            for file in gitlab_files:
                console.print(f"  📄 {file}")
            
            # Check templates structure
            console.print("\n[yellow]Templates directory structure:[/yellow]")
            template_dirs = set()
            for file in template_files:
                parts = file.split('/templates/')
                if len(parts) > 1:
                    subpath = parts[1]
                    if '/' in subpath:
                        dir_name = subpath.split('/')[0]
                        template_dirs.add(dir_name)
            
            for dir_name in sorted(template_dirs):
                console.print(f"  📁 {dir_name}")
                # Count files in this directory
                dir_files = [f for f in template_files if f'/templates/{dir_name}/' in f]
                console.print(f"     ({len(dir_files)} files)")

if __name__ == "__main__":
    check_gitlab_templates()