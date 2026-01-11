# Token-Efficient Coding with AuZoom & Orchestrator

**Purpose**: Reduce token usage by 50-70% through progressive file reading and intelligent model routing.

**When to invoke**: This skill is automatically available. Sub-skills provide detailed guidance on specific tools.

---

## Core Principles

### 1. Progressive Disclosure (AuZoom)
**ALWAYS use `auzoom_read` instead of `Read` for code files.**

- **Skeleton first** (~15 tokens/node): See structure, choose what to explore
- **Summary next** (~75 tokens/node): Add docstrings and signatures
- **Full last** (~400 tokens/node): Only when you need implementation details

**Workflow**:
```
skeleton → identify relevant functions → summary for those → full only if needed
```

**Token savings**: 4-27x reduction vs reading full file immediately.

### 2. Smart Model Routing (Orchestrator)
**Use `orchestrator_route` to choose the right model for each task.**

- Simple edits (0-3 complexity) → Gemini Flash ($0.01/1M)
- Standard tasks (4-6 complexity) → Haiku ($0.80/1M)
- Complex work (7-8 complexity) → Sonnet ($3/1M)
- Critical tasks (9-10 complexity) → Opus ($15/1M)

**Cost savings**: Route simple tasks to cheap models, reserve expensive models for hard problems.

### 3. Avoid Unnecessary Documentation
**CRITICAL: Do NOT create markdown files unless explicitly requested.**

- No README files unless user asks
- No ARCHITECTURE.md, CONTRIBUTING.md, etc. unless requested
- No summary documents after completing tasks
- Focus on **working code**, not documentation

**Exception**: User explicitly says "create a README" or "document this"

---

## Available Tools

### AuZoom Tools (Code Navigation)
- `auzoom_read(path, level)` - Read files progressively
- `auzoom_find(pattern)` - Search by name pattern
- `auzoom_get_dependencies(node_id, depth)` - Explore dependencies
- `auzoom_stats()` - Check cache performance
- `auzoom_validate(path, scope)` - Validate code structure

**See**: `/skills auzoom-use` for detailed usage patterns

### Orchestrator Tools (Smart Routing)
- `orchestrator_route(task, context)` - Get model recommendation
- `orchestrator_execute(model, prompt, max_tokens)` - Execute on specific model
- `orchestrator_validate(task, output)` - Quality checkpoint

**See**: `/skills orchestrator-use` for routing strategies

---

## Quick Start Patterns

### Pattern 1: Explore Unknown Codebase
```
1. auzoom_read("src/", level="skeleton") → See all modules
2. auzoom_read("src/main.py", level="skeleton") → See structure
3. auzoom_read("src/main.py", level="summary") → Read key functions
4. auzoom_read("src/main.py", level="full") → Only if implementation needed
```

**Why**: Start broad, narrow down progressively. Save 10-20x tokens vs reading everything.

### Pattern 2: Make Changes
```
1. auzoom_read(target_file, level="skeleton") → Locate function
2. auzoom_read(target_file, level="summary") → Understand function
3. Make changes with Edit tool
4. auzoom_validate(target_file) → Check structure compliance
```

**Why**: Only read what you need to change. AuZoom validates you didn't break structure.

### Pattern 3: Route Complex Task
```
1. orchestrator_route(task="Implement OAuth2", context={files_count: 10, requires_tests: true})
   → Returns: {model: "sonnet", complexity_score: 7.5, reason: "..."}
2. Use recommended model (or Claude Code's Task tool with model parameter)
3. orchestrator_validate(task, output) → Quality checkpoint
```

**Why**: Don't use Opus for simple tasks, don't use Flash for complex ones.

---

## Anti-Patterns (What NOT to Do)

❌ **Don't**: Use `Read` tool for Python files
✅ **Do**: Use `auzoom_read` with progressive levels

❌ **Don't**: Read entire file at full level immediately
✅ **Do**: Start with skeleton, drill down as needed

❌ **Don't**: Create README/docs after completing tasks
✅ **Do**: Only create docs when explicitly requested

❌ **Don't**: Use Opus for simple refactoring
✅ **Do**: Use `orchestrator_route` to pick appropriate model

❌ **Don't**: Load all skill documentation at once
✅ **Do**: Use `/skills <name>` to load specific sub-skills on-demand

---

## Sub-Skills (Load on Demand)

- **auzoom-use**: Detailed AuZoom usage patterns and best practices
- **orchestrator-use**: Model routing strategies and cost optimization

**Invoke**: `/skills auzoom-use` or `/skills orchestrator-use`

---

## Performance Metrics

**Token Savings** (actual measurements from Phase 1):
- Skeleton vs Full: 27x reduction (15 vs 400 tokens/node)
- Summary vs Full: 5x reduction (75 vs 400 tokens/node)
- Cache hits: 100x+ speedup (5ms → <0.1ms)

**Cost Savings** (projected from Phase 2):
- Route 60% tasks to Gemini Flash → $0 extra cost
- Route 30% tasks to Haiku → 10x cheaper than Opus
- Reserve Opus for <10% critical tasks → 70% cost reduction

---

## Getting Help

- **File reading**: `/skills auzoom-use`
- **Model routing**: `/skills orchestrator-use`
- **Report issues**: Check repository README for issue tracker
- **Documentation**: See README.md in project root

**Remember**: The goal is **speed and efficiency**. Use progressive disclosure, route intelligently, avoid unnecessary documentation.
