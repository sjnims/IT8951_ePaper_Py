<!-- markdownlint-disable MD013 MD029 MD036 -->
# Roadmap Priorities - Remaining Open Items

## Executive Summary

After completing Phases 1-5, we have 5 remaining phases with items prioritized by impact on code quality, performance, and user experience.

## 🔥 High Priority - Immediate Impact

### Phase 6: Code Quality & Architecture Improvements (v0.6.0)

**Impact: High | Effort: Low-Medium | Timeline: 1-2 weeks**

These items directly improve code maintainability and performance:

1. **Refactor Duplicated Alignment Logic** (~5% code duplication)
   - Single source of truth for alignment rules
   - Reduces maintenance burden

2. **Extract Remaining Magic Numbers**
   - LUT_BUSY_BIT = 0x80
   - LUT_STATE_BIT_POSITION = 7
   - Improves code readability

3. **Numpy-based Pixel Packing Optimization**
   - 5-10x performance improvement potential
   - Critical for large image operations

4. **Fix Configuration Inconsistencies**
   - NumPy version mismatch (pyproject.toml vs README)
   - Tool version alignment
   - Prevents user confusion

## 🎯 Medium Priority - Quality of Life

### Phase 7: Debugging and Diagnostics (v0.7.0)

**Impact: Medium | Effort: Medium | Timeline: 1-2 weeks**

Enables better troubleshooting:

1. **Extended Display Mode Testing** (GLR16, GLD16, DU4)
   - Currently defined but untested
   - Could unlock performance for specific use cases

### Phase 8: Developer Experience (v0.8.0)

**Impact: Medium | Effort: Low | Timeline: 1 week**

Improves developer onboarding:

1. **Enhanced Examples**
   - Performance optimization guide
   - Battery-powered device example
   - Mode selection guide

2. **Comprehensive Testing**
   - Performance benchmarks
   - Power management tests

## 🔧 Low Priority - Nice to Have

### Phase 9: CI/CD Optimizations (v0.9.0)

**Impact: Low (internal) | Effort: High | Timeline: 2-3 weeks**

Speeds up development workflow:

1. **Test Parallelization** (currently disabled)
   - Reduce CI time from ~5min to <3min
   - Fix test isolation issues

2. **Codecov ATS Integration**
   - Run only affected tests
   - Faster PR feedback

### Phase 10: Long-term Enhancements (v1.0.0)

**Impact: Low (future-proofing) | Effort: High | Timeline: 1-2 months**

Architectural improvements:

1. **Design Patterns**
   - Builder pattern for complex operations
   - Plugin architecture

2. **Async Support**
   - Non-blocking operations
   - Better for web applications

## 📊 Impact vs Effort Matrix

```text
High Impact ┃ Phase 6: Code Quality │ Phase 7: Diagnostics
            ┃ (Quick wins)          │ (Medium effort)
            ┃───────────────────────┼─────────────────────
Low Impact  ┃ Phase 8: Dev UX       │ Phase 9: CI/CD
            ┃ (Easy)                │ Phase 10: Long-term
            ┗━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━
              Low Effort               High Effort
```

## 🎬 Recommended Action Plan

### Next 2 Weeks (Phase 6)

1. **Day 1-2**: Fix configuration inconsistencies and extract magic numbers
2. **Day 3-5**: Refactor alignment logic (biggest code quality win)
3. **Week 2**: Implement numpy pixel packing optimization (biggest performance win)

### Following Month

4. **Week 3-4**: Phase 7 - Test extended display modes
5. **Week 5**: Phase 8 - Add missing examples and benchmarks

### Future Considerations

- Phase 9 (CI/CD) - Only if test times become painful
- Phase 10 (Long-term) - Consider for v1.0.0 release

## 💡 Key Insights

1. **Phase 6 delivers the most immediate value** with code quality improvements that benefit both maintainers and users

2. **Performance optimization in Phase 6** (numpy pixel packing) could provide 5-10x speedup for a few days of work

3. **Phases 9-10 are lower priority** as the current CI/CD works adequately and the architecture is already clean

4. **Focus on user-visible improvements** rather than internal optimizations unless they become pain points

## 📈 Success Metrics

- **Phase 6**: Reduce code duplication from ~5% to <3%, achieve 5x pixel packing speedup
- **Phase 7**: Document all display modes with examples
- **Phase 8**: Add 5+ new examples covering edge cases
- **Phase 9**: Reduce CI time to <3 minutes
- **Phase 10**: Prepare for v1.0.0 with stable API
