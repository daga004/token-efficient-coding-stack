# Routing Rules Reference

## Rule Priority Order

Rules are evaluated in order; first match wins.

## Base Rules

### 1. Validation Checkpoints (Highest Priority)

```yaml
- condition: "checkpoint == 'validation'"
  model: sonnet
  output_limit: 100
  prompt_template: "validation_compact"
  reason: "Input-heavy validation - Sonnet reads output, emits minimal feedback"
```

### 2. Strategic Redirects

```yaml
- condition: "checkpoint == 'major' AND needs_redirect"
  model: opus
  output_limit: 50
  reason: "Opus for architectural decisions only"
```

### 3. Complexity-Based Routing

```yaml
# Simple tasks → Local models (free)
- condition: "complexity <= 2"
  model: local/qwen3-30b-a3b
  reason: "MoE model, only 3B active params, zero cost"

# Medium code tasks → Fast API
- condition: "complexity <= 4 AND task_type == 'code_generation'"
  model: cerebras/glm-4.7
  reason: "1000 t/s, 94.5% code-edit accuracy"

# Medium non-code → Haiku
- condition: "complexity <= 4 AND task_type != 'code_generation'"
  model: haiku
  reason: "$0.25/$1.25 per 1M tokens"

# Complex tasks → Sonnet
- condition: "complexity <= 7"
  model: sonnet
  reason: "Strong reasoning for complex tasks"

# Highly complex → Opus
- condition: "complexity > 7"
  model: opus
  reason: "Best judgment for architecture"
```

## Escalation Triggers

```yaml
escalation_rules:
  - trigger: "validation_confidence < 0.7"
    action: escalate_to_opus
    
  - trigger: "consecutive_failures >= 2"
    action: escalate_to_next_tier
    
  - trigger: "task_type == 'security_critical'"
    action: force_sonnet_validation
    
  - trigger: "output_tokens > 2000"
    action: split_and_validate
```

## Override Rules

```yaml
overrides:
  # User preference overrides
  - condition: "user_preference == 'always_validate'"
    action: force_validation_checkpoint
    
  # Cost-saving mode
  - condition: "budget_mode == 'aggressive'"
    model_preference: [local, haiku, sonnet]
    avoid: [opus]
    
  # Quality mode
  - condition: "quality_mode == 'maximum'"
    model_preference: [sonnet, opus]
    always_validate: true
```

## Task Type Classification

```yaml
task_types:
  code_generation:
    patterns: ["write", "create", "implement", "build", "generate code"]
    default_model: cerebras/glm-4.7
    
  code_review:
    patterns: ["review", "check", "validate", "analyze code"]
    default_model: sonnet
    
  refactoring:
    patterns: ["refactor", "restructure", "clean up", "improve"]
    complexity_boost: +2
    
  debugging:
    patterns: ["fix", "debug", "error", "bug", "issue"]
    default_model: sonnet
    
  documentation:
    patterns: ["document", "explain", "describe", "readme"]
    default_model: haiku
    
  architecture:
    patterns: ["architect", "design", "plan", "structure"]
    complexity_boost: +3
    default_model: opus
```

## Adaptive Updates

Routing rules are updated based on:

1. **Weekly evaluation results** - Model performance on test suite
2. **Usage feedback** - Success/failure signals from actual usage
3. **Cost tracking** - Adjust thresholds if budget exceeded
4. **New model availability** - Re-evaluate when new models released

Update trigger:
```bash
python scripts/update_routing_rules.py --from-evaluation
```
