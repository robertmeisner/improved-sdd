#!/usr/bin/env python3
"""Debug script to check the ZIP structure from feature branch."""

import asyncio
import tempfile
import zipfile
from pathlib import Path

import httpx


async def debug_zip_structure():
    """Download and inspect the ZIP structure."""
    branch = "feature/spec-gitlab-flow-integration"
    url = f"https://github.com/robertmeisner/improved-sdd/archive/refs/heads/{branch}.zip"
    
    print(f"🔍 Downloading ZIP from: {url}")
    
    # Download the ZIP file
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(url)
        if response.status_code != 200:
            print(f"❌ Failed to download: {response.status_code}")
            print(f"📍 Final URL: {response.url}")
            return
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_file:
            temp_file.write(response.content)
            temp_zip_path = Path(temp_file.name)
    
    try:
        # Inspect ZIP contents
        print(f"📦 ZIP file downloaded successfully")
        print(f"📏 Size: {len(response.content)} bytes")
        
        with zipfile.ZipFile(temp_zip_path, 'r') as zip_file:
            all_files = zip_file.namelist()
            print(f"📄 Total files in ZIP: {len(all_files)}")
            
            # Look for files containing 'template'
            template_files = [f for f in all_files if 'template' in f.lower()]
            print(f"\n🎯 Files containing 'template': {len(template_files)}")
            for file in template_files[:10]:  # Show first 10
                print(f"   📝 {file}")
            
            if len(template_files) > 10:
                print(f"   ... and {len(template_files) - 10} more")
            
            # Look for gitlab-flow specifically
            gitlab_files = [f for f in all_files if 'gitlab' in f.lower()]
            print(f"\n🦊 GitLab Flow files: {len(gitlab_files)}")
            for file in gitlab_files:
                print(f"   📝 {file}")
            
            # Check directory structure
            print(f"\n📁 Root level structure:")
            root_items = set()
            for file in all_files[:20]:  # Sample
                parts = file.split('/')
                if len(parts) > 0:
                    root_items.add(parts[0])
            
            for item in sorted(root_items):
                print(f"   📂 {item}/")
            
            # Check for expected prefix
            expected_prefix = f"improved-sdd-{branch.replace('/', '-')}/templates/"
            print(f"\n🔍 Expected prefix: {expected_prefix}")
            
            matching_files = [f for f in all_files if f.startswith(expected_prefix)]
            print(f"📊 Files matching expected prefix: {len(matching_files)}")
            
            if matching_files:
                print("✅ Found matching files:")
                for file in matching_files[:5]:
                    print(f"   📝 {file}")
            else:
                print("❌ No files match expected prefix")
                # Try to find what the actual prefix might be
                template_dirs = [f for f in all_files if f.endswith('/templates/') or '/templates/' in f]
                if template_dirs:
                    print("🔍 Found template directories:")
                    for dir_path in template_dirs[:3]:
                        print(f"   📂 {dir_path}")
    
    finally:
        # Clean up
        temp_zip_path.unlink()


if __name__ == "__main__":
    print("🐛 Debugging Feature Branch ZIP Structure")
    print("=" * 50)
    
    try:
        asyncio.run(debug_zip_structure())
    except Exception as e:
        print(f"💥 Error: {e}")