---
name: hierarchical-orchestrator
description: |
  Cost-optimized multi-model orchestration with self-improving routing for Claude Code. Use when:
  (1) Executing coding tasks that benefit from model hierarchy (Haiku writes, Sonnet validates, Opus directs)
  (2) Optimizing for cost while maintaining quality through validation checkpoints
  (3) Leveraging local LLMs (Qwen3, DeepSeek) alongside API models (Haiku, Sonnet, Cerebras GLM)
  (4) Building agentic workflows with adaptive routing that learns from usage patterns
  (5) Need unified memory across projects for consistent context and preferences
  
  Implements input-heavy validation (larger models read/judge, smaller models write), 
  adaptive routing from usage patterns, and cross-project memory for continuous learning.
---

# Hierarchical Model Orchestrator

## Core Principle: Input-Heavy Validation

**Output tokens cost 5x more than input tokens.** This skill exploits this asymmetry:

- **Writers** (Haiku, Local LLMs, GLM 4.7): Generate code/responses
- **Validators** (Sonnet): Read outputs, emit compact feedback (max 100 tokens)
- **Directors** (Opus): Strategic redirects only (max 50 tokens)

## Task Execution Flow

```
1. RECEIVE → Score complexity (0-10)
2. ROUTE   → Select model based on complexity + past performance
3. GENERATE → Writer model produces output
4. VALIDATE → Sonnet reviews (input-heavy, compact output)
5. ESCALATE → Opus if confidence < 0.7 or major decision needed
6. LOG     → Update memory and model profiles
```

## Model Selection Matrix

| Complexity | Task Type | Model | Reason |
|------------|-----------|-------|--------|
| 0-2 | Any | Local (Qwen3-30B-A3B) | Free, 15-20 t/s |
| 2-4 | Code generation | Cerebras GLM 4.7 | 1000 t/s, 94% accuracy |
| 2-4 | Non-code | Haiku | Cost-effective |
| 4-7 | Complex reasoning | Sonnet | Strong reasoning |
| 7+ | Architecture | Opus | Best judgment |
| Any | Validation checkpoint | Sonnet (input-heavy) | Read much, output little |

## Validation Checkpoint Protocol

Insert checkpoints:
- After each file modification
- Before committing changes  
- At architectural decisions
- When generator confidence < 0.7

Sonnet validation prompt template:
```
<context>{task_and_requirements}</context>
<output_to_validate>{generated_code}</output_to_validate>

Validate. Respond ONLY with JSON (max 100 tokens):
{"pass": bool, "issues": ["max 3 items"], "confidence": 0-1, "escalate": bool}
```

## Complexity Scoring

Run `scripts/score_complexity.py` or apply heuristics:

```python
def score_complexity(task: str, context: dict) -> float:
    score = 0
    score += min(3, len(task.split()) / 50)  # Length factor
    score += 2 if any(w in task.lower() for w in ["refactor", "architect", "migrate"]) else 0
    score += 1.5 if context.get("files", 0) > 1 else 0
    score += 2 if context.get("requires_tests") else 0
    return min(10, score)
```

## Memory Integration

Before starting a task, retrieve relevant context:
```bash
python scripts/retrieve_context.py "task description"
```

After completion, log the outcome:
```bash
python scripts/log_outcome.py --task "..." --model "qwen3-30b" --success true --feedback 0.9
```

## Local Model Setup (64GB Mac M4)

Recommended models via Ollama:
```bash
ollama pull qwen3:30b-a3b      # MoE, only 3B active, fast
ollama pull qwen2.5-coder:32b  # State-of-the-art coding
ollama pull qwen3:14b          # Fast fallback
```

## API Configuration

Set environment variables:
```bash
export ANTHROPIC_API_KEY="..."
export CEREBRAS_API_KEY="..."  # For GLM 4.7 at 1000 t/s
```

## Weekly Maintenance

Run evaluation and profile update:
```bash
python scripts/run_weekly_evaluation.py
```

This will:
1. Benchmark all models on test suite
2. Update routing profiles in `memory/model_profiles/`
3. Generate adaptive tests from usage patterns
4. Produce weekly performance report

## References

- [routing_rules.md](references/routing_rules.md) - Detailed routing logic and override rules
- [model_profiles.md](references/model_profiles.md) - Current model capabilities and benchmarks
- [memory_schema.md](references/memory_schema.md) - Memory structure and Qdrant integration
