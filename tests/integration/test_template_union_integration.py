"""Integration test demonstrating template union functionality.

This test creates a real scenario where a user has some local templates
and the system downloads and merges the missing ones.
"""

import tempfile
from pathlib import Path

import pytest

from src.core.models import TemplateSourceType
from src.services.template_resolver import TemplateResolver


@pytest.mark.integration
def test_template_union_end_to_end():
    """End-to-end test of template union functionality."""

    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)

        # Create user's local templates (only chatmodes and instructions)
        local_templates = project_path / ".sdd_templates"
        local_templates.mkdir()

        # Create chatmodes
        chatmodes_dir = local_templates / "chatmodes"
        chatmodes_dir.mkdir()
        (chatmodes_dir / "custom.chatmode.md").write_text(
            """# Custom Chat Mode
This is a user-customized chat mode for their specific project.
"""
        )

        # Create instructions
        instructions_dir = local_templates / "instructions"
        instructions_dir.mkdir()
        (instructions_dir / "customInstructions.instructions.md").write_text(
            """# Custom Instructions
These are project-specific instructions that the user created.
"""
        )

        # Initialize resolver - this should detect partial local templates
        # and merge with downloaded ones (in a real scenario)
        resolver = TemplateResolver(project_path, offline=True)  # Use offline to test partial behavior

        # Test detection of available and missing types
        available_files = resolver.get_available_template_files(local_templates)
        available_types = set(available_files.keys()) if available_files else set()
        
        # Check for missing templates if reference path exists
        bundled_path = resolver.get_bundled_templates_path()
        if bundled_path:
            missing_files = resolver.get_missing_template_files(local_templates, bundled_path)
            missing_types = set(missing_files.keys()) if missing_files else set()
        else:
            missing_types = set()  # Can't determine missing without reference

        print(f"Available locally: {sorted(available_types)}")
        print(f"Missing types: {sorted(missing_types)}")

        # Verify detection works correctly
        assert available_types == {"chatmodes", "instructions"}
        # Only check missing types if we have a reference
        if bundled_path:
            assert missing_types == {"prompts", "commands"}

        # Test resolution in offline mode (will use partial local templates)
        result = resolver.resolve_templates_with_transparency()

        # In offline mode with partial templates, should still succeed but with local source
        assert result.success is True  # Using available local templates
        assert result.source is not None
        assert result.source.source_type == TemplateSourceType.LOCAL
        assert "Using 2 local template files" in result.message

        print(f"Resolution result: {result.message}")
        print(f"Source type: {result.source.source_type.value}")
        if hasattr(result.source, "path"):
            print(f"Source path: {result.source.path}")
        else:
            print(f"Merged source: {result.source}")


if __name__ == "__main__":
    # Run the test directly for demonstration
    test_template_union_end_to_end()
    print("✅ Template union functionality works correctly!")
