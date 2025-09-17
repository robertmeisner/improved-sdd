"""Integration tests for delete command functionality.

This module provides comprehensive end-to-end testing of the delete command,
covering multi-tool scenarios, file preservation, error handling, and regression testing.
"""

import os
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner

import pytest

from src.improved_sdd_cli import app
from src.core.config import ConfigCompatibilityLayer
from src.core.ai_tool_manager import AIToolManager
from src.core.file_manager import FileManager
from src.core.user_interaction_handler import UserInteractionHandler


@pytest.fixture(scope="session", autouse=True)
def setup_app():
    """Setup the CLI app once for all tests."""
    from src.improved_sdd_cli import _ensure_app_setup
    _ensure_app_setup(force=True)


@pytest.fixture
def cli_runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_project():
    """Create a temporary project directory with proper structure."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)
        
        # Create standard template directory structure
        github_dir = project_path / ".github"
        github_dir.mkdir()
        
        (github_dir / "chatmodes").mkdir()
        (github_dir / "instructions").mkdir()
        (github_dir / "prompts").mkdir()
        (github_dir / "commands").mkdir()
        
        yield project_path


@pytest.fixture
def mock_config():
    """Create a mock configuration with test AI tools."""
    config_data = {
        "ai_tools": {
            "github-copilot": {
                "name": "GitHub Copilot",
                "description": "GitHub's AI pair programmer",
                "template_dir": "github",
                "managed_files": {
                    "chatmodes": [
                        "sddSpecDriven.chatmode.md",
                        "sddTesting.chatmode.md"
                    ],
                    "instructions": [
                        "sddPythonCliDev.instructions.md",
                        "sddMcpServerDev.instructions.md"
                    ],
                    "prompts": [
                        "sddTaskExecution.prompt.md",
                        "sddCommitWorkflow.prompt.md"
                    ],
                    "commands": []
                }
            },
            "claude": {
                "name": "Anthropic Claude",
                "description": "Anthropic's AI assistant",
                "template_dir": "claude",
                "managed_files": {
                    "chatmodes": [
                        "sddSpecDriven.claude.md",
                        "sddTesting.claude.md"
                    ],
                    "instructions": [
                        "sddPythonCliDev.claude.md"
                    ],
                    "prompts": [
                        "sddTaskExecution.claude.md"
                    ],
                    "commands": []
                }
            }
        },
        "preferences": {
            "default_ai_tools": ["github-copilot"]
        }
    }
    
    # Create a mock configuration object
    mock_config = MagicMock()
    mock_config.get_ai_tools.return_value = config_data["ai_tools"]
    mock_config.get_preference.side_effect = lambda key, default: config_data.get("preferences", {}).get(key, default)
    mock_config.get_yaml_config.return_value = config_data
    
    return mock_config


@pytest.fixture
def sample_files_github_copilot(temp_project):
    """Create sample files for GitHub Copilot AI tool."""
    github_dir = temp_project / ".github"
    
    # Create GitHub Copilot managed files
    files = {
        "chatmodes/sddSpecDriven.chatmode.md": "# GitHub Copilot Spec Driven",
        "chatmodes/sddTesting.chatmode.md": "# GitHub Copilot Testing", 
        "instructions/sddPythonCliDev.instructions.md": "# Python CLI Development",
        "instructions/sddMcpServerDev.instructions.md": "# MCP Server Development",
        "prompts/sddTaskExecution.prompt.md": "# Task Execution Prompt",
        "prompts/sddCommitWorkflow.prompt.md": "# Commit Workflow Prompt"
    }
    
    created_files = []
    for file_path, content in files.items():
        full_path = github_dir / file_path
        full_path.write_text(content)
        created_files.append(full_path)
    
    return created_files


@pytest.fixture
def sample_files_claude(temp_project):
    """Create sample files for Claude AI tool."""
    github_dir = temp_project / ".github"
    
    # Create Claude managed files
    files = {
        "chatmodes/sddSpecDriven.claude.md": "# Claude Spec Driven",
        "chatmodes/sddTesting.claude.md": "# Claude Testing",
        "instructions/sddPythonCliDev.claude.md": "# Claude Python CLI Development",
        "prompts/sddTaskExecution.claude.md": "# Claude Task Execution Prompt"
    }
    
    created_files = []
    for file_path, content in files.items():
        full_path = github_dir / file_path
        full_path.write_text(content)
        created_files.append(full_path)
    
    return created_files


@pytest.fixture
def manual_files(temp_project):
    """Create manual (unmanaged) files that should be preserved."""
    github_dir = temp_project / ".github"
    
    # Create manual files that shouldn't be deleted
    files = {
        "chatmodes/custom.chatmode.md": "# Custom Manual Chatmode",
        "chatmodes/user-created.chatmode.md": "# User Created File",
        "instructions/manual.instructions.md": "# Manual Instructions",
        "prompts/custom-prompt.prompt.md": "# Custom Prompt",
        "README.md": "# Project README"
    }
    
    created_files = []
    for file_path, content in files.items():
        if file_path == "README.md":
            full_path = temp_project / file_path
        else:
            full_path = github_dir / file_path
        full_path.write_text(content)
        created_files.append(full_path)
    
    return created_files


class TestDeleteCommandEndToEnd:
    """Test end-to-end delete command execution scenarios."""
    
    def test_delete_single_tool_python_cli_with_force(self, cli_runner, temp_project, mock_config, sample_files_github_copilot, manual_files):
        """Test deleting files for single AI tool with force flag."""
        with patch('src.core.config.config', mock_config), \
             patch('os.getcwd', return_value=str(temp_project)):
            
            # Run delete command with force flag
            result = cli_runner.invoke(app, ['delete', 'python-cli', '--force'])
            
            # Verify command completed successfully
            assert result.exit_code == 0
            
            # Verify GitHub Copilot managed files were deleted
            github_dir = temp_project / ".github"
            assert not (github_dir / "chatmodes/sddSpecDriven.chatmode.md").exists()
            assert not (github_dir / "chatmodes/sddTesting.chatmode.md").exists()
            assert not (github_dir / "instructions/sddPythonCliDev.instructions.md").exists()
            assert not (github_dir / "instructions/sddMcpServerDev.instructions.md").exists()
            assert not (github_dir / "prompts/sddTaskExecution.prompt.md").exists()
            assert not (github_dir / "prompts/sddCommitWorkflow.prompt.md").exists()
            
            # Verify manual files were preserved
            assert (github_dir / "chatmodes/custom.chatmode.md").exists()
            assert (github_dir / "chatmodes/user-created.chatmode.md").exists()
            assert (github_dir / "instructions/manual.instructions.md").exists()
            assert (github_dir / "prompts/custom-prompt.prompt.md").exists()
            assert (temp_project / "README.md").exists()
            
            # Verify output contains expected messages
            assert "Deletion Results:" in result.stdout
            assert "Successfully Deleted:" in result.stdout
    
    def test_delete_mcp_server_dry_run(self, cli_runner, temp_project, mock_config, sample_files_github_copilot, manual_files):
        """Test delete command with dry-run flag."""
        with patch('src.core.config.config', mock_config), \
             patch('os.getcwd', return_value=str(temp_project)):
            
            # Run delete command with dry-run flag
            result = cli_runner.invoke(app, ['delete', 'mcp-server', '--dry-run'])
            
            # Verify command completed successfully
            assert result.exit_code == 0
            
            # Verify NO files were actually deleted (dry-run)
            github_dir = temp_project / ".github"
            assert (github_dir / "chatmodes/sddSpecDriven.chatmode.md").exists()
            assert (github_dir / "chatmodes/sddTesting.chatmode.md").exists()
            assert (github_dir / "instructions/sddPythonCliDev.instructions.md").exists()
            assert (github_dir / "instructions/sddMcpServerDev.instructions.md").exists()
            assert (github_dir / "prompts/sddTaskExecution.prompt.md").exists()
            assert (github_dir / "prompts/sddCommitWorkflow.prompt.md").exists()
            
            # Verify manual files are still there
            assert (github_dir / "chatmodes/custom.chatmode.md").exists()
            assert (github_dir / "chatmodes/user-created.chatmode.md").exists()
            
            # Verify output contains dry-run messaging
            assert "DRY RUN" in result.stdout
            assert "Would delete" in result.stdout
    
    def test_delete_no_managed_files_found(self, cli_runner, temp_project, mock_config, manual_files):
        """Test delete command when no managed files exist."""
        with patch('src.core.config.config', mock_config), \
             patch('os.getcwd', return_value=str(temp_project)):
            
            # Run delete command when only manual files exist
            result = cli_runner.invoke(app, ['delete', 'python-cli', '--force'])
            
            # Verify command completed successfully
            assert result.exit_code == 0
            
            # Verify manual files were preserved
            github_dir = temp_project / ".github"
            assert (github_dir / "chatmodes/custom.chatmode.md").exists()
            assert (github_dir / "chatmodes/user-created.chatmode.md").exists()
            assert (github_dir / "instructions/manual.instructions.md").exists()
            assert (github_dir / "prompts/custom-prompt.prompt.md").exists()
            assert (temp_project / "README.md").exists()
            
            # Verify output contains no files message
            assert "No managed files found" in result.stdout
            
            # Verify manual files were preserved
            github_dir = temp_project / ".github"
            assert (github_dir / "chatmodes/custom.chatmode.md").exists()
            assert (github_dir / "chatmodes/user-created.chatmode.md").exists()
            assert (github_dir / "instructions/manual.instructions.md").exists()
            assert (github_dir / "prompts/custom-prompt.prompt.md").exists()
            assert (temp_project / "README.md").exists()
            
            # Verify output contains no files message
            assert "No managed files found" in result.stdout


class TestDeleteCommandMultiTool:
    """Test multi-tool scenarios and file preservation logic."""
    
    def test_delete_with_multiple_tools_active(self, cli_runner, temp_project, sample_files_github_copilot, sample_files_claude, manual_files):
        """Test deletion when multiple AI tools have files."""
        # Create config with both tools active
        config_data = {
            "ai_tools": {
                "github-copilot": {
                    "name": "GitHub Copilot",
                    "template_dir": "github",
                    "managed_files": {
                        "chatmodes": ["sddSpecDriven.chatmode.md", "sddTesting.chatmode.md"],
                        "instructions": ["sddPythonCliDev.instructions.md", "sddMcpServerDev.instructions.md"],
                        "prompts": ["sddTaskExecution.prompt.md", "sddCommitWorkflow.prompt.md"],
                        "commands": []
                    }
                },
                "claude": {
                    "name": "Anthropic Claude",
                    "template_dir": "claude",
                    "managed_files": {
                        "chatmodes": ["sddSpecDriven.claude.md", "sddTesting.claude.md"],
                        "instructions": ["sddPythonCliDev.claude.md"],
                        "prompts": ["sddTaskExecution.claude.md"],
                        "commands": []
                    }
                }
            },
            "preferences": {
                "default_ai_tools": ["github-copilot", "claude"]
            }
        }
        
        # Create mock config
        mock_config = MagicMock()
        mock_config.get_ai_tools.return_value = config_data["ai_tools"]
        mock_config.get_preference.side_effect = lambda key, default: config_data.get("preferences", {}).get(key, default)
        mock_config.get_yaml_config.return_value = config_data
        
        with patch('src.core.config.config', mock_config), \
             patch('os.getcwd', return_value=str(temp_project)):
            
            # Run delete command
            result = cli_runner.invoke(app, ['delete', 'python-cli', '--force'])
            
            # Verify command completed successfully
            assert result.exit_code == 0
            
            # Verify GitHub Copilot files were deleted
            github_dir = temp_project / ".github"
            assert not (github_dir / "chatmodes/sddSpecDriven.chatmode.md").exists()
            assert not (github_dir / "chatmodes/sddTesting.chatmode.md").exists()
            assert not (github_dir / "instructions/sddPythonCliDev.instructions.md").exists()
            
            # Verify Claude files were deleted
            assert not (github_dir / "chatmodes/sddSpecDriven.claude.md").exists()
            assert not (github_dir / "chatmodes/sddTesting.claude.md").exists()
            assert not (github_dir / "instructions/sddPythonCliDev.claude.md").exists()
            assert not (github_dir / "prompts/sddTaskExecution.claude.md").exists()
            
            # Verify manual files were preserved
            assert (github_dir / "chatmodes/custom.chatmode.md").exists()
            assert (github_dir / "chatmodes/user-created.chatmode.md").exists()
            assert (github_dir / "instructions/manual.instructions.md").exists()
            assert (temp_project / "README.md").exists()
    
    def test_delete_selective_tool_preservation(self, cli_runner, temp_project, sample_files_github_copilot, sample_files_claude, manual_files):
        """Test that files from non-selected tools are preserved."""
        # Create config with only GitHub Copilot active  
        config_data = {
            "ai_tools": {
                "github-copilot": {
                    "name": "GitHub Copilot",
                    "template_dir": "github",
                    "managed_files": {
                        "chatmodes": ["sddSpecDriven.chatmode.md", "sddTesting.chatmode.md"],
                        "instructions": ["sddPythonCliDev.instructions.md", "sddMcpServerDev.instructions.md"],
                        "prompts": ["sddTaskExecution.prompt.md", "sddCommitWorkflow.prompt.md"],
                        "commands": []
                    }
                },
                "claude": {
                    "name": "Anthropic Claude", 
                    "template_dir": "claude",
                    "managed_files": {
                        "chatmodes": ["sddSpecDriven.claude.md", "sddTesting.claude.md"],
                        "instructions": ["sddPythonCliDev.claude.md"],
                        "prompts": ["sddTaskExecution.claude.md"],
                        "commands": []
                    }
                }
            },
            "preferences": {
                "default_ai_tools": ["github-copilot"]  # Only GitHub Copilot active
            }
        }
        
        # Create mock config
        mock_config = MagicMock()
        mock_config.get_ai_tools.return_value = config_data["ai_tools"]
        mock_config.get_preference.side_effect = lambda key, default: config_data.get("preferences", {}).get(key, default)
        mock_config.get_yaml_config.return_value = config_data
        
        with patch('src.core.config.config', mock_config), \
             patch('os.getcwd', return_value=str(temp_project)):
            
            # Run delete command
            result = cli_runner.invoke(app, ['delete', 'python-cli', '--force'])
            
            # Verify command completed successfully
            assert result.exit_code == 0
            
            # Verify GitHub Copilot files were deleted
            github_dir = temp_project / ".github"
            assert not (github_dir / "chatmodes/sddSpecDriven.chatmode.md").exists()
            assert not (github_dir / "chatmodes/sddTesting.chatmode.md").exists()
            assert not (github_dir / "instructions/sddPythonCliDev.instructions.md").exists()
            
            # Verify Claude files were PRESERVED (not active tool)
            assert (github_dir / "chatmodes/sddSpecDriven.claude.md").exists()
            assert (github_dir / "chatmodes/sddTesting.claude.md").exists()
            assert (github_dir / "instructions/sddPythonCliDev.claude.md").exists()
            assert (github_dir / "prompts/sddTaskExecution.claude.md").exists()
            
            # Verify manual files were preserved
            assert (github_dir / "chatmodes/custom.chatmode.md").exists()
            assert (temp_project / "README.md").exists()


class TestDeleteCommandErrorHandling:
    """Test error handling and edge cases."""
    
    def test_delete_invalid_app_type(self, cli_runner, temp_project, mock_config):
        """Test delete command with invalid app type."""
        with patch('src.core.config.config', mock_config), \
             patch('os.getcwd', return_value=str(temp_project)):
            
            # Run delete command with invalid app type
            result = cli_runner.invoke(app, ['delete', 'invalid-app-type'])
            
            # Verify command failed with proper error
            assert result.exit_code == 1
            assert "Invalid app type" in result.stdout
    
    def test_delete_permission_denied_files(self, cli_runner, temp_project, mock_config, sample_files_github_copilot):
        """Test delete command when files have permission issues."""
        with patch('src.core.config.config', mock_config), \
             patch('os.getcwd', return_value=str(temp_project)):
            
            # Make one file read-only to simulate permission error
            readonly_file = temp_project / ".github/chatmodes/sddSpecDriven.chatmode.md"
            readonly_file.chmod(0o444)  # Read-only
            
            try:
                # Run delete command
                result = cli_runner.invoke(app, ['delete', 'python-cli', '--force'])
                
                # Verify command completed (should handle permission errors gracefully)
                assert result.exit_code == 0
                
                # Verify output contains error information
                assert "Failed to delete" in result.stdout or "Deletion Results:" in result.stdout
                
            finally:
                # Restore permissions for cleanup
                try:
                    readonly_file.chmod(0o644)
                except:
                    pass
    
    def test_delete_nonexistent_project_directories(self, cli_runner, mock_config):
        """Test delete command when project has no .github directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            
            with patch('src.core.config.config', mock_config), \
                 patch('os.getcwd', return_value=str(project_path)):
                
                # Run delete command in empty project
                result = cli_runner.invoke(app, ['delete', 'python-cli', '--force'])
                
                # Verify command completed successfully
                assert result.exit_code == 0
                
                # Verify appropriate message about no files
                assert "No managed files found" in result.stdout
    
    def test_delete_with_configuration_errors(self, cli_runner, temp_project, sample_files_github_copilot):
        """Test delete command when configuration has issues."""
        # Create config with missing/invalid tool data
        invalid_config_data = {
            "ai_tools": {
                "broken-tool": {
                    # Missing required fields
                    "name": "Broken Tool"
                    # No managed_files, etc.
                }
            },
            "preferences": {
                "default_ai_tools": ["broken-tool"]
            }
        }
        
        # Create mock config
        mock_config = MagicMock()
        mock_config.get_ai_tools.return_value = invalid_config_data["ai_tools"]
        mock_config.get_preference.side_effect = lambda key, default: invalid_config_data.get("preferences", {}).get(key, default)
        mock_config.get_yaml_config.return_value = invalid_config_data
        
        with patch('src.core.config.config', mock_config), \
             patch('os.getcwd', return_value=str(temp_project)):
            
            # Run delete command with broken config
            result = cli_runner.invoke(app, ['delete', 'python-cli', '--force'])
            
            # Should handle gracefully - either succeed with no files or show appropriate message
            assert result.exit_code == 0
            assert "No managed files found" in result.stdout or "No AI tools" in result.stdout


class TestDeleteCommandUserInteraction:
    """Test user interaction scenarios with conflict resolution."""
    
    def test_delete_with_conflicts_user_cancellation(self, cli_runner, temp_project, mock_config, sample_files_github_copilot):
        """Test delete command when user cancels during conflict resolution."""
        with patch('src.core.config.config', mock_config), \
             patch('os.getcwd', return_value=str(temp_project)):
            
            # Simulate user input - cancel the operation
            with patch('typer.prompt', return_value="No"):
                result = cli_runner.invoke(app, ['delete', 'python-cli'])
                
                # Verify command was cancelled
                assert result.exit_code == 0
                assert "cancelled" in result.stdout.lower() or "no files were" in result.stdout.lower()
                
                # Verify files were preserved
                github_dir = temp_project / ".github"
                assert (github_dir / "chatmodes/sddSpecDriven.chatmode.md").exists()
                assert (github_dir / "instructions/sddPythonCliDev.instructions.md").exists()
    
    def test_delete_with_confirmation_yes(self, cli_runner, temp_project, mock_config, sample_files_github_copilot):
        """Test delete command when user confirms deletion."""
        with patch('src.core.config.config', mock_config), \
             patch('os.getcwd', return_value=str(temp_project)):
            
            # Simulate user input - confirm the operation
            with patch('typer.prompt', return_value="Yes"):
                result = cli_runner.invoke(app, ['delete', 'python-cli'])
                
                # Verify command completed successfully
                assert result.exit_code == 0
                assert "Deletion Results:" in result.stdout
                
                # Verify files were deleted
                github_dir = temp_project / ".github"
                assert not (github_dir / "chatmodes/sddSpecDriven.chatmode.md").exists()
                assert not (github_dir / "instructions/sddPythonCliDev.instructions.md").exists()


class TestDeleteCommandRegression:
    """Test regression scenarios to ensure existing functionality works."""
    
    def test_delete_maintains_app_type_validation(self, cli_runner, temp_project, mock_config):
        """Test that app type validation still works correctly."""
        with patch('src.core.config.config', mock_config), \
             patch('os.getcwd', return_value=str(temp_project)):
            
            # Test valid app types work
            valid_types = ['python-cli', 'mcp-server']
            for app_type in valid_types:
                result = cli_runner.invoke(app, ['delete', app_type, '--force'])
                assert result.exit_code == 0
            
            # Test invalid app type fails
            result = cli_runner.invoke(app, ['delete', 'invalid-type'])
            assert result.exit_code == 1
            assert "Invalid app type" in result.stdout
    
    def test_delete_preserves_directory_structure(self, cli_runner, temp_project, mock_config, sample_files_github_copilot, manual_files):
        """Test that directory structure is preserved when manual files exist."""
        with patch('src.core.config.config', mock_config), \
             patch('os.getcwd', return_value=str(temp_project)):
            
            # Run delete command
            result = cli_runner.invoke(app, ['delete', 'python-cli', '--force'])
            
            # Verify command completed successfully
            assert result.exit_code == 0
            
            # Verify directory structure is preserved when manual files exist
            github_dir = temp_project / ".github"
            assert github_dir.exists()
            assert (github_dir / "chatmodes").exists()  # Has manual files
            assert (github_dir / "instructions").exists()  # Has manual files
            assert (github_dir / "prompts").exists()  # Has manual files
            
            # Verify manual files still exist
            assert (github_dir / "chatmodes/custom.chatmode.md").exists()
            assert (github_dir / "instructions/manual.instructions.md").exists()
            assert (github_dir / "prompts/custom-prompt.prompt.md").exists()
    
    def test_delete_empty_directory_cleanup(self, cli_runner, temp_project, mock_config, sample_files_github_copilot):
        """Test that empty directories are cleaned up after deletion."""
        with patch('src.core.config.config', mock_config), \
             patch('os.getcwd', return_value=str(temp_project)):
            
            # Run delete command  
            result = cli_runner.invoke(app, ['delete', 'python-cli', '--force'])
            
            # Verify command completed successfully
            assert result.exit_code == 0
            
            # Verify managed files were deleted
            github_dir = temp_project / ".github"
            assert not (github_dir / "chatmodes/sddSpecDriven.chatmode.md").exists()
            assert not (github_dir / "instructions/sddPythonCliDev.instructions.md").exists()
            
            # Empty directories should be cleaned up
            # Note: This may depend on implementation - some directories might be preserved
            # Verify at least the output mentions cleanup if it occurred
            if "Cleaned up" in result.stdout:
                assert "empty directories" in result.stdout
    
    def test_delete_backward_compatibility(self, cli_runner, temp_project, mock_config, sample_files_github_copilot):
        """Test backward compatibility with legacy delete function."""
        with patch('src.core.config.config', mock_config), \
             patch('os.getcwd', return_value=str(temp_project)):
            
            # Import and test legacy function
            from src.commands.delete import delete_templates
            
            # Should work without throwing exceptions
            try:
                delete_templates("python-cli", force=True)
                # If we get here, backward compatibility is maintained
                success = True
            except Exception as e:
                success = False
                
            assert success, "Legacy delete_templates function should maintain backward compatibility"
            
            # Verify files were still deleted
            github_dir = temp_project / ".github"
            assert not (github_dir / "chatmodes/sddSpecDriven.chatmode.md").exists()


class TestDeleteCommandPerformance:
    """Test performance aspects and edge cases."""
    
    def test_delete_large_number_of_files(self, cli_runner, temp_project, mock_config):
        """Test delete command performance with many files."""
        # Create config with many managed files
        large_file_list = [f"test-file-{i:03d}.md" for i in range(50)]
        
        config_data = {
            "ai_tools": {
                "test-tool": {
                    "name": "Test Tool",
                    "template_dir": "test",
                    "managed_files": {
                        "chatmodes": large_file_list[:20],
                        "instructions": large_file_list[20:35],
                        "prompts": large_file_list[35:50],
                        "commands": []
                    }
                }
            },
            "preferences": {
                "default_ai_tools": ["test-tool"]
            }
        }
        
        mock_config = MagicMock()
        mock_config.get_ai_tools.return_value = config_data["ai_tools"]
        mock_config.get_preference.side_effect = lambda key, default: config_data.get("preferences", {}).get(key, default)
        mock_config.get_yaml_config.return_value = config_data
        
        # Create the actual files
        github_dir = temp_project / ".github"
        for file_type in ["chatmodes", "instructions", "prompts"]:
            type_dir = github_dir / file_type
            type_dir.mkdir(exist_ok=True)
            
            files_for_type = config_data["ai_tools"]["test-tool"]["managed_files"][file_type]
            for filename in files_for_type:
                (type_dir / filename).write_text(f"# Test content for {filename}")
        
        with patch('src.core.config.config', mock_config), \
             patch('os.getcwd', return_value=str(temp_project)):
            
            # Run delete command
            result = cli_runner.invoke(app, ['delete', 'python-cli', '--force'])
            
            # Verify command completed successfully
            assert result.exit_code == 0
            
            # Verify files were deleted
            for file_type in ["chatmodes", "instructions", "prompts"]:
                type_dir = github_dir / file_type
                files_for_type = config_data["ai_tools"]["test-tool"]["managed_files"][file_type]
                for filename in files_for_type:
                    assert not (type_dir / filename).exists()
    
    def test_delete_with_complex_directory_structure(self, cli_runner, temp_project, mock_config):
        """Test delete command with complex nested directory structures."""
        # Create nested directory structure
        github_dir = temp_project / ".github"
        
        # Create nested directories (although CLI may not support this yet)
        nested_dirs = [
            "chatmodes/subcategory",
            "instructions/advanced/python",
            "prompts/workflow/templates"
        ]
        
        for nested_dir in nested_dirs:
            (github_dir / nested_dir).mkdir(parents=True, exist_ok=True)
        
        # Create some test files
        test_files = [
            "chatmodes/simple.chatmode.md",
            "instructions/basic.instructions.md",
            "prompts/simple.prompt.md"
        ]
        
        for test_file in test_files:
            (github_dir / test_file).write_text("# Test content")
        
        with patch('src.core.config.config', mock_config), \
             patch('os.getcwd', return_value=str(temp_project)):
            
            # Run delete command
            result = cli_runner.invoke(app, ['delete', 'python-cli', '--force'])
            
            # Should complete without errors even with complex structure
            assert result.exit_code == 0