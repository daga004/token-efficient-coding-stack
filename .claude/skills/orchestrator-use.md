# Orchestrator Usage & Smart Routing

**Loaded on-demand**. Return to main skill: `/skills token-efficient-coding`

---

## Model Selection Strategy

### Complexity Tiers (0-10 scale)

**Tier 0: Gemini Flash** (0-2.5 complexity)
- Cost: $0.01/1M tokens (100x cheaper than Opus!)
- Speed: Very fast
- Use for:
  * Typo fixes, simple refactoring
  * Adding comments or docstrings
  * Formatting changes
  * Simple file operations

**Tier 1: Claude Haiku** (2.5-5.5 complexity)
- Cost: $0.80 in / $4.00 out per 1M
- Speed: Fast
- Use for:
  * Standard bug fixes
  * Feature additions (1-3 files)
  * Unit test writing
  * Code review and suggestions

**Tier 2: Claude Sonnet** (5.5-8.0 complexity)
- Cost: $3.00 in / $15.00 out per 1M
- Speed: Medium
- Use for:
  * Multi-file refactoring
  * API design
  * Complex algorithms
  * Security-sensitive code

**Tier 3: Claude Opus** (8.0-10.0 complexity)
- Cost: $15.00 in / $75.00 out per 1M
- Speed: Medium
- Use for:
  * Architecture decisions
  * Data migrations
  * Critical debugging
  * Performance optimization

---

## Routing Decision Process

### Step 1: Get Recommendation
```python
result = orchestrator_route(
    task="Add user authentication to API endpoint",
    context={
        "files_count": 3,
        "requires_tests": True,
        "external_apis": ["Auth0"],
        "subsystems": ["api", "auth"]
    }
)

# Returns:
# {
#   "model": "haiku",
#   "complexity_score": 5.2,
#   "complexity_factors": {...},
#   "reason": "Task scored 5.2/10. Recommended: Claude 3.5 Haiku",
#   "confidence": 0.85,
#   "estimated_cost": {...}
# }
```

### Step 2: Execute or Use Task Tool
```python
# Option A: Use orchestrator_execute for Gemini models
result = orchestrator_execute(
    model="gemini-flash",
    prompt="Fix typo in README: 'recieve' → 'receive'",
    max_tokens=100
)

# Option B: Use Claude Code's Task tool for Claude models
# For haiku/sonnet/opus: Use Task tool with model parameter
# Task(model="haiku", prompt="...")
```

### Step 3: Validate Output (Optional)
```python
validation = orchestrator_validate(
    task="Add user authentication",
    output="<implementation>"
)

# Returns:
# {
#   "pass": True/False,
#   "issues": ["Issue 1", "Issue 2", ...],  # Max 3
#   "confidence": 0.9,
#   "escalate": False  # True if needs manual review
# }
```

---

## Context Hints for Better Routing

### Provide Rich Context
```python
# Poor (underestimates complexity)
orchestrator_route(task="Add feature")

# Good (accurate routing)
orchestrator_route(
    task="Add OAuth2 authentication flow with refresh tokens",
    context={
        "files_count": 8,           # How many files affected
        "requires_tests": True,      # Tests needed?
        "external_apis": ["OAuth2", "JWT"],  # External dependencies
        "subsystems": ["auth", "api", "database"]  # Multiple subsystems
    }
)
```

### Context Parameters
- **files_count**: 1 file = simple, 5+ files = complex
- **requires_tests**: Tests add +1.5 complexity
- **external_apis**: Each API adds +0.75 complexity
- **subsystems**: Multiple subsystems = complex coordination

---

## Cost Optimization Patterns

### Pattern 1: Progressive Escalation
```python
# Start cheap, escalate if needed
try:
    result = orchestrator_execute(model="gemini-flash", prompt=task)
    if not result["success"]:
        # Escalate to Haiku
        result = orchestrator_execute(model="haiku", prompt=task)
except Exception:
    # Final escalation to Sonnet
    result = orchestrator_execute(model="sonnet", prompt=task)
```

### Pattern 2: Batch Simple Tasks
```python
# Instead of 10 Haiku calls ($0.80 each)
# Use 10 Gemini Flash calls ($0.01 each)
simple_tasks = ["fix typo 1", "fix typo 2", ...]

for task in simple_tasks:
    if orchestrator_route(task)["complexity_score"] < 3:
        orchestrator_execute(model="gemini-flash", prompt=task)
```

### Pattern 3: Validation Checkpoints
```python
# Use Sonnet for validation (input-heavy mode)
# Input: Large task context
# Output: Small validation result
# Cost-effective despite higher rate

validation = orchestrator_validate(
    task="<large task description>",  # Many tokens
    output="<small output>"           # Few tokens
)
# Input-heavy: cheaper than full Opus execution
```

---

## Complexity Scoring Factors

The orchestrator uses 7 weighted factors:

1. **Task Length** (0-3 points)
   - <100 chars: 1 point
   - 100-500 chars: 2 points
   - >500 chars: 3 points

2. **Keywords** (0-2 points)
   - High complexity: "architecture", "refactor", "security"
   - Critical: "migration", "performance", "optimization"

3. **File Count** (0-2 points)
   - 1 file: 0.5 points
   - 2-5 files: 1.5 points
   - 6+ files: 2 points

4. **Tests Required** (0-1.5 points)
   - Tests = +1.5 complexity

5. **External APIs** (0-1.5 points)
   - Each API = +0.75

6. **Subsystems** (0-2 points)
   - 1 subsystem: 0.5
   - 2-3 subsystems: 1.5
   - 4+ subsystems: 2

7. **Task Nature** (inferred from keywords)

**Total**: 0-10 scale, mapped to model tiers

---

## Common Routing Scenarios

### Scenario: Quick Edit
```
Task: "Fix typo in variable name"
Complexity: 1.0
Model: Gemini Flash
Cost: ~$0.00001
```

### Scenario: Feature Addition
```
Task: "Add new API endpoint for user profile"
Files: 3 (route, controller, test)
Tests: Required
Complexity: 4.5
Model: Haiku
Cost: ~$0.002
```

### Scenario: Refactoring
```
Task: "Refactor authentication system to use OAuth2"
Files: 8
External APIs: OAuth2, JWT
Subsystems: auth, api, database
Tests: Required
Complexity: 7.5
Model: Sonnet
Cost: ~$0.015
```

### Scenario: Architecture Design
```
Task: "Design microservices architecture for scaling to 1M users"
Files: N/A (design task)
Complexity: 9.5
Model: Opus
Cost: ~$0.050
```

---

## Validation Strategies

### When to Validate
- After complex implementations (complexity > 6)
- Before deploying to production
- When output quality is critical
- For security-sensitive code

### Validation Methods
```python
# 1. Semantic validation (Sonnet LLM)
orchestrator_validate(task, output)

# 2. Syntax validation (tree-sitter parse)
auzoom_validate(file_path)

# 3. Test execution (pytest)
# Run tests manually

# 4. Combination (strongest validation)
syntax_valid = auzoom_validate(file_path)
semantic_valid = orchestrator_validate(task, output)
tests_pass = run_tests()
```

---

## Cost Tracking

### Monitor Spending
```python
# Track cumulative costs across tasks
total_cost = 0

for task in tasks:
    route = orchestrator_route(task)
    estimated_cost = route["estimated_cost"]

    # Execute
    result = orchestrator_execute(...)

    # Calculate actual cost
    actual_cost = (
        result["tokens"]["input"] / 1_000_000 * cost_per_1m_input +
        result["tokens"]["output"] / 1_000_000 * cost_per_1m_output
    )

    total_cost += actual_cost
```

### Budget Guards
```python
# Set budget limit
MAX_BUDGET = 1.00  # $1.00 limit

if total_cost + estimated_cost > MAX_BUDGET:
    print("Warning: Approaching budget limit")
    # Escalate to cheaper model or skip
```

---

**Remember**: Route intelligently to minimize costs while maintaining quality. Use Gemini Flash aggressively for simple tasks!
