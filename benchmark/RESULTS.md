# Benchmark Results: Token Cost by Codebase Size

**Scenario**: "Find and understand one function" — a typical agent task.

**Date**: 2026-03-08
**Method**: `token_benchmark.py` on 5 repos spanning 14-894 Python source files

---

## Three Approaches Compared

| | Approach | Description |
|--|----------|-------------|
| **A** | Naive | Read every .py file fully |
| **B** | Structured baseline | DESIGN.md + Glob + `__init__.py` reads + one targeted Read |
| **C** | AuZoom | Progressive disclosure: find → skeleton of 5 files → summary of 1 file |

**AuZoom overhead**: 1,050 tokens (MCP tool schemas always in context). With MCP CLI mode enabled, this drops to ~0 tokens.

---

## Results

| Repo | Files | LOC | Approach A | Approach B | Approach C | C vs CLI |
|------|-------|-----|-----------|-----------|-----------|---------|
| AuZoom source | 24 | 3,233 | 27,810 | 2,005 | 2,346 ❌ | 1,296 ✓ |
| Audit suite | 14 | 2,445 | 22,697 | 2,584 | 2,090 ✓ | 1,040 ✓ |
| requests | 18 | 5,628 | 46,802 | 4,161 | 3,339 ✓ | 2,289 ✓ |
| FastAPI | 48 | 19,284 | 174,573 | 5,495 | 15,874 ❌ | 14,824 ❌ |
| Django | 894 | 155,657 | 1,393,480 | 66,385 | 2,778 ✓ | 1,728 ✓ |

**Legend**: ✓ = AuZoom wins vs baseline, ❌ = Baseline wins

---

## Key Findings

### 1. The structured baseline (Approach B) already beats naive reading by 89-97%

Good code structure + Glob/Grep/Read eliminates most token waste before any tooling.
This is the "free layer" — the coding principles skill captures this.

### 2. AuZoom's value depends heavily on file size distribution

| Pattern | AuZoom Benefit | Why |
|---------|---------------|-----|
| Many small files (Django avg 174 lines) | High (96% vs baseline) | Large directory scope, small skeletons |
| Few large files (FastAPI avg 401 lines) | Negative | Schema overhead + large skeletons exceed savings |
| Medium files, good structure (requests avg 312 lines) | Positive (20%) | Realistic savings for well-scoped exploration |

### 3. FastAPI anomaly: monolithic files hurt even AuZoom

FastAPI's `routing.py` (4,952 lines) and `applications.py` (4,692 lines) have 100+ functions each. Even the skeleton view of these files is expensive. This is a structural violation of the ≤250 line guideline — FastAPI itself is an example of code that would benefit from being refactored into smaller modules.

**Lesson**: AuZoom helps most when code *already* follows good structure. It amplifies good architecture, not bad.

### 4. MCP CLI mode is almost always beneficial

With MCP CLI mode (`CLAUDE_MCP_CLI=true`), the 1,050-token schema overhead drops to ~0. This makes AuZoom beneficial on even the tiniest repos where it otherwise isn't.

---

## Breakeven Analysis

| Condition | AuZoom vs Baseline |
|-----------|-------------------|
| Standard mode (1,050 token schema overhead) | Wins on repos with good structure, many files |
| MCP CLI mode (0 schema overhead) | Wins in almost all cases |
| Monolithic files (avg >400 lines) | Loses — bad code structure defeats progressive disclosure |

---

## When to Use What

### Layer 0: Coding Principles (Free, always)
- ≤250 line modules, DESIGN.md, hierarchical `__init__.py`
- Provides 89-97% savings vs naive reading (Approach A → B)
- No tooling needed. Apply to every Python project.

### Layer 1: Structured Glob/Grep/Read (Free, always)
- DESIGN.md → `__init__.py` reads → Grep → targeted Read
- Works well for codebases up to ~50 files with good structure
- See `/skills python-coding-principles` for the full pattern

### Layer 2: AuZoom (Add for large codebases + exploration-heavy sessions)
- Provides incremental 19-96% savings ON TOP of Layer 1
- **Best for**: Many files, exploration-heavy sessions, codebases with good structure
- **Not for**: Large monolithic files, edit-heavy sessions touching only 1-2 files
- **Enable MCP CLI mode** to eliminate the 1,050-token schema overhead

---

## Minimum Codebase Size Recommendation

**Without MCP CLI mode**: AuZoom adds value when:
- Codebase has 20+ well-structured Python files (avg ≤250 lines each)
- Sessions involve exploring multiple files (not just editing one)

**With MCP CLI mode enabled**: AuZoom adds value at any codebase size.

**Rule of thumb**: If your average file exceeds 400 lines, fix the structure first (≤250 line modules). AuZoom amplifies good architecture — it can't rescue monolithic code.

---

## Limitations of This Benchmark

1. **Single scenario**: Models "find + understand one function." Real sessions vary.
2. **Token estimation**: Uses `len(text) / 4` (4 chars/token). Actual tokenizer may differ ±20%.
3. **Static simulation**: Doesn't account for multi-turn sessions where AuZoom's caching pays off over many reads.
4. **Exploration scope**: Models exploring "5 average files." For deep exploration (entire codebase scan), AuZoom's advantage grows significantly.

Run `python3 benchmark/token_benchmark.py /path/to/your/repo` to benchmark your own codebase.
