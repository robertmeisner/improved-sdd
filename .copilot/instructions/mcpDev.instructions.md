---
applyTo: '**'
---
# MCP Development Instructions

## Overview
This document provides comprehensive guidelines for developing, maintaining, and enhancing the MCP Project Analyzer server. These instructions apply to all Python files in this project and ensure consistent MCP development practices.

## Project Context
This project implements an MCP (Model Context Protocol) server that provides project analysis capabilities to AI applications. The server follows MCP 2025-06-18 specification and uses the FastMCP Python SDK for implementation.

**MCP Python SDK**: https://github.com/modelcontextprotocol/python-sdk

## Architecture Overview

### MCP Architecture Components
```mermaid
graph TB
    subgraph "MCP Host (AI Application)"
        HOST[Claude Desktop/VS Code/Custom AI App]
        
        subgraph "Client Manager"
            CLIENT[MCP Client - Connection Manager]
        end
    end
    
    subgraph "Transport Layer"
        STDIO[stdio Transport - Local Development]
        HTTP[Streamable HTTP - Production]
    end
    
    subgraph "Project Analyzer MCP Server"
        ANALYZER[FastMCP Server - Project Analysis]
        
        subgraph "Tools"
            ANALYZE[analyze_project()]
            ANALYZE_FILE[analyze_file()]
            SEARCH[search_codebase()]
            EXPLAIN[explain_code_purpose()]
            AI_ANALYZE[ai_summarize_file()]
        end
        
        subgraph "Resources"
            PROJECT_DATA[project://structure]
            FILE_DATA[file://analysis/{path}]
        end
    end
    
    HOST --> CLIENT
    CLIENT -.->|stdio/HTTP| STDIO
    CLIENT -.->|HTTP| HTTP
    STDIO --> ANALYZER
    HTTP --> ANALYZER
    
    ANALYZER --> ANALYZE
    ANALYZER --> ANALYZE_FILE
    ANALYZER --> SEARCH
    ANALYZER --> EXPLAIN
    ANALYZER --> AI_ANALYZE
    
    ANALYZER --> PROJECT_DATA
    ANALYZER --> FILE_DATA
```

### Protocol Flow
1. **Initialization**: Client connects, capabilities negotiated
2. **Discovery**: Tools/resources listed and schemas provided
3. **Execution**: Tools called with validated parameters
4. **Results**: Structured responses with analysis data

## Core Development Principles

### 1. MCP Protocol Compliance
- **Specification Adherence**: Follow MCP 2025-06-18 specification strictly
- **JSON-RPC 2.0**: All protocol messages use JSON-RPC 2.0 format
- **Capability Declaration**: Properly declare server capabilities during initialization
- **Error Handling**: Use standard MCP error response formats

### 2. FastMCP Framework Usage
- **Decorators**: Use `@mcp.tool()`, `@mcp.resource()`, `@mcp.prompt()` appropriately
- **Context Objects**: Always include `Context` parameter for logging/progress
- **Structured Output**: Use Pydantic models, TypedDicts, or dataclasses
- **Lifespan Management**: Implement proper server lifecycle management

### 3. Tool Design Standards
- **Single Responsibility**: Each tool has one clear, well-defined purpose
- **Composability**: Tools work well together for complex workflows
- **Schema Validation**: All parameters have proper JSON schemas
- **Error Resilience**: Graceful error handling with meaningful messages

## File Organization Standards

### Directory Structure
```
src/
├── __init__.py                     # Package initialization
├── server.py                       # Main MCP server entry point
├── server_config.py                # Server configuration
├── error_handler.py                # Error handling utilities
├── core/                           # Core system functionality
│   ├── config.py                  # Configuration management
│   ├── constants.py               # System constants
│   ├── exceptions.py              # Custom exceptions
│   ├── file_manager.py            # File operations
│   ├── models.py                  # Data models
│   └── utils.py                   # Core utilities
├── analysis/                       # Analysis implementations
│   ├── analyzers.py               # General analyzers
│   ├── base.py                    # Base analyzer classes
│   ├── core_analysis.py           # Core analysis functions
│   ├── language_detection.py      # Language detection
│   ├── manager.py                 # Analysis coordination
│   ├── pattern_detection.py       # Pattern analysis
│   ├── project_insights.py        # Project insights
│   ├── quality_analyzer.py        # Code quality analysis
│   ├── security_analyzer.py       # Security analysis
│   ├── structure_analyzer.py      # Project structure analysis
│   └── utils.py                   # Analysis utilities
├── tools/                          # MCP tool implementations
│   ├── analysis.py                # Core analysis tools
│   ├── caching.py                 # Caching tools
│   ├── configuration.py           # Configuration tools
│   ├── enhanced_analysis.py       # AI-enhanced analysis tools
│   ├── prompts.py                 # Prompt management
│   └── resources.py               # Resource handlers
├── ai/                            # MCP-specific AI functionality (sampling, elicitation classes)
└── resources/                     # Resource management
```

### Module Responsibilities
- **server.py**: MCP server initialization, transport configuration, tool registration
- **core/**: Core system functionality, configuration, file management, models
- **analysis/**: All analysis implementations and coordination
- **tools/**: MCP tool implementations (core analysis, AI-enhanced, caching, configuration)
- **ai/**: MCP-specific AI functionality (sampling, elicitation classes)
- **cache/**: Caching system and utilities
- **resources/**: Resource management and handlers

## Code Quality Standards

### Python Specific Standards
- **Required imports**: Use `FastMCP`, `Context` from `mcp.server.fastmcp`
- **Type hints**: Import from `typing` and `typing_extensions` (TypedDict)
- **Tool definition**: Use `@mcp.tool()` decorator with async functions
- **Context parameter**: Always include `Context` parameter for logging/progress
- **Error handling**: Wrap in try/except with proper error logging via context
- **Progress reporting**: Use `await ctx.report_progress()` for long operations
- **Structured returns**: Return dictionaries with consistent key naming

### Error Handling Patterns
- **File operations**: Check existence, permissions, and encoding before reading
- **Context logging**: Use `ctx.debug()`, `ctx.info()`, `ctx.error()` appropriately
- **Exception mapping**: Convert specific exceptions to appropriate MCP errors
- **Graceful degradation**: Provide fallback responses when operations fail
- **Error propagation**: Re-raise with meaningful messages for upstream handling

### Structured Output Standards
- **Use TypedDict**: Define data structures with `TypedDict` for type checking
- **Consistent keys**: Use standard keys like `project_name`, `file_count`, `languages`
- **Optional fields**: Mark optional fields with `Optional[]` type hints
- **Timestamps**: Include ISO format timestamps for analysis results
- **Metadata**: Add analysis type and version information to responses

### AI Integration Standards
- **Sampling requests**: Use `ctx.session.create_message()` for AI completions
- **Prompt structure**: Include context, code snippets, and specific analysis requests
- **Token limits**: Set appropriate `max_tokens` based on expected response length
- **Fallback handling**: Provide non-AI analysis when sampling fails
- **Capability checking**: Test sampling availability before attempting AI features
- **Response processing**: Extract text content and structure appropriately

### Testing Standards
- **Mock Context**: Create mock Context objects with AsyncMock for logging methods
- **Fixtures**: Use pytest fixtures for common test setup (mock_context, tmp_path)
- **Async tests**: Mark tests with `@pytest.mark.asyncio` for async tool testing
- **Assertions**: Verify both return values and context method calls
- **Error scenarios**: Test invalid inputs and error handling paths
- **Integration**: Test MCP client-server communication with real protocol messages

### Server Configuration Standards
- **Server initialization**: Use `FastMCP()` with server name and optional lifespan management
- **Lifespan context**: Implement async context manager for resource setup/cleanup
- **Tool registration**: Import and register tools from module functions
- **Transport selection**: Use stdio for development, Streamable HTTP for production
- **Logging setup**: Configure appropriate log levels and formatters
- **Error handling**: Implement graceful shutdown and resource cleanup

### Environment Configuration
- **Default config**: Define configuration constants with sensible defaults
- **Environment variables**: Support `MCP_ANALYZER_*` prefix for configuration override
- **Type conversion**: Handle boolean, integer, and string environment variable conversion
- **Global access**: Provide module-level configuration instance for easy access
- **Key settings**: Configure server name, log level, file size limits, cache settings, AI timeouts

### Security Standards
- **Path validation**: Use `pathlib.Path.resolve()` to prevent path traversal attacks
- **Input sanitization**: Validate string inputs for length and dangerous characters
- **File permissions**: Check read/write permissions before file operations
- **Resource limits**: Implement concurrent operation limits and timeouts
- **Error information**: Avoid exposing sensitive system information in error messages

### Resource Management
- **Concurrent limits**: Use asyncio.Lock and global counters to limit concurrent operations
- **Context managers**: Implement async context managers for resource allocation/cleanup
- **Timeouts**: Set appropriate timeouts for long-running operations
- **Memory management**: Clean up large objects and temporary files
- **Error recovery**: Ensure resource cleanup even when operations fail

### Performance Standards
- **Caching strategy**: Use module-level cache dictionary with TTL and size limits
- **Cache key generation**: Create consistent cache keys from function parameters
- **Decorator pattern**: Implement caching decorators for expensive operations
- **Cache cleanup**: Remove expired entries and manage cache size limits
- **Async operations**: Use asyncio.Semaphore to limit concurrent expensive operations
- **Progress reporting**: Use context progress reporting for long-running tasks

### Development Workflow

#### Local Development Setup
```bash
# Environment setup with conda
conda env create -f environment.yml
conda activate mcp_project_analyzer
# OR: conda create -n mcp_project_analyzer python=3.11

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Development tools
python -m mcp dev src/server.py      # Interactive debugging
python -m mcp install src/server.py  # Install to Claude Desktop
pytest tests/ -v                     # Run tests
```

#### Debugging Guidelines
- **Logging levels**: Configure MCP and project-specific loggers for detailed output
- **Debug context**: Add debug information to tools using context methods
- **Exception handling**: Log exceptions with stack traces before re-raising
- **Development mode**: Use MCP Inspector for interactive tool testing

## Critical Development Context

### Live Development Reality
⚠️ **IMPORTANT**: This MCP Project Analyzer server IS the active MCP server being used in development environments. This means:

1. **Direct Testing**: Code changes immediately affect MCP tool behavior
2. **Real-time Validation**: Working tools prove implementations are functional
3. **User Experience**: We're simultaneously developers AND users of our MCP server
4. **Quality Critical**: Poor implementations directly impact developer productivity

### Common Development Pitfalls

#### 1. Import and Registration Issues
- **Wrong**: Defining functions inside registration functions (not importable)
- **Correct**: Define functions at module level, then register them
- **Solution**: Create module-level wrapper functions for problematic imports

#### 2. Running Server Directly
- **❌ NEVER**: `python server.py` or `cd src && python server.py` (server will hang)
- **✅ USE**: 
  - `python -m mcp dev src/server.py` (Interactive debugging)
  - `python -m mcp install src/server.py` (Install to Claude Desktop)
  - `pytest tests/` (Run tests)

#### 3. Quality vs "Just Working"
- Import fixes ≠ Quality fixes
- Test output quality, not just functionality
- Provide meaningful data, not placeholders
- User feedback indicates real quality issues

#### Quality Validation Process
- Test both import success AND output quality
- Verify MCP responses contain useful information
- Ensure fallbacks are meaningful, not "unknown"
- User feedback is critical quality indicator

## Conclusion

These instructions ensure consistent, high-quality MCP development across all Python files in the project. Following these patterns will result in:

- Reliable and maintainable MCP tools
- Consistent user experience across all analysis capabilities
- Proper error handling and resource management
- Effective testing and debugging capabilities
- Security and performance best practices

Remember: You're building both a solution AND a development tool. Quality, reliability, and user experience are paramount for MCP development success.