# Improved-SDD CLI Usage

## Installation

### Option 1: Using pip (recommended for regular use)
```bash
# Install dependencies
pip install -r requirements.txt

# Run the CLI
python src/improved_sdd_cli.py --help
python src/improved_sdd_cli.py init
python src/improved_sdd_cli.py init --app-type mcp-server
python src/improved_sdd_cli.py init my-project --new-dir
```

### Option 2: Using uv (for development)
```bash
# Run directly with uv (no installation needed)
uvx src/improved_sdd_cli.py init
uv run src/improved_sdd_cli.py init
```

## Commands

- `init` - Install Improved-SDD templates for GitHub Copilot Studio
- `check` - Check that all required tools are installed

## Common Usage

```bash
# Install in current directory
python src/improved_sdd_cli.py init

# Create new project directory
python src/improved_sdd_cli.py init my-project --new-dir

# Skip confirmation prompts
python src/improved_sdd_cli.py init --force

# Specify app type
python src/improved_sdd_cli.py init --app-type python-cli
```
