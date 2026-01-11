# Validation Test Suite

**Date**: 2026-01-12
**Purpose**: Formally validate token/cost savings through 10 representative development tasks
**Target**: ≥50% token reduction, ≥70% cost reduction

---

## Test Suite Overview

10 tasks across 5 categories representing real-world development scenarios:
1. Code exploration (2 tasks)
2. Simple edits (2 tasks)
3. Feature implementation (2 tasks)
4. Refactoring (2 tasks)
5. Debugging (2 tasks)

Each task measures:
- Token consumption (baseline vs optimized)
- Cost (baseline vs optimized)
- Time taken
- Quality of outcome

---

## Category 1: Code Exploration

### Task 1.1: Explore Unknown Python Package

**Scenario**: New developer needs to understand AuZoom codebase structure

**Target**: `auzoom/` directory (15 Python files, ~2000 lines)

**Goal**: Answer: "What are the main modules and their purposes?"

**Baseline Approach**:
1. Use Read tool on all .py files in auzoom/src/auzoom/
2. Read sequentially: __init__.py, core/*.py, mcp/*.py
3. Files to read: 15 files × ~150 lines avg = 2,250 lines
4. Estimated tokens: 2,250 lines × 4 chars/line ÷ 4 = ~2,250 tokens
5. Model: Sonnet for analysis
6. Time: ~60 seconds

**Optimized Approach**:
1. Use auzoom_read("auzoom/src/auzoom/core/__init__.py", level="skeleton")
2. Use auzoom_read("auzoom/src/auzoom/mcp/server.py", level="skeleton")
3. Use auzoom_read("auzoom/src/auzoom/mcp/server.py", level="summary") for key file
4. Estimated tokens: (15 nodes × 3 files skeleton) + (20 nodes × summary) = 45 + 1500 = ~1,545 tokens
5. Model: Haiku for analysis (simpler task with structured data)
6. Time: ~20 seconds (cache speedup)

**Success Criteria**:
- Both approaches identify: core (parser, graph, cache), mcp (server), structure
- Token savings ≥30%
- Quality: Same understanding

---

### Task 1.2: Find Specific Function

**Scenario**: Find and understand `score_task` function in orchestrator

**Target**: `orchestrator/` directory

**Goal**: Locate function and understand its purpose without reading entire codebase

**Baseline Approach**:
1. Use Grep to search for "score_task"
2. Grep returns: orchestrator/src/orchestrator/scoring.py:45
3. Use Read tool on scoring.py (full file, ~180 lines)
4. Estimated tokens: ~720 tokens (180 lines × 4 chars/line ÷ 4)
5. Model: Sonnet
6. Time: ~15 seconds

**Optimized Approach**:
1. Use auzoom_find("score_task")
2. Returns: orchestrator/src/orchestrator/scoring.py::ComplexityScorer.score_task
3. Use auzoom_read("orchestrator/src/orchestrator/scoring.py", level="summary")
4. Read only relevant method signature and docstring
5. Estimated tokens: ~30 (find) + ~450 (summary) = ~480 tokens
6. Model: Haiku
7. Time: ~8 seconds

**Success Criteria**:
- Both approaches locate and understand function
- Token savings ≥30%
- Quality: Same understanding of function purpose

---

## Category 2: Simple Edits

### Task 2.1: Fix Typo in Docstring

**Scenario**: Fix spelling error in auzoom/mcp/server.py docstring

**Target**: Change "Dispach" → "Dispatch" (if exists, or similar typo)

**Goal**: Make minimal edit with minimal token usage

**Baseline Approach**:
1. Use Read tool on auzoom/src/auzoom/mcp/server.py (full file, 216 lines)
2. Identify typo location
3. Use Edit tool to fix
4. Estimated tokens: ~860 tokens (216 lines × 4 chars ÷ 4)
5. Model: Sonnet
6. Time: ~20 seconds

**Optimized Approach**:
1. Use auzoom_read("auzoom/src/auzoom/mcp/server.py", level="skeleton")
2. Identify method with typo
3. Use auzoom_read with level="summary" to find exact location
4. Use Edit tool to fix
5. Estimated tokens: ~50 (skeleton) + ~400 (summary) = ~450 tokens
6. Model: Haiku or Flash (routing: complexity=1.5)
7. Time: ~10 seconds

**Success Criteria**:
- Both approaches fix the typo correctly
- Token savings ≥40%
- Cost savings ≥70% (Flash vs Sonnet)

---

### Task 2.2: Update Constant Value

**Scenario**: Change MAX_TOKENS default in orchestrator from 4096 to 8192

**Target**: `orchestrator/src/orchestrator/` (find constant)

**Goal**: Locate and update constant value

**Baseline Approach**:
1. Use Grep to find "MAX_TOKENS"
2. Read full file containing constant
3. Update with Edit tool
4. Estimated tokens: ~600 tokens (file read)
5. Model: Sonnet
6. Cost: ~$0.002
7. Time: ~15 seconds

**Optimized Approach**:
1. Use auzoom_find("MAX_TOKENS")
2. Use auzoom_read with level="skeleton" to verify location
3. Update with Edit tool
4. Estimated tokens: ~30 (find) + ~80 (skeleton) = ~110 tokens
5. Model: Flash (routing: complexity=0.5)
6. Cost: ~$0.00001
7. Time: ~8 seconds

**Success Criteria**:
- Both approaches update constant correctly
- Token savings ≥80%
- Cost savings ≥99% (Flash vs Sonnet)

---

## Category 3: Feature Implementation

### Task 3.1: Add New Validation Rule

**Scenario**: Add "max 3 files per directory" validation to AuZoom validator

**Target**: `auzoom/src/auzoom/core/validator.py`

**Goal**: Implement new validation check

**Baseline Approach**:
1. Read validator.py full (assume ~200 lines)
2. Understand existing validation patterns
3. Implement new rule
4. Test with pytest
5. Estimated tokens: ~800 tokens (full read)
6. Model: Sonnet (complexity ~5.5)
7. Cost: ~$0.002
8. Time: ~90 seconds

**Optimized Approach**:
1. Use auzoom_read("validator.py", level="skeleton")
2. Use auzoom_read("validator.py", level="summary")
3. Implement new rule following pattern
4. Test with pytest
5. Estimated tokens: ~80 (skeleton) + ~350 (summary) = ~430 tokens
6. Model: Haiku (routing: complexity=5.0)
7. Cost: ~$0.0003
8. Time: ~70 seconds

**Success Criteria**:
- Both approaches implement working validation
- Token savings ≥45%
- Cost savings ≥85%
- Tests pass

---

### Task 3.2: Add Cost Tracking

**Scenario**: Add cumulative cost tracking to orchestrator executor

**Target**: `orchestrator/src/orchestrator/executor.py`

**Goal**: Track and report total costs across executions

**Baseline Approach**:
1. Read executor.py full (~150 lines)
2. Add cost accumulator
3. Update execute methods to track costs
4. Write test
5. Estimated tokens: ~600 tokens
6. Model: Sonnet (complexity ~6.0)
7. Cost: ~$0.002
8. Time: ~120 seconds

**Optimized Approach**:
1. Use auzoom_read("executor.py", level="summary")
2. Identify methods to modify
3. Implement cost tracking
4. Write test
5. Estimated tokens: ~375 tokens (summary)
6. Model: Haiku (routing: complexity=5.5)
7. Cost: ~$0.0003
8. Time: ~100 seconds

**Success Criteria**:
- Both approaches implement working cost tracking
- Token savings ≥35%
- Cost savings ≥85%
- Tests pass

---

## Category 4: Refactoring

### Task 4.1: Extract Helper Function

**Scenario**: Extract common validation logic in auzoom/core/validator.py

**Target**: Identify duplicate code and extract to helper

**Goal**: DRY improvement without breaking functionality

**Baseline Approach**:
1. Read validator.py full (~200 lines)
2. Identify duplication
3. Extract helper function
4. Update call sites
5. Run tests
6. Estimated tokens: ~800 tokens
7. Model: Sonnet (complexity ~5.0)
8. Cost: ~$0.002
9. Time: ~90 seconds

**Optimized Approach**:
1. Use auzoom_read("validator.py", level="summary")
2. Identify duplication from signatures/docstrings
3. Extract helper function
4. Update call sites
5. Run tests
6. Estimated tokens: ~350 tokens (summary)
7. Model: Haiku (routing: complexity=4.5)
8. Cost: ~$0.0003
9. Time: ~75 seconds

**Success Criteria**:
- Both approaches extract helper correctly
- Token savings ≥55%
- Cost savings ≥85%
- All tests pass

---

### Task 4.2: Rename Module

**Scenario**: Rename `models.py` → `data_models.py` and update imports

**Target**: Hypothetical module (simulate on test file)

**Goal**: Rename file and fix all import references

**Baseline Approach**:
1. Use Grep to find all imports of "models"
2. Read all files that import it (assume 5 files × 100 lines = 500 lines)
3. Update imports with Edit tool
4. Rename file with mv command
5. Estimated tokens: ~2000 tokens (read all importing files)
6. Model: Sonnet
7. Cost: ~$0.006
8. Time: ~60 seconds

**Optimized Approach**:
1. Use auzoom_find("models")
2. Use auzoom_get_dependencies to find all importers
3. Update imports with Edit tool (targeted)
4. Rename file with mv command
5. Estimated tokens: ~30 (find) + ~200 (dependencies) = ~230 tokens
6. Model: Haiku (routing: complexity=3.5)
7. Cost: ~$0.0002
8. Time: ~40 seconds

**Success Criteria**:
- Both approaches update all imports correctly
- Token savings ≥88%
- Cost savings ≥97%
- No broken imports

---

## Category 5: Debugging

### Task 5.1: Diagnose Test Failure

**Scenario**: Understand why `test_mcp_server` fails in auzoom

**Target**: `auzoom/tests/test_mcp_server.py` and implementation

**Goal**: Read test + implementation to identify issue

**Baseline Approach**:
1. Read test file full (~150 lines)
2. Read implementation file full (~216 lines)
3. Compare expected vs actual
4. Identify issue
5. Estimated tokens: ~1460 tokens (366 lines total)
6. Model: Sonnet
7. Time: ~45 seconds

**Optimized Approach**:
1. Read test file skeleton to see what's being tested
2. Read implementation skeleton to see structure
3. Read summary of relevant methods
4. Identify issue
5. Estimated tokens: ~100 (test skeleton) + ~100 (impl skeleton) + ~300 (summaries) = ~500 tokens
6. Model: Haiku (routing: complexity=4.5)
7. Time: ~30 seconds

**Success Criteria**:
- Both approaches identify the issue
- Token savings ≥65%
- Cost savings ≥85%
- Diagnosis correct

---

### Task 5.2: Fix Import Error

**Scenario**: Resolve circular import in orchestrator (simulated)

**Target**: Identify import chain causing error

**Goal**: Trace imports to find cycle

**Baseline Approach**:
1. Read all modules in package (assume 8 files × 150 lines = 1200 lines)
2. Trace imports manually
3. Identify cycle
4. Proposed fix
5. Estimated tokens: ~4800 tokens
6. Model: Sonnet
7. Cost: ~$0.014
8. Time: ~90 seconds

**Optimized Approach**:
1. Use auzoom_get_dependencies on suspected modules (depth=2)
2. Visualize dependency graph
3. Identify cycle from graph
4. Proposed fix
5. Estimated tokens: ~400 tokens (dependency traversal)
6. Model: Haiku (routing: complexity=5.0)
7. Cost: ~$0.0003
8. Time: ~45 seconds

**Success Criteria**:
- Both approaches identify circular import
- Token savings ≥92%
- Cost savings ≥98%
- Correct cycle identified

---

## Test Suite Summary

| Category | Tasks | Expected Token Savings | Expected Cost Savings |
|----------|-------|------------------------|----------------------|
| Code exploration | 2 | 30%+ | 70%+ |
| Simple edits | 2 | 40-80% | 70-99% |
| Feature implementation | 2 | 35-45% | 85%+ |
| Refactoring | 2 | 55-88% | 85-97% |
| Debugging | 2 | 65-92% | 85-98% |
| **Overall Average** | **10** | **≥50%** | **≥70%** |

---

## Measurement Methodology

### Token Estimation
- Baseline: Lines of code × 4 chars/line ÷ 4 chars/token = tokens
- Optimized: Node count × tokens/node (skeleton=15, summary=75, full=400)

### Cost Calculation
- Baseline: All tasks use Sonnet ($3/1M tokens)
- Optimized: Use orchestrator_route to determine model
  - Flash: $0.01/1M
  - Haiku: $0.80/1M
  - Sonnet: $3.00/1M

### Quality Assessment
- Functional: Does it work correctly?
- Complete: Does it achieve the goal?
- Same/Better: Is outcome quality equal or improved?

---

## Execution Plan

1. **Execute Baseline** (Task-by-task measurement)
   - Document exact steps taken
   - Count tokens consumed
   - Calculate costs
   - Measure time
   - Assess quality

2. **Execute Optimized** (Task-by-task measurement)
   - Document exact steps taken with AuZoom + Orchestrator
   - Count tokens consumed
   - Calculate costs
   - Measure time
   - Assess quality (must match baseline)

3. **Compare Results**
   - Calculate savings per task
   - Calculate category averages
   - Calculate overall averages
   - Validate targets met (≥50% token, ≥70% cost)

4. **Generate Report**
   - Statistical analysis
   - Success criteria validation
   - V1 certification decision

---

**Test Suite Status**: ✅ DEFINED

**Next Step**: Execute baseline measurements

**Date**: 2026-01-12
