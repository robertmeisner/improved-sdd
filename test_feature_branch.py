#!/usr/bin/env python3
"""Test script to verify GitLab Flow templates can be downloaded from feature branch."""

import asyncio
import tempfile
from pathlib import Path

from src.services.github_downloader import GitHubDownloader
from src.services.template_resolver import TemplateResolver


async def test_feature_branch_download():
    """Test downloading templates from the feature branch."""
    print("🧪 Testing GitLab Flow template download from feature branch...")
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        print(f"📁 Using temporary directory: {temp_path}")
        
        # Create GitHub downloader for feature branch
        downloader = GitHubDownloader(
            repo_owner="robertmeisner",
            repo_name="improved-sdd", 
            branch="feature/spec-gitlab-flow-integration"
        )
        
        print(f"📦 Configured downloader for: {downloader.repo_owner}/{downloader.repo_name}@{downloader.branch}")
        print(f"🌐 Archive URL pattern: https://github.com/{downloader.repo_owner}/{downloader.repo_name}/archive/refs/heads/{downloader.branch}.zip")
        
        try:
            # Download templates from feature branch
            print("⬇️  Downloading templates from feature branch...")
            result = await downloader.download_templates(temp_path)
            
            print(f"✅ Download successful!")
            print(f"📄 Source type: {result.source_type}")
            print(f"📂 Downloaded to: {result.path}")
            
            # Check for GitLab Flow templates specifically
            gitlab_flow_dir = temp_path / "gitlab-flow"
            if gitlab_flow_dir.exists():
                print(f"🎯 GitLab Flow templates found!")
                gitlab_files = list(gitlab_flow_dir.rglob("*.md"))
                for file in gitlab_files:
                    print(f"   📝 {file.relative_to(temp_path)}")
            else:
                print(f"⚠️  GitLab Flow directory not found, checking structure...")
                for item in temp_path.rglob("*gitlab*"):
                    print(f"   📁 {item.relative_to(temp_path)}")
            
            # Test template resolution with feature branch
            print("\n🔍 Testing template resolution with feature branch...")
            resolver = TemplateResolver(project_path=temp_path)
            resolver.offline = False  # Enable online mode
            
            # Test resolution - this should use our feature branch templates
            resolution_result = resolver.resolve_templates_with_transparency()
            print(f"📊 Resolution result: {resolution_result.success}")
            print(f"💬 Message: {resolution_result.message}")
            
            if resolution_result.source:
                print(f"📦 Final source type: {resolution_result.source.source_type}")
                if hasattr(resolution_result.source, 'path'):
                    available_types = list((resolution_result.source.path).iterdir())
                    print(f"📂 Available template types: {[d.name for d in available_types if d.is_dir()]}")
            
            return True
            
        except Exception as e:
            print(f"❌ Download failed: {e}")
            print(f"🔍 Error type: {type(e).__name__}")
            return False


def test_url_construction():
    """Test that the URL construction works correctly for the feature branch."""
    print("\n🔧 Testing URL construction...")
    
    downloader = GitHubDownloader(
        repo_owner="robertmeisner",
        repo_name="improved-sdd", 
        branch="feature/spec-gitlab-flow-integration"
    )
    
    expected_url = "https://github.com/robertmeisner/improved-sdd/archive/refs/heads/feature/spec-gitlab-flow-integration.zip"
    print(f"📋 Expected URL: {expected_url}")
    print(f"⚙️  Repo: {downloader.repo_owner}/{downloader.repo_name}")
    print(f"🌿 Branch: {downloader.branch}")
    
    # Test URL validation
    import urllib.parse
    parsed = urllib.parse.urlparse(expected_url)
    print(f"✅ URL is well-formed: {parsed.scheme and parsed.netloc and parsed.path}")


if __name__ == "__main__":
    print("🚀 GitLab Flow Feature Branch Test")
    print("=" * 50)
    
    # Test URL construction first
    test_url_construction()
    
    # Test actual download
    try:
        result = asyncio.run(test_feature_branch_download())
        if result:
            print("\n🎉 All tests passed! GitLab Flow templates accessible from feature branch.")
        else:
            print("\n💥 Tests failed! Check error messages above.")
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user.")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")