# Task Verification & Enhancement Framework

## Verification Protocol

### 1. Completion Status Check
- [ ] Identify what was supposed to be done
- [ ] Locate what has been implemented
- [ ] Compare requirements vs. actual implementation

### 2. Quality Verification
- [ ] **Correctness**: Does it solve the stated problem?
- [ ] **Completeness**: Are all requirements fully addressed?
- [ ] **Robustness**: Error handling and edge cases covered?
- [ ] **Security**: No vulnerabilities or risks introduced?
- [ ] **Best Practices**: Follows standards for this task type?
- [ ] **Dependencies**: If applicable, are they current and secure?

### 3. Testing & Validation
- Test the implementation
- Verify expected outputs
- Check failure scenarios
- Validate performance

## Response Format

### 📋 Verification Summary
**Task**: [What was requested]
**Implementation Status**: ✅ Found | ⚠️ Partial | ❌ Not Found
**Verification Result**: ✅ Verified | ⚠️ Issues Found | ❌ Failed

### ✅ Verified Working
- What's correctly implemented
- Tests that passed

### ⚠️ Issues Discovered
| Issue | Current State | Expected State | Severity |
|-------|--------------|----------------|----------|
| | | | 🔴🟠🟡🟢 |

### 🔧 Improvements Made/Needed
```[enhanced code/solution if applicable]```

### 📊 Verification Outcome
- **Confidence Level**: X%
- **Production Ready**: Yes/No/After fixes
- **Action Required**: None/Minor fixes/Major rework
