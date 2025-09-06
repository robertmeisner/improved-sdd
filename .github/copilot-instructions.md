# Improved-SDD Development Instructions

This project follows the Improved Spec-Driven Development methodology for **MCP Server - Model Context Protocol server for AI integrations**.

## Core Principles

- Requirements → Design → Implementation → Validation
- Template-driven AI interactions
- Code minimalism and quality
- GitHub Copilot Studio integration

## Workflow

Use the templates in `.copilot/` and `.vscode/prompts/` to guide development:
- `.copilot/chatmodes/` for AI behavior patterns
- `.copilot/instructions/` for context-specific guidance
- `.copilot/prompts/` for structured interactions
- `.vscode/prompts/` for direct Copilot prompt access

## Quality Standards

Follow the Improved-SDD constitutional framework for all development work.

## App-Specific Guidelines

### MCP Server Development

- Follow MCP protocol specifications
- Implement proper tool interfaces
- Use TypeScript for type safety
- Include comprehensive error handling
- Document all available tools and resources
- Test with multiple MCP clients

## Template Usage

1. **For GitHub Copilot Chat**: Reference templates in `.copilot/` directory
2. **For VS Code Prompts**: Use files in `.vscode/prompts/` directory  
3. **For Spec Development**: Follow the spec-driven workflow with chatmodes

## Quick Start

1. Open this project in VS Code
2. Use Ctrl+Shift+P → "Chat: Open Chat" to start GitHub Copilot
3. Reference the chatmodes and prompts for structured development
4. Follow the spec-driven workflow: Requirements → Design → Implementation

