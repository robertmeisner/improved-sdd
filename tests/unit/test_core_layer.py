"""Unit tests for core layer components.

This module tests the core layer components including:
- Configuration management and compatibility layer
- Exception hierarchy and context preservation
- Data models and enums functionality
- Basic validation and integration
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

# Import core components
from src.core import (
    # Configuration
    AIToolConfig,
    AppTypeConfig,
    ConfigCompatibilityLayer,
    config,
    AI_TOOLS,
    APP_TYPES,
    BANNER,
    TAGLINE,
    # Exceptions
    TemplateError,
    NetworkError,
    GitHubAPIError,
    RateLimitError,
    TimeoutError,
    ValidationError,
    # Models
    TemplateSourceType,
    ProgressInfo,
    TemplateSource,
    TemplateResolutionResult,
)


class TestConfiguration:
    """Test configuration management and compatibility layer."""

    def test_configuration_constants_available(self):
        """Test that configuration constants are properly imported."""
        assert AI_TOOLS is not None
        assert APP_TYPES is not None
        assert BANNER is not None
        assert TAGLINE is not None
        
        # Verify types
        assert isinstance(AI_TOOLS, dict)
        assert isinstance(APP_TYPES, dict)
        assert isinstance(BANNER, str)
        assert isinstance(TAGLINE, str)

    def test_ai_tools_structure(self):
        """Test AI_TOOLS configuration structure."""
        assert len(AI_TOOLS) >= 4  # github-copilot, claude, cursor, gemini
        
        # Check required AI tools exist
        required_tools = ["github-copilot", "claude", "cursor", "gemini"]
        for tool in required_tools:
            assert tool in AI_TOOLS
            
        # Check structure of each tool
        for tool_id, tool_config in AI_TOOLS.items():
            assert "name" in tool_config
            assert "description" in tool_config
            assert "template_dir" in tool_config
            assert "file_extensions" in tool_config
            assert "keywords" in tool_config
            
            # Check file extensions structure
            file_exts = tool_config["file_extensions"]
            required_exts = ["chatmodes", "instructions", "prompts", "commands"]
            for ext_type in required_exts:
                assert ext_type in file_exts
                assert file_exts[ext_type].startswith(".")
            
            # Check keywords structure
            keywords = tool_config["keywords"]
            required_keywords = ["{AI_ASSISTANT}", "{AI_SHORTNAME}", "{AI_COMMAND}"]
            for keyword in required_keywords:
                assert keyword in keywords
                assert isinstance(keywords[keyword], str)
                assert len(keywords[keyword]) > 0

    def test_app_types_structure(self):
        """Test APP_TYPES configuration structure."""
        assert len(APP_TYPES) >= 2  # mcp-server, python-cli
        
        # Check required app types exist
        required_types = ["mcp-server", "python-cli"]
        for app_type in required_types:
            assert app_type in APP_TYPES
            
        # Check structure of each app type
        for type_id, type_config in APP_TYPES.items():
            assert "description" in type_config
            assert "instruction_files" in type_config
            assert isinstance(type_config["description"], str)
            assert isinstance(type_config["instruction_files"], list)
            assert len(type_config["instruction_files"]) > 0

    def test_banner_and_tagline(self):
        """Test banner and tagline content."""
        # Banner should be ASCII art with IMPROVED-SDD pattern
        assert "__" in BANNER  # ASCII art pattern
        assert "_____" in BANNER  # ASCII art pattern
        assert len(BANNER.split("\n")) >= 5  # Multi-line ASCII art
        
        # Tagline should mention key features
        tagline_lower = TAGLINE.lower()
        assert "spec-driven development" in tagline_lower
        assert "github copilot" in tagline_lower

    def test_config_compatibility_layer(self):
        """Test ConfigCompatibilityLayer functionality."""
        assert isinstance(config, ConfigCompatibilityLayer)
        
        # Test property access
        assert config.AI_TOOLS == AI_TOOLS
        assert config.APP_TYPES == APP_TYPES
        assert config.BANNER == BANNER
        assert config.TAGLINE == TAGLINE
        
        # Test that returned values are copies (not references)
        ai_tools_copy = config.AI_TOOLS
        ai_tools_copy["test"] = "modified"
        assert "test" not in AI_TOOLS  # Original should be unchanged

    def test_ai_tool_config_dataclass(self):
        """Test AIToolConfig dataclass functionality."""
        tool_config = AIToolConfig(
            name="Test Tool",
            description="Test description",
            template_dir="test",
            file_extensions={
                "chatmodes": ".test.md",
                "instructions": ".test.md",
                "prompts": ".test.md",
                "commands": ".test.md",
            },
            keywords={
                "{AI_ASSISTANT}": "Test AI",
                "{AI_SHORTNAME}": "Test",
                "{AI_COMMAND}": "test command",
            }
        )
        
        assert tool_config.name == "Test Tool"
        assert tool_config.description == "Test description"
        assert tool_config.template_dir == "test"
        assert len(tool_config.file_extensions) == 4
        assert len(tool_config.keywords) == 3

    def test_app_type_config_dataclass(self):
        """Test AppTypeConfig dataclass functionality."""
        app_config = AppTypeConfig(
            description="Test app type",
            instruction_files=["test1", "test2"]
        )
        
        assert app_config.description == "Test app type"
        assert app_config.instruction_files == ["test1", "test2"]

    def test_config_get_ai_tool_config(self):
        """Test getting typed AI tool configuration."""
        # Test with valid tool
        github_config = config.get_ai_tool_config("github-copilot")
        assert isinstance(github_config, AIToolConfig)
        assert github_config.name == "GitHub Copilot"
        assert "github" in github_config.template_dir
        
        # Test with invalid tool
        with pytest.raises(KeyError):
            config.get_ai_tool_config("invalid-tool")

    def test_config_get_app_type_config(self):
        """Test getting typed app type configuration."""
        # Test with valid app type
        mcp_config = config.get_app_type_config("mcp-server")
        assert isinstance(mcp_config, AppTypeConfig)
        assert "MCP Server" in mcp_config.description
        assert len(mcp_config.instruction_files) > 0
        
        # Test with invalid app type
        with pytest.raises(KeyError):
            config.get_app_type_config("invalid-type")

    def test_config_validation_methods(self):
        """Test configuration validation methods."""
        # Test AI tool validation
        assert config.validate_ai_tool_id("github-copilot") is True
        assert config.validate_ai_tool_id("invalid-tool") is False
        
        # Test app type validation
        assert config.validate_app_type("mcp-server") is True
        assert config.validate_app_type("invalid-type") is False

    def test_config_get_methods(self):
        """Test configuration getter methods."""
        # Test get all AI tools
        all_tools = config.get_available_ai_tools()
        assert isinstance(all_tools, list)
        assert "github-copilot" in all_tools
        assert len(all_tools) >= 4
        
        # Test get all app types
        all_types = config.get_available_app_types()
        assert isinstance(all_types, list)
        assert "mcp-server" in all_types
        assert len(all_types) >= 2


class TestExceptions:
    """Test exception hierarchy and context preservation."""

    def test_template_error_basic(self):
        """Test basic TemplateError functionality."""
        error = TemplateError("Test error message")
        
        assert str(error) == "Test error message"
        assert error.operation is None
        assert error.file_path is None
        assert error.context == {}
        assert error.original_error is None
        assert isinstance(error.timestamp, datetime)

    def test_template_error_with_context(self):
        """Test TemplateError with rich context."""
        test_path = Path("/test/file.txt")
        test_context = {"key1": "value1", "key2": "value2"}
        original_error = ValueError("Original error")
        
        error = TemplateError(
            "Test error with context",
            operation="test_operation",
            file_path=test_path,
            context=test_context,
            original_error=original_error
        )
        
        assert error.operation == "test_operation"
        assert error.file_path == test_path
        assert error.context == test_context
        assert error.original_error == original_error
        
        # Test string representation includes context
        error_str = str(error)
        assert "Test error with context" in error_str
        assert "Operation: test_operation" in error_str
        assert "test" in error_str and "file.txt" in error_str  # Windows/Unix path handling
        assert "key1=value1" in error_str
        assert "key2=value2" in error_str
        assert "Caused by: ValueError: Original error" in error_str

    def test_template_error_context_summary(self):
        """Test TemplateError context summary method."""
        error = TemplateError(
            "Test error",
            operation="test_op",
            file_path=Path("test.txt"),
            context={"test": "value"}
        )
        
        summary = error.get_context_summary()
        
        assert summary["message"] == "Test error"
        assert summary["operation"] == "test_op"
        assert summary["file_path"] == "test.txt"
        assert summary["context"] == {"test": "value"}
        assert "timestamp" in summary
        assert summary["original_error"]["type"] is None

    def test_network_error_inheritance_and_context(self):
        """Test NetworkError inherits from TemplateError with network context."""
        assert issubclass(NetworkError, TemplateError)
        
        error = NetworkError(
            "Network connection failed",
            operation="download",
            url="https://example.com",
            status_code=500
        )
        
        assert error.url == "https://example.com"
        assert error.status_code == 500
        assert error.operation == "download"
        assert "url=https://example.com" in str(error)
        assert "status_code=500" in str(error)

    def test_github_api_error_inheritance_and_context(self):
        """Test GitHubAPIError inherits from TemplateError with GitHub context."""
        assert issubclass(GitHubAPIError, TemplateError)
        
        error = GitHubAPIError(
            "API rate limit exceeded",
            status_code=403,
            api_endpoint="/repos/owner/repo",
            rate_limit_remaining=0
        )
        
        assert error.status_code == 403
        assert error.api_endpoint == "/repos/owner/repo"
        assert error.rate_limit_remaining == 0
        assert "github_status_code=403" in str(error)
        assert "api_endpoint=/repos/owner/repo" in str(error)

    def test_rate_limit_error_inheritance_and_context(self):
        """Test RateLimitError inherits from GitHubAPIError with rate limit context."""
        assert issubclass(RateLimitError, GitHubAPIError)
        assert issubclass(RateLimitError, TemplateError)
        
        error = RateLimitError(
            retry_after=3600,
            rate_limit_reset=1672531200  # Unix timestamp
        )
        
        assert error.retry_after == 3600
        assert error.rate_limit_reset == 1672531200
        assert error.status_code == 429
        assert "GitHub API rate limit exceeded" in str(error)
        assert "retry_after_seconds=3600" in str(error)
        assert "rate_limit_reset_timestamp=1672531200" in str(error)

    def test_timeout_error_inheritance_and_context(self):
        """Test TimeoutError inherits from NetworkError with timeout context."""
        assert issubclass(TimeoutError, NetworkError)
        assert issubclass(TimeoutError, TemplateError)
        
        error = TimeoutError(
            "Request timed out",
            timeout_seconds=30.0,
            url="https://api.github.com"
        )
        
        assert error.timeout_seconds == 30.0
        assert error.url == "https://api.github.com"
        assert "timeout_seconds=30.0" in str(error)

    def test_validation_error_inheritance_and_context(self):
        """Test ValidationError inherits from TemplateError with validation context."""
        assert issubclass(ValidationError, TemplateError)
        
        error = ValidationError(
            "Invalid template format",
            validation_type="format_check",
            expected_value="markdown",
            actual_value="text"
        )
        
        assert error.validation_type == "format_check"
        assert error.expected_value == "markdown"
        assert error.actual_value == "text"
        assert "validation_type=format_check" in str(error)
        assert "expected_value=markdown" in str(error)
        assert "actual_value=text" in str(error)

    def test_exception_hierarchy_structure(self):
        """Test the complete exception hierarchy structure."""
        # Test inheritance chain
        assert issubclass(NetworkError, TemplateError)
        assert issubclass(GitHubAPIError, TemplateError)
        assert issubclass(ValidationError, TemplateError)
        assert issubclass(TimeoutError, NetworkError)
        assert issubclass(RateLimitError, GitHubAPIError)
        
        # Test that they're all ultimately exceptions
        for exc_class in [TemplateError, NetworkError, GitHubAPIError, 
                         RateLimitError, TimeoutError, ValidationError]:
            assert issubclass(exc_class, Exception)

    def test_backward_compatibility_exception_names(self):
        """Test that exception names are preserved for backward compatibility."""
        # These should be the exact same names as in the original code
        exception_names = [
            "TemplateError", "NetworkError", "GitHubAPIError",
            "RateLimitError", "TimeoutError", "ValidationError"
        ]
        
        for name in exception_names:
            # Should be importable from core
            assert hasattr(__import__("src.core", fromlist=[name]), name)


class TestModels:
    """Test data models and enums functionality."""

    def test_template_source_type_enum(self):
        """Test TemplateSourceType enum values."""
        assert TemplateSourceType.LOCAL.value == "local"
        assert TemplateSourceType.BUNDLED.value == "bundled"
        assert TemplateSourceType.GITHUB.value == "github"
        
        # Test all expected values exist
        expected_values = {"local", "bundled", "github"}
        actual_values = {item.value for item in TemplateSourceType}
        assert actual_values == expected_values

    def test_progress_info_dataclass(self):
        """Test ProgressInfo dataclass functionality."""
        progress = ProgressInfo(
            phase="download",
            bytes_completed=1024,
            bytes_total=2048,
            percentage=50.0,
            speed_bps=1024,
            eta_seconds=1
        )
        
        assert progress.phase == "download"
        assert progress.bytes_completed == 1024
        assert progress.bytes_total == 2048
        assert progress.percentage == 50.0
        assert progress.speed_bps == 1024
        assert progress.eta_seconds == 1
        
        # Test speed_mbps property
        expected_mbps = 1024 / (1024 * 1024)  # Convert bytes to MB
        assert progress.speed_mbps == expected_mbps

    def test_progress_info_optional_fields(self):
        """Test ProgressInfo with optional fields."""
        progress = ProgressInfo(
            phase="extract",
            bytes_completed=512,
            bytes_total=1024,
            percentage=50.0
        )
        
        assert progress.speed_bps is None
        assert progress.eta_seconds is None
        assert progress.speed_mbps is None

    def test_template_source_dataclass(self):
        """Test TemplateSource dataclass functionality."""
        source_path = Path("/test/templates")
        source = TemplateSource(
            path=source_path,
            source_type=TemplateSourceType.LOCAL,
            size_bytes=4096
        )
        
        assert source.path == source_path
        assert source.source_type == TemplateSourceType.LOCAL
        assert source.size_bytes == 4096
        
        # Test string representation
        str_repr = str(source)
        assert "local templates at" in str_repr
        assert "test" in str_repr and "templates" in str_repr  # Windows/Unix path handling

    def test_template_source_optional_size(self):
        """Test TemplateSource with optional size."""
        source = TemplateSource(
            path=Path("/test"),
            source_type=TemplateSourceType.GITHUB
        )
        
        assert source.size_bytes is None
        assert source.source_type == TemplateSourceType.GITHUB

    def test_template_resolution_result_dataclass(self):
        """Test TemplateResolutionResult dataclass functionality."""
        source = TemplateSource(
            path=Path("/local/templates"),
            source_type=TemplateSourceType.LOCAL
        )
        
        result = TemplateResolutionResult(
            source=source,
            success=True,
            message="Templates found locally",
            fallback_attempted=False
        )
        
        assert result.source == source
        assert result.success is True
        assert result.message == "Templates found locally"
        assert result.fallback_attempted is False

    def test_template_resolution_result_properties(self):
        """Test TemplateResolutionResult convenience properties."""
        # Test local source
        local_source = TemplateSource(
            path=Path("/local"),
            source_type=TemplateSourceType.LOCAL
        )
        local_result = TemplateResolutionResult(
            source=local_source,
            success=True,
            message="Local"
        )
        
        assert local_result.is_local is True
        assert local_result.is_bundled is False
        assert local_result.is_github is False
        
        # Test bundled source
        bundled_source = TemplateSource(
            path=Path("/bundled"),
            source_type=TemplateSourceType.BUNDLED
        )
        bundled_result = TemplateResolutionResult(
            source=bundled_source,
            success=True,
            message="Bundled"
        )
        
        assert bundled_result.is_local is False
        assert bundled_result.is_bundled is True
        assert bundled_result.is_github is False
        
        # Test GitHub source
        github_source = TemplateSource(
            path=Path("/github"),
            source_type=TemplateSourceType.GITHUB
        )
        github_result = TemplateResolutionResult(
            source=github_source,
            success=True,
            message="GitHub"
        )
        
        assert github_result.is_local is False
        assert github_result.is_bundled is False
        assert github_result.is_github is True

    def test_template_resolution_result_no_source(self):
        """Test TemplateResolutionResult with no source."""
        result = TemplateResolutionResult(
            source=None,
            success=False,
            message="No templates found"
        )
        
        assert result.source is None
        assert result.is_local is False
        assert result.is_bundled is False
        assert result.is_github is False


class TestCoreLayerIntegration:
    """Test integration between core layer components."""

    def test_all_core_imports_work(self):
        """Test that all core components can be imported together."""
        # This test ensures no circular import issues
        from src.core import (
            config, AI_TOOLS, APP_TYPES, BANNER, TAGLINE,
            TemplateError, NetworkError, GitHubAPIError,
            TemplateSourceType, ProgressInfo, TemplateSource
        )
        
        # Basic functionality check
        assert config is not None
        assert len(AI_TOOLS) > 0
        assert len(APP_TYPES) > 0
        assert len(BANNER) > 0
        assert len(TAGLINE) > 0
        
        # Exception creation
        error = TemplateError("test")
        assert isinstance(error, Exception)
        
        # Model creation
        progress = ProgressInfo("test", 0, 100, 0.0)
        assert progress.phase == "test"

    def test_configuration_with_models(self):
        """Test configuration integration with models."""
        # Get AI tool config and verify it works with models
        tool_config = config.get_ai_tool_config("github-copilot")
        
        # Create a source using the template directory
        source = TemplateSource(
            path=Path(f"/templates/{tool_config.template_dir}"),
            source_type=TemplateSourceType.BUNDLED
        )
        
        assert "github" in str(source)
        assert source.source_type == TemplateSourceType.BUNDLED

    def test_exceptions_with_models(self):
        """Test exception integration with models."""
        # Create a template source
        source = TemplateSource(
            path=Path("/test/templates"),
            source_type=TemplateSourceType.LOCAL
        )
        
        # Create exception with model context
        error = ValidationError(
            "Invalid template source",
            operation="template_validation",
            file_path=source.path,
            context={"source_type": source.source_type.value}
        )
        
        assert error.file_path == source.path
        assert "source_type=local" in str(error)

    def test_core_layer_functionality_preservation(self):
        """Test that core layer preserves original CLI functionality."""
        # Test that we can still access everything the CLI needs
        
        # Configuration access (as CLI would use it)
        assert "github-copilot" in AI_TOOLS
        assert "mcp-server" in APP_TYPES
        assert "__" in BANNER  # ASCII art pattern check
        
        # Exception creation (as CLI would use it)
        try:
            raise NetworkError("Test network error", url="https://example.com")
        except TemplateError as e:
            assert isinstance(e, NetworkError)
            assert "https://example.com" in str(e)
        
        # Model creation (as CLI would use it)
        progress = ProgressInfo("download", 100, 200, 50.0, speed_bps=1024)
        assert progress.speed_mbps is not None
        
        resolution = TemplateResolutionResult(
            source=TemplateSource(Path("/test"), TemplateSourceType.LOCAL),
            success=True,
            message="Found"
        )
        assert resolution.is_local is True

    def test_backward_compatibility_guarantees(self):
        """Test that backward compatibility is maintained."""
        # Test that all original names are still available
        original_names = [
            "AI_TOOLS", "APP_TYPES", "BANNER", "TAGLINE",
            "TemplateError", "NetworkError", "GitHubAPIError", 
            "RateLimitError", "TimeoutError", "ValidationError",
            "TemplateSourceType", "ProgressInfo", "TemplateSource", 
            "TemplateResolutionResult"
        ]
        
        for name in original_names:
            assert hasattr(__import__("src.core", fromlist=[name]), name)
        
        # Test that exceptions maintain original interface
        # (Original GitHubAPIError constructor)
        github_error = GitHubAPIError("Test error", status_code=404)
        assert github_error.status_code == 404
        
        # (Original RateLimitError constructor)
        rate_error = RateLimitError(retry_after=3600)
        assert rate_error.retry_after == 3600