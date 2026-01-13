# Deferred Issues & Fix Tasks

**Purpose:** Track gaps, bugs, and enhancements identified during audit for future implementation.

**Status Key:**
- 🔴 **CRITICAL** - Blocks V1 certification or significantly impacts core claims
- 🟡 **IMPORTANT** - Should be fixed before V1 but not blocking
- 🟢 **ENHANCEMENT** - Nice-to-have improvements for V1.1+

---

## Critical Fixes (Must Fix Before V1)

### ISS-001: Implement Small File Auto-Bypass

**Priority:** CRITICAL
**Category:** Performance / Token Savings
**Status:** Open
**Assigned to:** Phase 7 (Small File Overhead Assessment)

**Problem:**
Progressive disclosure adds significant overhead for small files (< 300 lines):
- Summary view: 1,125 tokens (constant overhead)
- Small files: 149-254 tokens (full read)
- Result: 4 of 10 simple tasks show negative token savings (-474% to -655%)
- Current token savings: -95.6% (optimized WORSE than baseline)

**Impact:**
- **CRITICAL**: Token savings claim REFUTED (-95.6% vs claimed 23%)
- 4 of 10 simple tasks fail validation
- User experience degraded for common small file operations

**Required Fix:**
Implement automatic small file bypass in AuZoom MCP server:

```python
# In auzoom_read handler
def handle_read(path: str, level: str = "skeleton") -> Dict:
    file_info = get_file_info(path)

    # Auto-bypass for small files
    if file_info.line_count < 300:  # Threshold from audit
        return read_full_file(path)  # Use Read tool equivalent

    # Otherwise use progressive disclosure
    return progressive_read(path, level)
```

**Implementation:**
- Add line count check before progressive disclosure decision
- If file < 300 lines, return full content directly
- Bypass skeleton/summary generation for small files
- Document bypass in MCP tool response

**Expected impact:**
- Fix 4 of 10 failing tasks
- Token savings improve from -95.6% to positive
- Cost savings remain at 50.7% (already optimal on small files due to model routing)

3. **ISS-002: Real Claude Code Task execution validation**

**Priority:** Medium (Strategic validation)
**Effort:** High (15-30 hours, $2-10 API costs)
**Target:** Phase 12 or Post-V1

**Problem:**
- File measurements used instead of real Claude Code Task execution
- Token estimates for progressive disclosure (not actual MCP responses)
- Quality validation incomplete (no pass/fail scoring)

**Required changes:**
1. Create comprehensive test harness using Task tool
2. Spawn agents for all 25 tasks (10 simple + 15 challenging)
3. Measure actual API token consumption (not file estimates)
4. Validate quality with objective scoring framework
5. Compare to claimed metrics with real execution data

**Expected impact:**
- Definitive validation of all claims (cost, token, quality)
- Real MCP server progressive disclosure measurements
- Objective quality scores (not subjective)

**Deferred to:** Phase 12 (Final Certification) or post-V1 production validation
**Reason:** Cost ($2-10) and time (15-30 hours) prohibitive for audit phase

---

## ISS-002: Fix Small File Overhead (Auto-Bypass)

**Status:** Open
**Priority:** CRITICAL (P0)
**Severity:** High - Affects 40% of simple tasks (4 of 10)
**Created:** 2026-01-13 (Phase 5-03 Audit)
**Discovered in:** Phase 5-01 validation (Task 1)

**Problem:**
Progressive disclosure adds significant token overhead for small files (<300 lines):
- Summary view: 1,125 tokens (constant overhead)
- Small files: 149-254 tokens (full read)
- Result: 4 of 10 simple tasks show -474% to -655% token increases

**Impact:**
- Token savings claim REFUTED (-95.6% vs 23% claimed)
- 40% of simple tasks fail due to this issue
- Cost savings reduced (50.7% vs 79.5% claimed)

**Current behavior:**
```python
# Always use progressive disclosure, regardless of file size
response = auzoom_read(path, level="summary")  # 1,125 tokens overhead
```

**Expected behavior:**
```python
# Auto-detect file size and bypass for small files
if file_line_count < 300:
    use Read tool (full file read)
else:
    use progressive disclosure (skeleton → summary → full)
```

**Fix location:**
- `auzoom/src/auzoom/server.py` - MCP tool handlers
- Logic: Check file size before deciding progressive disclosure vs direct read

**Test cases:**
- File with 149 lines → Use Read tool (no progressive disclosure)
- File with 300+ lines → Use progressive disclosure (skeleton/summary/full)

**Expected impact:**
- Token savings improve from -95.6% to positive
- 4 of 10 failing tasks become passing
- Cost savings remain strong (already 50.7%)

**Priority:** CRITICAL (blocks V1 certification)

---

**ISS-002: Real Claude Code Task Execution Validation**

**Phase:** 12 (Final Certification) or Post-V1
**Priority:** High (but deferred due to cost/time)
**Effort:** 15-30 hours, $2-10 API costs

**Description:**
Current validation uses file measurements with estimated progressive disclosure tokens. Real Claude Code Task execution required for definitive validation.

**Requirements:**
1. Use Task tool to spawn agents for all 25 tasks (10 simple + 15 challenging)
2. Measure actual API token consumption from real execution
3. Validate quality with objective scoring framework
4. Compare to file-measurement-based estimates

**Expected impact:**
- Validates actual vs estimated progressive disclosure tokens
- Confirms quality claims with real execution
- Provides definitive validation (not file-based estimates)

**Effort:** $2-10 API costs, 15-30 hours implementation time

---

### ISS-003: Comprehensive Challenging Tasks Testing

**Category:** Validation Gap
**Priority:** Medium
**Phase Found:** Phase 5-02 (Challenging Tasks Re-execution)
**Impact:** High uncertainty - only 33% sample coverage

**Problem:**
Only 5 of 15 challenging tasks tested (33% coverage):
- Previously tested: Tasks 11, 6, 9, 7, 13
- Never tested: Tasks 8, 10, 12, 14-20
- Critical tier (7.0-8.5) mostly untested (only Task 13 at 0%)

Claimed 67% success rate based on insufficient sample size.

**Fix:**
Test all 15 challenging tasks with real Claude Code Task execution:
1. Implement all 15 features defined in `audit/tests/test_challenging_validation.py`
2. Measure quality with objective scoring (pass/fail against success criteria)
3. Calculate actual success rate from 15 tasks (not 5)
4. Statistical confidence intervals

**Acceptance criteria:**
- All 15 challenging tasks executed with real Claude API calls
- Quality scored objectively (pass/fail against success criteria)
- 100% sample coverage (not 33%)
- Statistical confidence intervals calculated

**Estimated effort:** 15-30 hours (feature implementation + measurement)
**Estimated cost:** $2-10 (30 API calls: 15 baseline + 15 optimized)

**Status:** Deferred to Phase 12 or post-V1

---

## ISS-003: Comprehensive Challenging Tasks Testing

**Created:** 2026-01-13
**Phase:** 5 (Validation Metrics Re-execution)
**Task:** Phase 5-02 (Challenging Tasks Re-execution)
**Priority:** Medium
**Category:** Validation gap

**Issue:** Only 5 of 15 challenging tasks tested (33% sample coverage) - insufficient for statistical confidence

**Impact:**
- Claimed 67% success rate based on small sample
- 10 tasks never tested (Tasks 8, 10, 12, 14-20)
- Critical tier (7.0-8.5) mostly untested
- High variance possible, low confidence in claims

**Current State:**
- 15 tasks defined with requirements and success criteria
- Test suite created (`audit/tests/test_challenging_validation.py`)
- Expected quality by tier calculated (Haiku 100%, Sonnet 71-86%, Opus 38%)
- Real execution deferred due to cost ($2-10) and time (15-30 hours)

**Fix Required:**
1. Execute all 15 challenging tasks with real Claude API
2. Implement features and measure quality objectively
3. Calculate actual success rates by tier
4. Validate or revise claimed 67% success rate
5. Provide statistical confidence intervals

**Priority:** Medium (defer to Phase 12 or post-V1 production validation)

**Estimated Effort:** 15-30 hours + $2-10 API costs

**Evidence:**
- Task definitions: `audit/tests/test_challenging_validation.py`
- Analysis: `audit/reports/05-02-quality-validation.md`
- Phase 5-02 Summary: `.planning/phases/05-validation-metrics-reexecution/05-02-SUMMARY.md`

---

## ISS-004: Inflated Baseline Claims

**Category:** Methodology Issue
**Discovered:** Phase 5-01 (2026-01-13)
**Status:** DOCUMENTED (revision complete)

**Description:**
Original validation used hypothetical file sizes for baseline measurements, resulting in inflated baseline tokens and overstated cost savings.

**Impact:**
- Claimed baseline: 4,298 tokens
- Actual baseline: 2,722 tokens
- Inflation: 37% higher than reality
- Worst case: Task 1.1 claimed 1,115 tokens vs 235 actual (374% inflation)
- Cost savings overstated by 28.8 percentage points

**Root Cause:**
- Used "assume 150 lines" estimates instead of measuring real codebase files
- Hypothetical file sizes not validated against actual implementation

**Fix Completed:**
1. ✅ Re-measured all simple tasks with actual file sizes
2. ✅ Corrected baseline from 4,298 → 2,722 tokens
3. ✅ Revised cost savings claim from 81% → 50.7%
4. ✅ Updated VALIDATION-SUMMARY.md with corrected metrics
5. ✅ Added audit disclaimer and findings section

**No Further Action Required** - Issue resolved through documentation revision.

**Evidence:**
- Real measurements: `audit/evidence/simple_validation_20260113_014847.jsonl`
- Comparison: `audit/reports/05-01-simple-tasks-comparison.md`
- Phase 5-01 Summary: `.planning/phases/05-validation-metrics-reexecution/05-01-SUMMARY.md`

---

## Issue Summary

| ID | Priority | Status | Category |
|----|----------|--------|----------|
| ISS-001 | HIGH | Open | Implementation |
| ISS-002 | MEDIUM | Open | Validation |
| ISS-003 | MEDIUM | Open | Validation |
| ISS-004 | - | DOCUMENTED | Methodology |

**Next Steps:**
1. Implement ISS-001 (small file bypass) in Phase 6 or 7
2. Plan ISS-002 (real Task execution) for Phase 12
3. Plan ISS-003 (comprehensive testing) for Phase 12 or post-V1
4. Track progress in STATE.md Blockers/Concerns section
