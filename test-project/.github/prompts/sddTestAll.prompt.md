# Pragmatic Codebase Testing & Fix Agent

## Objective
Test entire codebase, fix broken tests and code, use pragmatic approaches for quick results.

## Context
- **Framework**: pytest with Python (asyncio support enabled)
- **Package Manager**: pip/conda
- **Architecture**: Backend in `src/` (current), Frontend in `frontend/` (coming soon)
- **Default Focus**: Backend testing unless frontend explicitly requested
- **Test Locations**: Backend tests in `tests/`, Frontend tests in `frontend/` (when available)
- **Focus**: Fix what's broken, skip perfection

## Execution Instructions

### 1. Discovery
- List all test files using `pytest --collect-only` or `pytest --collect-only -q`
- Check current test status with `pytest --tb=short`
- Identify coverage with `pytest --cov=src --cov-report=term-missing`
- Use Python environment activation: Check `conda activate` or `venv activation`
- **Backend Focus**: Test backend by default (tests/)
- **Frontend Optional**: Test frontend when available with separate test runner

### 2. Test Execution Order
```bash
# Use pytest commands for Python project
# Backend testing (default/current)
1. pytest -x                                         # Stop on first failure
2. pytest tests/ --tb=short                          # Quick test run with short traceback
3. pytest -m "not slow"                              # Skip slow tests
4. pytest --cov=src --cov-report=html                # Coverage check

# Backend-specific patterns
5. pytest tests/test_config.py -v                    # Config module tests
6. pytest tests/test_cache_manager.py -v             # Cache module tests
7. pytest tests/test_server.py -v                    # Server tests
8. pytest -m unit                                    # Unit tests only
9. pytest -m integration                             # Integration tests only

# Module-specific testing
10. pytest tests/test_enhanced_cache.py -v           # Enhanced cache tests
11. pytest tests/ -k "cache" -v                      # All cache-related tests
12. pytest tests/ -k "config" -v                     # All config-related tests
13. pytest --cov=src tests/ --cov-report=html        # Full coverage report
```

### 3. Fix Priority
1. **Build/Compilation errors** - Code won't run
2. **Test setup failures** - Before/After hooks
3. **Test assertion failures** - Logic issues
4. **Flaky tests** - Timing/async issues
5. **Missing tests** - Coverage gaps

### 4. Pragmatic Rules
- Fix the test if it's wrong, fix the code if it's broken
- Skip perfect coverage, aim for critical paths
- Use `--cache-clear` if tests behave unexpectedly
- Add `--tb=long` for debugging complex failures
- Quick fixes over architectural rewrites
- **Python Environment**: Always ensure virtual environment is activated
- **Test timeout**: Configure in pytest.ini or use `--timeout=10`
- **Backend Priority**: Always test backend first, frontend only when requested or available

### 5. Common pytest Fixes
- Hanging tests: Use `pytest-timeout` or `--timeout=10` flag
- Async issues: Ensure `pytest-asyncio` is installed and `asyncio_mode = auto` in pytest.ini
- Mock issues: Use `unittest.mock` or `pytest-mock` with proper cleanup in `yield` fixtures
- Database locks: Proper async cleanup with `await manager.cleanup()` in fixtures
- Import issues: Check `PYTHONPATH` and module resolution, use `src/` as source root
- Setup issues: Check `pytest.ini` configuration and fixture scoping
- Windows file locks: Add proper async cleanup and `asyncio.sleep()` delays
- Frontend config: May need separate test runner for frontend/ when implemented

## Required Output

### Summary
- Total tests: Before vs After (separated by backend/frontend when applicable)
- Passing rate: Before vs After (backend priority)
- Coverage: Before vs After (backend priority)
- Time to run: Before vs After
- Test modules: Backend (Cache, Config, Server, Analysis), Frontend (when available)

### Critical Fixes
- List each broken test/code fixed
- Show the actual fix applied
- Confirm fix works
- Indicate module (backend: cache/config/server/analysis, frontend: when available)

### Remaining Issues
- What couldn't be fixed automatically
- Why it needs manual intervention
- Suggested approach
- Module-specific issues (backend vs frontend)

### Commands for CI/CD
- Provide working test commands for pipeline
- Include any special flags needed
- Use pytest commands for consistency: `pytest tests/`, `pytest --cov=src`
- Separate backend and frontend commands when frontend/ exists

## Response Constraints
- Show actual code fixes, not descriptions
- Provide executable commands, not explanations
- Focus on results, not process
- Use pytest commands and Python best practices
- Default to backend testing unless frontend explicitly requested
- Reference actual project structure (current: tests/, future: frontend/)
