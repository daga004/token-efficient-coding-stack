# Implementing New Feature (Cost-Efficient)

## Objective

Add new functionality using the most appropriate model tier to minimize cost while maintaining quality.

## When to Use

- Adding new API endpoints
- Creating new UI components
- Implementing business logic
- Extending existing functionality

## Workflow Steps

### Step 1: Route the Task
```python
orchestrator_route(
    task="Add user profile API with CRUD operations",
    context={
        "files_count": 4,
        "requires_tests": True,
        "external_apis": ["database"],
        "subsystems": ["api", "auth"]
    }
)
```
**Returns**: Model recommendation + complexity score
**Decision Point**: Use recommended model or escalate if uncertain

### Step 2: Understand Existing Patterns
```python
# Find similar existing features
auzoom_find("*API*")  # or relevant pattern

# Read skeleton to see structure
auzoom_read("src/api/users.py", level="skeleton")

# Read summary to understand patterns
auzoom_read("src/api/users.py", level="summary")
```
**Cost**: ~300-500 tokens
**Goal**: Match existing code style and patterns

### Step 3: Implement Using Recommended Model
```python
# If complexity_score < 4: Use Haiku or Flash
# If complexity_score 4-7: Use Haiku or Sonnet
# If complexity_score > 7: Use Sonnet or Opus

# Implementation happens here via Task tool or direct execution
```

### Step 4: Validate Structure (Optional)
```python
auzoom_validate("src/api/profiles.py", scope="file")
```
**Cost**: ~50 tokens
**Check**: Ensures code meets structural standards (≤50 lines/function)

### Step 5: Validate Output Quality
```python
orchestrator_validate(
    task="Add user profile API with CRUD operations",
    output="<implementation_code>"
)
```
**Returns**: Pass/fail + confidence + issues
**Decision Point**: If validation fails, escalate to next model tier

### Step 6: Escalate If Needed
```python
# If Haiku output failed validation
orchestrator_execute(
    model="sonnet",
    prompt="<original_task>"
)
```
**Cost**: Higher tier, but ensures quality
**Trade-off**: 3-10x more expensive, but correct

## Cost Budget

| Task Complexity | Model | Estimated Cost | Traditional (Opus) | Savings |
|----------------|-------|----------------|-------------------|---------|
| Simple CRUD | Haiku | $0.002 | $0.015 | 87% |
| Standard API | Haiku/Sonnet | $0.005-0.015 | $0.050 | 70-90% |
| Complex feature | Sonnet | $0.015-0.030 | $0.080 | 63-81% |
| Critical/novel | Opus | $0.050 | $0.050 | 0% |

## Expected Savings

**Cost Reduction**: 40-87% (depending on complexity)
**Quality**: Same or better (validation catches issues)
**Development Time**: Similar (routing adds <5 seconds)

## Routing Guidelines

### Use Flash/Haiku (0-4) For:
- Simple CRUD operations
- Straightforward data transformations
- Basic validation logic
- Standard patterns with examples

### Use Haiku/Sonnet (4-7) For:
- Multi-file features
- Integration with external APIs
- Features requiring tests
- Moderate business logic

### Use Sonnet/Opus (7-10) For:
- Complex algorithms
- Security-critical features
- Novel architecture decisions
- High-stakes production code

## Anti-Patterns to Avoid

❌ Always using Opus/Sonnet for everything
❌ Skipping orchestrator_route (missing cost optimization)
❌ Not validating cheaper model outputs
❌ Reading full files when summary sufficient
❌ Implementing without understanding existing patterns

## Success Indicators

✅ Used appropriate model tier for task complexity
✅ Validation passed on first or second attempt
✅ Code matches existing project patterns
✅ Cost was 40-80% less than default approach
✅ Implementation quality meets standards
