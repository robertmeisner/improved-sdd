# Publishing to PyPI

## Prerequisites

1. **Create PyPI Account**: https://pypi.org/account/register/
2. **Create TestPyPI Account**: https://test.pypi.org/account/register/
3. **Get API Tokens**:
   - PyPI: https://pypi.org/manage/account/token/
   - TestPyPI: https://test.pypi.org/manage/account/token/
   - Create tokens scoped to this project
   - Save them securely (you'll need them for uploading)

## Publishing Steps

### 1. Update Version
```bash
# Edit pyproject.toml and bump the version
version = "0.1.1"  # or whatever the next version should be
```

### 2. Build the Package
```bash
# Clean previous builds
rm -rf dist/ build/

# Build new distribution
python -m build
```

### 3. Test with TestPyPI First
```bash
# Upload to TestPyPI for testing
twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ improved-sdd

# Test the CLI
improved-sdd --help
```

### 4. Upload to Production PyPI
```bash
# After successful TestPyPI testing, upload to production
twine upload dist/*

# View your package at: https://pypi.org/project/improved-sdd/
```

## Using with uvx

Once published to PyPI, users can install and run your tool with:

```bash
# Run directly (uvx manages the virtual environment)
uvx improved-sdd init

# Install persistently
uvx install improved-sdd
improved-sdd init

# Run specific commands
uvx improved-sdd check
uvx improved-sdd init --help
```

## Alternative Installation Methods

```bash
# pipx (similar to uvx)
pipx install improved-sdd

# pip in virtual environment
pip install improved-sdd

# pip with user flag
pip install --user improved-sdd

# From TestPyPI (for testing)
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ improved-sdd
```

## Testing Before Publishing

Always test locally first:

```bash
# Build the package
python -m build

# Install locally
pip install dist/improved_sdd-*.whl

# Test the CLI
improved-sdd --help
```

## Version Management

Follow semantic versioning:
- **0.1.0** → **0.1.1**: Bug fixes
- **0.1.0** → **0.2.0**: New features (backward compatible)
- **0.1.0** → **1.0.0**: Breaking changes

## Repository Integration

Consider setting up GitHub Actions for automated publishing:
- Build on every push
- Publish to TestPyPI on pull requests
- Publish to PyPI on git tags
- Run tests before publishing

## Useful Links

- **Live Package**: https://pypi.org/project/improved-sdd/
- **TestPyPI Package**: https://test.pypi.org/project/improved-sdd/
- **Twine Documentation**: https://twine.readthedocs.io/
- **PyPI Publishing Guide**: https://packaging.python.org/en/latest/tutorials/packaging-projects/
