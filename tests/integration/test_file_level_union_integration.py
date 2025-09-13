"""Integration test demonstrating file-level template union functionality.

This test creates a real scenario where a user has individual template files
and the system downloads and merges the missing files at granular level.
"""

import tempfile
from pathlib import Path

import pytest

from src.core.models import TemplateSourceType
from src.services.template_resolver import TemplateResolver


@pytest.mark.integration
def test_file_level_template_union_end_to_end():
    """End-to-end test of file-level template union functionality."""

    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)

        # Create user's local templates (individual files across different types)
        local_templates = project_path / ".sdd_templates"
        local_templates.mkdir()

        # User has ONE custom prompt
        prompts_dir = local_templates / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "sddCommitWorkflow.prompt.md").write_text(
            """# My Custom Commit Workflow
This is my personalized commit workflow that I've customized for my team.
It includes our specific branching strategy and review process.
"""
        )

        # User has ONE custom chatmode
        chatmodes_dir = local_templates / "chatmodes"
        chatmodes_dir.mkdir()
        (chatmodes_dir / "myProjectMode.chatmode.md").write_text(
            """# My Project-Specific Mode
This chat mode is tailored to my specific project requirements.
It includes context about our architecture and coding standards.
"""
        )

        # User has empty instructions folder (will be ignored)
        instructions_dir = local_templates / "instructions"
        instructions_dir.mkdir()

        # User has NO commands folder at all

        # Initialize resolver - this should detect individual files and merge at file level
        resolver = TemplateResolver(project_path, offline=True)  # Use offline to test file detection

        # Test detection of available files (not just types)
        available_files = resolver.get_available_template_files(local_templates)

        print(f"Available local files: {available_files}")

        # Verify file-level detection works correctly
        expected_local_files = {
            "prompts": {"sddCommitWorkflow.prompt.md"},
            "chatmodes": {"myProjectMode.chatmode.md"}
            # instructions and commands should not appear because they're empty/missing
        }
        assert available_files == expected_local_files

        # Test resolution in offline mode (will use individual local files)
        result = resolver.resolve_templates_with_transparency()

        # Should succeed because we have some files, even if incomplete
        assert result.success is True
        assert result.source is not None
        assert result.source.source_type == TemplateSourceType.LOCAL
        assert "2 local template files" in result.message

        print(f"Resolution result: {result.message}")
        print(f"Source type: {result.source.source_type.value}")

        # Demonstrate the file-level granularity
        print("\nFile-level breakdown:")
        for template_type, files in available_files.items():
            print(f"  {template_type}: {len(files)} file(s)")
            for filename in sorted(files):
                file_path = local_templates / template_type / filename
                first_line = file_path.read_text().split("\n")[0]
                print(f"    - {filename}: {first_line}")

        print(f"\nTotal local template files available: {sum(len(files) for files in available_files.values())}")


@pytest.mark.integration
def test_file_level_union_demonstrates_individual_file_priority():
    """Demonstrate that individual files take priority over downloaded versions."""

    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)

        # Create scenario with overlapping filenames
        local_templates = project_path / ".sdd_templates"
        local_templates.mkdir()

        # User customizes JUST the commit workflow prompt
        prompts_dir = local_templates / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "sddCommitWorkflow.prompt.md").write_text("# LOCAL VERSION - Custom Workflow")

        # Create mock downloaded templates with same filename + additional files
        downloaded_templates = project_path / "downloaded"
        downloaded_templates.mkdir()

        downloaded_prompts = downloaded_templates / "prompts"
        downloaded_prompts.mkdir()
        (downloaded_prompts / "sddCommitWorkflow.prompt.md").write_text("# DOWNLOADED VERSION - Standard Workflow")
        (downloaded_prompts / "sddTaskExecution.prompt.md").write_text("# Downloaded Task Execution")
        (downloaded_prompts / "sddProjectAnalysis.prompt.md").write_text("# Downloaded Project Analysis")

        downloaded_chatmodes = downloaded_templates / "chatmodes"
        downloaded_chatmodes.mkdir()
        (downloaded_chatmodes / "sddSpecDriven.chatmode.md").write_text("# Downloaded Spec Driven")

        # Test file resolution
        resolver = TemplateResolver(project_path)

        local_files = resolver.get_available_template_files(local_templates)
        downloaded_files = resolver.get_available_template_files(downloaded_templates)

        print(f"Local files: {local_files}")
        print(f"Downloaded files: {downloaded_files}")

        # Verify overlap detection
        assert "sddCommitWorkflow.prompt.md" in local_files["prompts"]
        assert "sddCommitWorkflow.prompt.md" in downloaded_files["prompts"]

        # Create merged source to test priority
        from src.core.models import MergedTemplateSource

        merged_source = MergedTemplateSource(
            local_path=local_templates,
            downloaded_path=downloaded_templates,
            local_files=local_files,
            downloaded_files=downloaded_files,
        )

        # Test that local file takes priority
        commit_workflow_source = merged_source.get_file_source("prompts", "sddCommitWorkflow.prompt.md")
        assert commit_workflow_source == local_templates / "prompts" / "sddCommitWorkflow.prompt.md"

        # Verify content to ensure it's the local version
        assert commit_workflow_source is not None
        content = commit_workflow_source.read_text()
        assert "LOCAL VERSION" in content
        assert "DOWNLOADED VERSION" not in content

        # Test that non-overlapping files come from downloaded
        task_execution_source = merged_source.get_file_source("prompts", "sddTaskExecution.prompt.md")
        assert task_execution_source == downloaded_templates / "prompts" / "sddTaskExecution.prompt.md"

        # Get all available files to see final union
        all_files = merged_source.get_all_available_files()
        print(f"Final merged files: {all_files}")

        # Should have 3 prompts total: 1 local (priority) + 2 downloaded unique
        assert len(all_files["prompts"]) == 3
        assert "sddCommitWorkflow.prompt.md" in all_files["prompts"]  # From local
        assert "sddTaskExecution.prompt.md" in all_files["prompts"]  # From downloaded
        assert "sddProjectAnalysis.prompt.md" in all_files["prompts"]  # From downloaded

        print("✅ File-level priority system working correctly!")


if __name__ == "__main__":
    # Run the tests directly for demonstration
    test_file_level_template_union_end_to_end()
    print("\n" + "=" * 70 + "\n")
    test_file_level_union_demonstrates_individual_file_priority()
    print("✅ File-level template union functionality works perfectly!")
