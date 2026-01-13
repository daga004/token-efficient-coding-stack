# Simple Tasks Validation: Real vs Claimed Metrics

**Date**: 2026-01-13
**Purpose**: Compare actual measurements against claimed token/cost savings
**Evidence**: audit/evidence/simple_validation_20260113_014847.jsonl

---

## Executive Summary

**Methodology Issue Identified**: Original claimed results used **hypothetical file sizes** rather than actual codebase measurements. This validation uses **real file line counts** from the actual codebase but still relies on **estimated progressive disclosure tokens** (not actual MCP server responses).

**Key Finding**: Claimed baseline significantly overestimated file sizes, inflating savings claims.

---

## Methodology Comparison

### Claimed Approach (BASELINE-RESULTS.md)
- **File sizes**: Hypothetical estimates (e.g., "assume 150 lines")
- **Token calculation**: Estimated lines × 1 token/line
- **Progressive disclosure**: Estimated skeleton/summary tokens
- **Model execution**: Theoretical (no actual API calls)

### Actual Validation Approach
- **File sizes**: Real line counts from actual codebase files ✓
- **Token calculation**: Actual lines × 1 token/line ✓
- **Progressive disclosure**: Estimated skeleton/summary tokens (NOT real MCP responses) ⚠️
- **Model execution**: Simulated (no actual Claude Code task execution) ⚠️

**Conclusion**: This is a **partial validation** - real baselines, estimated optimized approach.

---

## Task-by-Task Comparison

### Task 1.1: Explore AuZoom Codebase

| Metric | Claimed Baseline | Actual Baseline | Claimed Optimized | Actual Optimized | Discrepancy |
|--------|------------------|-----------------|-------------------|------------------|-------------|
| Files read | 8 files | 5 files | N/A | 5 skeleton | Different scope |
| Lines | 1,115 lines | 235 lines | N/A | N/A | **79% overestimate** |
| Tokens | 1,115 | 235 | 750 | 750 | Baseline **374% inflated** |
| Model | Sonnet | Sonnet | Haiku | Haiku | Consistent |
| Cost | $0.003345 | $0.000705 | $0.000600 | $0.000600 | Baseline **374% inflated** |
| Savings claimed | N/A | N/A | 33% tokens, 82% cost | -219% tokens, 15% cost | **Negative savings** |

**Issue**: Claimed baseline read 8 files (1,115 lines), actual codebase only has 5 relevant files (235 lines). Progressive disclosure (750 tokens) uses MORE tokens than actual full read.

---

### Task 1.2: Find score_task Function

| Metric | Claimed Baseline | Actual Baseline | Claimed Optimized | Actual Optimized | Discrepancy |
|--------|------------------|-----------------|-------------------|------------------|-------------|
| Lines | 167 (grep + file) | 157 | 210 (find + skeleton) | 150 | Baseline: 6% over |
| Tokens | 167 | 157 | 210 | 150 | Close match |
| Cost | $0.000501 | $0.000471 | $0.000168 | $0.000120 | Close match |
| Savings | N/A | N/A | -26% tokens, 66% cost | 4.5% tokens, 74.5% cost | **Better than claimed** |

**Issue**: Actual optimized approach (skeleton only) beats claimed (find + skeleton).

---

### Task 2.1: Fix Typo in Docstring

| Metric | Claimed Baseline | Actual Baseline | Claimed Optimized | Actual Optimized | Discrepancy |
|--------|------------------|-----------------|-------------------|------------------|-------------|
| Lines | 228 | 228 | 390 (skeleton + summary) | 150 (skeleton) | Exact match baseline |
| Tokens | 228 | 228 | 390 | 150 | Optimized approach differs |
| Model | Sonnet | Sonnet | Flash | Flash | Consistent |
| Cost | $0.000684 | $0.000684 | $0.000004 | $0.000002 | Close match |
| Savings | N/A | N/A | -71% tokens, 99.4% cost | 34.2% tokens, 99.8% cost | **Much better actual** |

**Issue**: Claimed used skeleton+summary (390 tokens), actual uses skeleton-only (150 tokens).

---

### Task 2.2: Update Constant

| Metric | Claimed Baseline | Actual Baseline | Claimed Optimized | Actual Optimized | Discrepancy |
|--------|------------------|-----------------|-------------------|------------------|-------------|
| Lines | 206 (grep + file) | 196 | 110 (find + skeleton) | 150 (skeleton) | Close match |
| Tokens | 206 | 196 | 110 | 150 | Reasonable match |
| Cost | $0.000618 | $0.000588 | $0.000001 | $0.000002 | Close match |
| Savings | N/A | N/A | 47% tokens, 99.8% cost | 23.5% tokens, 99.7% cost | Lower but still good |

---

### Task 3.1: Add Validation Rule

| Metric | Claimed Baseline | Actual Baseline | Claimed Optimized | Actual Optimized | Discrepancy |
|--------|------------------|-----------------|-------------------|------------------|-------------|
| Lines | 149 | 149 | 430 (skeleton + summary) | 1,125 (summary) | Exact baseline |
| Tokens | 149 | 149 | 430 | 1,125 | **Optimized 162% worse** |
| Model | Sonnet | Sonnet | Haiku | Haiku | Consistent |
| Cost | $0.000447 | $0.000447 | $0.000300 | $0.000900 | **Optimized costs MORE** |
| Savings | N/A | N/A | 45% tokens, 85% cost | **-655% tokens, -101% cost** | **MASSIVE REGRESSION** |

**CRITICAL ISSUE**: Summary view (1,125 tokens) for small file (149 lines) creates **massive overhead**. This is the "small file problem" mentioned in STATE.md.

---

### Task 3.2: Add Cost Tracking

| Metric | Claimed Baseline | Actual Baseline | Claimed Optimized | Actual Optimized | Discrepancy |
|--------|------------------|-----------------|-------------------|------------------|-------------|
| Lines | 196 | 196 | 375 (summary) | 1,125 (summary) | Exact baseline |
| Tokens | 196 | 196 | 375 | 1,125 | **Optimized 200% worse** |
| Cost | $0.000588 | $0.000588 | $0.000300 | $0.000900 | **Optimized costs MORE** |
| Savings | N/A | N/A | 35% tokens, 85% cost | **-474% tokens, -53% cost** | **REGRESSION** |

**CRITICAL ISSUE**: Same small file overhead problem.

---

### Task 4.1: Extract Helper Function

| Metric | Claimed Baseline | Actual Baseline | Claimed Optimized | Actual Optimized | Discrepancy |
|--------|------------------|-----------------|-------------------|------------------|-------------|
| Lines | 149 | 149 | 350 (summary) | 1,125 (summary) | Exact baseline |
| Tokens | 149 | 149 | 350 | 1,125 | **Optimized 222% worse** |
| Cost | $0.000447 | $0.000447 | $0.000300 | $0.000900 | **Optimized costs MORE** |
| Savings | N/A | N/A | 55% tokens, 85% cost | **-655% tokens, -101% cost** | **MASSIVE REGRESSION** |

**CRITICAL ISSUE**: Same small file overhead problem.

---

### Task 4.2: Rename Module

| Metric | Claimed Baseline | Actual Baseline | Claimed Optimized | Actual Optimized | Discrepancy |
|--------|------------------|-----------------|-------------------|------------------|-------------|
| Lines | 510 (grep + 5 files) | 254 (3 files) | 230 (find + deps) | 150 (skeleton) | Baseline **101% inflated** |
| Tokens | 510 | 254 | 230 | 150 | Claimed overstated |
| Cost | $0.001530 | $0.000762 | $0.000200 | $0.000120 | Baseline **101% inflated** |
| Savings | N/A | N/A | 55% tokens, 87% cost | 40.9% tokens, 84.3% cost | Good savings |

**Issue**: Claimed baseline assumed 5 files × 100 lines. Actual: only 3 files needed, 254 lines total.

---

### Task 5.1: Diagnose Test Failure

| Metric | Claimed Baseline | Actual Baseline | Claimed Optimized | Actual Optimized | Discrepancy |
|--------|------------------|-----------------|-------------------|------------------|-------------|
| Lines | 378 (2 files) | 549 (2 files) | 500 (2 skeletons + summary) | 300 (2 skeletons) | **Actual 45% higher** |
| Tokens | 378 | 549 | 500 | 300 | Baseline understated |
| Cost | $0.001134 | $0.001647 | $0.000400 | $0.000240 | Close match |
| Savings | N/A | N/A | -32% tokens, 65% cost | 45.4% tokens, 85.4% cost | **Better than claimed** |

**Note**: Actual baseline higher because test file was larger than estimated. Optimized approach still wins.

---

### Task 5.2: Fix Circular Import

| Metric | Claimed Baseline | Actual Baseline | Claimed Optimized | Actual Optimized | Discrepancy |
|--------|------------------|-----------------|-------------------|------------------|-------------|
| Lines | 1,200 (8 files × 150) | 609 (5 files) | 400 (deps) | 300 (2 skeletons) | Baseline **97% inflated** |
| Tokens | 1,200 | 609 | 400 | 300 | Claimed overstated |
| Cost | $0.003600 | $0.001827 | $0.000300 | $0.000240 | Baseline **97% inflated** |
| Savings | N/A | N/A | 67% tokens, 92% cost | 50.7% tokens, 86.9% cost | Good savings |

**Issue**: Claimed 8 files needed, actual analysis required only 5 files (609 lines).

---

## Aggregate Comparison

| Metric | Claimed Baseline | Actual Baseline | Claimed Optimized | Actual Optimized |
|--------|------------------|-----------------|-------------------|------------------|
| Total tokens | 4,298 | **2,722** | ~3,500 (estimated) | **5,475** |
| Total cost | $0.012894 | **$0.008166** | ~$0.003000 | **$0.003983** |
| Token savings | N/A | N/A | ~50% claimed | **-101% (WORSE)** |
| Cost savings | N/A | N/A | ~79.5% claimed | **51.2%** |

**Critical Finding**:
- **Claimed cost savings: 79.5%**
- **Actual cost savings: 51.2%** (28.3 percentage points lower)
- **Token savings: NEGATIVE** (optimized uses more tokens overall)

---

## Root Cause Analysis

### 1. Inflated Baseline Claims

**Tasks with inflated baselines**:
- Task 1.1: 374% inflation (1,115 claimed vs 235 actual)
- Task 4.2: 101% inflation (510 claimed vs 254 actual)
- Task 5.2: 97% inflation (1,200 claimed vs 609 actual)

**Impact**: Inflated baselines make savings appear larger than reality.

---

### 2. Small File Overhead Problem

**Tasks with negative savings** (optimized WORSE than baseline):
- Task 1.1: -219% token increase
- Task 3.1: -655% token increase, -101% cost increase
- Task 3.2: -474% token increase, -53% cost increase
- Task 4.1: -655% token increase, -101% cost increase

**Root cause**: Progressive disclosure estimates assume:
- Skeleton: 10 nodes × 15 tokens = 150 tokens
- Summary: 15 nodes × 75 tokens = 1,125 tokens

For **small files** (149-228 lines = 149-228 tokens), summary view (1,125 tokens) creates **massive overhead** (655-755% increase).

**STATE.md claimed this was resolved**, but measurements show it persists.

---

### 3. Model Routing Saves Cost Despite Token Increase

Even with negative token savings, **cost savings remain positive** due to model routing:
- Flash: $0.01/1M (300x cheaper than Sonnet)
- Haiku: $0.80/1M (3.75x cheaper than Sonnet)

**Example** (Task 3.1):
- Baseline: 149 tokens × $3.00/1M = $0.000447
- Optimized: 1,125 tokens × $0.80/1M = $0.000900
- Token efficiency: -655% (terrible)
- Cost efficiency: -101% (worse - costs more!)

This only works when the token overhead is offset by cheaper model pricing.

---

## Methodology Limitations

### What This Validation Measured

✓ **Real baseline file sizes** - Used actual codebase files
✓ **Real line counts** - Not hypothetical estimates
✓ **Actual pricing** - Current Claude model rates

### What This Validation Did NOT Measure

⚠️ **Real progressive disclosure tokens** - Used estimates (skeleton=150, summary=1,125), not actual MCP server responses
⚠️ **Actual Claude Code execution** - Did not spawn Task agents or measure real API token consumption
⚠️ **Quality assessment** - Did not verify that optimized approach produces same quality results
⚠️ **Real model routing** - Did not use orchestrator to select models based on actual complexity

**Conclusion**: This is a **file-size-corrected theoretical validation**, not a **real execution validation**.

---

## Recommended Next Steps

### Immediate Actions

1. **Re-run validation with real MCP server responses**
   - Use actual auzoom_read calls to measure real skeleton/summary tokens
   - Compare to these estimates (skeleton=150, summary=1,125)
   - Identify if small file overhead is real or estimation artifact

2. **Re-run with real Claude Code execution**
   - Use Task tool to spawn agents for each task
   - Measure actual token consumption from agent execution
   - Compare baseline (Read tool) vs optimized (auzoom_read MCP) approaches

3. **Fix small file detection**
   - Implement auto-bypass: if file < 300 lines, use Read tool instead of summary view
   - This would fix tasks 1.1, 3.1, 3.2, 4.1 (4 of 10 tasks)

### Strategic Questions

1. **Are the claimed 79.5% cost savings achievable?**
   - Current validation: 51.2% (28 points lower)
   - With small file bypass: Likely ~60-65%
   - With real MCP data: Unknown

2. **Is progressive disclosure worth it for small files?**
   - Answer: **No** - current data shows 655% token overhead
   - Solution: Auto-bypass for files < 300 lines

3. **What's the real token savings claim?**
   - Claimed: ≥50%
   - Measured: -101% (worse)
   - With bypass: Likely 20-30%

---

## Verdict

### Metrics Status

| Claim | Claimed Value | Validated Value | Status |
|-------|---------------|-----------------|--------|
| Token savings | ≥50% | **-101%** | ❌ **FAILED** |
| Cost savings | ≥70% | **51.2%** | ⚠️ **PARTIAL** (below target) |
| Quality maintained | 100% | **Not measured** | ⚠️ **UNTESTED** |

### Methodology Status

| Aspect | Status | Notes |
|--------|--------|-------|
| Baseline measurements | ✅ **VALIDATED** | Real file sizes, corrects inflated claims |
| Optimized measurements | ⚠️ **ESTIMATED** | Token counts not from real MCP responses |
| Execution approach | ❌ **SIMULATED** | Should use Claude Code Task tool, not Python script |
| Quality assessment | ❌ **MISSING** | Did not verify output quality |

---

## Final Assessment

**METRICS INFLATED**

**Evidence**:
1. Claimed baseline used hypothetical file sizes (374% inflation in worst case)
2. Actual measurements show 51.2% cost savings vs claimed 79.5% (28 points lower)
3. Token savings are NEGATIVE (-101%) vs claimed ≥50% (151 points lower)
4. Small file overhead persists despite STATE.md claiming it was resolved
5. Methodology uses estimates rather than real API execution

**Recommendation**:
- **Reject claimed 79.5% cost savings** as inflated
- **Conduct real execution validation** using Claude Code Task tool
- **Fix small file bypass** before claiming V1 certification
- **Re-measure with actual MCP server responses** to validate progressive disclosure benefits

---

**Report Date**: 2026-01-13
**Evidence**: audit/evidence/simple_validation_20260113_014847.jsonl
**Status**: Methodology issues identified, real execution validation required
