# 🐱 AuZoom - AutoContextZoom

> *"Because curiosity shouldn't cost you 10,000 tokens"*

Multi-resolution code navigation for AI agents. Navigate by names, fetch code only when modifying.

```
Traditional: Read 500-line file → 8,000 tokens → Find one function
AuZoom:        Navigate skeleton → 200 tokens → Zoom to function → 400 tokens total
```

## How It Works

Three layers, fetched on demand:

| Layer | Contains | Tokens/Node |
|-------|----------|-------------|
| `skeleton` | Names + dependencies | ~15 |
| `summary` | + Docstrings, signatures | ~75 |
| `full` | + Source code | ~400 |

```python
# Start broad
auzoom_get_graph(node_id="root", depth_down=2, fetch_level="skeleton")  # 300 tokens

# Zoom to target
auzoom_get_graph(node_id="AuthService.login", fetch_level="full")  # 350 tokens

# Total: 650 tokens vs 6,000+ reading files directly
```

## 🚨 File Read Override

AuZoom replaces standard file reads for code files:

```python
# ❌ BLOCKED
view("src/auth/service.py")

# ✅ REQUIRED  
auzoom_get_graph("src/auth/service.py", fetch_level="skeleton")
```

## ⚠️ Requires Well-Structured Code

AuZoom efficiency depends on self-documenting names:

```python
# ✅ Works: Name tells the story
OrderService.submit_order() → PaymentGateway.charge() → NotificationService.send()

# ❌ Fails: Must fetch docstrings
Service.process() → Helper.do() → Manager.handle()
```

**Enforced limits:** Functions ≤50 lines, Modules ≤250 lines, Directories ≤7 files

## MCP Tools

| Tool | Purpose |
|------|---------|
| `auzoom_read` | Read files with hierarchical navigation (skeleton/summary/full) |
| `auzoom_find` | Search by name pattern |
| `auzoom_get_dependencies` | Trace incoming/outgoing deps |
| `auzoom_stats` | Cache performance statistics |
| `auzoom_validate` | Check structural compliance (≤50 line functions, ≤250 line modules, ≤7 files/dir) |

## Integration

AuZoom works **alongside** standard tools (Read, Edit, Write), not replacing them:

- **Navigation:** Use `auzoom_read` with progressive disclosure to explore
- **Editing:** Use standard `Edit` tool to modify code
- **Validation:** Use `auzoom_validate` to check structure

The GSD expertise skill teaches when to use each tool for optimal efficiency.

## Installation

```bash
pip install auzoom
auzoom index /path/to/project
auzoom serve
```

Claude Code config:
```json
{"mcpServers": {"auzoom": {"command": "auzoom", "args": ["serve", "--project", "."]}}}
```

## Migration

With AI agents, restructuring is cheap. Use test-driven migration:

1. **Capture** - Write tests for all behaviors
2. **Analyze** - `auzoom_validate(scope="all")`
3. **Restructure** - AI-assisted rewrite to AuZoom standards
4. **Verify** - Tests pass = behavior preserved

## Docs

- [AGENT-SKILL.md](./docs/AGENT-SKILL.md) - How agents should use AuZoom
- [ARCHITECTURE.md](./docs/ARCHITECTURE.md) - Technical specification
- [CODING-STANDARD.md](./docs/CODING-STANDARD.md) - Size and structure rules
- [NAMING-CONVENTIONS.md](./docs/NAMING-CONVENTIONS.md) - Self-documenting names

## License

MIT

---
<p align="center">🐱 Navigate like a cat—curious, precise, efficient.</p>
