# Python Coding Principles

Structural discipline that makes ANY reading approach efficient — with or without specialized tooling.

## Why This Matters

Following these principles gives you ~60-70% of AuZoom's token savings for free.
Well-structured code is readable by standard Glob/Grep/Read without special tools.

---

## Module Size Limits (Hard Constraints)

| Unit | Limit | Action if Exceeded |
|------|-------|--------------------|
| Module (.py file) | ≤250 lines | Split into submodules with `__init__.py` re-exports |
| Function/method | ≤50 lines | Extract helper functions |
| Class | ≤5 public methods | Split by responsibility |
| Directory | ≤7 .py files | Create subdirectory/subpackage |

**Rationale**: At ≤250 lines, a full Read costs ~2,000 tokens. At 1,000 lines, it costs ~8,000 tokens — 4x more, with most tokens irrelevant to your task.

---

## Project State File (Required)

Every repo should have a `DESIGN.md` (or `ARCHITECTURE.md`) at the root:

```markdown
# Project Architecture

## Module Map
- `src/core/` — business logic (models, services, validators)
- `src/api/` — HTTP layer (routes, serializers, middleware)
- `src/utils/` — shared utilities (logging, config, helpers)

## Key Abstractions
- `UserService`: handles all user operations (src/core/services.py)
- `APIRouter`: entry point for all HTTP requests (src/api/router.py)

## Data Flow
Request → APIRouter → Service → Repository → Database

## Design Decisions
- Use dataclasses over dicts for all internal data structures
- All validation happens in the Service layer, never in routes
```

This costs one Read (~200 tokens) and gives the orientation that normally requires reading 10+ files.

---

## Hierarchical Project Structure

```
repo/
├── DESIGN.md              ← Architecture overview (READ THIS FIRST)
├── src/
│   ├── __init__.py        ← Package docstring = module-level summary
│   ├── core/
│   │   ├── __init__.py    ← Exports key abstractions, lists submodule purposes
│   │   ├── models.py      ← ≤250 lines: data structures only
│   │   ├── services.py    ← ≤250 lines: business logic only
│   │   └── validators.py  ← ≤250 lines: validation only
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py      ← ≤250 lines
│   │   └── serializers.py ← ≤250 lines
│   └── utils/
│       ├── __init__.py
│       ├── logging.py     ← ≤250 lines
│       └── config.py      ← ≤250 lines
└── tests/
    └── ... (mirrors src/ structure)
```

**Key convention**: Each `__init__.py` should have a module docstring listing what's inside and re-exporting public APIs. This acts as a free "skeleton" readable with one small Read call.

---

## Hierarchical Reading Pattern (The Baseline)

For any task, read in this order — stop as soon as you have enough context:

```
Step 1: Read DESIGN.md (or ARCHITECTURE.md)        ~200 tokens
  → "Which module owns this feature?"

Step 2: Glob("src/*/__init__.py") + Read each      ~50 tokens each
  → "Which submodule has what I need?"

Step 3: Grep("function_name", path="src/target/")  ~30 tokens
  → "Which file and line?"

Step 4: Read(file, offset=N, limit=60)             ~500 tokens
  → "What does this function actually do?"
```

**Total for typical task**: ~800-1,000 tokens (vs naive Read-all: 15,000-80,000 tokens)

---

## AuZoom Incremental Value

If AuZoom is available, it adds value ON TOP of this baseline:

```
Replace Step 4 with progressive disclosure:

4a. auzoom_read(file, level="skeleton")  → ~180 tokens (signatures only)
    "Do I even need the full function, or just the interface?"

4b. auzoom_read(file, level="summary")  → ~900 tokens (only if needed)
    "What does the logic do, roughly?"

4c. auzoom_read(file, level="full")     → ~4,800 tokens (only when editing)
    "Show me the complete source to make changes"
```

**When AuZoom adds significant value**:
- Exploring unfamiliar modules across 50+ files
- Tracing dependencies without reading every file
- Large files (>250 lines) where only one function is relevant

**When plain Glob/Grep/Read is sufficient**:
- Well-structured codebases with ≤250-line modules
- Tasks touching ≤5 files
- Codebases with <50 Python files

---

## __init__.py Convention

Each package's `__init__.py` should be a navigation guide:

```python
"""
core/ — Business logic layer

Submodules:
    models.py       → Dataclasses: User, Session, Permission
    services.py     → UserService, SessionService (main entry points)
    validators.py   → Input validation for all operations

Public API (re-exported here):
    from core import UserService, User, validate_user_input
"""

from .models import User, Session, Permission
from .services import UserService, SessionService
from .validators import validate_user_input

__all__ = ["User", "Session", "Permission", "UserService", "SessionService", "validate_user_input"]
```

Reading this `__init__.py` (~30 tokens) tells you everything in the package without reading the submodules.

---

## Validation

Check your codebase against these standards:

```bash
# Count files per directory (flag any with >7)
find src/ -name "*.py" | sed 's|/[^/]*$||' | sort | uniq -c | sort -rn

# Find modules exceeding 250 lines
find src/ -name "*.py" -exec wc -l {} + | awk '$1 > 250' | sort -rn

# Find functions exceeding 50 lines (rough heuristic)
grep -n "^    def \|^def " src/**/*.py | head -50
```

If using AuZoom:
```python
auzoom_validate(path="src/", scope="project")
```
