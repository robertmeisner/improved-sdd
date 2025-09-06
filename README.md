# Improved-SDD: Spec-Driven Development with Custom Templates

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Cross-Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](https://github.com/your-username/improved-sdd)

> **An enhanced Spec-Driven Development toolkit with customizable templates for AI-assisted software development**

Improved-SDD builds on the foundation of [GitHub's spec-kit](https://github.com/github/spec-kit) but provides your own custom templates for chatmodes, instructions, and prompts, enabling teams to build software systematically through requirements-driven workflows with AI assistants.

## 🌟 Key Features

- **🎯 Custom AI Templates**: Tailored chatmodes, instructions, and prompts for your specific workflow
- **🔄 Systematic Workflow**: Requirements → Design → Implementation → Validation
- **🤖 AI Assistant Integration**: Works with Claude Code, GitHub Copilot, Cursor, Gemini CLI, and others
- **🖥️ Cross-Platform**: PowerShell scripts for Windows, with plans for Bash scripts
- **📋 Progress Tracking**: Built-in todo management and implementation status tracking
- **🔒 Quality Gates**: Constitutional principles enforce code quality and consistency
- **📖 Template-Driven**: Reusable patterns for consistent, high-quality development

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** (required)
- **Git** (optional, recommended)
- **AI Assistant** (Claude Code, GitHub Copilot, Cursor, etc.)

### Installation

```bash
# Using uvx (recommended)
uvx --from git+https://github.com/your-username/improved-sdd.git improved-sdd init my-project

# Or clone and run directly
git clone https://github.com/your-username/improved-sdd.git
cd improved-sdd
python src/improved_sdd_cli.py init my-project
```

### Initialize Your First Project

```bash
# Create a new project
improved-sdd init my-awesome-project

# Or initialize in current directory
improved-sdd init --here

# Specify your AI assistant
improved-sdd init my-project --ai claude
improved-sdd init my-project --ai copilot
improved-sdd init my-project --ai cursor
```

## 📁 Project Structure

```
your-project/
├── templates/              # 🎨 Custom AI interaction templates
│   ├── chatmodes/         #    AI assistant behavior definitions
│   │   ├── specMode.chatmode.md
│   │   └── testMode.chatmode.md
│   ├── instructions/      #    Context-specific guidance
│   │   └── mcpDev.instructions.md
│   ├── prompts/          #    Reusable interaction patterns
│   │   ├── analyzeProject.prompt.md
│   │   ├── executeTask.prompt.md
│   │   └── doubleCheck.prompt.md
│   └── commands/         #    Command definitions (future)
├── scripts/              # ⚙️ PowerShell management scripts
│   ├── common.ps1
│   ├── create-new-feature.ps1
│   ├── setup-plan.ps1
│   └── check-task-prerequisites.ps1
├── memory/               # 📖 Project constitution and guidelines
│   ├── constitution.md
│   └── constitution_update_checklist.md
├── specs/               # 📝 Feature specifications (created as needed)
│   └── [###-feature]/
│       ├── feasibility.md
│       ├── requirements.md
│       ├── design.md
│       ├── tasks.md
│       └── retrospective.md
└── .github/             # 🔧 GitHub-specific configurations
    └── copilot-instructions.md
```

## 🔄 Spec-Driven Development Workflow

Improved-SDD follows a systematic workflow designed to work seamlessly with AI assistants:

### Phase 0: Feasibility Assessment
```markdown
- Technical feasibility evaluation
- Effort estimation
- Risk identification
- Go/no-go decision
```

### Phase 1: Requirements Gathering
```markdown
- User stories in clear format
- EARS (Easy Approach to Requirements Syntax) criteria
- Success metrics definition
- Out-of-scope documentation
```

### Phase 2: Design Creation
```markdown
- Technical architecture
- API contracts and interfaces
- Security considerations
- Performance requirements
```

### Phase 3: Task Planning
```markdown
- Implementation checklist
- Dependency mapping
- Parallel work identification
- Testing strategy
```

### Phase 4: Implementation & Validation
```markdown
- Code development following specifications
- Test-driven development
- Quality verification
- Requirements traceability
```

## 🎨 Template System

### Chatmodes
Define AI assistant behavior patterns for different development contexts:

- **`specMode.chatmode.md`**: Complete spec-driven development workflow
- **`testMode.chatmode.md`**: Testing and quality assurance focus
- **Custom modes**: Create your own for specific domains

### Instructions
Provide context-specific guidance for AI assistants:

- **`mcpDev.instructions.md`**: MCP (Model Context Protocol) development guidelines
- **Domain-specific**: Add instructions for your technology stack

### Prompts
Reusable interaction patterns for common development tasks:

- **`analyzeProject.prompt.md`**: Comprehensive project analysis
- **`executeTask.prompt.md`**: Structured task execution framework
- **`doubleCheck.prompt.md`**: Quality validation and review

## 🤖 AI Assistant Integration

### GitHub Copilot (VS Code)
```markdown
1. Open your project in VS Code
2. Use .github/copilot-instructions.md for context
3. Apply chatmode templates in your interactions
4. Follow the spec-driven workflow
```

### Claude Code
```markdown
1. Import chatmode templates
2. Use structured prompts for development tasks
3. Follow constitutional principles
4. Leverage spec synchronization features
```

### Cursor AI
```markdown
1. Configure with chatmode templates
2. Use instructions for context-specific guidance
3. Apply prompts for consistent interactions
4. Follow quality gates
```

### Other AI Assistants
The template system is designed to be adaptable to any AI assistant that supports structured prompts and context.

## ⚙️ PowerShell Scripts

Improved-SDD includes PowerShell scripts for Windows development environments:

### `create-new-feature.ps1`
```powershell
# Create a new feature branch and spec structure
.\scripts\create-new-feature.ps1 "user authentication system"
.\scripts\create-new-feature.ps1 -Json "payment integration"
```

### `setup-plan.ps1`
```powershell
# Initialize planning documents for current feature
.\scripts\setup-plan.ps1
.\scripts\setup-plan.ps1 -Json
```

### `check-task-prerequisites.ps1`
```powershell
# Verify all required documents exist before task execution
.\scripts\check-task-prerequisites.ps1
.\scripts\check-task-prerequisites.ps1 -Json
```

## 📜 Constitutional Principles

Improved-SDD follows constitutional principles that ensure quality and consistency:

### Core Principles
1. **Template-First Development**: Every workflow uses structured templates
2. **Spec-Driven Methodology**: Requirements → Design → Implementation → Validation
3. **Code Minimalism**: Maximum value with minimum code
4. **Multi-Platform Compatibility**: Support for Windows, macOS, and Linux
5. **AI Assistant Integration**: Built for modern AI-assisted development
6. **Observability**: Transparent development process with progress tracking
7. **Security & Best Practices**: Security and quality by design

### Quality Gates
- Feasibility assessment approval
- Requirements document approval  
- Design document approval
- Task list approval
- Implementation validation

## 🔧 Development Workflow Example

### 1. Create a New Feature
```powershell
# Start a new feature
.\scripts\create-new-feature.ps1 "real-time chat system"
```

### 2. Requirements Phase
```markdown
# Use specMode.chatmode.md with your AI assistant
- Define user stories
- Create acceptance criteria in EARS format
- Set success metrics
- Document out-of-scope items
```

### 3. Design Phase
```markdown
# Continue with specMode for technical design
- Create system architecture
- Define API contracts
- Plan data models
- Consider security and performance
```

### 4. Implementation Phase
```markdown
# Use executeTask.prompt.md for development
- Follow task checklist
- Implement with TDD approach
- Maintain spec synchronization
- Use doubleCheck.prompt.md for quality
```

## 🎯 Template Customization

### Creating Custom Chatmodes
```markdown
Create `templates/chatmodes/yourMode.chatmode.md`:

```chatmode
---
description: 'Your custom AI assistant behavior'
tools: ['relevant', 'tools', 'list']
---
# Your Custom Mode

## Identity
Define the AI assistant's role and purpose

## Capabilities
List what the assistant can do

## Rules
Set behavioral guidelines

## Workflow
Define the step-by-step process
```

### Adding Domain Instructions
```markdown
Create `templates/instructions/yourDomain.instructions.md`:

```instructions
---
applyTo: '**/*.yourExtension'
---
# Your Domain Instructions

## Overview
Domain-specific context and guidelines

## Standards
Quality and coding standards

## Best Practices
Recommended approaches and patterns
```

### Custom Prompts
```markdown
Create `templates/prompts/yourTask.prompt.md`:

```prompt
---
mode: agent
---
# Your Task Template

## Objective
Clear task description

## Process
Step-by-step execution guide

## Output Format
Expected response structure
```

## 🧪 Testing and Quality

### Built-in Quality Measures
- Constitutional compliance checking
- Requirements ↔ Design ↔ Code synchronization
- Implementation status tracking
- Progress monitoring through all phases

### Testing Support
- Test-driven development enforcement
- Quality validation prompts
- Code review templates
- Performance consideration guidelines

## 🤝 Contributing

1. **Fork the repository**
2. **Follow constitutional principles** in `memory/constitution.md`
3. **Create feature specs** using the spec-driven workflow
4. **Test with multiple AI assistants** to ensure compatibility
5. **Submit pull requests** with clear documentation

### Development Setup
```bash
# Clone the repository
git clone https://github.com/your-username/improved-sdd.git
cd improved-sdd

# Initialize development environment
python src/improved_sdd_cli.py init --here --ai your-assistant

# Follow the constitutional guidelines
cat memory/constitution.md
```

## 📚 Documentation

- **[Constitutional Principles](memory/constitution.md)**: Core principles and quality gates
- **[Template Guide](docs/templates.md)**: How to create and customize templates
- **[AI Integration Guide](docs/ai-integration.md)**: AI assistant specific setup
- **[PowerShell Scripts Guide](docs/scripts.md)**: Script usage and customization
- **[Workflow Examples](docs/examples.md)**: Real-world usage scenarios

## 🔮 Roadmap

### Version 1.1 (Planned)
- [ ] Bash script equivalents for macOS/Linux
- [ ] Web-based template editor
- [ ] Integration with more AI assistants
- [ ] Advanced template inheritance system

### Version 1.2 (Future)
- [ ] Visual workflow designer
- [ ] Template marketplace
- [ ] Advanced analytics and metrics
- [ ] Team collaboration features

## 🐛 Troubleshooting

### Common Issues

**PowerShell Execution Policy**
```powershell
# If scripts won't run, update execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Git Not Found**
```bash
# Install git and ensure it's in PATH
# Windows: https://git-scm.com/download/win
# macOS: brew install git
# Linux: sudo apt install git
```

**Python Version Issues**
```bash
# Ensure Python 3.11+ is installed
python --version
# If needed: https://python.org/downloads
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **[GitHub Spec-Kit](https://github.com/github/spec-kit)**: Foundation and inspiration for spec-driven development
- **[FastMCP](https://github.com/modelcontextprotocol/python-sdk)**: Model Context Protocol implementation
- **AI Assistant Communities**: Claude, GitHub Copilot, and Cursor development communities

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-username/improved-sdd/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/improved-sdd/discussions)
- **Documentation**: [Project Wiki](https://github.com/your-username/improved-sdd/wiki)

---

**Built with ❤️ for the AI-assisted development community**