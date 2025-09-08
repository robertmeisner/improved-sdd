"""Exception hierarchy for improved-sdd CLI operations.

This module provides a comprehensive exception hierarchy with rich context preservation
for template operations, network errors, and validation issues.
"""

import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class TemplateError(Exception):
    """Base exception for template-related operations with rich context preservation.

    This is the root exception for all template-related errors in the improved-sdd CLI.
    It provides enhanced context preservation including operation details, file paths,
    timestamps, and additional metadata to aid in debugging and error reporting.

    Attributes:
        operation: The operation being performed when error occurred
        file_path: Path to the file being processed (if applicable)
        timestamp: When the error occurred
        context: Additional context information
        original_error: The original exception that caused this error (if any)
    """

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        file_path: Optional[Path] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ):
        """Initialize TemplateError with rich context.

        Args:
            message: Human-readable error message
            operation: Description of operation being performed
            file_path: Path to file being processed when error occurred
            context: Additional context information as key-value pairs
            original_error: Original exception that caused this error
        """
        super().__init__(message)
        self.operation = operation
        self.file_path = Path(file_path) if file_path else None
        self.timestamp = datetime.now()
        self.context = context or {}
        self.original_error = original_error
        self._traceback_info = traceback.format_stack()

    def __str__(self) -> str:
        """Format error with context information."""
        parts = [super().__str__()]

        if self.operation:
            parts.append(f"Operation: {self.operation}")

        if self.file_path:
            parts.append(f"File: {self.file_path}")

        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            parts.append(f"Context: {context_str}")

        if self.original_error:
            parts.append(f"Caused by: {type(self.original_error).__name__}: {self.original_error}")

        return " | ".join(parts)

    def get_context_summary(self) -> Dict[str, Any]:
        """Get a summary of all context information.

        Returns:
            Dictionary containing all context information
        """
        return {
            "message": str(super().__str__()),
            "operation": self.operation,
            "file_path": str(self.file_path) if self.file_path else None,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
            "original_error": {
                "type": type(self.original_error).__name__ if self.original_error else None,
                "message": str(self.original_error) if self.original_error else None,
            },
        }


class NetworkError(TemplateError):
    """Exception for network-related errors during template operations.

    This exception is raised for network connectivity issues, DNS resolution failures,
    connection timeouts, and other network-related problems during template downloads
    or GitHub API interactions.
    """

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        file_path: Optional[Path] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
        url: Optional[str] = None,
        status_code: Optional[int] = None,
    ):
        """Initialize NetworkError with network-specific context.

        Args:
            message: Human-readable error message
            operation: Description of network operation being performed
            file_path: Path to file being processed
            context: Additional context information
            original_error: Original network exception
            url: URL being accessed when error occurred
            status_code: HTTP status code (if applicable)
        """
        # Enhance context with network-specific information
        enhanced_context = context or {}
        if url:
            enhanced_context["url"] = url
        if status_code:
            enhanced_context["status_code"] = status_code

        super().__init__(
            message=message,
            operation=operation or "network operation",
            file_path=file_path,
            context=enhanced_context,
            original_error=original_error,
        )
        self.url = url
        self.status_code = status_code


class GitHubAPIError(TemplateError):
    """Exception for GitHub API-specific errors.

    This exception is raised for GitHub API authentication issues, rate limiting,
    repository access problems, and other GitHub-specific API errors.
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        operation: Optional[str] = None,
        file_path: Optional[Path] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
        api_endpoint: Optional[str] = None,
        rate_limit_remaining: Optional[int] = None,
    ):
        """Initialize GitHubAPIError with GitHub-specific context.

        Args:
            message: Human-readable error message
            status_code: HTTP status code from GitHub API
            operation: Description of GitHub operation being performed
            file_path: Path to file being processed
            context: Additional context information
            original_error: Original API exception
            api_endpoint: GitHub API endpoint that failed
            rate_limit_remaining: Remaining API calls in rate limit
        """
        # Enhance context with GitHub-specific information
        enhanced_context = context or {}
        if status_code:
            enhanced_context["github_status_code"] = status_code
        if api_endpoint:
            enhanced_context["api_endpoint"] = api_endpoint
        if rate_limit_remaining is not None:
            enhanced_context["rate_limit_remaining"] = rate_limit_remaining

        super().__init__(
            message=message,
            operation=operation or "GitHub API operation",
            file_path=file_path,
            context=enhanced_context,
            original_error=original_error,
        )
        self.status_code = status_code
        self.api_endpoint = api_endpoint
        self.rate_limit_remaining = rate_limit_remaining


class RateLimitError(GitHubAPIError):
    """Exception for GitHub API rate limit errors.

    This exception is raised when the GitHub API rate limit is exceeded.
    It includes information about when the rate limit will reset.
    """

    def __init__(
        self,
        retry_after: Optional[int] = None,
        operation: Optional[str] = None,
        file_path: Optional[Path] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
        rate_limit_remaining: Optional[int] = None,
        rate_limit_reset: Optional[int] = None,
    ):
        """Initialize RateLimitError with rate limit specific context.

        Args:
            retry_after: Seconds to wait before retrying
            operation: Description of operation that hit rate limit
            file_path: Path to file being processed
            context: Additional context information
            original_error: Original rate limit exception
            rate_limit_remaining: Remaining API calls (should be 0)
            rate_limit_reset: Unix timestamp when rate limit resets
        """
        # Enhance context with rate limit information
        enhanced_context = context or {}
        if retry_after:
            enhanced_context["retry_after_seconds"] = retry_after
        if rate_limit_reset:
            enhanced_context["rate_limit_reset_timestamp"] = rate_limit_reset
            reset_time = datetime.fromtimestamp(rate_limit_reset)
            enhanced_context["rate_limit_reset_time"] = reset_time.isoformat()

        super().__init__(
            message="GitHub API rate limit exceeded",
            status_code=429,
            operation=operation or "GitHub API rate limited operation",
            file_path=file_path,
            context=enhanced_context,
            original_error=original_error,
            rate_limit_remaining=rate_limit_remaining or 0,
        )
        self.retry_after = retry_after
        self.rate_limit_reset = rate_limit_reset


class TimeoutError(NetworkError):
    """Exception for timeout errors during network operations.

    This exception is raised when network operations exceed their timeout limits,
    including connection timeouts and read timeouts.
    """

    def __init__(
        self,
        message: str = "Operation timed out",
        timeout_seconds: Optional[float] = None,
        operation: Optional[str] = None,
        file_path: Optional[Path] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
        url: Optional[str] = None,
    ):
        """Initialize TimeoutError with timeout-specific context.

        Args:
            message: Human-readable error message
            timeout_seconds: Timeout duration that was exceeded
            operation: Description of operation that timed out
            file_path: Path to file being processed
            context: Additional context information
            original_error: Original timeout exception
            url: URL being accessed when timeout occurred
        """
        # Enhance context with timeout information
        enhanced_context = context or {}
        if timeout_seconds:
            enhanced_context["timeout_seconds"] = timeout_seconds

        super().__init__(
            message=message,
            operation=operation or "network operation with timeout",
            file_path=file_path,
            context=enhanced_context,
            original_error=original_error,
            url=url,
        )
        self.timeout_seconds = timeout_seconds


class ValidationError(TemplateError):
    """Exception for template validation errors.

    This exception is raised when template content, structure, or metadata
    fails validation checks.
    """

    def __init__(
        self,
        message: str,
        validation_type: Optional[str] = None,
        expected_value: Optional[Any] = None,
        actual_value: Optional[Any] = None,
        operation: Optional[str] = None,
        file_path: Optional[Path] = None,
        context: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None,
    ):
        """Initialize ValidationError with validation-specific context.

        Args:
            message: Human-readable error message
            validation_type: Type of validation that failed
            expected_value: Expected value that wasn't found
            actual_value: Actual value that was found
            operation: Description of validation operation
            file_path: Path to file being validated
            context: Additional context information
            original_error: Original validation exception
        """
        # Enhance context with validation information
        enhanced_context = context or {}
        if validation_type:
            enhanced_context["validation_type"] = validation_type
        if expected_value is not None:
            enhanced_context["expected_value"] = str(expected_value)
        if actual_value is not None:
            enhanced_context["actual_value"] = str(actual_value)

        super().__init__(
            message=message,
            operation=operation or "template validation",
            file_path=file_path,
            context=enhanced_context,
            original_error=original_error,
        )
        self.validation_type = validation_type
        self.expected_value = expected_value
        self.actual_value = actual_value


# Exception hierarchy for easy reference:
# Exception
# └── TemplateError (base for all template operations)
#     ├── NetworkError (network-related failures)
#     │   └── TimeoutError (timeout-specific failures)
#     ├── GitHubAPIError (GitHub API specific errors)
#     │   └── RateLimitError (rate limit specific errors)
#     └── ValidationError (data validation failures)

# Backwards compatibility exports (maintain exact same names)
__all__ = [
    "TemplateError",
    "NetworkError",
    "GitHubAPIError",
    "RateLimitError",
    "TimeoutError",
    "ValidationError",
]
