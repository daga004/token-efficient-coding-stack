# Code Review / PR Review (Token-Efficient)

## Objective

Review pull requests or code changes thoroughly while minimizing token consumption through strategic reading.

## When to Use

- Pull request review
- Pre-commit code review
- Architecture review
- Security review
- Quality assurance

## Workflow Steps

### Step 1: Get Changed Files List
```bash
# For Git PR/branch
git diff --name-only main...feature-branch

# Or use GitHub CLI
gh pr diff 123 --name-only
```
**Cost**: Negligible
**Output**: List of changed files

### Step 2: Triage Changes by Scope
**Quick scan using skeleton**:
```python
# For each changed file
auzoom_read("src/changed_file.py", level="skeleton")
```
**Cost**: ~50 tokens per file
**Goal**: Understand what changed (new functions, modified functions)

**Categories**:
- Critical (security, auth, payment): Deep review
- Standard (business logic): Normal review
- Minor (style, comments): Quick review

### Step 3: Read Summaries for Context
```python
# For critical and standard files
auzoom_read("src/critical_file.py", level="summary")
```
**Cost**: ~200-400 tokens per file
**Goal**: Understand function purpose and signatures before diving deep

### Step 4: Validate Structure Compliance
```python
# Check if changes meet standards
auzoom_validate("src/new_module.py", scope="file")
```
**Cost**: ~50-100 tokens
**Benefit**: Automatic structural review (functions ≤50 lines, etc.)

### Step 5: Full Read for Critical Sections Only
```python
# Only read full implementation for:
# - Security-sensitive code
# - Complex algorithms
# - Public API changes

auzoom_read("src/auth/new_oauth.py", level="full")
```
**Cost**: ~2000-4000 tokens per file
**Strategy**: Reserve full reads for high-risk changes

### Step 6: Check Dependencies and Impact
```python
# For public API changes
auzoom_get_dependencies(node_id, depth=2)
```
**Cost**: ~200-400 tokens
**Goal**: Identify what might break from this change

### Step 7: Route Review Comments
```python
# For generating review feedback
orchestrator_route(
    task="Review OAuth implementation for security issues",
    context={
        "files_count": 3,
        "security_critical": True,
        "requires_tests": True
    }
)
```
**Decision**: Security reviews use Sonnet/Opus; style reviews use Haiku/Flash

### Step 8: Summarize Findings
**Use cheaper model for summary**:
```python
orchestrator_execute(
    model="haiku",
    prompt="Summarize these review findings: ..."
)
```

## Token Budget

| Review Type | Files | Traditional | Token-Efficient | Savings |
|-------------|-------|-------------|-----------------|---------|
| Minor PR (1-2 files) | 2 | 8,000 | 800 | 90% |
| Standard PR (5-8 files) | 7 | 28,000 | 3,500 | 87% |
| Major PR (15+ files) | 20 | 80,000 | 8,000 | 90% |

## Expected Savings

**Token Reduction**: 87-90%
**Cost Reduction**: 85-95% (routing + token savings)
**Review Quality**: Same or better (structured approach)
**Review Time**: Similar (focused reading saves time)

## Review Checklist by Change Type

### New Feature (5-10 files changed)
1. ✅ Skeleton all files (~500 tokens)
2. ✅ Summary for main files (~1000 tokens)
3. ✅ Validate structure (~200 tokens)
4. ✅ Full read critical logic (~4000 tokens)
5. ✅ Check dependencies (~300 tokens)
**Total**: ~6000 tokens vs 50,000+ traditional (88% savings)

### Bug Fix (1-3 files changed)
1. ✅ Skeleton affected files (~150 tokens)
2. ✅ Summary to understand context (~400 tokens)
3. ✅ Full read of fix (~1500 tokens)
4. ✅ Check test coverage (~500 tokens)
**Total**: ~2550 tokens vs 12,000+ traditional (79% savings)

### Refactoring (3-8 files changed)
1. ✅ Skeleton before/after structure (~400 tokens)
2. ✅ Validate compliance (~300 tokens)
3. ✅ Summary for key changes (~1000 tokens)
4. ✅ Verify dependencies unchanged (~400 tokens)
**Total**: ~2100 tokens vs 32,000+ traditional (93% savings)

### Documentation Only (README, docs/)
1. ✅ Quick read (~500 tokens)
2. ✅ Use Flash for spell/grammar check ($0.0001)
**Total**: ~500 tokens, $0.0001 (99% cost savings vs Sonnet)

## Priority-Based Reading Strategy

**High Priority (Full Read)**:
- Security-critical code (auth, crypto, permissions)
- Payment/financial logic
- Data validation/sanitization
- Public API changes
- Complex algorithms

**Medium Priority (Summary Read)**:
- Business logic
- Database queries
- Integration code
- State management

**Low Priority (Skeleton Read)**:
- Utilities
- Helpers
- Configuration
- Tests (verify existence, don't deep review)

## Cost Optimization by Review Type

| Review Focus | Recommended Model | Complexity | Example Cost |
|--------------|------------------|------------|--------------|
| Security | Sonnet/Opus | 8-10 | $0.024-0.080 |
| Architecture | Sonnet | 6-8 | $0.018-0.045 |
| Logic correctness | Haiku/Sonnet | 4-7 | $0.004-0.018 |
| Style/formatting | Haiku/Flash | 1-3 | $0.0001-0.002 |
| Documentation | Flash | 0-2 | $0.0001 |

## Automated Checks Before Manual Review

**Use auzoom_validate to catch structural issues automatically**:
```python
auzoom_validate(".", scope="project")
```

**Common catches**:
- Functions >50 lines
- Modules >250 lines
- Directories >7 files
- Malformed structure

**Benefit**: Reviewer focuses on logic/security, not structure

## Anti-Patterns to Avoid

❌ Reading all changed files at full level
❌ Using Opus for style-only reviews
❌ Not checking dependencies for API changes
❌ Reviewing without understanding context (skip skeleton/summary)
❌ Deep diving into minor changes (style, comments)

## Success Indicators

✅ Identified critical issues (security, logic errors)
✅ Used <15% tokens vs reading everything
✅ Routed review work to appropriate model tiers
✅ Review completed in reasonable time
✅ Cost was 85-95% less than baseline approach

## Example: Review 8-File Feature PR

```python
# PR: "Add user profile API with avatar upload"
# Files changed: 8 (3 new, 5 modified)

# Step 1: Get file list
git diff --name-only main...feature/user-profiles
# Output: src/api/profiles.py, src/models/user.py, src/storage/s3.py, ...

# Step 2: Skeleton all files
for file in changed_files:
    auzoom_read(file, level="skeleton")
# Cost: 8 × 50 = 400 tokens
# Understand: New API endpoint, new model fields, S3 integration

# Step 3: Triage by priority
# High: src/api/profiles.py (new public API)
# High: src/storage/s3.py (security: file uploads)
# Medium: src/models/user.py (data model changes)
# Low: tests/, docs/ (existence check)

# Step 4: Validate structure
auzoom_validate("src/api/profiles.py")
auzoom_validate("src/storage/s3.py")
# Cost: 2 × 50 = 100 tokens
# Result: ✅ All passed

# Step 5: Summary for medium priority
auzoom_read("src/models/user.py", level="summary")
# Cost: 300 tokens
# Check: Field types, migrations, validation

# Step 6: Full read for high priority
auzoom_read("src/api/profiles.py", level="full")
auzoom_read("src/storage/s3.py", level="full")
# Cost: 2 × 2000 = 4000 tokens
# Review: Security (file validation, auth), error handling

# Step 7: Check dependencies
auzoom_get_dependencies("src/api/profiles.py", depth=1)
# Cost: 200 tokens
# Verify: Properly integrates with auth, storage

# Step 8: Route review summary
orchestrator_route("Generate security review summary for file upload feature")
# Returns: sonnet (security-critical)

# Total Costs:
# - Tokens: 5000 vs 32,000 traditional (84% savings)
# - Model: Sonnet for review ($0.015)
# - Total: $0.018 vs $0.096 (81% savings)
```

## Integration with GitHub

**Efficient PR review with gh CLI**:
```bash
# Get PR details
gh pr view 123

# Get diff file list
gh pr diff 123 --name-only

# For each file, use auzoom_read progressively
# Then post review:
gh pr review 123 --comment -b "Review findings..."
```

**Token savings**: 90% vs fetching full PR content via API
