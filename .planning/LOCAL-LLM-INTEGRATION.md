# Local LLM Integration Plan

**Status**: 🔄 IN PLANNING
**Priority**: POST-PHASE-2
**Hardware**: 64GB M4 Mac Mini Pro @ dhiraj@dhirajs-mac-mini
**LMStudio**: Installed and available

## Objective

Integrate local LLMs into the orchestrator for cost-effective task execution with intelligent escalation based on verifiable outcomes.

## User Requirements

1. **Hardware**: 64GB M4 Mac Mini Pro with LMStudio
2. **Known Working Model**: Qwen3 30B3A (reasonable speed)
3. **Escalation Matrix**: Different escalation orders for different task types
4. **Verifiable Outcomes**: Define measurable success criteria for each task
5. **Worker + Checker**: Assign executor and validator, escalate until success or skip decision
6. **Task Attribution**: Track which tasks are needed during development, categorize by type

## Research: Best LLMs for 64GB M4 Mac Mini Pro

### Hardware Constraints
- **RAM**: 64GB unified memory
- **CPU**: M4 (high performance, efficient)
- **Model Size Target**: 30-70B parameters (Q4-Q8 quantization)
- **Speed Requirement**: "Reasonable speed" per user

### Candidate Models (2026 Q1)

#### Tier 0: Ultra-Fast (Local Flash)
- **Qwen2.5 14B** (Q4_K_M: ~8GB VRAM)
  - Speed: Very fast (~100 tokens/s)
  - Use case: Quick edits, simple refactoring, documentation
  - Cost: $0 (local)

- **Llama 3.3 70B** (Q4_K_M: ~40GB VRAM)
  - Speed: Fast on M4 (~40-50 tokens/s)
  - Use case: General coding tasks, moderate complexity
  - Cost: $0 (local)

#### Tier 1: Balanced (Local Haiku)
- **Qwen3 30B3A** (Q6_K: ~24GB VRAM) - **USER VALIDATED**
  - Speed: Reasonable per user
  - Use case: Standard development tasks, testing, analysis
  - Cost: $0 (local)

- **DeepSeek-Coder-V2 33B** (Q5_K_M: ~25GB VRAM)
  - Speed: Good (~30-40 tokens/s)
  - Use case: Code generation, debugging, architecture
  - Cost: $0 (local)

#### Tier 2: High Quality (Local Sonnet)
- **Qwen2.5-Coder 32B** (Q8_0: ~35GB VRAM)
  - Speed: Moderate (~20-30 tokens/s)
  - Use case: Complex algorithms, system design, security
  - Cost: $0 (local)

- **Codestral 22B** (Q8_0: ~24GB VRAM)
  - Speed: Good (~35-45 tokens/s)
  - Use case: Multi-file refactoring, API design
  - Cost: $0 (local)

#### Tier 3: Maximum Quality (Cloud Fallback)
- **Claude Opus 4.5** (API)
  - Speed: Cloud latency
  - Use case: Critical tasks, architecture decisions, complex debugging
  - Cost: $15/$75 per 1M tokens

### Recommended Stack (Initial)
1. **Qwen2.5 14B** - Fast local tier (Tier 0)
2. **Qwen3 30B3A** - User-validated balanced tier (Tier 1)
3. **Qwen2.5-Coder 32B** - High-quality local tier (Tier 2)
4. **Cloud Models** - Fallback for critical tasks (Tier 3+)

## Escalation Matrix Design

### Task Type Categorization

#### Type 1: Quick Edits (0-2 complexity)
- Examples: Typo fixes, simple refactoring, adding comments
- **Escalation Order**: Local-14B → Gemini-Flash → (skip)
- **Checker**: None (self-validating)
- **Max Attempts**: 2

#### Type 2: Standard Development (3-5 complexity)
- Examples: Feature additions, bug fixes, unit tests
- **Escalation Order**: Qwen3-30B → Local-32B → Haiku → (skip)
- **Checker**: Qwen3-30B or Gemini-Flash
- **Max Attempts**: 3

#### Type 3: Complex Architecture (6-8 complexity)
- Examples: System design, multi-file refactoring, API design
- **Escalation Order**: Local-32B → Haiku → Sonnet → (manual review)
- **Checker**: Local-32B or Sonnet
- **Max Attempts**: 3

#### Type 4: Critical Tasks (9-10 complexity)
- Examples: Security fixes, data migrations, performance optimization
- **Escalation Order**: Sonnet → Opus → (manual review)
- **Checker**: Sonnet or Opus
- **Max Attempts**: 2 (high stakes)

### Escalation Rules
1. **Success**: Pass checker validation → Done
2. **Failure**: Retry with same model (max 2 retries)
3. **Persistent Failure**: Escalate to next tier
4. **Max Tier Reached**: Manual review or skip decision
5. **Cost Guard**: Warn before escalating to paid tiers

## Verifiable Outcomes

### Outcome Types

#### 1. Syntax Validation
- **Method**: Parse output with tree-sitter
- **Pass**: No syntax errors
- **Fast**: ~10ms
- **Confidence**: 100%

#### 2. Test Execution
- **Method**: Run test suite
- **Pass**: All tests pass
- **Speed**: Depends on suite
- **Confidence**: 95%

#### 3. Compilation Check
- **Method**: Compile/typecheck output
- **Pass**: No errors
- **Speed**: ~1-5s
- **Confidence**: 90%

#### 4. Semantic Validation
- **Method**: LLM checker (input-heavy)
- **Pass**: Meets requirements (confidence > 0.8)
- **Speed**: ~5-10s
- **Confidence**: 70-85%

#### 5. Performance Benchmark
- **Method**: Run benchmarks
- **Pass**: Meets performance targets
- **Speed**: Depends on benchmark
- **Confidence**: 95%

### Validation Strategy by Task Type
- **Quick Edits**: Syntax only
- **Standard Dev**: Syntax + Tests
- **Complex Architecture**: Syntax + Tests + Semantic
- **Critical Tasks**: All validations + Manual review

## Worker + Checker Assignment

### Assignment Algorithm

```python
def assign_worker_checker(task_type: str, complexity: float):
    \"\"\"Assign worker and checker based on task type and complexity.\"\"\"

    # Get escalation chain for task type
    escalation_chain = ESCALATION_MATRIX[task_type]

    # Start with first tier
    worker = escalation_chain[0]

    # Assign checker (usually same tier or one below)
    if complexity < 5:
        checker = None  # Self-validating for simple tasks
    elif complexity < 8:
        checker = escalation_chain[0]  # Same tier
    else:
        checker = escalation_chain[min(1, len(escalation_chain)-1)]  # Next tier

    return {
        "worker": worker,
        "checker": checker,
        "escalation_chain": escalation_chain,
        "max_attempts": get_max_attempts(complexity)
    }
```

### Execution Flow

```
1. Classify Task → Task Type + Complexity Score
2. Assign Worker + Checker
3. Worker Executes → Output
4. Validate Outcome → Pass/Fail
5. If Fail:
   a. Retry with same worker (max 2 times)
   b. If still fail → Escalate to next tier
   c. Repeat until success or max tier reached
6. If Max Tier Reached:
   a. Manual review flag
   b. Skip decision (user prompt)
```

## Implementation Phases

### Phase 2.5: Local LLM Foundation (NEXT)
**Duration**: ~3 hours
**Status**: Not started

**Tasks**:
1. Set up LMStudio connection from orchestrator
2. Add local model tier (Tier -1) to registry
3. Implement LMStudio client (similar to GeminiClient)
4. Test with Qwen3 30B3A
5. Benchmark speed vs cloud models

**Verification**:
- Can execute prompts on Qwen3 30B3A
- Response time acceptable (< 30s for typical prompts)
- Token counting accurate
- Error handling robust

### Phase 2.6: Escalation Matrix (NEXT)
**Duration**: ~4 hours
**Status**: Not started

**Tasks**:
1. Define task type classifier (keyword-based initially)
2. Create escalation matrix configuration
3. Implement escalation logic in Executor
4. Add cost tracking and guards
5. Test escalation flows

**Verification**:
- Task type classification accurate (>80%)
- Escalation follows defined chains
- Cost guards prevent runaway escalation
- Manual review flags work

### Phase 2.7: Verifiable Outcomes (NEXT)
**Duration**: ~5 hours
**Status**: Not started

**Tasks**:
1. Implement syntax validator (tree-sitter)
2. Implement test runner integration
3. Implement compilation checker
4. Implement semantic validator (LLM-based)
5. Create validation strategy selector
6. Add confidence scoring

**Verification**:
- Each validator works independently
- Validation strategy selector chooses correctly
- Confidence scores correlate with actual success
- Fast validators complete in <1s

### Phase 2.8: Worker + Checker System (NEXT)
**Duration**: ~6 hours
**Status**: Not started

**Tasks**:
1. Implement worker assignment algorithm
2. Implement checker assignment algorithm
3. Add retry logic with backoff
4. Add escalation tracking and logging
5. Create manual review interface
6. Test full execution flow

**Verification**:
- Worker/checker assignments correct
- Retry logic prevents infinite loops
- Escalation stops at max tier
- Manual review prompts work
- Full flow tested end-to-end

## Integration with Existing System

### Registry Updates
```python
class ModelTier(Enum):
    LOCAL_FAST = -2      # Qwen2.5 14B (local)
    LOCAL_BALANCED = -1  # Qwen3 30B3A (local)
    FLASH = 0            # Gemini Flash (cloud, cheap)
    PRO = 0              # Gemini Pro (cloud, cheap)
    HAIKU = 1            # Claude Haiku (cloud)
    SONNET = 2           # Claude Sonnet (cloud)
    OPUS = 3             # Claude Opus (cloud)
```

### Executor Updates
- Add `execute_with_validation_and_escalation()` method
- Track task attribution (store task types encountered)
- Log escalation events for analysis
- Add cost tracking across tiers

### MCP Server Updates
- Add `orchestrator_execute_with_escalation` tool
- Add `orchestrator_classify_task` tool
- Add `orchestrator_validate_outcome` tool
- Update schemas for new tools

## Cost Analysis

### Local vs Cloud Comparison

**Scenario**: 1000 standard development tasks (avg 2000 tokens in, 1000 tokens out)

**Cloud Only** (Current):
- Haiku: $2.40 ($0.80 in + $4.00 out per 1M)
- Sonnet: $9.00 ($3.00 in + $15.00 out per 1M)
- **Total**: $2.40 - $9.00

**With Local LLMs** (Proposed):
- 60% handled by Qwen3 30B3A: $0 (local)
- 30% escalate to Haiku: $0.72
- 10% escalate to Sonnet: $0.90
- **Total**: $1.62

**Savings**: 40-82% cost reduction

### ROI on Hardware
- M4 Mac Mini 64GB: ~$1600 one-time
- Monthly savings: ~$50-200 (depending on usage)
- Break-even: 8-32 months

## Task Attribution & Learning

### Track During Development
```python
task_log = {
    "task_id": "uuid",
    "timestamp": "2026-01-11T10:30:00Z",
    "task_type": "standard_development",
    "description": "Add user authentication",
    "complexity_score": 5.5,
    "worker": "qwen3-30b",
    "checker": "qwen3-30b",
    "outcome": "pass",
    "attempts": 1,
    "escalations": 0,
    "validation_method": "syntax+tests",
    "latency_ms": 8500,
    "tokens_in": 2000,
    "tokens_out": 1200
}
```

### Analytics
- Most common task types
- Success rate by worker
- Average escalations per task type
- Cost per task type
- Optimal worker/checker pairs

### Adaptive Learning
- Adjust escalation matrix based on success rates
- Update complexity scoring weights
- Tune task type classification
- Optimize worker/checker assignments

## Security & Safety

### LMStudio Security
- Local execution (no data leaves machine)
- SSH tunnel for remote access: `ssh -L 1234:localhost:1234 dhiraj@dhirajs-mac-mini`
- No API keys stored for local models

### Escalation Guards
- Confirm before paid tier escalation
- Budget limits per task type
- Manual review for critical tasks
- Audit log for all escalations

## Next Steps

1. ✅ Complete Phase 2 (Orchestrator)
2. ⏳ Research local LLMs (this document)
3. ⏳ Phase 2.5: LMStudio integration
4. ⏳ Phase 2.6: Escalation matrix
5. ⏳ Phase 2.7: Verifiable outcomes
6. ⏳ Phase 2.8: Worker + checker system
7. ⏳ Phase 3: Integration & validation
8. ⏳ Benchmark and optimize

## Open Questions

1. **Model Selection**: Should we support multiple models per tier for A/B testing?
2. **Remote Access**: How to handle SSH connection failures to Mac Mini?
3. **Context Length**: How to handle tasks that exceed model context window?
4. **Model Updates**: How to update local models without downtime?
5. **Parallel Execution**: Should we run multiple local models in parallel?

## References

- LMStudio: https://lmstudio.ai/
- Qwen3 30B3A: (User validated, "works decently well")
- M4 Mac Mini Specs: 64GB unified memory, high-performance architecture
