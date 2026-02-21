# Global Instructions — Token-Efficient Coding Stack

## Tool Usage Rules (Apply to All Projects)

### Python Files: Always Use AuZoom
- Use `auzoom_read` instead of `Read` for `.py` files
- Start at `level="skeleton"` → escalate to `"summary"` → `"full"` only when editing
- Small files (<300 tokens) are auto-bypassed — no manual intervention needed

### Task Routing: Always Use Orchestrator
- Call `orchestrator_route` before executing any non-trivial task
- Follow the routing recommendation — even 1 tier saves significant cost
- Trivial (0-3): Gemini Flash | Simple (3-5): Haiku | Complex (5-8): Sonnet | Critical (8-10): Opus

### Progressive Disclosure Workflow
```
auzoom_find(pattern)           → locate code (~50 tokens)
auzoom_read(level="skeleton")  → structure (~15 tokens/node)
auzoom_read(level="summary")   → logic (~75 tokens/node)
auzoom_read(level="full")      → edit (~400 tokens/node)
```

### Multi-File Tasks
- Call `auzoom_get_dependencies(node_id, depth=2)` before reading multiple files
- Only read files the graph shows are actually relevant

## General Rules
- Don't create documentation files unless explicitly asked
- Don't add features beyond what's requested
- Prefer editing existing files over creating new ones
