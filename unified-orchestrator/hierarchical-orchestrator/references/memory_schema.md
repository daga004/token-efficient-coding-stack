# Memory Schema Reference

## Directory Structure

```
~/.claude-orchestrator/
├── memory/
│   ├── semantic/           # Extracted facts
│   ├── episodic/           # Specific experiences  
│   ├── procedural/         # How-to knowledge
│   └── model_profiles/     # Learned model affinities
├── evaluations/
│   ├── test_suites/        # Benchmark tests
│   └── results/            # Evaluation results
└── config/
    ├── routing_rules.yaml
    └── checkpoints.yaml
```

## Semantic Memory

### libraries.json
```json
{
  "pandas": {
    "usage_count": 45,
    "common_patterns": ["df.groupby", "df.merge", "pd.read_csv"],
    "preferred_version": "2.0+",
    "last_used": "2025-01-07T10:30:00Z"
  },
  "pytest": {
    "usage_count": 30,
    "common_patterns": ["@pytest.fixture", "parametrize"],
    "preferred_version": "7.0+",
    "last_used": "2025-01-06T15:00:00Z"
  }
}
```

### code_style.json
```json
{
  "python": {
    "indent": "4 spaces",
    "quotes": "double",
    "max_line_length": 100,
    "docstring_style": "google",
    "type_hints": true,
    "formatter": "black"
  },
  "typescript": {
    "indent": "2 spaces",
    "quotes": "single",
    "semicolons": false,
    "formatter": "prettier"
  }
}
```

### preferences.json
```json
{
  "testing_framework": "pytest",
  "async_library": "asyncio",
  "http_client": "httpx",
  "orm": "sqlalchemy",
  "validation": "pydantic",
  "logging": "structlog"
}
```

## Episodic Memory

### Session Log Format (JSONL)

```jsonl
{"id": "exp_001", "timestamp": "2025-01-07T10:30:00Z", "task": "Write async request handler", "model": "qwen3-30b", "complexity": 3, "success": true, "feedback": 0.9, "tokens_in": 850, "tokens_out": 420, "duration_ms": 8500}
{"id": "exp_002", "timestamp": "2025-01-07T10:45:00Z", "task": "Refactor authentication module", "model": "sonnet", "complexity": 6, "success": true, "feedback": 0.85, "tokens_in": 2100, "tokens_out": 1800, "duration_ms": 45000}
```

### Weekly Summary Format

```markdown
# Week 2025-W01 Summary

## Task Distribution
- Total tasks: 142
- Success rate: 89%
- Average complexity: 3.2

## Model Usage
| Model | Tasks | Success Rate | Avg Time |
|-------|-------|--------------|----------|
| qwen3-30b | 65 | 92% | 3.2s |
| haiku | 35 | 88% | 1.8s |
| sonnet | 30 | 95% | 12.5s |
| glm-4.7 | 10 | 90% | 2.1s |
| opus | 2 | 100% | 25.0s |

## Learned Patterns
- Async handlers: qwen3-30b sufficient for complexity < 4
- Refactoring: Always validate with Sonnet
- Database queries: Haiku adequate for simple CRUD

## Cost Analysis
- Total tokens: 1.2M in / 0.8M out
- Estimated cost: $32.50
- vs all-Sonnet baseline: $180.00 (82% savings)
```

## Qdrant Integration

### Collections

```python
collections = {
    "experiences": {
        "vector_size": 384,  # all-MiniLM-L6-v2
        "distance": "Cosine",
        "payload_schema": {
            "task": "text",
            "model": "keyword",
            "success": "bool",
            "feedback": "float",
            "complexity": "integer",
            "timestamp": "datetime"
        }
    },
    "code_patterns": {
        "vector_size": 384,
        "distance": "Cosine",
        "payload_schema": {
            "pattern_type": "keyword",
            "code_snippet": "text",
            "language": "keyword",
            "usage_count": "integer"
        }
    }
}
```

### Retrieval Query

```python
def retrieve_relevant(query: str, limit: int = 5) -> list:
    embedding = encoder.encode(query)
    
    results = client.search(
        collection_name="experiences",
        query_vector=embedding.tolist(),
        limit=limit,
        query_filter={
            "must": [
                {"key": "success", "match": {"value": True}},
                {"key": "feedback", "range": {"gte": 0.7}}
            ]
        }
    )
    
    return [
        {
            "task": r.payload["task"],
            "model": r.payload["model"],
            "similarity": r.score
        }
        for r in results
    ]
```

## Model Profile Schema

```json
{
  "model_id": "qwen3-30b-a3b",
  "last_updated": "2025-01-07T10:30:00Z",
  "task_affinities": {
    "code_generation": {
      "simple_functions": {
        "success_rate": 0.92,
        "avg_time_ms": 3200,
        "sample_size": 45
      },
      "async_patterns": {
        "success_rate": 0.78,
        "avg_time_ms": 8500,
        "sample_size": 23
      }
    }
  },
  "routing_recommendations": {
    "prefer_for": ["simple_functions", "formatting"],
    "avoid_for": ["complex_refactoring"],
    "escalate_when": ["confidence < 0.7", "complexity > 4"]
  }
}
```

## Adaptive Test Generation

### Source: Usage Patterns

```python
def generate_tests_from_usage():
    # Find repeating patterns
    patterns = memory.find_repeating_tasks(
        min_occurrences=3,
        min_success_rate=0.8
    )
    
    tests = []
    for p in patterns:
        tests.append({
            "id": f"learned_{p.hash[:8]}",
            "prompt": generalize_prompt(p.task),
            "expected_patterns": extract_patterns(p.outputs),
            "complexity": p.avg_complexity,
            "source": "usage_learning"
        })
    
    return tests
```

### Test Suite Structure

```yaml
# test_suites/code_generation/learned_suite.yaml
name: learned_code_generation
version: 1.0
generated_from: usage_patterns
generation_date: 2025-01-07

tasks:
  - id: learned_async_001
    prompt: "Write an async function to fetch data with retry"
    expected_patterns: ["async def", "await", "retry"]
    complexity: 3
    source_task_count: 5
    source_success_rate: 0.92
    
  - id: learned_crud_001
    prompt: "Create CRUD endpoints for a resource"
    expected_patterns: ["@router", "async def", "return"]
    complexity: 2
    source_task_count: 8
    source_success_rate: 0.95
```

## Cleanup & Maintenance

### Daily Cleanup
```bash
# Remove sessions older than 30 days
python scripts/cleanup.py --sessions --older-than 30d
```

### Weekly Summarization
```bash
# Summarize past week, archive details
python scripts/summarize_week.py
```

### Monthly Profile Refresh
```bash
# Full re-evaluation of all models
python scripts/full_evaluation.py --all-models
```
