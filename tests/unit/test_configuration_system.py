"""Unit tests for configuration system components.

Tests cover:
- ConfigurationValidator: YAML validation, schema validation, duplicate detection
- ConfigurationLoader: Local/remote config loading, hierarchy, merging
- ValidationResult: Warning/error management, categorization
- Configuration hierarchy and fallback behavior
- Error handling for invalid configurations
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, mock_open
from typing import Dict, Any

import pytest
import httpx
import yaml

from src.core.config import (
    ConfigurationValidator,
    ConfigurationLoader, 
    ValidationResult,
    ValidationWarning
)
from src.core.exceptions import ValidationError


class TestValidationWarning:
    """Test ValidationWarning class functionality."""
    
    def test_create_warning(self):
        """Test creating a validation warning."""
        warning = ValidationWarning("Test warning", "test")
        assert str(warning) == "[WARNING] Test warning"
        assert warning.category == "test"
        assert warning.severity == "warning"
    
    def test_warning_with_custom_severity(self):
        """Test creating warning with custom severity."""
        warning = ValidationWarning("Test error", "test", "error")
        assert str(warning) == "[ERROR] Test error"
        assert warning.severity == "error"


class TestValidationResult:
    """Test ValidationResult class functionality."""
    
    def test_initial_state(self):
        """Test initial validation result state."""
        result = ValidationResult()
        assert result.valid is True
        assert result.parsed_content == {}
        assert result.warnings == []
        assert result.errors == []
        assert not result.has_warnings()
        assert not result.has_errors()
    
    def test_add_warning(self):
        """Test adding warnings to result."""
        result = ValidationResult()
        result.add_warning("Test warning", "test")
        
        assert result.has_warnings()
        assert len(result.warnings) == 1
        assert result.warnings[0].message == "Test warning"
        assert result.warnings[0].category == "test"
    
    def test_add_error(self):
        """Test adding errors to result."""
        result = ValidationResult()
        result.add_error("Test error", "test")
        
        assert result.has_errors()
        assert not result.valid
        assert len(result.errors) == 1
        assert result.errors[0].message == "Test error"
    
    def test_get_warnings_by_category(self):
        """Test filtering warnings by category."""
        result = ValidationResult()
        result.add_warning("Duplicate warning", "duplicate")
        result.add_warning("Empty warning", "empty")
        result.add_warning("Another duplicate", "duplicate")
        
        duplicate_warnings = result.get_warnings_by_category("duplicate")
        assert len(duplicate_warnings) == 2
        assert all(w.category == "duplicate" for w in duplicate_warnings)
        
        empty_warnings = result.get_warnings_by_category("empty")
        assert len(empty_warnings) == 1
        assert empty_warnings[0].category == "empty"
    
    def test_summary(self):
        """Test validation result summary generation."""
        result = ValidationResult()
        assert result.summary() == "Configuration is valid"
        
        result.add_warning("Test warning", "test")
        assert result.summary() == "Validation completed with 1 warnings"
        
        result.add_error("Test error", "test")
        assert result.summary() == "Validation completed with 1 errors, 1 warnings"


class TestConfigurationValidator:
    """Test ConfigurationValidator class functionality."""
    
    @pytest.fixture
    def validator(self):
        """Create a configuration validator for testing."""
        return ConfigurationValidator()
    
    def test_valid_yaml_configuration(self, validator):
        """Test validation of valid YAML configuration."""
        config_yaml = """
        version: "1.0"
        ai_tools:
          test-tool:
            name: "Test Tool"
            template_dir: "test"
            managed_files:
              chatmodes:
                - "test.chatmode.md"
              instructions:
                - "test.instructions.md"
              prompts: []
              commands: []
        """
        
        result = validator.validate_config(config_yaml, "test")
        assert result.valid
        assert "version" in result.parsed_content
        assert "ai_tools" in result.parsed_content
    
    def test_invalid_yaml_syntax(self, validator):
        """Test handling of invalid YAML syntax."""
        invalid_yaml = """
        version: "1.0"
        invalid_syntax: [unclosed bracket
        """
        
        result = validator.validate_config(invalid_yaml, "test")
        assert not result.valid
        assert result.has_errors()
        error_messages = [str(e) for e in result.errors]
        assert any("Invalid YAML syntax" in msg for msg in error_messages)
    
    def test_empty_configuration(self, validator):
        """Test handling of empty configuration."""
        result = validator.validate_config("", "test")
        assert result.has_warnings()
        warning_messages = [str(w) for w in result.warnings]
        assert any("Empty test" in msg for msg in warning_messages)
    
    def test_duplicate_file_detection_within_category(self, validator):
        """Test detection of duplicate files within same category."""
        config_yaml = """
        version: "1.0"
        ai_tools:
          test-tool:
            name: "Test Tool"
            template_dir: "test"
            managed_files:
              chatmodes:
                - "test.chatmode.md"
                - "test.chatmode.md"  # Duplicate
              instructions: []
              prompts: []
              commands: []
        """
        
        result = validator.validate_config(config_yaml, "test")
        assert result.valid  # Still valid, just warnings
        assert result.has_warnings()
        
        duplicate_warnings = result.get_warnings_by_category("duplicate")
        assert len(duplicate_warnings) > 0
        assert any("duplicate file" in str(w).lower() for w in duplicate_warnings)
    
    def test_duplicate_file_detection_across_tools(self, validator):
        """Test detection of duplicate files across AI tools."""
        config_yaml = """
        version: "1.0"
        ai_tools:
          tool1:
            name: "Tool 1"
            template_dir: "tool1"
            managed_files:
              chatmodes:
                - "shared.chatmode.md"
              instructions: []
              prompts: []
              commands: []
          tool2:
            name: "Tool 2"
            template_dir: "tool2"
            managed_files:
              chatmodes:
                - "shared.chatmode.md"  # Cross-tool duplicate
              instructions: []
              prompts: []
              commands: []
        """
        
        result = validator.validate_config(config_yaml, "test")
        assert result.valid
        assert result.has_warnings()
        
        duplicate_warnings = result.get_warnings_by_category("duplicate")
        assert len(duplicate_warnings) > 0
        assert any("multiple AI tools" in str(w) for w in duplicate_warnings)
    
    def test_empty_list_detection(self, validator):
        """Test detection of empty managed file lists."""
        config_yaml = """
        version: "1.0"
        ai_tools:
          test-tool:
            name: "Test Tool"
            template_dir: "test"
            managed_files:
              chatmodes: []  # Empty list
              instructions: []  # Empty list
              prompts: []
              commands: []
        """
        
        result = validator.validate_config(config_yaml, "test")
        assert result.valid
        assert result.has_warnings()
        
        empty_warnings = result.get_warnings_by_category("empty")
        assert len(empty_warnings) > 0
        assert any("empty managed_files" in str(w) for w in empty_warnings)
    
    def test_invalid_file_pattern_detection(self, validator):
        """Test detection of invalid file patterns."""
        config_yaml = """
        version: "1.0"
        ai_tools:
          test-tool:
            name: "Test Tool"
            template_dir: "test"
            managed_files:
              chatmodes:
                - "valid.chatmode.md"
                - "invalid-pattern*.txt"  # Invalid pattern
              instructions: []
              prompts: []
              commands: []
        """
        
        result = validator.validate_config(config_yaml, "test")
        assert result.valid
        assert result.has_warnings()
        
        pattern_warnings = result.get_warnings_by_category("pattern")
        assert len(pattern_warnings) > 0
        assert any("invalid file pattern" in str(w).lower() for w in pattern_warnings)
    
    @patch('src.core.config.ValidationError', None)  # Simulate missing Pydantic
    def test_graceful_degradation_without_pydantic(self, validator):
        """Test graceful degradation when Pydantic is not available."""
        config_yaml = """
        version: "1.0"
        ai_tools:
          test-tool:
            name: "Test Tool"
            template_dir: "test"
            managed_files:
              chatmodes: []
              instructions: []
              prompts: []
              commands: []
        """
        
        result = validator.validate_config(config_yaml, "test")
        assert result.valid
        assert result.has_warnings()
        
        # Should have warning about Pydantic not being available
        schema_warnings = result.get_warnings_by_category("schema")
        assert any("Pydantic not available" in str(w) for w in schema_warnings)
    
    def test_missing_version_field(self, validator):
        """Test warning for missing version field."""
        config_yaml = """
        ai_tools:
          test-tool:
            name: "Test Tool"
            template_dir: "test"
            managed_files:
              chatmodes: []
              instructions: []
              prompts: []
              commands: []
        """
        
        result = validator.validate_config(config_yaml, "test")
        assert result.valid
        assert result.has_warnings()
        
        schema_warnings = result.get_warnings_by_category("schema")
        assert any("Missing 'version' field" in str(w) for w in schema_warnings)


class TestConfigurationLoader:
    """Test ConfigurationLoader class functionality."""
    
    @pytest.fixture
    def loader(self):
        """Create a configuration loader for testing."""
        return ConfigurationLoader()
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    def test_load_local_config_exists(self, loader, temp_project_dir):
        """Test loading local configuration when file exists."""
        # Create local config directory and file
        sdd_dir = temp_project_dir / ".sdd_templates"
        sdd_dir.mkdir()
        config_file = sdd_dir / "sdd-config.yaml"
        
        config_content = {
            "version": "1.0",
            "ai_tools": {
                "test-tool": {
                    "name": "Test Tool",
                    "template_dir": "test",
                    "managed_files": {
                        "chatmodes": ["test.chatmode.md"],
                        "instructions": [],
                        "prompts": [],
                        "commands": []
                    }
                }
            }
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(config_content, f)
        
        result = loader.load_local_config(temp_project_dir)
        assert result["version"] == "1.0"
        assert "ai_tools" in result
        assert "test-tool" in result["ai_tools"]
    
    def test_load_local_config_missing(self, loader, temp_project_dir):
        """Test loading local configuration when file doesn't exist."""
        result = loader.load_local_config(temp_project_dir)
        assert result == {}
    
    def test_load_local_config_invalid_yaml(self, loader, temp_project_dir):
        """Test handling of invalid YAML in local config."""
        # Create local config directory and file with invalid YAML
        sdd_dir = temp_project_dir / ".sdd_templates"
        sdd_dir.mkdir()
        config_file = sdd_dir / "sdd-config.yaml"
        
        with open(config_file, 'w') as f:
            f.write("invalid: yaml: syntax: [")
        
        result = loader.load_local_config(temp_project_dir)
        assert result == {}
    
    @patch('httpx.Client')
    def test_load_remote_config_success(self, mock_client_class, loader):
        """Test successful loading of remote configuration."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.text = """
        version: "1.0"
        ai_tools:
          github-copilot:
            name: "GitHub Copilot"
            template_dir: "github"
            managed_files:
              chatmodes: ["sddSpecDriven.chatmode.md"]
              instructions: []
              prompts: []
              commands: []
        """
        mock_response.raise_for_status.return_value = None
        
        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = None
        mock_client_class.return_value = mock_client
        
        result = loader.load_remote_config()
        assert "version" in result
        assert "ai_tools" in result
        assert "github-copilot" in result["ai_tools"]
    
    @patch('httpx.Client')
    def test_load_remote_config_http_error(self, mock_client_class, loader):
        """Test handling of HTTP errors when loading remote config."""
        # Mock HTTP error
        mock_client = MagicMock()
        mock_client.get.side_effect = httpx.RequestError("Network error")
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = None
        mock_client_class.return_value = mock_client
        
        result = loader.load_remote_config()
        assert result == {}
    
    @patch('src.core.config.httpx', None)  # Simulate missing httpx
    def test_load_remote_config_no_httpx(self, loader):
        """Test handling when httpx is not available."""
        result = loader.load_remote_config()
        assert result == {}
    
    def test_configuration_hierarchy_local_only(self, loader, temp_project_dir):
        """Test configuration hierarchy with only local config."""
        # Create local config
        sdd_dir = temp_project_dir / ".sdd_templates"
        sdd_dir.mkdir()
        config_file = sdd_dir / "sdd-config.yaml"
        
        config_content = {
            "version": "1.0",
            "ai_tools": {
                "local-tool": {
                    "name": "Local Tool",
                    "template_dir": "local"
                }
            }
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(config_content, f)
        
        with patch.object(loader, 'load_remote_config', return_value={}):
            result = loader.load_configuration_hierarchy(temp_project_dir)
            assert "local-tool" in result["ai_tools"]
    
    @patch('httpx.Client')
    def test_configuration_hierarchy_merge(self, mock_client_class, loader, temp_project_dir):
        """Test configuration hierarchy merging local and remote configs."""
        # Setup remote config mock
        mock_response = Mock()
        mock_response.text = """
        version: "1.0"
        ai_tools:
          github-copilot:
            name: "GitHub Copilot"
            template_dir: "github"
        cli:
          delete_behavior:
            confirm_before_delete: true
        """
        mock_response.raise_for_status.return_value = None
        
        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = None
        mock_client_class.return_value = mock_client
        
        # Create local config that overrides some settings
        sdd_dir = temp_project_dir / ".sdd_templates"
        sdd_dir.mkdir()
        config_file = sdd_dir / "sdd-config.yaml"
        
        local_config = {
            "ai_tools": {
                "local-tool": {
                    "name": "Local Tool",
                    "template_dir": "local"
                }
            },
            "cli": {
                "delete_behavior": {
                    "confirm_before_delete": False  # Override remote setting
                }
            }
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(local_config, f)
        
        result = loader.load_configuration_hierarchy(temp_project_dir)
        
        # Should have both remote and local tools
        assert "github-copilot" in result["ai_tools"]
        assert "local-tool" in result["ai_tools"]
        
        # Local should override remote settings
        assert result["cli"]["delete_behavior"]["confirm_before_delete"] is False
    
    def test_detect_configuration_conflicts(self, loader):
        """Test detection of configuration conflicts."""
        config = {
            "ai_tools": {
                "tool1": {
                    "managed_files": {
                        "chatmodes": ["shared.md"],
                        "instructions": ["unique1.md"]
                    }
                },
                "tool2": {
                    "managed_files": {
                        "chatmodes": ["shared.md"],  # Conflict
                        "instructions": ["unique2.md"]
                    }
                }
            }
        }
        
        conflicts = loader.detect_configuration_conflicts(config)
        assert len(conflicts) > 0
        assert any("shared.md" in conflict for conflict in conflicts)
        assert any("tool1" in conflict and "tool2" in conflict for conflict in conflicts)
    
    def test_detect_configuration_conflicts_none(self, loader):
        """Test configuration with no conflicts."""
        config = {
            "ai_tools": {
                "tool1": {
                    "managed_files": {
                        "chatmodes": ["tool1.md"],
                        "instructions": ["tool1-inst.md"]
                    }
                },
                "tool2": {
                    "managed_files": {
                        "chatmodes": ["tool2.md"],
                        "instructions": ["tool2-inst.md"]
                    }
                }
            }
        }
        
        conflicts = loader.detect_configuration_conflicts(config)
        assert len(conflicts) == 0
    
    def test_deep_merge_configs(self, loader):
        """Test deep merging of configuration dictionaries."""
        base_config = {
            "version": "1.0",
            "ai_tools": {
                "tool1": {
                    "name": "Tool 1",
                    "settings": {
                        "option1": "value1",
                        "option2": "value2"
                    }
                }
            },
            "cli": {
                "delete_behavior": {
                    "confirm_before_delete": True
                }
            }
        }
        
        override_config = {
            "ai_tools": {
                "tool1": {
                    "settings": {
                        "option2": "override_value2",  # Override
                        "option3": "value3"  # Add new
                    }
                },
                "tool2": {  # Add new tool
                    "name": "Tool 2"
                }
            },
            "cli": {
                "delete_behavior": {
                    "show_preview": True  # Add new setting
                }
            }
        }
        
        result = loader.deep_merge_configs(base_config, override_config)
        
        # Version should remain from base
        assert result["version"] == "1.0"
        
        # Tool1 settings should be merged
        assert result["ai_tools"]["tool1"]["name"] == "Tool 1"
        assert result["ai_tools"]["tool1"]["settings"]["option1"] == "value1"
        assert result["ai_tools"]["tool1"]["settings"]["option2"] == "override_value2"
        assert result["ai_tools"]["tool1"]["settings"]["option3"] == "value3"
        
        # Tool2 should be added
        assert "tool2" in result["ai_tools"]
        assert result["ai_tools"]["tool2"]["name"] == "Tool 2"
        
        # CLI settings should be merged
        assert result["cli"]["delete_behavior"]["confirm_before_delete"] is True
        assert result["cli"]["delete_behavior"]["show_preview"] is True


class TestConfigurationSystemIntegration:
    """Integration tests for configuration system components."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @patch('httpx.Client')
    def test_end_to_end_configuration_loading_and_validation(self, mock_client_class, temp_project_dir):
        """Test end-to-end configuration loading and validation."""
        # Setup remote config mock
        mock_response = Mock()
        mock_response.text = """
        version: "1.0"
        ai_tools:
          github-copilot:
            name: "GitHub Copilot"
            template_dir: "github"
            managed_files:
              chatmodes:
                - "sddSpecDriven.chatmode.md"
              instructions:
                - "sddPythonCliDev.instructions.md"
              prompts: []
              commands: []
        """
        mock_response.raise_for_status.return_value = None
        
        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__.return_value = mock_client
        mock_client.__exit__.return_value = None
        mock_client_class.return_value = mock_client
        
        # Create local config with some issues for validation
        sdd_dir = temp_project_dir / ".sdd_templates"
        sdd_dir.mkdir()
        config_file = sdd_dir / "sdd-config.yaml"
        
        local_config = {
            "ai_tools": {
                "claude": {
                    "name": "Claude",
                    "template_dir": "claude",
                    "managed_files": {
                        "chatmodes": ["sddSpecDriven.chatmode.md"],  # Conflict with github-copilot
                        "instructions": [],  # Empty list
                        "prompts": [],  # Empty list
                        "commands": []  # Empty list
                    }
                }
            }
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(local_config, f)
        
        # Load configuration hierarchy
        loader = ConfigurationLoader()
        config = loader.load_configuration_hierarchy(temp_project_dir)
        
        # Validate the merged configuration
        validator = ConfigurationValidator()
        config_yaml = yaml.dump(config)
        result = validator.validate_config(config_yaml, "merged config")
        
        # Should be valid but have warnings
        assert result.valid
        assert result.has_warnings()
        
        # Should detect empty lists
        empty_warnings = result.get_warnings_by_category("empty")
        assert len(empty_warnings) > 0
        
        # Should detect conflicts
        conflicts = loader.detect_configuration_conflicts(config)
        assert len(conflicts) > 0
    
    def test_error_recovery_and_fallbacks(self, temp_project_dir):
        """Test error recovery and fallback mechanisms."""
        # Create invalid local config
        sdd_dir = temp_project_dir / ".sdd_templates"
        sdd_dir.mkdir()
        config_file = sdd_dir / "sdd-config.yaml"
        
        with open(config_file, 'w') as f:
            f.write("invalid: yaml: syntax: [")
        
        # Mock failing remote config
        loader = ConfigurationLoader()
        with patch.object(loader, 'load_remote_config', side_effect=Exception("Network error")):
            config = loader.load_configuration_hierarchy(temp_project_dir)
            # Should return empty config due to failures
            assert config == {}
        
        # Test validation of invalid config
        validator = ConfigurationValidator()
        result = validator.validate_config("invalid: yaml: [", "test")
        assert not result.valid
        assert result.has_errors()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])