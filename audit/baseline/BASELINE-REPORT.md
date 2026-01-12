# Baseline State Report

**Captured at**: 2026-01-12 13:30:00 +0530
**Purpose**: Pre-audit baseline for measuring impact of verification and fixes
**Baseline Version**: 1.0

---

## Executive Summary

This baseline snapshot captures the complete state of the Token-Efficient AI Coding Stack before any audit modifications. All metrics frozen for reproducibility and comparison after audit phases complete.

**Key Metrics:**
- 📊 Token reduction: **23%** (target: ≥50%, **missed by 27 points**)
- 💰 Cost reduction: **81%** (target: ≥70%, **exceeded by 11 points**)
- ✅ Quality: **100%** simple tasks, **67%** challenging tasks
- 📁 Codebase: 63 Python files, 5,401 total LOC

---

## Git State

### Current Commit
- **Hash**: `024c988fd07af28bc5d0e31c255a3a2228b8c35f`
- **Short**: `024c988`
- **Branch**: `main`
- **Message**: docs(01-02): complete audit infrastructure plan
- **Timestamp**: 2026-01-12 13:06:20 +0530

### Repository Status
⚠️ **Dirty working tree detected**

Uncommitted changes:
- `M evolving-memory-mcp` (modified submodule)
- `?? audit/evidence/` (untracked directory)
- `?? audit/logs/` (untracked directory)

**Note**: These uncommitted changes exist at baseline capture. Post-audit comparison should account for this.

---

## Validation Metrics (from VALIDATION-SUMMARY.md)

### Simple Tasks (10 tasks, Complexity 0.5-5.5)

| Metric | Baseline | Optimized | Change | % Change |
|--------|----------|-----------|--------|----------|
| Total Tokens | 4,298 | 3,308 | -990 | **-23%** |
| Total Cost | $0.01289 | $0.00246 | -$0.01043 | **-81%** |
| Success Rate | — | — | — | **100%** |

**Analysis:**
- Token reduction achieved: **23%** (below ≥50% target, **missed by 27 points**)
- Cost reduction achieved: **81%** (exceeds ≥70% target, **+11 points**)
- Quality maintained at 100% - all simple tasks functionally correct

### Challenging Tasks (5 executed, Complexity 4.5-7.0)

| Metric | Baseline | Optimized | Change | % Change |
|--------|----------|-----------|--------|----------|
| Total Tokens | 7,120 | 3,685 | -3,435 | **-48%** |
| Total Cost | $0.04364 | $0.02071 | -$0.02293 | **-53%** |
| Success Rate | — | — | — | **67%** |

**Analysis:**
- 3 fully working, 2 partial (1 wrong assertion, 1 missing edge cases)
- Token reduction better than simple tasks (48% vs 23%)
- Cost savings lower than simple tasks (53% vs 81%)

### Overall Performance

| Metric | Baseline | Optimized | Delta | % Savings |
|--------|----------|-----------|-------|-----------|
| **Total Tasks** | 15 | 15 | — | — |
| **Total Tokens** | 11,418 | 6,993 | -4,425 | **39%** |
| **Total Cost** | $0.05653 | $0.02317 | -$0.03336 | **59%** |

**Critical Finding:**
- README.md claims: **79.5% cost savings** (Claude-only routing)
- Combined actual savings: **59%** (simple + challenging tasks)
- **Delta: -20.5 points** from claimed savings

**Explanation**: The 79.5% figure is specific to simple tasks with Claude-only routing (81% rounded). Overall savings are lower when challenging tasks included.

### Target Achievement

| Target | Required | Actual | Status | Delta |
|--------|----------|--------|--------|-------|
| Token Reduction | ≥50% | 23% | ❌ **MISSED** | -27 points |
| Cost Reduction | ≥70% | 81% | ✅ **EXCEEDED** | +11 points |
| Quality (Simple) | 100% | 100% | ✅ **MET** | ±0 |
| Quality (Complex) | — | 67% | ⚠️ **REVIEW** | — |

---

## Codebase Statistics

### File Counts
- **Total Python files**: 63
- **Packages**: AuZoom, Orchestrator, Audit
- **Test files**: Included in count

### Lines of Code
- **AuZoom**: 3,006 lines
- **Orchestrator**: 2,395 lines
- **Total**: 5,401 lines

**Note**: `cloc` tool not available on system. Counts from `wc -l` (includes comments, blank lines).

### Structural Compliance
⏳ **Not yet measured** - Will be captured in Phase 3 (AuZoom Structural Compliance)

Deferred to Phase 3:
- Run `auzoom_validate` on entire codebase
- Document violations (function length, file length, directory files)
- Assess impact on claimed benefits

---

## MCP Server Status

### AuZoom MCP Server
- **Location**: `auzoom/src/auzoom/mcp/server.py`
- **Status**: ✅ Available
- **Tools**: 5 tools defined

| Tool | Purpose | Status |
|------|---------|--------|
| `auzoom_read` | Hierarchical file reading (skeleton/summary/full) | ✅ Defined |
| `auzoom_find` | Search for code by name pattern | ✅ Defined |
| `auzoom_get_dependencies` | Get dependency graph for node | ✅ Defined |
| `auzoom_stats` | Get cache performance statistics | ✅ Defined |
| `auzoom_validate` | Validate code structure compliance | ✅ Defined |

### Orchestrator MCP Server
- **Location**: `orchestrator/src/orchestrator/mcp/server.py`
- **Status**: ✅ Available
- **Tools**: 3 tools defined

| Tool | Purpose | Status |
|------|---------|--------|
| `orchestrator_route` | Get routing recommendation based on complexity | ✅ Defined |
| `orchestrator_execute` | Execute task on specified model | ✅ Defined |
| `orchestrator_validate` | Validate output using Sonnet | ✅ Defined |

**Total MCP Tools**: 8 (5 AuZoom + 3 Orchestrator)

---

## Known Issues at Baseline

### Critical Gaps (from WISHLIST-COMPLIANCE.md)

1. **Token reduction target missed** (High severity)
   - Required: ≥50%
   - Actual: 23%
   - Gap: -27 points
   - Audit: Phase 7 (Small File Overhead Assessment)

2. **Theoretical Gemini Flash costs** (Medium severity)
   - Issue: Claims not based on real API execution
   - Impact: Cost savings may be inflated
   - Audit: Phase 6 (Gemini Flash Real Integration)

3. **Small file overhead** (High severity)
   - Issue: Token increases on files <200 lines (tasks 2.1, 3.1, 4.1)
   - Impact: Contradicts "reduces tokens" claim
   - Audit: Phase 7 (Small File Overhead Assessment)

4. **Non-Python file handling** (Medium severity)
   - Issue: Metadata summaries only (V2 semantic summaries deferred)
   - Impact: May not meet "progressive discovery" claim
   - Audit: Phase 8 (Non-Python File Handling Audit)

---

## Baseline Reproducibility

### How to Reproduce This Baseline

1. **Checkout baseline commit**:
   ```bash
   git checkout 024c988fd07af28bc5d0e31c255a3a2228b8c35f
   ```

2. **Note working tree state**:
   - Submodule `evolving-memory-mcp` was modified at baseline
   - Directories `audit/evidence/` and `audit/logs/` existed but untracked

3. **Re-run validation metrics**:
   - See VALIDATION-SUMMARY.md for task-by-task breakdown
   - Re-execute tasks using test harness if needed

4. **Compare against this report**:
   - All metrics should match within ±1% (measurement variance)
   - File counts may vary if files added/removed post-baseline

---

## Files Referenced

### Source Files for Metrics
- `.planning/PROJECT.md` - Requirements and targets
- `.planning/ROADMAP.md` - Phase structure
- `.planning/STATE.md` - Current position (Phase 1, Plan 3)
- `VALIDATION-SUMMARY.md` - Task-by-task validation results
- `README.md` - Published claims (79.5% cost savings)

### Phase Summaries
- `.planning/phases/01-audit-foundation-traceability/01-01-SUMMARY.md` - WISHLIST-COMPLIANCE reconstruction
- `.planning/phases/01-audit-foundation-traceability/01-02-SUMMARY.md` - Audit infrastructure

### MCP Server Implementations
- `auzoom/src/auzoom/mcp/server.py` - AuZoom MCP tools
- `orchestrator/src/orchestrator/mcp/server.py` - Orchestrator MCP tools

---

## Next Steps

This baseline will be used for:

1. **Phase 2-11**: Audit verification against this frozen state
2. **Phase 12**: Post-audit comparison to measure improvements
3. **Gap analysis**: Track what changed from baseline to post-audit
4. **Regression prevention**: Ensure fixes don't break working functionality

**Comparison framework**: See `audit/baseline_compare.py` (created in Task 2 of this plan)

---

## Baseline Integrity

**SHA256 Hash of this report**:
```bash
shasum -a 256 audit/baseline/BASELINE-REPORT.md
# To be computed post-creation
```

**Structured data**: See `audit/baseline/metrics.json` for machine-readable version

**Immutability**: This baseline should NOT be modified after creation. Any corrections should be documented in `audit/baseline/BASELINE-CORRECTIONS.md` if needed.

---

*Baseline captured during Phase 1 Plan 03 (Baseline Metrics Capture)*
*Audit milestone: V1 Comprehensive Audit*
*Date: 2026-01-12*
