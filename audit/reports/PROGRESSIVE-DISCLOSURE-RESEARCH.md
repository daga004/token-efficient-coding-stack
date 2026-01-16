# Progressive Disclosure in Code Navigation: Deep Research & Analysis

**Date**: 2026-01-13
**Status**: Research phase
**Purpose**: Understand token overhead, critique current approach, prescribe optimizations

---

## Executive Summary

**Problem**: Progressive disclosure (skeleton → summary → full) adds **massive token overhead** for small files:
- **Skeleton**: 150 tokens (21 nodes × 7 tokens/node)
- **Summary**: 1,125 tokens (21 nodes × 54 tokens/node)
- **Full file (raw)**: 450 tokens

**Root cause**: Summary level includes metadata that **exceeds** raw source code for small files.

**Key finding**: The issue is NOT with the progressive disclosure philosophy, but with the **implementation granularity** and **metadata verbosity**.

---

## Part 1: What's Actually in the Metadata

### Analysis of server.py (224 lines, 21 nodes)

#### Skeleton Level (~150 tokens)

**Per node includes**:
```json
{
  "id": "/Users/dhirajd/.../server.py::AuZoomMCPServer._tool_read",
  "name": "_tool_read",
  "type": "method",
  "dependencies": ["...::_read_python_file", "...::_read_non_python_file"]
}
```

**Token estimate**: ~7 tokens/node
- `id`: ~35 chars (8-9 tokens) - FULL ABSOLUTE PATH
- `name`: ~10 chars (2-3 tokens)
- `type`: ~6 chars (1-2 tokens)
- `dependencies`: ~30 chars (7-8 tokens) per dependency (FULL PATHS)

**Total skeleton**: 21 nodes × 7 tokens = **~147 tokens**

#### Summary Level (~1,125 tokens)

**Additional per node**:
```json
{
  "signature": "_tool_read(self, args: dict)",
  "docstring": "Handle auzoom_read - the main file reading tool.",
  "line_start": 47,
  "line_end": 70
}
```

**Token estimate**: ~54 tokens/node
- Everything from skeleton: 7 tokens
- `signature`: ~20 chars (5 tokens)
- `docstring`: ~60 chars truncated (15 tokens)
- `line_start/end`: 2 fields × 2 tokens = 4 tokens
- **JSON overhead**: brackets, quotes, commas (~23 tokens per node)

**Total summary**: 21 nodes × 54 tokens = **~1,134 tokens**

#### Full Level (raw source code: ~450 tokens)

**Additional per node**:
```json
{
  "children": ["child_id1", "child_id2"],
  "file_path": "/Users/dhirajd/.../server.py",
  "source": "def _tool_read(self, args: dict):\n    ..."
}
```

**Token estimate**: ~100 tokens/node average (depends on source length)

---

## Part 2: Token Estimates for Different File Sizes

### Formula Analysis

Using empirical data from server.py:

| File Size | Lines | Nodes | Raw Tokens | Skeleton | Summary | Full (JSON) | Progressive Overhead |
|-----------|-------|-------|------------|----------|---------|-------------|---------------------|
| **Tiny** | 50 | 5 | 110 | 35 | 270 | 500 | +145% (skeleton→summary) |
| **Small** | 150 | 12 | 330 | 84 | 648 | 1,200 | +96% |
| **Medium** | 250 | 20 | 550 | 140 | 1,080 | 2,000 | +96% |
| **Large** | 500 | 40 | 1,100 | 280 | 2,160 | 4,000 | +96% |
| **Huge** | 1000 | 80 | 2,200 | 560 | 4,320 | 8,000 | +96% |

**Key insight**: **250-line file = ~550 tokens raw, ~1,080 tokens summary** (2× overhead)

### Breakeven Analysis

**Question**: At what file size does progressive win?

**Scenario**: Shallow task (skeleton sufficient)
- File < 300 lines: **Skeleton (140 tokens) < Raw (650 tokens)** → Progressive wins ✅
- File < 500 lines: Skeleton still wins

**Scenario**: Medium task (summary needed)
- File < 500 lines: **Summary (1,080 tokens) > Raw (1,100 tokens)** → Progressive loses ❌
- File > 600 lines: Summary < Raw → Progressive starts winning

**Scenario**: Deep task (full needed, but progressive reads skeleton → summary → full)
- File < any size: **Progressive ALWAYS loses** (overhead from intermediate reads) ❌

---

## Part 3: What Metadata is Necessary vs Unnecessary

### Current Metadata in Summary Level

| Field | Necessary? | Tokens | Justification |
|-------|-----------|--------|---------------|
| **id** (full path) | ⚠️ BLOATED | 8-9 | Absolute paths unnecessary - relative or shortened IDs sufficient |
| **name** | ✅ YES | 2-3 | Core identifier |
| **type** | ✅ YES | 1-2 | Essential for understanding |
| **dependencies** (full paths) | ⚠️ BLOATED | 7-8 each | Full paths unnecessary - names sufficient |
| **signature** | ✅ YES | 5 | Critical for function understanding |
| **docstring** (truncated) | ⚠️ MAYBE | 15 | Useful but truncation at 100 chars adds little value |
| **line_start/end** | ⚠️ OPTIONAL | 4 | Useful for navigation, but not essential for understanding |
| **JSON formatting** | ❌ BLOAT | 23 | Indentation, quotes, brackets - necessary evil of JSON |

### Dependency Information Analysis

**Current approach** (dependencies field):
```json
"dependencies": [
  "/Users/dhirajd/Documents/claude/auzoom/src/auzoom/mcp/server.py::AuZoomMCPServer._read_python_file",
  "/Users/dhirajd/Documents/claude/auzoom/src/auzoom/mcp/server.py::AuZoomMCPServer._read_non_python_file"
]
```

**Problems**:
1. **Full absolute paths** - Massive token waste (8-9 tokens per dependency)
2. **Repeated prefix** - Same file path repeated for each dependency
3. **Module hierarchy** - Full qualified names when short names would suffice in context

**Better approach** (relative names):
```json
"dependencies": ["_read_python_file", "_read_non_python_file"]
```
**Savings**: 16 tokens → 4 tokens (75% reduction)

---

## Part 4: Core Philosophy Alignment

### Your Stated Philosophy

> "The name of the modules and hierarchy of the modules itself should be sufficient to get a high-level view. The user can zoom in based on the need on a specific part."

**Analysis**: Current implementation **violates** this principle.

**What's wrong**:
1. **Skeleton includes full paths** - Not just "names and hierarchy", but verbose absolute paths
2. **Summary includes truncated docstrings** - Forces read of summary even when skeleton name alone might suffice
3. **JSON verbosity** - Format adds ~40% overhead (brackets, quotes, formatting)
4. **Node-level granularity** - Every import, every method gets full metadata

**What should be** (aligned with philosophy):
1. **Skeleton** = Module structure only (files, classes, functions) - no imports, minimal IDs
2. **Names only** = Function/class names without signatures or docstrings
3. **Hierarchy visible** = Parent-child relationships clear
4. **Zoom on demand** = Select specific function → get summary/full for THAT function only

---

## Part 5: Graph Representation Efficiency

### Current Graph Format

**Skeleton level** (21 nodes):
```json
{
  "type": "python",
  "file_path": "/Users/dhirajd/.../server.py",
  "level": "skeleton",
  "nodes": [
    { "id": "...", "name": "...", "type": "...", "dependencies": [...] },
    ...  // 20 more nodes
  ],
  "node_count": 21,
  "cached": true
}
```

**Token breakdown**:
- Wrapper metadata: 30 tokens
- Per-node: 7 tokens × 21 = 147 tokens
- **Total**: ~177 tokens (vs 147 estimated earlier)

### More Token-Efficient Representations

#### Option 1: Hierarchical Tree (Indented Text)

```
server.py
  imports: json, Path, Optional, LazyCodeGraph, FetchLevel, ...
  main() → AuZoomMCPServer.run
  class AuZoomMCPServer
    __init__(project_root, auto_warm)
    handle_tool_call(tool_name, arguments)
    _tool_read(args) → _read_python_file, _read_non_python_file
    _read_python_file(file_path, level_str)
    _read_non_python_file(file_path, level_str, offset, limit)
    _tool_find(args)
    _tool_get_dependencies(args)
    _tool_stats(args)
    _tool_validate(args)
    run()
```

**Token estimate**: ~80 tokens (55% reduction vs JSON skeleton)

**Pros**:
- Human readable
- Clear hierarchy
- Minimal tokens
- Dependencies shown inline (→)

**Cons**:
- Less structured for programmatic parsing
- Harder to extract specific nodes

#### Option 2: Compact JSON (Short IDs)

```json
{
  "file": "server.py",
  "nodes": [
    {"n": "main", "t": "fn", "d": ["run"]},
    {"n": "AuZoomMCPServer", "t": "cls", "ch": ["__init__", "handle_tool_call", ...]},
    {"n": "_tool_read", "t": "mth", "d": ["_read_python_file", "_read_non_python_file"]},
    ...
  ]
}
```

**Token estimate**: ~110 tokens (38% reduction vs current JSON)

**Pros**:
- Still parseable JSON
- Significant token savings (short keys)
- Relative names only

**Cons**:
- Less readable for humans
- Requires documentation of short keys

#### Option 3: Hybrid (Markdown + JSON for details)

**Skeleton** = Markdown hierarchy (80 tokens)
**Summary** = JSON with full details for specific nodes when requested (per-node basis)
**Full** = Source code only (no JSON wrapper)

**Token savings**: 45-60% across all levels

---

## Part 6: Literature Review - Progressive Disclosure in Code

### Existing Approaches

#### 1. **IDE Folding** (VSCode, IntelliJ)
- **Mechanism**: Collapse code blocks (functions, classes) to single line
- **Token savings**: Visual only (full code still in memory/context)
- **Limitation**: Not token-aware, just UI convenience

#### 2. **Language Server Protocol (LSP) - Outline**
- **Mechanism**: Provides document symbols (flat or hierarchical list)
- **Format**: Array of `{name, kind, range, children}`
- **Token efficiency**: High (minimal metadata, no source)
- **Use case**: File navigation, not full code understanding

**LSP Example**:
```json
[
  {"name": "AuZoomMCPServer", "kind": 5, "range": {"start": 12, "end": 216},
   "children": [
     {"name": "__init__", "kind": 6, "range": {"start": 20, "end": 26}},
     ...
   ]}
]
```

**Token estimate for server.py**: ~60 tokens (LSP outline) vs 147 tokens (our skeleton)

#### 3. **Code Summarization (ML-based)**
- **Papers**:
  - "A Neural Architecture for Generating Natural Language Descriptions from Source Code Changes" (2017)
  - "Structured Neural Summarization" (2018)
  - "CodeBERT: A Pre-Trained Model for Programming and Natural Languages" (2020)

- **Approach**: Generate natural language summaries of code
- **Token efficiency**: High (20-50 tokens for entire function)
- **Limitation**: Requires ML inference, not always accurate

**Example**:
```
Function: _tool_read
Summary: "Handles file reading with support for Python and non-Python files at different detail levels"
Tokens: ~20
```

vs our summary: ~54 tokens with full JSON metadata

#### 4. **Tree-sitter** (Syntax Tree Navigation)
- **Mechanism**: Incremental parsing, fast queries
- **Format**: S-expressions or JSON AST
- **Token efficiency**: Low (full AST is verbose), but queries can be selective
- **Use case**: Code analysis, refactoring tools

#### 5. **Semantic Code Search** (Sourcegraph, GitHub)
- **Mechanism**: Index code symbols, search by name/type
- **Format**: Search results with snippets
- **Token efficiency**: High (only return matches)
- **Limitation**: Requires query, not progressive disclosure

### Best Practices from Literature

1. **Hierarchical navigation** - Start broad (file/module), drill down (class → method)
2. **Context-sensitive detail** - Show more detail where user is focused
3. **Semantic chunking** - Group related code (class + methods, not individual lines)
4. **Minimal metadata** - Only include what's needed for current navigation level
5. **Lazy loading** - Fetch details on demand, not upfront

---

## Part 7: Critique of Current Approach

### What's Good ✅

1. **Lazy parsing** - Files only parsed when accessed
2. **Caching** - Parsed results cached to disk
3. **Dependency tracking** - AST-based, 100% accurate (Phase 2 validation)
4. **Three-level hierarchy** - Skeleton/summary/full is good conceptually

### What's Broken ❌

1. **Granularity too fine** - Every import gets a node (9 import nodes in server.py)
2. **Full absolute paths** - Massive token waste (8-9 tokens per ID)
3. **JSON verbosity** - Format adds 40% overhead
4. **Summary = mini-full** - Includes too much (line numbers, truncated docstrings, etc.)
5. **No file-size awareness** - Same approach for 50-line and 5000-line files
6. **Import nodes bloat skeleton** - 9 of 21 nodes are imports (43%)

### Specific Issues

#### Issue 1: Import Nodes

**Current**:
```json
{
  "id": "/Users/dhirajd/.../server.py::import::json",
  "name": "import json",
  "type": "import",
  "dependencies": []
}
```

**Problem**: Each import is a separate node (7 tokens each × 9 imports = 63 tokens)

**Solution**: Collapse imports into single summary
```json
{"imports": ["json", "Path", "Optional", "LazyCodeGraph", "FetchLevel", "FileSummarizer", "JSONRPCHandler", "CodeValidator", "os"]}
```

**Savings**: 63 tokens → 15 tokens (76% reduction)

#### Issue 2: Full Absolute Path IDs

**Current**: `/Users/dhirajd/Documents/claude/auzoom/src/auzoom/mcp/server.py::AuZoomMCPServer._tool_read`

**Token count**: ~35 chars = 8-9 tokens

**Solution**: Relative path + short ID
- Within file: Just `_tool_read` (current context = server.py)
- Cross-file: `server.py::_tool_read`
- With file context header: Just `_tool_read`

**Savings**: 8-9 tokens → 2-3 tokens (70% reduction)

#### Issue 3: JSON Format Overhead

**Current** (per node):
```json
{
  "id": "...",
  "name": "...",
  "type": "...",
  "dependencies": [...]
}
```

**Token breakdown**:
- Content: 7 tokens
- JSON formatting: `{}`, quotes, colons, commas = ~5 tokens
- **Overhead**: 41%

**Solution A**: Use more compact format (YAML, CSV, custom)

**Solution B**: Use text-based hierarchy (Markdown/indented)

---

## Part 8: Optimization Experiments (Prescriptions)

### Experiment 1: Minimal Skeleton (Hierarchy Only)

**Hypothesis**: Showing only module structure (no imports, no dependency lists) is sufficient for initial navigation.

**Implementation**:
```
server.py (224 lines)
  main()
  class AuZoomMCPServer
    __init__()
    handle_tool_call()
    _tool_read()
    _read_python_file()
    _read_non_python_file()
    _tool_find()
    _tool_get_dependencies()
    _tool_stats()
    _tool_validate()
    run()
```

**Token estimate**: ~40 tokens (73% reduction vs current 147)

**Test**: Can agents complete shallow tasks (Task 1: "List public functions") with this?

**Success criteria**: ≥90% task success, <50 tokens

---

### Experiment 2: Compact JSON Skeleton

**Implementation**:
```json
{
  "file": "server.py",
  "imports": ["json", "Path", "Optional", ...],
  "nodes": [
    {"name": "main", "type": "function"},
    {"name": "AuZoomMCPServer", "type": "class", "methods": [
      "__init__", "handle_tool_call", "_tool_read", ...
    ]}
  ]
}
```

**Token estimate**: ~80 tokens (46% reduction)

**Changes from current**:
- No full path IDs
- Imports collapsed to array
- Methods listed under class (not separate nodes)
- No dependencies in skeleton

**Test**: Same as Experiment 1

---

### Experiment 3: Smart Summary (Context-Aware Detail)

**Hypothesis**: Summary level should only include metadata for requested nodes, not all nodes in file.

**Current behavior**: `auzoom_read(server.py, level=summary)` returns summary for ALL 21 nodes

**Proposed behavior**:
1. `auzoom_read(server.py, level=skeleton)` → Full file skeleton (40-80 tokens)
2. Agent identifies function of interest: `_tool_read`
3. `auzoom_read(server.py::_tool_read, level=summary)` → Summary for THAT function only
4. Response: ~54 tokens (signature, docstring, line range) for ONE node

**Token savings**: Instead of 1,125 tokens (summary for all), get 40 + 54 = 94 tokens (skeleton + 1 summary)

**API change required**: Support node-level requests, not just file-level

---

### Experiment 4: File Size Thresholds

**Hypothesis**: Small files (<300 tokens raw) should bypass progressive disclosure.

**Implementation**:
```python
def get_file(file_path, level):
    raw_size = estimate_raw_tokens(file_path)

    if raw_size < 300:
        # Small file: always return full, ignore level
        return read_file_raw(file_path)
    else:
        # Large file: use progressive disclosure
        return get_progressive_view(file_path, level)
```

**Test**: Re-run Task 3 ("Explain auzoom_read") with this change
- Current: 1,325 tokens (skeleton + summary)
- Expected: 450 tokens (raw file bypasses progressive)
- **Savings**: -194% → +0% (no overhead)

**Success criteria**: Net savings ≥0% on medium tasks for small files

---

### Experiment 5: Dependency Graph Compression

**Current** (in skeleton):
```json
"dependencies": [
  "/Users/dhirajd/.../server.py::AuZoomMCPServer._read_python_file",
  "/Users/dhirajd/.../server.py::AuZoomMCPServer._read_non_python_file"
]
```

**Tokens**: ~16

**Compressed** (short names, file context implicit):
```json
"deps": ["_read_python_file", "_read_non_python_file"]
```

**Tokens**: ~4 (75% reduction)

**Test**: Can agents still use dependency graph effectively with short names?

**Success criteria**: Task 9 (find callers) still works with same quality

---

### Experiment 6: LSP-Inspired Format

**Hypothesis**: Language Server Protocol outline format is more token-efficient.

**Implementation**:
```json
{
  "symbols": [
    {"name": "main", "kind": "function", "range": [219, 224]},
    {"name": "AuZoomMCPServer", "kind": "class", "range": [12, 216], "children": [
      {"name": "__init__", "kind": "method", "range": [20, 26]},
      {"name": "handle_tool_call", "kind": "method", "range": [28, 45]},
      ...
    ]}
  ]
}
```

**Token estimate**: ~60 tokens (59% reduction vs current skeleton)

**Test**: Can agents navigate effectively with LSP-style outline?

---

### Experiment 7: Natural Language Summaries

**Hypothesis**: Single-sentence summaries are more token-efficient than structured metadata.

**Current summary** (~54 tokens per node):
```json
{
  "id": "...",
  "name": "_tool_read",
  "signature": "_tool_read(self, args: dict)",
  "docstring": "Handle auzoom_read - the main file reading tool.",
  "line_start": 47,
  "line_end": 70
}
```

**NL summary** (~15 tokens):
```
_tool_read: Handles file reading with Python/non-Python dispatch (lines 47-70)
```

**Test**: Can agents answer questions (Task 3: "What does auzoom_read do?") with NL summaries?

**Challenge**: Generating accurate NL summaries programmatically (without ML)

---

## Part 9: Recommended Experiment Sequence

### Phase 1: Quick Wins (Low-hanging fruit)

**Experiment 4 (File size threshold)** + **Experiment 5 (Dependency compression)**
- **Time**: 2-3 hours implementation + 1 hour testing
- **Expected impact**: 40-60% token reduction on small files
- **Risk**: Low (easy to revert)

### Phase 2: Format Optimization

**Experiment 2 (Compact JSON)** + **Experiment 1 (Minimal skeleton) as fallback**
- **Time**: 4-6 hours implementation + 2 hours testing
- **Expected impact**: 50-70% token reduction on skeleton level
- **Risk**: Medium (breaks existing clients)

### Phase 3: Smart Summary

**Experiment 3 (Node-level requests)**
- **Time**: 8-12 hours implementation (API changes) + 3 hours testing
- **Expected impact**: 80-90% token reduction on summary level
- **Risk**: High (significant API change)

### Phase 4: Alternative Formats (Research)

**Experiment 6 (LSP-inspired)** or **Experiment 7 (NL summaries)**
- **Time**: 16-24 hours research + implementation + testing
- **Expected impact**: 60-80% token reduction (if successful)
- **Risk**: High (major redesign)

---

## Part 10: Updated Phase 6.5 Plan 01 Scope

### Original Scope
- Execute 10 tasks measuring progressive traversal patterns
- Validate agents traverse progressively (skeleton → summary → full)
- Calculate net token savings

### **Expanded Scope (Research + Optimization)**

#### Task 1: Document Current Metadata Bloat (DONE)
- ✅ Analyzed skeleton/summary/full formats
- ✅ Identified specific bloat sources (full paths, imports, JSON overhead)
- ✅ Calculated token breakdowns per node

#### Task 2: Prescribe Optimization Experiments (DONE)
- ✅ Designed 7 experiments targeting different bloat sources
- ✅ Estimated token savings for each
- ✅ Prioritized by impact vs effort

#### Task 3: Implement Quick Wins (NEW - 3-4 hours)
- Experiment 4: File size threshold (bypass progressive for <300 token files)
- Experiment 5: Dependency compression (short names instead of full paths)
- Create optimized branch of auzoom
- Re-run Task 3 to measure improvement

#### Task 4: Validate Optimization Impact (NEW - 1-2 hours)
- Execute 3-5 tasks with optimized auzoom
- Compare token consumption: original vs optimized
- Calculate actual savings vs estimates
- Assess quality impact (any degradation?)

#### Task 5: Comprehensive Report & Recommendations (NEW - 2 hours)
- Synthesize all findings
- Recommend path forward (quick wins first, then major redesign?)
- Update V1 certification impact (can we claim token savings with optimizations?)

**Total estimated time**: 6-8 hours (vs original 20-30 min)

---

## Part 11: Immediate Next Steps

### Option A: Continue Original Plan (Execute remaining 7 tasks)
- **Time**: ~20 min
- **Value**: Complete data set, confirm pattern
- **Limitation**: Doesn't fix underlying issue

### Option B: Implement Quick Win Optimizations First
- **Time**: 3-4 hours
- **Value**: Validate that optimizations solve small file overhead
- **Risk**: Time investment before validating full progressive approach

### Option C: Hybrid (Quick optimization + selective task execution)
- **Time**: 4-5 hours total
- **Steps**:
  1. Implement Experiment 4 (file size threshold) - 1 hour
  2. Implement Experiment 5 (dependency compression) - 1 hour
  3. Re-run Task 3 with optimized auzoom - 10 min
  4. Execute 2 new tasks (1 deep, 1 large file) - 30 min
  5. Analyze results and write comprehensive report - 2 hours

**Recommendation**: **Option C** - Prove optimizations work with targeted tests, then decide on full validation

---

## Conclusion

**Core insight**: Progressive disclosure philosophy is sound, but current implementation is bloated.

**Key problems**:
1. Full absolute path IDs (8-9 tokens each)
2. Individual import nodes (43% of skeleton)
3. JSON formatting overhead (40%)
4. Summary includes all nodes, not requested node only
5. No file-size awareness

**Optimization potential**: 50-80% token reduction across all levels

**Recommended path**:
1. Implement quick wins (file threshold + dependency compression)
2. Validate with targeted tasks
3. If successful, pursue deeper optimizations (node-level requests, format redesign)
4. Update Phase 6.5 plans with optimization-focused experiments

**V1 certification impact**: With optimizations, progressive disclosure can claim token savings. Without them, cannot certify.
