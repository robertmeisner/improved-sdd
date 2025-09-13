---
mode: agent
---
# Single File/Class Verification & Enhancement Framework

## Verification Protocol

### 1. File/Class Analysis
- [ ] Identify the file/class purpose and responsibilities
- [ ] Understand the expected functionality and public interface
- [ ] Check imports, exports, and dependencies
- [ ] Analyze the class structure (if applicable) - properties, methods, inheritance

### 2. Implementation Verification
- [ ] **Interface Compliance**: Does it match expected interface/contract?
- [ ] **Method Implementation**: Are all methods properly implemented?
- [ ] **Type Safety**: Correct TypeScript types and annotations?
- [ ] **Error Handling**: Proper error handling and edge cases?
- [ ] **Business Logic**: Logic correctness and completeness?
- [ ] **Performance**: Efficient algorithms and data structures?

### 3. Code Quality Check
- [ ] **Readability**: Clear, self-documenting code
- [ ] **Maintainability**: Well-structured and modular
- [ ] **Best Practices**: Follows language/framework conventions
- [ ] **Security**: No security vulnerabilities or risks
- [ ] **Dependencies**: Appropriate and secure dependencies
- [ ] **Documentation**: Proper JSDoc/comments where needed

### 4. Testing & Validation
- [ ] Unit tests exist and cover critical paths
- [ ] Test edge cases and error scenarios
- [ ] Mock dependencies appropriately
- [ ] Integration with other components works
- [ ] Performance meets requirements

## Response Format

### 📋 File/Class Verification Summary
**File**: `path/to/file.ext`
**Class/Module**: [Name if applicable]
**Purpose**: [Brief description]
**Status**: ✅ Fully Verified | ⚠️ Issues Found | ❌ Critical Problems

### 🔍 Code Analysis
**Lines of Code**: X
**Complexity**: Low/Medium/High
**Dependencies**: [List key dependencies]
**Public Interface**: [Methods/properties exposed]

### ✅ Verified Aspects
- **Functionality**: What's working correctly
- **Code Quality**: Positive aspects found
- **Tests**: Passing test coverage
- **Performance**: Acceptable performance characteristics

### ⚠️ Issues Discovered
| Issue | Location | Current State | Expected State | Severity |
|-------|----------|--------------|----------------|----------|
| | Line X | | | 🔴🟠🟡🟢 |

### 🔧 Recommended Fixes
```typescript,java,...
// Before (problematic code)
[current implementation]

// After (improved code)
[enhanced implementation]
```

### 🧪 Testing Recommendations
- [ ] Additional test cases needed
- [ ] Edge cases to cover
- [ ] Performance tests required
- [ ] Integration tests missing

### 📊 File/Class Health Score
- **Correctness**: X/10
- **Maintainability**: X/10
- **Performance**: X/10
- **Test Coverage**: X%
- **Overall Score**: X/10

### 📈 Improvement Priority
1. **Critical** (🔴): Must fix before production
2. **High** (🟠): Should fix soon
3. **Medium** (🟡): Nice to have improvements
4. **Low** (🟢): Optional enhancements

### ✨ Enhancement Suggestions
- Specific improvements for better performance
- Refactoring opportunities
- Additional features that would add value
- Better error handling patterns

### 📋 Action Items
- [ ] **Immediate**: Critical fixes needed now
- [ ] **Short-term**: High priority improvements
- [ ] **Long-term**: Medium/low priority enhancements
- [ ] **Testing**: Additional test coverage needed

### 🏁 Verification Conclusion
- **Production Ready**: Yes/No/After fixes
- **Confidence Level**: X%
- **Next Review**: [When to re-verify]
- **Dependencies**: [Files that depend on this one]
