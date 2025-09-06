"""Sample test data and configurations for improved-sdd tests."""

# Sample AI tools configuration
SAMPLE_AI_TOOLS = {
    "test-ai": {
        "name": "Test AI Assistant",
        "description": "AI assistant for testing",
        "template_dir": "test",
        "file_extensions": {
            "chatmodes": ".test.md",
            "instructions": ".test.md",
            "prompts": ".test.md",
            "commands": ".test.md"
        },
        "keywords": {
            "{AI_ASSISTANT}": "Test AI Assistant",
            "{AI_SHORTNAME}": "TestAI",
            "{AI_COMMAND}": "test-command"
        }
    }
}

# Sample app types
SAMPLE_APP_TYPES = {
    "test-app": "Test Application - For testing purposes only",
}

# Sample template content with placeholders
SAMPLE_TEMPLATE_CONTENT = """# Template for {AI_ASSISTANT}

This is a test template for {AI_SHORTNAME}.

Use {AI_COMMAND} to activate.

## Features
- Feature 1
- Feature 2
- Feature 3
"""

# Expected customized content for test-ai
EXPECTED_CUSTOMIZED_CONTENT = """# Template for Test AI Assistant

This is a test template for TestAI.

Use test-command to activate.

## Features
- Feature 1
- Feature 2
- Feature 3
"""

# Sample project files for testing
SAMPLE_PROJECT_FILES = {
    "README.md": "# Test Project\n\nThis is a test project.",
    "main.py": "#!/usr/bin/env python3\nprint('Hello, World!')",
    "requirements.txt": "typer>=0.9.0\nrich>=13.0.0",
    "pyproject.toml": """[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"

[project]
name = "test-project"
version = "0.1.0"
""",
}

# Sample .github structure for testing
SAMPLE_GITHUB_STRUCTURE = {
    "chatmodes": ["specMode.md", "testMode.md"],
    "instructions": ["CLIPythonDev.md", "mcpDev.md"],
    "prompts": ["analyzeProject.md", "commitAnalysis.md"],
    "commands": ["testCommand.md", "buildCommand.md"],
}

# Test user inputs for interactive commands
TEST_USER_INPUTS = {
    "app_type_selection": ["1", "2"],  # First and second app type options
    "ai_tools_selection": ["1", "2", "all"],  # Various AI tool selections
    "confirmation_yes": ["y", "yes", "Y", "YES"],
    "confirmation_no": ["n", "no", "N", "NO"],
    "deletion_confirmation": ["Yes", "No"],
}

# Mock tool availability scenarios
TOOL_AVAILABILITY_SCENARIOS = {
    "all_available": {
        "python": "/usr/bin/python",
        "code": "/usr/bin/code",
        "git": "/usr/bin/git",
        "claude": "/usr/bin/claude",
    },
    "python_only": {
        "python": "/usr/bin/python",
        "code": None,
        "git": None,
        "claude": None,
    },
    "none_available": {
        "python": None,
        "code": None,
        "git": None,
        "claude": None,
    },
}

# Expected file structures after operations
EXPECTED_STRUCTURES = {
    "github_copilot_python_cli": {
        ".github/chatmodes/specMode.chatmode.md": True,
        ".github/chatmodes/testMode.chatmode.md": True,
        ".github/instructions/CLIPythonDev.instructions.md": True,
        ".github/instructions/mcpDev.instructions.md": False,  # Should not exist
        ".github/prompts/analyzeProject.prompt.md": True,
        ".github/commands/testCommand.command.md": True,
    },
    "claude_mcp_server": {
        ".github/claude/chatmodes/specMode.claude.md": True,
        ".github/claude/instructions/mcpDev.claude.md": True,
        ".github/claude/instructions/CLIPythonDev.claude.md": False,  # Should not exist
    },
    "multiple_ai_tools": {
        # GitHub Copilot files (root .github)
        ".github/chatmodes/specMode.chatmode.md": True,
        ".github/instructions/CLIPythonDev.instructions.md": True,
        # Claude files (claude subdirectory)
        ".github/claude/chatmodes/specMode.claude.md": True,
        ".github/claude/instructions/CLIPythonDev.claude.md": True,
    },
}