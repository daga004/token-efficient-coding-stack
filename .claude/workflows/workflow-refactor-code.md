# Refactoring Code (Token & Cost Efficient)

## Objective

Improve code structure, reduce duplication, and enhance maintainability while minimizing token usage and execution cost.

## When to Use

- Code smells detected (long functions, duplication)
- Preparing for feature addition
- Technical debt reduction
- Post-review improvements
- Structural compliance (AuZoom standards)

## Workflow Steps

### Step 1: Assess Scope with Validation
```python
auzoom_validate("src/module.py", scope="file")
# Or for entire project
auzoom_validate(".", scope="project")
```
**Cost**: ~100-500 tokens
**Output**: Specific violations (functions >50 lines, modules >250 lines, etc.)

### Step 2: Understand Current Structure
```python
# Read skeleton to see overall structure
auzoom_read("src/module.py", level="skeleton")

# Read summary for function signatures
auzoom_read("src/module.py", level="summary")
```
**Cost**: ~150-300 tokens
**Goal**: Identify refactoring targets without reading full implementation

### Step 3: Route Refactoring Task
```python
orchestrator_route(
    task="Extract duplicate validation logic into helper function",
    context={
        "files_count": 1,
        "requires_tests": False,
        "code_quality": True
    }
)
```
**Decision**: Most refactorings are complexity 2-5 → Use Haiku or Flash

### Step 4: Read Full Only for Target Areas
```python
# Only read the specific functions/areas being refactored
auzoom_read("src/module.py", level="full", offset=45, limit=30)
```
**Cost**: ~500-1000 tokens (vs 4000+ for full file)
**Strategy**: Targeted reading reduces waste

### Step 5: Execute Refactoring
```python
# Use cheaper model for straightforward refactorings
orchestrator_execute(
    model="haiku",  # or "gemini-flash" for very simple
    prompt="Extract lines 45-75 into separate function..."
)
```
**Cost**: $0.0001-0.002 (vs $0.015+ with Sonnet)

### Step 6: Validate After Changes
```python
auzoom_validate("src/module.py", scope="file")
```
**Cost**: ~50 tokens
**Verification**: Ensures refactoring met structural goals

### Step 7: Check Dependencies (If Public API Changed)
```python
auzoom_get_dependencies(node_id, depth=1)
```
**Cost**: ~100-200 tokens
**Goal**: Identify what might break from signature changes

## Cost Budget

| Refactoring Type | Traditional (Sonnet) | Token-Efficient (Haiku/Flash) | Savings |
|------------------|---------------------|-------------------------------|---------|
| Extract function | $0.015 | $0.001 | 93% |
| Rename variable | $0.010 | $0.0001 | 99% |
| Split large module | $0.030 | $0.005 | 83% |
| DRY improvements | $0.020 | $0.002 | 90% |

## Expected Savings

**Token Reduction**: 80-90% (targeted reading vs full file reads)
**Cost Reduction**: 90-99% (routing to Flash/Haiku)
**Quality**: Same (validation ensures correctness)

## Complexity-Based Routing

### Use Flash (Complexity 0-2) For:
- Rename variables/functions
- Fix formatting/style
- Simple extractions (no logic changes)
- Comment additions

### Use Haiku (Complexity 2-5) For:
- Extract function with parameters
- DRY improvements (removing duplication)
- Split large functions/modules
- Reorganize imports

### Use Sonnet (Complexity 5-7) For:
- Complex algorithmic refactoring
- Major architectural changes
- Refactoring with side effects
- When tests must be updated

## Validation-Driven Refactoring

**Pattern**: Use auzoom_validate to guide refactoring priorities

1. Run `auzoom_validate(".", scope="project")`
2. Get list of violations:
   ```
   - src/auth.py:authenticate() - 87 lines (exceeds 50)
   - src/data/models.py - 342 lines (exceeds 250)
   ```
3. Prioritize by impact
4. Refactor each violation
5. Re-validate to confirm

**Benefit**: Systematic, measurable improvement

## Anti-Patterns to Avoid

❌ Reading entire file when refactoring small section
❌ Using Sonnet/Opus for simple renames/extractions
❌ Refactoring without understanding dependencies
❌ Not validating after changes
❌ Batch refactoring without testing between steps

## Success Indicators

✅ auzoom_validate shows 0 violations (or significant reduction)
✅ Cost was 80-95% less than traditional approach
✅ All dependent code still works
✅ Code is more maintainable
✅ Used targeted reading (not full file reads)

## Example: Extract Helper Function

```python
# 1. Validate to find issue
auzoom_validate("src/auth.py")
# Output: authenticate() - 87 lines (exceeds 50)

# 2. Read skeleton to understand structure
auzoom_read("src/auth.py", level="skeleton")
# See: authenticate(), validate_token(), check_permissions()

# 3. Read summary for signatures
auzoom_read("src/auth.py", level="summary")
# Understand what authenticate() does

# 4. Route refactoring
orchestrator_route("Split authenticate() into smaller functions")
# Returns: haiku, complexity=3.5

# 5. Execute with Haiku
# Use Edit tool to split function

# 6. Re-validate
auzoom_validate("src/auth.py")
# Output: ✅ All checks passed

# Cost: $0.002 vs $0.020 with Sonnet (90% savings)
```
