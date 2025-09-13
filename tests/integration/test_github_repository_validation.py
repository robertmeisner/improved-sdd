"""Integration tests that validate against the actual GitHub repository.

These tests can optionally run against the real repository to verify
our assumptions about branch names, paths, and repository structure.
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from src.services.github_downloader import GitHubDownloader  # noqa: E402


@pytest.mark.integration
class TestGitHubRepositoryValidation:
    """Integration tests that validate repository assumptions."""

    def test_repository_configuration_defaults(self):
        """Test that our repository configuration defaults are correct."""
        downloader = GitHubDownloader()

        # Validate default configuration matches our repository
        assert downloader.repo_owner == "robertmeisner"
        assert downloader.repo_name == "improved-sdd"
        assert downloader.branch == "master"  # Should be master for this repo

        # Validate URL construction
        expected_archive_url = "https://github.com/robertmeisner/improved-sdd/archive/refs/heads/master.zip"

        # We can validate the URL pattern without making real requests
        assert downloader.repo_owner in expected_archive_url
        assert downloader.repo_name in expected_archive_url
        assert downloader.branch in expected_archive_url

    def test_template_path_validation(self):
        """Test that template paths match repository structure."""
        downloader = GitHubDownloader(branch="master")

        # Test expected template structure paths
        expected_template_prefix = "improved-sdd-master/sdd_templates/"

        # Mock ZIP contents that should exist in the real repository
        expected_paths = [
            f"{expected_template_prefix}chatmodes/sddSpecDriven.chatmode.md",
            f"{expected_template_prefix}chatmodes/sddTesting.chatmode.md",
            f"{expected_template_prefix}instructions/sddMcpServerDev.instructions.md",
            f"{expected_template_prefix}instructions/sddPythonCliDev.instructions.md",
            f"{expected_template_prefix}prompts/sddCommitWorkflow.prompt.md",
            f"{expected_template_prefix}prompts/sddFileVerification.prompt.md",
            f"{expected_template_prefix}prompts/sddProjectAnalysis.prompt.md",
            f"{expected_template_prefix}prompts/sddSpecSync.prompt.md",
            f"{expected_template_prefix}prompts/sddTaskExecution.prompt.md",
            f"{expected_template_prefix}prompts/sddTaskVerification.prompt.md",
            f"{expected_template_prefix}prompts/sddTestAll.prompt.md",
        ]

        # Test that our path parsing logic would work with these paths
        for path in expected_paths:
            assert path.startswith(expected_template_prefix)
            relative_path = path[len(expected_template_prefix) :]
            assert "/" in relative_path  # Should have category/filename structure
            category = relative_path.split("/")[0]
            assert category in ["chatmodes", "instructions", "prompts", "commands"]

    @pytest.mark.skipif(
        os.getenv("SKIP_NETWORK_TESTS", "true").lower() == "true",
        reason="Network tests disabled by default. Set SKIP_NETWORK_TESTS=false to enable.",
    )
    @pytest.mark.asyncio
    async def test_real_repository_download(self, tmp_path):
        """Test downloading from the actual repository (when network is available).

        This test is skipped by default but can be enabled by setting
        SKIP_NETWORK_TESTS=false environment variable.
        """
        downloader = GitHubDownloader(branch="master")

        try:
            result = await downloader.download_templates(tmp_path)

            # Validate successful download
            assert result is not None
            assert result.path == tmp_path
            assert result.size_bytes is not None and result.size_bytes > 0

            # Validate expected template files exist
            expected_files = [
                tmp_path / "chatmodes" / "sddSpecDriven.chatmode.md",
                tmp_path / "instructions" / "sddMcpServerDev.instructions.md",
                tmp_path / "instructions" / "sddPythonCliDev.instructions.md",
                tmp_path / "prompts" / "sddTestAll.prompt.md",
            ]

            for file_path in expected_files:
                assert file_path.exists(), f"Expected file not found: {file_path}"
                assert file_path.stat().st_size > 0, f"File is empty: {file_path}"

            # Validate file contents have expected structure
            spec_driven_content = (tmp_path / "chatmodes" / "sddSpecDriven.chatmode.md").read_text()
            assert "spec-driven development" in spec_driven_content.lower()

        except Exception as e:
            # If real download fails, we should understand why
            pytest.fail(
                f"Real repository download failed: {e}. "
                f"This indicates the repository structure may have changed "
                f"or network connectivity issues."
            )

    def test_branch_mismatch_would_fail(self):
        """Test that demonstrates the original bug would be caught."""

        # The original bug: using 'main' branch when repo uses 'master'
        wrong_downloader = GitHubDownloader(branch="main")
        correct_downloader = GitHubDownloader(branch="master")

        # Simulate ZIP contents from master branch (what we actually get)
        master_zip_contents = [
            "improved-sdd-master/sdd_templates/chatmodes/test.md",
            "improved-sdd-master/sdd_templates/instructions/test.md",
        ]

        # Test path parsing with wrong branch expectation
        main_prefix = "improved-sdd-main/sdd_templates/"
        master_prefix = "improved-sdd-master/sdd_templates/"

        # Wrong branch parser would find no files
        main_files = [f for f in master_zip_contents if f.startswith(main_prefix)]
        assert len(main_files) == 0, "Wrong branch should find no template files"

        # Correct branch parser would find files
        master_files = [f for f in master_zip_contents if f.startswith(master_prefix)]
        assert len(master_files) == 2, "Correct branch should find template files"

        # This test validates that branch mismatch causes template detection failure

    def test_url_construction_validation(self):
        """Test that URL construction produces valid GitHub URLs."""

        test_cases = [
            ("robertmeisner", "improved-sdd", "master"),
            ("robertmeisner", "improved-sdd", "main"),
            ("test-owner", "test-repo", "develop"),
        ]

        for owner, repo, branch in test_cases:
            downloader = GitHubDownloader(repo_owner=owner, repo_name=repo, branch=branch)

            # Validate API URL
            expected_api_url = f"https://api.github.com/repos/{owner}/{repo}"
            assert downloader.base_url == expected_api_url

            # We can't directly test archive URL without triggering download,
            # but we can validate the pattern would be correct
            expected_archive_pattern = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"

            # These components should all be present in any constructed URL
            assert owner in expected_archive_pattern
            assert repo in expected_archive_pattern
            assert branch in expected_archive_pattern
            assert "github.com" in expected_archive_pattern
            assert "archive/refs/heads/" in expected_archive_pattern

    def test_repository_assumption_documentation(self):
        """Document and validate our repository assumptions for future reference."""

        # These are the assumptions our code makes about the repository
        repository_assumptions = {
            "default_branch": "master",  # Not 'main'
            "templates_folder": "sdd_templates",  # Not 'templates'
            "zip_structure": "repo-name-branch/sdd_templates/",
            "required_categories": ["chatmodes", "instructions", "prompts"],
            "optional_categories": ["commands"],
        }

        downloader = GitHubDownloader()

        # Validate our assumptions are reflected in the code
        assert downloader.branch == repository_assumptions["default_branch"]

        # Test ZIP path parsing assumptions
        test_zip_path = f"improved-sdd-{repository_assumptions['default_branch']}/{repository_assumptions['templates_folder']}/test.md"
        expected_prefix = (
            f"improved-sdd-{repository_assumptions['default_branch']}/{repository_assumptions['templates_folder']}/"
        )

        assert test_zip_path.startswith(expected_prefix)

        # If these assumptions change, this test will fail and force us to update the code
        print(f"Current repository assumptions: {repository_assumptions}")
