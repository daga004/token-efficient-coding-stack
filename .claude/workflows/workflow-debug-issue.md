# Debugging Issues (Token-Efficient)

## Objective

Diagnose and fix bugs using minimal token consumption through progressive investigation.

## When to Use

- Test failures
- Runtime errors
- Unexpected behavior
- Performance issues
- Integration problems

## Workflow Steps

### Step 1: Locate Error Source
```python
# Option A: Known file, find specific code
auzoom_find("failing_function_name")

# Option B: Error message mentions module
auzoom_read("src/problematic_module.py", level="skeleton")
```
**Cost**: ~50-200 tokens
**Goal**: Narrow down to specific file/function

### Step 2: Read Context (Skeleton + Summary)
```python
# See function structure
auzoom_read("src/module.py", level="skeleton")

# Read docstrings and signatures
auzoom_read("src/module.py", level="summary")
```
**Cost**: ~200-400 tokens
**Strategy**: Understand without reading full implementation yet

### Step 3: Check Dependencies
```python
auzoom_get_dependencies(node_id, depth=1)
```
**Cost**: ~100-200 tokens
**Goal**: Identify what this code calls/imports (potential failure points)

### Step 4: Targeted Full Read
```python
# Only read the problematic function and immediate context
auzoom_read("src/module.py", level="full", offset=50, limit=40)
```
**Cost**: ~800-1500 tokens (vs 4000+ for full file)
**Strategy**: Read only relevant section

### Step 5: Route Diagnosis Task
```python
orchestrator_route(
    task="Diagnose why test_authentication fails with NoneType error",
    context={
        "files_count": 2,
        "requires_tests": True,
        "debugging": True
    }
)
```
**Decision**: Most debugging is complexity 4-6 → Use Haiku or Sonnet

### Step 6: Formulate Fix
```python
# Simple fixes: Use Haiku or Flash
orchestrator_execute(
    model="haiku",
    prompt="Fix NoneType error in authenticate() at line 67..."
)

# Complex fixes: Use Sonnet
# (architectural issues, race conditions, etc.)
```

### Step 7: Validate Fix
```python
# Run tests
# If structural issue was involved:
auzoom_validate("src/module.py")
```

## Token Budget

| Debugging Scenario | Traditional | Token-Efficient | Savings |
|-------------------|-------------|-----------------|---------|
| Simple null check | 4,000 tokens | 500 tokens | 87% |
| Logic error | 8,000 tokens | 1,200 tokens | 85% |
| Integration issue | 20,000 tokens | 3,000 tokens | 85% |
| Test failure | 6,000 tokens | 800 tokens | 87% |

## Expected Savings

**Token Reduction**: 85-90%
**Cost Reduction**: 80-90% (routing + token savings)
**Time to Fix**: Often faster (focused investigation)

## Debugging Patterns by Issue Type

### NullPointer / AttributeError
1. `auzoom_find("problematic_function")`
2. Read summary to see parameters
3. Check dependencies for what returns None
4. Targeted full read of specific lines
**Model**: Haiku (complexity 2-4)

### Test Failure
1. Read test file (skeleton → summary)
2. Read implementation being tested (summary)
3. Compare expected vs actual behavior
4. Identify mismatch
**Model**: Haiku (complexity 3-5)

### Import / Circular Dependency
1. `auzoom_get_dependencies` on both modules
2. Visualize dependency graph
3. Identify cycle
4. Refactor to break cycle
**Model**: Sonnet (complexity 5-7, needs architectural thinking)

### Performance Issue
1. Profile to identify bottleneck
2. `auzoom_read` of slow function (full)
3. Look for N+1 queries, inefficient algorithms
4. Optimize specific section
**Model**: Sonnet (complexity 6-8, optimization needs careful thought)

### Integration Error (External API)
1. Read API client code (skeleton → summary)
2. Check error handling logic
3. Verify request/response format
4. Fix integration mismatch
**Model**: Haiku/Sonnet (complexity 4-6)

## Cost Comparison

| Issue Type | Traditional (Sonnet, full reads) | Token-Efficient (Routed, progressive) | Savings |
|------------|----------------------------------|--------------------------------------|---------|
| Null check | $0.020 | $0.002 | 90% |
| Logic bug | $0.030 | $0.005 | 83% |
| Test fix | $0.025 | $0.003 | 88% |
| Circular import | $0.040 | $0.008 | 80% |
| Performance | $0.050 | $0.015 | 70% |

## Progressive Investigation Strategy

**Key Principle**: Start broad, zoom in progressively

```
1. Skeleton (50 tokens) → "Where is the problem?"
2. Summary (200 tokens) → "What does this code do?"
3. Dependencies (150 tokens) → "What does it interact with?"
4. Full (targeted, 800 tokens) → "What's the exact bug?"
```

**Total**: ~1200 tokens vs 10,000+ reading everything

## Anti-Patterns to Avoid

❌ Reading entire codebase to find error
❌ Starting with full-level reads
❌ Using Opus for simple null checks
❌ Not checking dependencies (missing context)
❌ Reading tests and implementation simultaneously (read test first)

## Success Indicators

✅ Bug identified with <20% token usage vs traditional
✅ Fix implemented with appropriate model tier
✅ Tests passing after fix
✅ Used progressive disclosure (didn't read everything)
✅ Cost 80-90% lower than baseline

## Example: Debug Test Failure

```python
# Error: "test_user_login failed: AssertionError expected True, got False"

# Step 1: Find test
auzoom_find("test_user_login")
# Returns: tests/test_auth.py:45

# Step 2: Read test (summary level)
auzoom_read("tests/test_auth.py", level="summary")
# Understand: Tests that login() returns True for valid credentials

# Step 3: Read implementation (skeleton first)
auzoom_read("src/auth.py", level="skeleton")
# See: login(), validate_credentials(), check_session()

# Step 4: Read implementation (summary)
auzoom_read("src/auth.py", level="summary")
# Understand flow: login() calls validate_credentials()

# Step 5: Check dependencies
auzoom_get_dependencies(node_id="src/auth.py:login", depth=1)
# See: calls database.query(), session.create()

# Step 6: Hypothesis formed, read full implementation
auzoom_read("src/auth.py", level="full", offset=20, limit=30)
# Find bug: login() doesn't return True, returns None

# Step 7: Route fix
orchestrator_route("Add return True to login() function")
# Returns: gemini-flash, complexity=1.5

# Step 8: Fix with Flash
# Edit: Add "return True" at end of login()

# Cost Analysis:
# - Tokens: 600 (vs 8,000 reading everything)
# - Cost: $0.0001 (Flash) vs $0.024 (Sonnet)
# - Savings: 92% tokens, 99.6% cost
```
