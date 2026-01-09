# Model Profiles Reference

## Local Models (64GB Mac M4 Mini Pro)

### Qwen3-30B-A3B (Recommended Primary)

```yaml
model_id: qwen3-30b-a3b
type: MoE (Mixture of Experts)
total_params: 30B
active_params: 3B  # Only subset activated per token
memory_usage: ~17GB (Q4)
speed: 15-20 tokens/sec
context: 128K tokens

strengths:
  - Zero marginal cost
  - Fast due to MoE efficiency
  - Thinking mode for complex reasoning
  - Good multilingual support

weaknesses:
  - Not as strong as dense 32B for complex code
  - Requires thinking mode for best results on hard tasks

best_for:
  - Simple to medium code generation
  - Quick iterations
  - Translation/formatting tasks
  - Initial drafts before validation

setup:
  command: "ollama pull qwen3:30b-a3b"
  memory: ~20GB with overhead
```

### Qwen2.5-Coder-32B (Best for Code)

```yaml
model_id: qwen2.5-coder-32b
type: Dense
params: 32B
memory_usage: ~18GB (Q4)
speed: 11-12 tokens/sec
context: 128K tokens

strengths:
  - State-of-the-art open-source coding
  - Matches GPT-4o on Aider benchmarks
  - Strong code reasoning and repair
  - 40+ programming languages

weaknesses:
  - Slower than MoE models
  - Higher memory usage

best_for:
  - Complex code generation
  - Code repair and debugging
  - Multi-language projects

benchmarks:
  humaneval: 92.5%
  aider_whole: 74%
  mbpp: 90.2%
```

### Qwen3-14B (Fast Fallback)

```yaml
model_id: qwen3-14b
type: Dense
params: 14B
memory_usage: ~8GB (Q4)
speed: 20-25 tokens/sec

best_for:
  - Very simple tasks
  - When speed > quality
  - Parallel task execution
```

## API Models

### Haiku (Claude)

```yaml
model_id: claude-3-haiku
provider: Anthropic
cost:
  input: $0.25/1M tokens
  output: $1.25/1M tokens
speed: 50-100 tokens/sec

strengths:
  - Very cost-effective
  - Good for simple to medium tasks
  - Fast response times

best_for:
  - Simple code generation
  - Documentation
  - Formatting tasks
  - High-volume low-complexity work

routing_threshold: complexity <= 4
```

### Sonnet (Claude)

```yaml
model_id: claude-3.5-sonnet
provider: Anthropic
cost:
  input: $3.00/1M tokens
  output: $15.00/1M tokens
speed: 30-50 tokens/sec

strengths:
  - Strong reasoning
  - Excellent code understanding
  - Reliable validation

best_for:
  - Complex code generation
  - Code review and validation
  - Debugging
  - Architecture decisions

primary_use: VALIDATION (input-heavy)
  - Read generated code (input tokens - cheap)
  - Output compact feedback (output tokens - expensive)
  - Target: max 100 tokens output per validation
```

### Opus (Claude)

```yaml
model_id: claude-3-opus
provider: Anthropic
cost:
  input: $15.00/1M tokens
  output: $75.00/1M tokens

strengths:
  - Best reasoning capability
  - Strongest judgment
  - Handles highest complexity

best_for:
  - Strategic redirects
  - Architecture decisions
  - When other models fail

primary_use: DIRECTOR (minimal output)
  - Major checkpoint reviews
  - Strategic guidance only
  - Target: max 50 tokens output
```

### GLM 4.7 (Cerebras)

```yaml
model_id: glm-4.7
provider: Cerebras
cost:
  input: $0.60/1M tokens
  output: $0.60/1M tokens
speed: 1000+ tokens/sec  # Key differentiator

strengths:
  - Fastest inference available
  - 94.5% code-edit accuracy
  - Strong tool use
  - Preserved thinking across turns

best_for:
  - Agentic coding workflows
  - High-iteration tasks
  - When speed > cost savings

benchmarks:
  swe_bench: 73.8%
  terminal_bench: 41%
  
special_features:
  - Interleaved Thinking: Thinks before every action
  - Preserved Thinking: Retains reasoning across turns
  - Turn-level Thinking: Enable/disable per request
```

## Model Selection Algorithm

```python
def select_model(task, context):
    complexity = score_complexity(task, context)
    
    # Check past performance for similar tasks
    similar = memory.retrieve_similar(task)
    if similar and similar.best_model_confidence > 0.8:
        return similar.best_model
    
    # Apply routing rules
    if context.get('checkpoint') == 'validation':
        return 'sonnet'  # Input-heavy validation
    
    if complexity <= 2:
        return 'local/qwen3-30b-a3b'
    elif complexity <= 4:
        if context.get('task_type') == 'code_generation':
            return 'cerebras/glm-4.7'
        return 'haiku'
    elif complexity <= 7:
        return 'sonnet'
    else:
        return 'opus'
```

## Updating Profiles

Profiles are updated based on:

1. **Weekly test suite evaluation**
2. **Continuous usage feedback**
3. **New model releases**

Update command:
```bash
python scripts/update_model_profiles.py --from-evaluation
```
