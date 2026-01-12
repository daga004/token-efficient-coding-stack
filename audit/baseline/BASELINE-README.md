# Baseline Comparison Framework

This directory contains the frozen baseline state captured before audit modifications, plus tools to compare post-audit state against this baseline.

---

## What's Captured

### Baseline Files
- **BASELINE-REPORT.md** - Human-readable baseline state documentation
- **metrics.json** - Structured baseline data for programmatic comparison
- **BASELINE-README.md** - This file (usage guide)

### Baseline Contents

1. **Git State**
   - Commit: `024c988fd07af28bc5d0e31c255a3a2228b8c35f`
   - Branch: `main`
   - Date: 2026-01-12 13:06:20 +0530
   - Status: Dirty (uncommitted changes present)

2. **Validation Metrics** (from VALIDATION-SUMMARY.md)
   - Simple tasks: 23% token reduction, 81% cost reduction
   - Challenging tasks: 48% token reduction, 53% cost reduction
   - Overall: 39% tokens, 59% cost
   - Success rates: 100% simple, 67% challenging

3. **Codebase Statistics**
   - Python files: 63
   - AuZoom LOC: 3,006
   - Orchestrator LOC: 2,395
   - Total LOC: 5,401

4. **MCP Server Tools**
   - AuZoom: 5 tools (read, find, dependencies, stats, validate)
   - Orchestrator: 3 tools (route, execute, validate)

---

## How Baseline Was Captured

**Date**: 2026-01-12 13:30:00 +0530
**Phase**: 1 Plan 03 (Baseline Metrics Capture)
**Method**: Automated extraction from git + VALIDATION-SUMMARY.md

### Capture Process

1. **Git state**: `git rev-parse HEAD`, `git branch --show-current`, `git status --porcelain`
2. **Validation metrics**: Parsed from VALIDATION-SUMMARY.md (lines 13-42)
3. **File counts**: `find . -name "*.py" | wc -l`
4. **LOC counts**: `wc -l` on AuZoom and Orchestrator packages
5. **MCP tools**: Inspected server.py files for tool definitions

All data frozen in `metrics.json` for reproducibility.

---

## How to Use Baseline Comparison

### After Audit Phases Complete

Run the comparison utility:

```bash
cd /Users/dhirajd/Documents/claude
python audit/baseline_compare.py
```

This will:
1. Load baseline metrics from `audit/baseline/metrics.json`
2. Re-capture current state (git, files, metrics)
3. Compute deltas between baseline and current
4. Generate comparison report with improvement indicators
5. Save report to `audit/baseline/comparison_report.md`

### Smoke Test (Current = Baseline)

To verify the comparison framework works correctly:

```bash
# From baseline commit
git checkout 024c988
python audit/baseline_compare.py
```

**Expected result**: 0 deltas on all metrics (commit unchanged, files unchanged)

### Post-Audit Comparison (Phase 12)

After all audit fixes applied:

```bash
# From latest commit
python audit/baseline_compare.py
```

**Expected improvements**:
- Token reduction: Increased from 23% baseline (target ≥50%)
- Cost reduction: Maintained or increased from 81%
- Structural violations: Reduced from baseline count
- Test coverage: Increased from baseline

**Expected regressions** (should be ZERO):
- Quality should not decrease
- Working functionality should not break
- MCP tools should remain available

---

## Comparison Categories

The `baseline_compare.py` script compares:

### 1. Validation Metrics
- **Token savings delta**: Baseline 23% → Post-audit X% (target: ≥50%)
- **Cost savings delta**: Baseline 81% → Post-audit X% (maintain or improve)
- **Success rate delta**: Baseline 100%/67% → Post-audit X%

**Color coding**:
- 🟢 Green: Improvement (increased savings, higher success rate)
- 🔴 Red: Regression (decreased savings, lower success rate)
- 🟡 Yellow: No change (within ±1% margin)

### 2. Structural Compliance
- **Violations fixed count**: How many AuZoom constraint violations addressed
- **Before**: Baseline violation count (from Phase 3 audit)
- **After**: Post-audit violation count
- **Target**: 0 violations

### 3. Test Coverage
- **New tests added**: Count of tests created during audit
- **Test pass rate**: Baseline 100% → Post-audit 100% (maintain)

### 4. Git Commits
- **Audit commits**: Number of commits made during Phases 2-12
- **Fix commits**: Commits tagged with `fix(XX-XX):`
- **Test commits**: Commits tagged with `test(XX-XX):`

---

## Expected Improvements from Audit

Based on PROJECT.md audit goals:

### Critical Fixes (Must Achieve)

1. **Token reduction target met**
   - Baseline: 23%
   - Target: ≥50%
   - Expected: File size threshold auto-detection implemented

2. **Gemini Flash real integration**
   - Baseline: Theoretical costs
   - Target: Actual API execution with token/cost measurement
   - Expected: Gemini CLI fixed, costs re-calculated

3. **Small file overhead handled**
   - Baseline: Token increases on <200 line files
   - Target: Auto-skip progressive disclosure when counterproductive
   - Expected: Heuristics added, tasks 2.1/3.1/4.1 re-tested

### Important Fixes (Should Achieve)

4. **Structural compliance**
   - Baseline: Unknown (will be measured in Phase 3)
   - Target: 0 violations
   - Expected: Long functions split, large files refactored

5. **Non-Python file handling verified**
   - Baseline: Metadata summaries only
   - Target: Adequate for "progressive discovery" claim
   - Expected: Evidence-based validation

### Enhancement Opportunities (May Achieve)

6. **Quality improvements**
   - Baseline: 67% success on challenging tasks
   - Target: 80%+ with review guidelines
   - Expected: Documentation on when to use what

---

## Regression Prevention

### What Should NOT Change

The following should remain stable or improve post-audit:

✅ **Working functionality**:
- All 5 AuZoom MCP tools continue working
- All 3 Orchestrator MCP tools continue working
- GSD workflow integration remains functional

✅ **Quality baselines**:
- Simple tasks: 100% success rate (maintain)
- Challenging tasks: ≥67% success rate (maintain or improve)

✅ **Cost savings**:
- Simple tasks: ≥81% cost reduction (maintain or improve)
- Should not regress below 70% target

### What to Monitor for Regressions

🔴 **Red flags** (critical regressions):
- Token reduction goes below 23% baseline
- Cost savings drop below 70% target
- Simple task success rate drops below 100%
- MCP tools fail or become unavailable

🟡 **Yellow flags** (investigate):
- File count increases significantly without justification
- LOC increases without new features
- Test pass rate below 100%

---

## Usage in Phase 12

At the end of Phase 12 (Critical Fixes & V1.1 Roadmap):

1. **Run final comparison**:
   ```bash
   python audit/baseline_compare.py
   ```

2. **Review comparison report**:
   - Check all critical targets met
   - Verify no regressions
   - Document any deviations

3. **Update documentation**:
   - Update README.md with new metrics
   - Update VALIDATION-SUMMARY.md if re-run
   - Archive baseline in `.planning/phases/12-*/`

4. **Archive baseline**:
   ```bash
   # Baseline remains in audit/baseline/ for future reference
   # Copy comparison report to final phase summary
   cp audit/baseline/comparison_report.md .planning/phases/12-critical-fixes/BASELINE-COMPARISON.md
   ```

---

## Programmatic Access

### Load Baseline in Python

```python
from audit.baseline_compare import load_baseline

baseline = load_baseline()
print(f"Baseline commit: {baseline['git_state']['commit_short']}")
print(f"Token reduction: {baseline['validation_metrics']['simple_tasks']['token_reduction_pct']}%")
```

### Compare States

```python
from audit.baseline_compare import load_baseline, capture_current, compare

baseline = load_baseline()
current = capture_current()
comparison = compare(baseline, current)

if comparison["commits"]["changed"]:
    print("✅ State has changed since baseline")
    print(f"File delta: {comparison['files']['delta']}")
```

---

## Baseline Integrity

### Immutability

This baseline should NOT be modified after creation. If errors discovered:

1. Document corrections in `BASELINE-CORRECTIONS.md`
2. Explain what was wrong and why
3. Do NOT modify original BASELINE-REPORT.md or metrics.json
4. Apply corrections in comparison logic if needed

### Verification

Verify baseline integrity:

```bash
# Check JSON is valid
python -c "import json; json.load(open('audit/baseline/metrics.json'))"

# Check commit matches
git rev-parse HEAD | grep 024c988  # Run from baseline commit
```

### SHA256 Hash

```bash
shasum -a 256 audit/baseline/BASELINE-REPORT.md
shasum -a 256 audit/baseline/metrics.json
```

Store hashes for tamper detection if needed.

---

## Files in This Directory

```
audit/baseline/
├── BASELINE-REPORT.md      # Human-readable baseline (this was captured)
├── BASELINE-README.md       # Usage documentation (you are here)
├── metrics.json             # Structured baseline data
└── comparison_report.md     # Generated by baseline_compare.py (after run)
```

---

## Support

**Questions about baseline**:
- See audit/README.md for audit infrastructure docs
- See .planning/phases/01-audit-foundation-traceability/01-03-PLAN.md for capture plan
- See .planning/phases/01-audit-foundation-traceability/01-03-SUMMARY.md for execution summary

**Issues with comparison**:
- Check baseline_compare.py docstrings
- Verify metrics.json is valid JSON
- Ensure git commands work in your environment

---

*Baseline captured: 2026-01-12 13:30:00 +0530*
*Audit milestone: V1 Comprehensive Audit*
*Phase: 1 Plan 03 (Baseline Metrics Capture)*
