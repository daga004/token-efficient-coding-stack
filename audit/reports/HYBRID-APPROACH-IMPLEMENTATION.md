# Hybrid Grep/AST Approach: Implementation Guide

**Date**: 2026-01-15
**Status**: Ready for implementation
**Estimated ROI**: 30-60% token reduction + maintained accuracy

---

## Quick Reference: Decision Matrix

Use this matrix to determine the best approach for each scenario.

### By Task Type

```
┌─────────────────────────────────────────────────────────────────────────┐
│ TASK TYPE              │ APPROACH           │ TOOLS            │ TOKENS  │
├─────────────────────────────────────────────────────────────────────────┤
│ Find files with X      │ Discover fast      │ grep -r, ls      │ 50-100  │
│ List public methods    │ Structure view     │ AuZoom skeleton  │ 140-300 │
│ Explain small func     │ Raw read           │ Read tool        │ 200-450 │
│ Explain large func     │ Progressive        │ AuZoom summary   │ 800-1600│
│ Find all callers       │ Graph traverse     │ AuZoom graph     │ 400-800 │
│ Understand patterns    │ Targeted search    │ grep + skeleton  │ 400-600 │
│ Refactor across files  │ Hybrid scan        │ grep + skeleton  │ 500-800 │
│ Cross-file dependency  │ Graph analysis     │ AuZoom graph     │ 600-1000│
└─────────────────────────────────────────────────────────────────────────┘
```

### By File Size

```
File Size          Best Approach              When to Switch
<50 lines          Raw read                   Never use AuZoom
50-200 lines       Raw read + grep            Only for structure
200-300 lines      Raw read                   Never use progressive
300-500 lines      Skeleton only              Never use summary
500-700 lines      Skeleton + grep            Conditional summary
700+ lines         Progressive viable        Safe to use summary
```

---

## Implementation Checklist

### Priority 1: File Size Bypass (30 min)

**Goal**: Don't use progressive disclosure on small files

**Code pattern**:
```python
def should_use_progressive(file_path: str, requested_level: str) -> bool:
    """Determine if progressive disclosure is worthwhile."""
    raw_size = estimate_raw_tokens(file_path)

    # Always bypass for tiny files
    if raw_size < 300:
        return False

    # Skeleton is always worth it above 300
    if requested_level == "skeleton":
        return True

    # Summary only viable for large files
    if requested_level == "summary":
        return raw_size > 600

    # Full read: skip progressive overhead
    return False
```

**Testing**:
```
Before: Task 3 = 1,325 tokens (skeleton 150 + summary 1,125)
After:  Task 3 = 450 tokens (raw read)
Goal:   100% improvement for <300 token files
```

---

### Priority 2: Dependency ID Compression (30 min)

**Goal**: Reduce metadata bloat in skeleton/summary

**Current** (8-9 tokens per dependency):
```json
"dependencies": [
  "/Users/dhirajd/Documents/claude/auzoom/src/auzoom/mcp/server.py::AuZoomMCPServer._read_python_file",
  "/Users/dhirajd/Documents/claude/auzoom/src/auzoom/mcp/server.py::AuZoomMCPServer._read_non_python_file"
]
```

**Improved** (2-3 tokens per dependency):
```json
"dependencies": ["_read_python_file", "_read_non_python_file"]
```

**Or with context** (for cross-file):
```json
"dependencies": {
  "_read_python_file": "same file",
  "_read_non_python_file": "same file"
}
```

**Testing**:
```
Before: 21 nodes × 7 tokens = 147 tokens (with full paths)
After:  21 nodes × 2 tokens = 42 tokens + structure = ~80 tokens
Goal:   45% reduction in skeleton size
```

---

### Priority 3: Targeted Node Requests (1.5 hours)

**Goal**: Allow `auzoom_read("file.py::function", level="summary")`

**Current limitation**:
```python
# Returns summary for ALL 21 nodes in server.py
auzoom_read("server.py", level="summary")  # 1,125 tokens
```

**Proposed solution**:
```python
# Returns summary for ONLY _tool_read
auzoom_read("server.py::_tool_read", level="summary")  # 54 tokens
```

**Implementation steps**:
1. Parse node selector from path: `split("::")`
2. Add `node_selector` parameter to `auzoom_read()`
3. In summary generation, filter to matching nodes only
4. Document new API behavior

**Token savings**:
```
Old workflow:
  - Skeleton all nodes: 140 tokens
  - Summary all nodes: 1,125 tokens
  - Total: 1,265 tokens

New workflow:
  - Skeleton all nodes: 140 tokens
  - Find function of interest in output
  - Summary only that function: 54 tokens
  - Total: 194 tokens

Improvement: 85% reduction
```

---

### Priority 4: Collapse Import Nodes (1 hour)

**Goal**: Don't list each import as separate node

**Current**:
```json
{
  "id": "server.py::import::json",
  "name": "import json",
  "type": "import",
  "dependencies": []
}
// × 9 imports = 63 tokens
```

**Improved**:
```json
{
  "imports": ["json", "Path", "Optional", "LazyCodeGraph", "FetchLevel", "FileSummarizer", "JSONRPCHandler", "CodeValidator", "os"],
  "import_count": 9
}
// Total: 15 tokens (76% reduction)
```

**Implementation**:
1. Detect import nodes in AST
2. Collapse into single `imports` array in root
3. Skip individual import nodes in output

**Impact**:
```
Before: 9 nodes × 7 = 63 tokens
After: 1 section = 15 tokens
Reduction: 76% on import overhead
```

---

## Agent Decision Rules

### Rule 1: Discovery Phase
```
Task: "Find all files using library X"

Steps:
1. Use grep to find matches
   └─ grep -r "from requests import" --include="*.py"
   └─ Cost: 50 tokens + results

2. Don't parse every file with AuZoom
   └─ Instead filter to promising matches

ROI: +60% savings vs full AuZoom scan
```

### Rule 2: Navigation Phase
```
Task: "Show me the structure of server.py"

Steps:
1. Use AuZoom skeleton to get structure
   └─ auzoom_read("server.py", level="skeleton")
   └─ Cost: 140 tokens

2. Don't request summary unless specifically needed
   └─ Skeleton shows complete file structure

ROI: Skeleton typically sufficient; save 75%+ by not reading summary
```

### Rule 3: Explanation Phase (Small Files)
```
Task: "Explain what _tool_read does" (file is 224 lines)

Steps:
1. Check file size: 224 lines < 300 lines
2. Use raw read instead of progressive
   └─ Read whole file: 450 tokens
   └─ Skip skeleton + summary overhead

ROI: +66% savings vs progressive disclosure
```

### Rule 4: Explanation Phase (Large Files)
```
Task: "Explain what _tool_read does" (file is 1200 lines)

Steps:
1. Check file size: 1200 lines > 600 lines
2. Progressive disclosure viable
   └─ Skeleton: 300 tokens
   └─ Targeted summary of _tool_read: 54 tokens
   └─ Total: 354 tokens

3. Alternative: raw read = 4,200 tokens

ROI: +92% savings vs raw read
```

### Rule 5: Graph Analysis
```
Task: "Find all functions calling validate_file"

Steps:
1. Use AuZoom graph tools (no alternative)
   └─ auzoom_find("validate_file")
   └─ auzoom_get_dependencies("validate_file", depth=2)
   └─ Cost: 600-800 tokens

2. Use grep only for verification/filtering
   └─ Don't use grep as primary search

ROI: Essential for accuracy (100% vs 70% with grep)
```

### Rule 6: Complex Search
```
Task: "Find all error handling for DatabaseError across codebase"

Steps:
1. Start with grep (discovery phase)
   └─ grep -r "DatabaseError" --include="*.py"
   └─ grep -r "except.*Database" --include="*.py"
   └─ Cost: 100 tokens, identifies 8 files

2. Scan those 8 files with AuZoom skeleton
   └─ 8 × 140 tokens = 1,120 tokens
   └─ Understand structure without reading full files

3. Use targeted reads on promising locations
   └─ grep + raw read for specific sections

Total: ~1,320 tokens
vs AuZoom full scan of 50+ files: 7,000+ tokens

ROI: +81% savings
```

---

## Expected Improvements After Implementation

### Metric 1: Small File Tasks (Current: -194% overhead)

**Before implementation**:
```
Task 3 (224 lines):
  - Progressive: 1,325 tokens (skeleton 150 + summary 1,125)
  - Baseline: 450 tokens
  - Overhead: -194%
```

**After Phase 1 (file size bypass)**:
```
Task 3 (224 lines):
  - Bypass to raw: 450 tokens
  - Baseline: 450 tokens
  - Overhead: 0% ✅
  - Improvement: +194%
```

---

### Metric 2: Medium File Summary Requests (Current: +54% overhead)

**Before implementation**:
```
500-line file summary request:
  - Summary all nodes: 2,160 tokens
  - Raw read: 1,400 tokens
  - Overhead: +54%
```

**After Phase 3 (targeted requests)**:
```
500-line file, explain one function:
  - Skeleton all: 280 tokens
  - Summary one node: 54 tokens
  - Total: 334 tokens
  - vs Raw: 1,400 tokens
  - Improvement: +76%
```

---

### Metric 3: Large File Graph Tasks (Current: -111% overhead)

**Before implementation**:
```
Graph traversal on server.py:
  - Progressive: 1,795 tokens (5 skeleton + 1 summary + overhead)
  - Baseline grep: 850 tokens
  - Overhead: -111%
```

**After Phase 4 (collapse imports, compress IDs)**:
```
Graph traversal on server.py:
  - Progressive: 1,100 tokens (compressed skeleton + minimal overhead)
  - Baseline grep: 850 tokens
  - Overhead: -29% (acceptable for 100% accuracy)
```

---

### Metric 4: Discovery Tasks (Current: no tracking)

**After implementation**:
```
Find all files using requests:
  - Hybrid (grep + selective skeleton): 400 tokens
  - AuZoom full scan: 1,200+ tokens
  - Expected savings: +67%
```

---

## Rollout Plan

### Week 1: Quick Wins
- [ ] Implement file size bypass (Phase 1)
- [ ] Test on Task 3 (expect +194% improvement)
- [ ] Compress dependency IDs (Phase 2)
- [ ] Test on Task 9 graph (expect 45% improvement)
- **Target**: 100+ tokens saved per task

### Week 2: Advanced Features
- [ ] Implement targeted node requests (Phase 3)
- [ ] Update API documentation
- [ ] Test on medium file explanation tasks
- **Target**: 600+ tokens saved per task

### Week 3: Metadata Optimization
- [ ] Collapse import nodes (Phase 4)
- [ ] Refactor skeleton format
- [ ] Comprehensive testing
- **Target**: Full stack validation

### Week 4: Validation & Documentation
- [ ] Run Phase 6.5 remaining tasks with optimized AuZoom
- [ ] Compare actual vs estimated savings
- [ ] Update Phase 6.5 plan with real results
- [ ] Document agent decision rules

---

## Success Criteria

### Phase 1 (File Size Bypass)
- [ ] Task 3 token cost: 450 (vs current 1,325)
- [ ] Task 1 unchanged: 150 tokens
- [ ] File size detection accurate for 90%+ of files

### Phase 2 (ID Compression)
- [ ] Skeleton size reduced 45%+ on files with dependencies
- [ ] Graph traversal tasks maintain 100% accuracy
- [ ] ID parsing still unambiguous

### Phase 3 (Targeted Requests)
- [ ] Targeted summary requests work for 90%+ of common functions
- [ ] Token cost per request: <75 tokens
- [ ] API documentation clear and discoverable

### Phase 4 (Import Collapse)
- [ ] Skeleton no longer contains individual import nodes
- [ ] Import list accessible in structured format
- [ ] File structure equally understandable

### Overall
- [ ] Average task token cost reduced 30-50%
- [ ] Code understanding quality unchanged (100% accuracy)
- [ ] Agent decisions align with decision matrix

---

## Monitoring & Validation

### Metrics to Track

1. **Token consumption per task type**
   ```
   Before: Classify tasks, record tokens
   After:  Same tasks, compare token usage
   Target: 30-50% reduction
   ```

2. **Accuracy of AI results**
   ```
   Validate against Phase 4 quality baselines
   Target: No degradation (maintain 100%)
   ```

3. **Agent decision patterns**
   ```
   Log which tool agents choose (grep vs AuZoom)
   Verify alignment with decision matrix
   ```

4. **Edge cases**
   ```
   Monitor file size estimates
   Track misses in targeted node requests
   Record hybrid approach effectiveness
   ```

---

## Appendix: Quick Reference Commands

### For Grep Approach
```bash
# Find files with pattern
grep -r "PATTERN" --include="*.py"

# Find function definitions
grep "^def " file.py | grep -v "^_"

# Find class definitions
grep "^class " file.py

# Find import statements
grep "^from\|^import" file.py

# Search with context
grep -B 5 -A 10 "PATTERN" file.py
```

### For AuZoom Approach
```python
# Shallow navigation
auzoom_read("file.py", level="skeleton")

# Small file
auzoom_read("file.py", level="full")

# Large file summary
auzoom_read("file.py", level="summary")

# Targeted summary (new)
auzoom_read("file.py::function_name", level="summary")

# Graph analysis
auzoom_find("function_name")
auzoom_get_dependencies("node_id", depth=2)
```

### Hybrid Pattern
```python
# 1. Discover with grep
results = bash("grep -r 'PATTERN' --include='*.py'")

# 2. Narrow down files
candidate_files = parse_grep_results(results)

# 3. Scan structures with skeleton
for file in candidate_files:
    structure = auzoom_read(file, level="skeleton")

# 4. Deep dive on promising files
for node in interesting_nodes:
    details = auzoom_read(file + "::" + node, level="summary")
```

