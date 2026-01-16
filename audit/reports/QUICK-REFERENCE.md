# AuZoom AST vs Grep: Quick Reference Guide

**One-page decision guide for tool selection**

---

## Decision at a Glance

```
┌──────────────────────────────────────────────────────────────────────┐
│                      WHAT DO YOU NEED TO DO?                        │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Search for files?              → Use grep -r                       │
│  See code structure?            → Use AuZoom skeleton               │
│  Understand small function?     → Use raw read                      │
│  Understand large function?     → Use AuZoom summary                │
│  Find all function callers?     → Use AuZoom graph                  │
│  Refactor multiple files?       → Use grep + skeleton hybrid        │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## By File Size

### Files <50 lines
```
Token cost breakdown:
  Raw read: ~140 tokens
  Skeleton: ~35 tokens
  Summary: ~270 tokens

Use: Raw read (simplest)
Avoid: Summary (190% overhead)
```

### Files 50-200 lines
```
Token cost breakdown:
  Raw read: ~210-560 tokens
  Skeleton: ~60-150 tokens
  Summary: ~320-810 tokens

Use: Raw read or skeleton
Avoid: Summary (50-100% overhead)
Reason: Summary metadata exceeds file size
```

### Files 200-500 lines
```
Token cost breakdown:
  Raw read: ~560-1,400 tokens
  Skeleton: ~140-350 tokens
  Summary: ~1,080-2,700 tokens

Use: Raw read for understanding, skeleton for structure
Avoid: Summary (50% overhead)
Reason: Progressive adds no value for this range
```

### Files 500-1000 lines
```
Token cost breakdown:
  Raw read: ~1,400-2,800 tokens
  Skeleton: ~350-700 tokens
  Summary: ~2,700-5,400 tokens

Use: Skeleton + targeted node summaries
Consider: Summary if need complete function documentation
Reason: Breakeven point approaching; context helps
```

### Files >1000 lines
```
Token cost breakdown:
  Raw read: >2,800 tokens
  Skeleton: >700 tokens
  Summary: >5,400 tokens

Use: Progressive disclosure (skeleton → summary)
Reason: Prevents reading unnecessary code
Savings: +40-60% vs raw read
```

---

## By Task Type

### "Find files with X"
```
Tool: grep -r "pattern" --include="*.py"
Cost: 50-150 tokens
Alternative: AuZoom find (auzoom_find)
Savings: +40-60% with grep
```

**Example**:
```bash
grep -r "DatabaseError" --include="*.py"
# Shows: 8 files with DatabaseError
# Cost: ~80 tokens
# vs AuZoom scanning 50+ files: 700+ tokens
```

---

### "List all public methods"
```
Tool: AuZoom skeleton
Cost: 140-300 tokens
Alternative: Grep (~80 tokens, 70% accurate)
Quality: 100% accuracy (AST-based)
Why AuZoom: Captures decorators, classmethods, nested functions
```

**Example**:
```
grep "^def " myfile.py  # Misses: classmethods, nested, decorated
# vs
auzoom_read("myfile.py", skeleton)  # Shows everything
```

---

### "Explain what function X does"
```
If file <300 tokens:
  Tool: Raw read
  Cost: 200-450 tokens
  Savings: +60% vs progressive

If file 300-600 tokens:
  Tool: Skeleton + grep for context
  Cost: 250-400 tokens
  Alternative: Raw read (350-900)

If file >600 tokens:
  Tool: Skeleton → targeted summary
  Cost: 140-500 tokens
  Savings: +30-50% vs raw read
```

**Example**:
```python
# Small file (224 lines)
auzoom_read("server.py", skeleton)  # 150 tokens
# Look for _tool_read
# grep -A 20 "def _tool_read" # 200 tokens
# Total: 350 tokens
# vs progressive: 1,325 tokens
# Savings: +279%
```

---

### "Find all functions calling X"
```
Tool: AuZoom graph (essential)
Cost: 600-1,000 tokens
Alternative: grep + manual filtering (900+ tokens, 70% accurate)
Quality: 100% accuracy, full dependency chain
```

**Why not grep**:
- False positives: "validate_file" matches in comments, strings
- Incomplete: Doesn't show call chains
- Manual work required to verify and trace

---

### "Implement feature across codebase"
```
Step 1: Discovery
  Tool: grep -r "related_function"
  Cost: 100 tokens
  Purpose: Find files to modify

Step 2: Structure analysis
  Tool: AuZoom skeleton (for each candidate file)
  Cost: 140 tokens × 5 files = 700 tokens
  Purpose: Understand what needs changing

Step 3: Implementation
  Tool: Raw reads on specific sections
  Cost: 300 tokens × 3 files = 900 tokens
  Purpose: See full context for changes

Total: 1,700 tokens
vs scanning all files with AuZoom: 3,000+ tokens
Savings: +43%
```

---

## Token Cost Comparison Table

### Quick lookup: Tool vs Token Cost

| Task | Grep | Raw Read | Skeleton | Summary | Graph | Winner |
|------|------|----------|----------|---------|-------|--------|
| Find files | 80 | — | 200 | — | 300 | **Grep** ⭐ |
| List methods | 120 | — | 140 | — | — | **Skeleton** ⭐ |
| Explain (small) | 200 | 300 | 150 | 500 | — | **Raw** ⭐ |
| Explain (medium) | 400 | 700 | 250 | 1,000 | — | **Skeleton+grep** ⭐ |
| Explain (large) | 500 | 1,500 | 350 | 800 | — | **Summary** ⭐ |
| Find callers | 900* | — | 600 | — | 700 | **Graph** ⭐ |
| Refactor | 600 | 1,200 | 800 | — | — | **Grep+Skeleton** ⭐ |

*Grep result requires manual filtering for accuracy

---

## Decision Matrix: File Size × Task Type

```
                    <200 lines          200-600 lines       >600 lines
┌─────────────────────────────────────────────────────────────────────┐
│ Shallow          Skeleton 70tk        Skeleton 100tk      Skeleton 200tk
│ (List, show)     Alt: Grep (80tk)     Alt: Grep (120tk)   Alt: None
├─────────────────────────────────────────────────────────────────────┤
│ Medium           Raw 280tk ⭐         Raw 500tk           Summary 800tk ⭐
│ (Explain, find)  Alt: Grep (150tk)    Alt: Skeleton       Alt: Raw 1500tk
├─────────────────────────────────────────────────────────────────────┤
│ Deep             Raw 280tk ⭐         Raw 500tk ⭐        Summary 800tk ⭐
│ (Understand)     Alt: Skeleton        Alt: Skeleton       Alt: Raw 1500tk
├─────────────────────────────────────────────────────────────────────┤
│ Discovery        Grep 80tk ⭐         Grep 100tk ⭐       Grep 120tk ⭐
│ (Find files)     Alt: Skeleton        Alt: Skeleton       Alt: Skeleton
├─────────────────────────────────────────────────────────────────────┤
│ Graph            Graph 600tk ⭐       Graph 700tk ⭐      Graph 800tk ⭐
│ (Find callers)   Alt: Grep 900tk*     Alt: Grep 1000tk*   Alt: Grep 1100tk*
└─────────────────────────────────────────────────────────────────────┘

⭐ = Recommended
* = Grep result needs manual filtering
```

---

## Real-World Examples

### Example 1: "Add logging to all DB calls"

```
Step 1: Find DB module files
  grep -r "class.*Database" --include="*.py"  → 80 tokens

Step 2: Check structure of promising files
  auzoom_read("models/database.py", skeleton)  → 140 tokens
  auzoom_read("models/user.py", skeleton)      → 140 tokens

Step 3: Understand specific functions
  grep -A 10 "def query" models/database.py   → 150 tokens

Step 4: Verify patterns
  Raw reads on 2 files × 300 tokens            → 600 tokens

Total: 1,110 tokens

vs using AuZoom on all 30 model files: 4,200 tokens
Savings: +278%
```

---

### Example 2: "Understand how authentication works"

```
Step 1: Find auth-related code
  grep -r "authenticate\|login\|auth" --include="*.py"  → 100 tokens

Step 2: Identify main auth module
  auzoom_read("auth/handler.py", skeleton)  → 200 tokens

Step 3: Get full context of auth flow
  auzoom_read("auth/handler.py", summary)   → 600 tokens

Step 4: Trace to dependencies
  auzoom_get_dependencies("authenticate", depth=2)  → 400 tokens

Total: 1,300 tokens
vs raw reading auth files: 1,600 tokens
Savings: +23%
```

---

### Example 3: "Find where config is loaded"

```
If config file small (<300 tokens):
  Raw read: 250 tokens ⭐

If config loading scattered across files:
  grep -r "load_config\|CONFIG" --include="*.py"  → 100 tokens
  auzoom_find("load_config")  → 50 tokens
  auzoom_get_dependencies("load_config", depth=1)  → 200 tokens

Total: 350 tokens
vs raw reading 10 files: 2,500 tokens
Savings: +614%
```

---

## Key Metrics to Remember

| Metric | Value | Impact |
|--------|-------|--------|
| 64% of files | <200 lines | Small files dominate |
| Small file summary overhead | -194% | Avoid summary on small files |
| Large file summary savings | +45% | Summary viable >600 lines |
| Grep discovery savings | +60% | Use grep for file searches |
| AST accuracy | 100% | Always better than regex |
| Skeleton accuracy | 100% | Equals summary for structure |
| Graph essential | Always | No grep alternative for accuracy |

---

## When to Break the Rules

### Use grep even for small files IF:
- You only need partial information
- Pattern is very specific
- Speed matters more than completeness
- E.g., "does this file import X?"

### Use summary even on small files IF:
- You need type information
- You need docstring details
- Cross-file relationships matter
- E.g., "what are the method signatures?"

### Use raw read on large files IF:
- Full context essential
- Need to see actual implementation
- Alternative approaches insufficient
- E.g., "how does this complex algorithm work?"

---

## Pro Tips

### Tip 1: Estimate file size first
```bash
wc -l file.py  # If <300 lines, use raw read for explanation
```

### Tip 2: Start with skeleton
```python
auzoom_read(file, skeleton)  # 140 tokens
# Understand structure, then decide next step
# Usually sufficient; rarely need to escalate
```

### Tip 3: Use targeted requests
```python
# Instead of:
auzoom_read("server.py", summary)  # 1,125 tokens

# Do:
auzoom_read("server.py", skeleton)  # 140 tokens
# Find function: _tool_read
auzoom_read("server.py::_tool_read", summary)  # 54 tokens
# Total: 194 tokens (83% savings)
```

### Tip 4: Combine grep + graph
```bash
# Find matching lines
grep -n "function_call" *.py  → Shows line numbers

# Get full dependency context
auzoom_get_dependencies("function_call", depth=2)  → Understand impact
```

### Tip 5: Think discovery first
Most tasks benefit from:
1. Grep to find relevant files (cheap)
2. Skeleton to understand structure (medium cost)
3. Targeted reads to understand details (expensive)

Don't skip step 1 (discovery) and jump to full reads.

---

## When to Use Each Tool

| Tool | When | Why | Cost |
|------|------|-----|------|
| **grep** | Find something across files | Cheap discovery | Low |
| **Skeleton** | Understand file structure | See everything relevant | Medium |
| **Raw read** | Need full implementation | Complete accuracy | Medium-High |
| **Summary** | Need docs + signatures | Documented structure | High |
| **Graph** | Need dependency chains | Only accurate approach | High |

---

## Checklist Before Using AuZoom

```
□ Is this a discovery task? (If yes: use grep first)
□ Is the file <300 tokens? (If yes: use raw read)
□ Do I only need structure? (If yes: use skeleton)
□ Do I need signatures/docs? (If yes: check file size first)
□ Is this a dependency analysis? (If yes: use graph)
□ Am I building on previous context? (If yes: targeted requests)
```

If mostly yes → AuZoom makes sense
If mostly no → Grep or raw read probably better

