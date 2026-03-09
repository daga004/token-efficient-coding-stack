# Token-Efficient Coding Stack — Project Instructions

## Intended Use Case

This stack is designed for **long-horizon coding tasks** on **growing Python codebases** (50+ files, weeks/months of development). For small codebases or quick edits, the free baseline below is sufficient.

**Free baseline first**: See `/skills python-coding-principles` — good code structure (≤250 line modules, DESIGN.md, hierarchical Glob/Grep/Read) gives you ~60-70% of AuZoom's benefit without any tooling.

---

## Tool Usage Rules

### Python Files: Prefer AuZoom for Large Codebases
- For Python files in this project, prefer `auzoom_read` over `Read` — it reads progressively (skeleton → summary → full), saving tokens on large files
- For files under ~100 lines, either `auzoom_read` or `Read` works fine
- Start at `level="skeleton"` (signatures only, ~15 tokens/node)
- Escalate to `level="summary"` only when you need docstrings + key logic
- Escalate to `level="full"` only when editing the file
- Small files (<300 tokens) are auto-bypassed to raw content — no manual intervention needed

### Task Routing: Use Orchestrator for Non-Trivial Tasks
- For non-trivial tasks, call `orchestrator_route` to get the optimal model
- Follow the routing recommendation — even 1 tier difference = significant cost savings
- Trivial tasks (score 0-3): Gemini Flash — 83% cheaper
- Simple tasks (score 3-5): Claude Haiku — 73% cheaper
- Complex tasks (score 5-8): Claude Sonnet — baseline
- Critical decisions (score 8-10): Claude Opus — use when needed

### Progressive Disclosure Workflow
```
1. auzoom_find(pattern)           → locate code (~50 tokens)
2. auzoom_read(level="skeleton")  → understand structure (~15 tokens/node)
3. auzoom_read(level="summary")   → understand logic (~75 tokens/node)
4. auzoom_read(level="full")      → edit code (~400 tokens/node)
```
Start with the minimum level needed — only escalate when required.

### Multi-File Tasks: Use Dependency Graphs
- Call `auzoom_get_dependencies(node_id, depth=2)` before reading multiple files
- This traces relationships without reading every file (71.1% file reduction validated)
- Only read files that the graph shows are actually relevant

---

## Code Quality Standards

### Structural Constraints (enforced by `auzoom_validate`)
- Functions: **≤50 lines**
- Modules: **≤250 lines**
- Directories: **≤7 files**
- Validate with: `auzoom_validate(path=".", scope="project")`

### General Rules
- Don't create documentation files unless explicitly asked
- Don't add features beyond what's requested
- Prefer editing existing files over creating new ones
- Follow existing patterns in the codebase

---

## MCP CLI Mode (Recommended)

This stack adds 9 MCP tool schemas to your context window. To eliminate that overhead:

```json
// In ~/.claude/settings.json
{
  "env": {
    "CLAUDE_MCP_CLI": "true"
  }
}
```

With MCP CLI mode enabled, tool schemas are loaded on-demand via bash calls instead of always occupying context. This makes the stack truly zero-overhead until tools are actually needed.

**Trade-off**: Slightly slower tool calls (bash invocation) vs cleaner context window.

---

## Validated Performance (V1 Audit)

These numbers apply to exploration-heavy tasks on codebases with 50+ Python files:

| Metric | Result | Context |
|--------|--------|---------|
| Progressive disclosure savings | 71.3% token reduction | Exploration tasks, 50+ file codebases |
| Graph navigation savings | 71.1% file reduction | Multi-file dependency tracing |
| Cost savings (model routing) | 50.7% cost reduction | API-billing users, mixed task distribution |
| Non-Python metadata | 91.7% token reduction | Non-Python file navigation |
| Quality (simple tasks) | 100% maintained | Simple tasks only |

For small codebases (<50 files), the coding principles skill provides similar benefits without tooling overhead. See `benchmark/RESULTS.md` for breakeven analysis.

---

## Project Layout

```
auzoom/          → Progressive code navigation MCP (6 tools)
orchestrator/    → Model routing MCP (3 tools)
.claude/         → Skills, workflows, hooks
audit/           → V1 verification (84+ tests)
benchmark/       → Empirical token measurements across repo sizes
.planning/       → GSD project management
```
