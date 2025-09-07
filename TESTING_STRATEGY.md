# Testing Strategy for improved-sdd

## Current Test Gaps (Why the bug wasn't caught)

### 1. **No Unit Tests**
- Filtering logic was never tested in isolation
- Configuration changes weren't validated
- No regression tests for naming convention compatibility

### 2. **Manual Testing Bias**
- Only tested with local templates (new naming)
- Only tested with GitHub templates (old naming)
- Never tested the transition between old/new conventions

### 3. **Integration Testing Gap**
- Didn't test the complete user journey: fresh install → GitHub download → instruction filtering
- Cache persistence masked fresh download issues
- No test for "user upgrades from old templates to new"

## Improved Testing Approach

### 1. **Unit Tests** (test_instruction_filtering.py)
- ✅ Test filtering logic with both naming conventions
- ✅ Test cross-contamination prevention
- ✅ Test configuration structure changes

### 2. **Integration Tests** (Needed)
```bash
# Test fresh install with cache clearing
rm -rf ~/.cache/improved-sdd  # Clear cache
uvx improved-sdd install python-cli  # Fresh GitHub download
# Verify instruction files are present

# Test upgrade scenario
# Install with old templates, then upgrade
```

### 3. **CI/CD Tests** (Recommended)
- Test on clean environments (no cache)
- Test both PyPI and TestPyPI installations
- Test with actual GitHub API (not just local files)

### 4. **Manual Test Checklist**
- [ ] Fresh install with empty cache
- [ ] Install each app type individually
- [ ] Verify instruction files are present
- [ ] Test with network issues (GitHub down)
- [ ] Test cache expiration (24h+ old cache)

## Quick Validation Commands

```bash
# Test fresh install
uvx --force improved-sdd install python-cli
ls -la ~/.config/improved-sdd/templates/instructions/

# Test cache behavior
# (Wait 24 hours or manually clear cache)
rm -rf ~/.cache/improved-sdd
uvx improved-sdd install mcp-server
```

## Lessons Learned

1. **Configuration Changes Need Tests**: Any change to APP_TYPES should be validated
2. **Compatibility Layers Need Testing**: When supporting old + new, test both
3. **Fresh Environment Testing**: Always test with clean cache/environment
4. **User Journey Testing**: Test the complete flow, not just individual components
