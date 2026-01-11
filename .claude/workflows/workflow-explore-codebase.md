# Exploring Unknown Codebase (Token-Efficient)

## Objective

Understand project structure and key components with minimal token usage.

## When to Use

- New to a codebase
- Need to understand architecture before making changes
- Looking for specific functionality across modules
- Code review or onboarding scenarios

## Workflow Steps

### Step 1: Get Project Overview
```python
auzoom_read(".", level="skeleton")
```
**Cost**: ~500 tokens
**Output**: Directory structure, all modules at a glance

### Step 2: Identify Entry Points
Look for:
- `main.py`, `__init__.py`, `app.py`
- `src/` or `lib/` directories
- Key module names that match your goal

### Step 3: Drill Into Key Modules
```python
# For each important module
auzoom_read("src/main.py", level="skeleton")
```
**Cost**: ~50-100 tokens per file
**Output**: Function/class names, structure

### Step 4: Read Summaries for Context
```python
auzoom_read("src/main.py", level="summary")
```
**Cost**: ~200-400 tokens per file
**Output**: Docstrings, signatures, high-level logic

### Step 5: Explore Dependencies (Optional)
```python
auzoom_get_dependencies(node_id, depth=1)
```
**Cost**: ~100-200 tokens
**Output**: What this module imports/calls

### Step 6: Full Read Only If Needed
```python
# Only for critical implementation details
auzoom_read("src/core.py", level="full")
```
**Cost**: ~2000-4000 tokens per file
**Use**: When you need to understand specific implementation

## Token Budget

| Phase | Traditional | Token-Efficient | Savings |
|-------|-------------|-----------------|---------|
| Overview | 50,000+ tokens | 500 tokens | 99% |
| Key modules (3) | 12,000 tokens | 600 tokens | 95% |
| Summaries (5) | 20,000 tokens | 1,500 tokens | 92% |
| Full reads (2) | 8,000 tokens | 4,000 tokens | 50% |
| **Total** | **90,000 tokens** | **6,600 tokens** | **93%** |

## Expected Savings

**Token Reduction**: 93%
**Time Reduction**: 80% (cache speedup + less reading)
**Cost Reduction**: 93% (proportional to tokens)

## Anti-Patterns to Avoid

❌ Reading all files with Read tool
❌ Starting with full-level reads
❌ Not using skeleton first to orient
❌ Reading implementation before understanding structure

## Success Indicators

✅ Can explain project architecture in 2-3 sentences
✅ Know where to find specific functionality
✅ Identified key modules and their relationships
✅ Used <10% of tokens vs traditional approach
