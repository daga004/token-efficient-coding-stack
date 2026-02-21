# Token-Efficient Coding Stack

**Cut Claude Code costs ~50% with intelligent model routing + progressive code reading**

Claude Code is powerful but expensive. This stack routes simple tasks to cheap models and reads files progressively — skeleton first, details only when needed. Your savings come from two validated mechanisms working together.

[![Tests](https://img.shields.io/badge/tests-98%20passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)]()
[![V1](https://img.shields.io/badge/status-V1%20Certified-success)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()

---

## Validated Results (V1 Audit, 2026-02-21)

| Metric | Validated | Confidence | Evidence |
|--------|-----------|------------|----------|
| **Progressive disclosure savings** | **71.3%** token reduction | High | Phase 6.5 — 100% win rate |
| **Graph navigation savings** | **71.1%** file read reduction | High | Phase 6.5 — 97.6% combined |
| **Cost savings (model routing)** | **50.7%** cost reduction | Medium | Phase 5+7 — pricing-based Gemini |
| **Non-Python metadata** | **91.7%** token reduction | High | Phase 9 — 4.0/5 usefulness |
| **Quality (simple tasks)** | **100%** maintained | Medium | Phase 4 — simple tasks only |

**How we validated**: 13-phase audit, 37 plans, 98 automated tests, 60+ evidence records. Self-correcting — caught and fixed 3 methodology errors during audit. See [V1 Certification Report](audit/reports/12-V1-CERTIFICATION.md).

**Caveats**: Cost savings use pricing-based Gemini (not real API execution). Quality validated for simple tasks only. Complex task success rate estimated 67-85% (limited sample).

---

## Quick Install

### macOS (Automated)
```bash
curl -fsSL https://raw.githubusercontent.com/daga004/token-efficient-coding-stack/main/quick-install.sh | bash
```

### Linux / Manual
```bash
git clone https://github.com/daga004/token-efficient-coding-stack.git
cd token-efficient-coding-stack

cd auzoom && pip install -e . && cd ..
cd orchestrator && pip install -e . && cd ..

claude mcp add --scope user auzoom $(which auzoom-mcp)
claude mcp add --scope user orchestrator python3 -m orchestrator.mcp.server

cp -r .claude/skills/* ~/.claude/skills/
```

**Requirements**: Python 3.11+, Claude Code CLI

### Enable MCP CLI Mode (Recommended)

The stack adds 9 MCP tool schemas to your context window (~2k tokens). MCP CLI mode eliminates this overhead by loading tools on-demand via bash instead of always in context:

```json
// In ~/.claude/settings.json
{
  "env": {
    "CLAUDE_MCP_CLI": "true"
  }
}
```

**Why it matters**: A token-efficiency stack that adds tokens via schemas is ironic. MCP CLI mode makes the stack truly zero-overhead until tools are actually needed.

**Trade-off**: Slightly slower tool calls (bash invocation) vs cleaner context window. Recommended for all users.

---

## How It Works

Three tools work together in your Claude Code workflow:

### 1. AuZoom — Progressive Code Reading

Instead of reading entire files, AuZoom reads at three levels:

- **Skeleton**: Class/function signatures only (~15 tokens/node)
- **Summary**: Signatures + docstrings + key logic (~75 tokens/node)
- **Full**: Complete source when editing (~400 tokens/node)

Plus dependency graphs that trace relationships without reading every file.

**Validated savings**: 71.3% token reduction on progressive tasks, 71.1% file reduction on graph navigation.

### 2. Orchestrator — Smart Model Routing

Routes each task to the cheapest model that works:

| Model | Cost/1M input | When Used | Savings vs Sonnet |
|-------|--------------|-----------|-------------------|
| Gemini Flash | $0.50 | Trivial tasks (score 0-3) | ~83% |
| Claude Haiku | $0.80 | Simple tasks (score 3-5) | ~73% |
| Claude Sonnet | $3.00 | Complex tasks (score 5-8) | Baseline |
| Claude Opus | $15.00 | Critical decisions (score 8-10) | Use when needed |

**Validated savings**: 50.7% cost reduction across task mix.

### 3. Get Shit Done (GSD) — Meta-Prompting System

Created by TACHES ([glittercowboy](https://github.com/glittercowboy/get-shit-done)). Structured workflows for planning, execution, and project management.

### How They Combine

```
Your Task
    |
    v
GSD Workflow ---- Planning & execution structure
    |
    v
Orchestrator ---- Routes to cheapest capable model
    |
    v
AuZoom ---------- Reads only what's needed (skeleton/summary/full)
```

**Combined effect**: Right model + minimal context = validated 50.7% cost savings.

---

## Getting the Most Out of This Stack

### Decision Flow: When to Use What

```
Task received
|
+-- Need to find code? --> auzoom_find (instant, ~50 tokens)
|
+-- Need to understand structure? --> auzoom_read(level="skeleton")
|
+-- Need function details? --> auzoom_read(level="summary")
|
+-- Need to edit code? --> auzoom_read(level="full") for target function
|
+-- Need dependency chain? --> auzoom_get_dependencies (graph query)
|
+-- Ready to implement? --> orchestrator_route to pick model, then execute
```

### Best Practices

1. **Start with skeleton, escalate as needed**: skeleton -> summary -> full. Most exploration needs only skeleton.
2. **Route every task**: Even 1 tier difference = significant savings. `orchestrator_route` before execution.
3. **Use graph queries for multi-file tasks**: `auzoom_get_dependencies` avoids reading 5+ files manually.
4. **Small files (<300 tokens)**: AuZoom auto-bypasses to raw content (threshold bypass implemented).
5. **Batch simple operations**: Route typo fixes, constant updates, etc. to Flash/Haiku for 99%+ savings.

### Usage Examples

#### Explore unfamiliar codebase (95% token savings)
```python
auzoom_read("src/", level="skeleton")       # ~500 tokens (all modules)
auzoom_read("src/main.py", level="summary") # ~200 tokens (entry point)
# vs reading 15 files = 18,000 tokens
```

#### Find and fix a bug (88% token savings)
```python
auzoom_find("authenticate_user")            # ~50 tokens (instant)
auzoom_read("src/auth.py", level="summary") # ~150 tokens (understand)
# vs reading entire 600-line file = 2,400 tokens
```

#### Trace dependencies before refactoring (92% token savings)
```python
auzoom_get_dependencies("process_payment", depth=2)  # ~100 tokens
auzoom_read("gateway.py", level="summary")            # ~150 tokens
# vs manually reading 4+ files = 4,600 tokens
```

#### Route implementation to save costs (73% cost savings)
```python
orchestrator_route("Add /users/{id}/profile endpoint with tests",
    context={"files_count": 3, "requires_tests": True})
# Returns: {model: "haiku", score: 4.5}
# Haiku: $0.80/1M vs Sonnet: $3.00/1M
```

**See more**: [USAGE-EXAMPLES.md](USAGE-EXAMPLES.md) (10 detailed scenarios with before/after comparisons)

---

## AuZoom MCP Tools

```python
# Read files progressively
auzoom_read(path="src/main.py", level="skeleton")  # Structure only
auzoom_read(path="src/main.py", level="summary")   # + docstrings, key logic
auzoom_read(path="src/main.py", level="full")      # Complete source

# Find code without reading files
auzoom_find(pattern="*Handler")

# Analyze dependencies without reading files
auzoom_get_dependencies(node_id="...", depth=1)

# Get call graph
auzoom_get_calls(node_id="...")

# Check cache performance
auzoom_stats()

# Validate code structure
auzoom_validate(path="src/", scope="project")
```

## Orchestrator MCP Tools

```python
# Get routing recommendation
orchestrator_route(
    task="Implement OAuth2 authentication",
    context={"files_count": 8, "requires_tests": True}
)
# Returns: {model: "sonnet", complexity_score: 7.5}

# Execute on specific model
orchestrator_execute(model="haiku", prompt="Add user auth", max_tokens=4096)

# Validate output quality
orchestrator_validate(task="Add authentication", output="<implementation>")
```

---

## Recommended Companion Tools

### Context7 MCP
Fetches latest library/framework documentation so Claude uses current APIs instead of outdated ones from training data. Particularly useful when working with tree-sitter APIs (which change across versions) or any rapidly-evolving library.

```bash
npx -y @anthropic-ai/claude-code mcp add context7 -- npx -y @upstash/context7-mcp@latest
```

### Claude Code Hooks
The stack ships with recommended hooks in `.claude/settings.json`:
- **Read hook**: Suggests `auzoom_read` when you try to `Read` a `.py` file (non-blocking)
- **Edit hook**: Blocks test file modification during plan execution (TDD protection)

See `.claude/settings.json` to customize or disable hooks.

---

## Architecture

```
Claude Code (User)
    |
    +--- MCP Protocol ---+
    |                     |
AuZoom MCP           Orchestrator MCP
    |                     |
Tree-Sitter          Complexity Scorer
Parser + Cache       Model Registry (4 tiers)
                     Task Executor
```

**AuZoom**: Tree-sitter Python parser -> Lazy graph -> Content-based cache (SHA256) -> MCP tools (6 tools)
**Orchestrator**: Complexity scorer -> Model registry -> Task executor -> Quality validator -> MCP tools (3 tools)
**GSD**: Meta-prompts -> Planning workflows -> Execution templates -> Context management

---

## Testing

```bash
# AuZoom tests
cd auzoom && pytest tests/ -v     # 30 tests

# Orchestrator tests
cd orchestrator && pytest tests/ -v  # 68 tests
```

---

## Project Structure

```
token-efficient-coding-stack/
+-- README.md
+-- VALIDATION-SUMMARY.md           # Detailed validation with audit findings
+-- USAGE-EXAMPLES.md               # 10 usage scenarios
+-- quick-install.sh                # One-command installer
+-- auzoom/                         # Progressive code navigation
|   +-- src/auzoom/
|   |   +-- core/                   # Parser, graph, caching
|   |   +-- mcp/                    # MCP server (6 tools)
|   +-- tests/                      # 30 tests
+-- orchestrator/                   # Intelligent model routing
|   +-- src/orchestrator/
|   |   +-- scoring.py              # Complexity scorer
|   |   +-- registry.py             # Model registry (4 tiers)
|   |   +-- executor.py             # Task executor
|   |   +-- mcp/                    # MCP server (3 tools)
|   +-- tests/                      # 68 tests
+-- audit/                          # V1 comprehensive audit
|   +-- reports/                    # Gap analysis, certification, V1.1 roadmap
|   +-- evidence/                   # Test evidence (JSONL)
+-- .claude/
|   +-- skills/                     # Claude Code skills
|   +-- workflows/                  # Reusable workflow templates
+-- .planning/                      # GSD project management
    +-- MILESTONES.md               # Shipped milestones
    +-- ROADMAP.md                  # Phase tracking
    +-- milestones/                 # Archived milestone details
```

---

## Roadmap

### V1.0 (Shipped 2026-02-21)
- [x] AuZoom MCP server (6 tools, 30 tests)
- [x] Orchestrator MCP server (3 tools, 68 tests)
- [x] GSD integration (skills, workflows)
- [x] Comprehensive V1 audit (13 phases, 37 plans, 98 tests)
- [x] V1 CERTIFIED — zero critical blockers
- [x] CLAUDE.md project instructions (auto-loaded by Claude Code)
- [x] Claude Code hooks (auzoom suggestions, TDD protection)
- [x] MCP CLI mode documentation (zero-overhead tool loading)

### V1.1 (Planned)
- [ ] Configuration file for user-customizable models/thresholds
- [ ] JS/TS tree-sitter support (doubles target audience)
- [ ] Feedback logging for routing visibility
- [ ] Basic escalation matrix (retry -> escalate)
- [ ] Real Gemini API execution validation

### V2 (Future)
- [ ] Multi-language support (Go, Rust, Java)
- [ ] Multi-level non-Python disclosure (metadata -> outline -> full)
- [ ] Incremental parsing for large repos
- [ ] Advanced compression techniques

---

## Known Limitations

**Validated caveats**:
- Cost savings (50.7%) use pricing-based Gemini, not real API execution
- Quality validated for simple tasks only (100%). Complex tasks estimated 67-85%
- Python-only for progressive disclosure (non-Python gets structural metadata)
- Complexity scorer has systematic under-scoring tendency (conservative routing)

**Use with caution for**:
- Security-critical code (0% success on sanitization tasks in audit)
- Complex concurrency (race conditions, deadlocks)
- Large-scale refactorings (>10 files) without review

**Best for**:
- Simple edits, code exploration, standard features
- Test writing, documentation updates, refactoring
- Dependency analysis, code review

---

## Platform Support

| Platform | Status |
|----------|--------|
| **macOS** | Tested & validated (automated install) |
| **Linux** | Supported (manual install) |
| **Windows** | Should work via WSL |

---

## Contributing

Follow AuZoom's structural standards:
- Functions <= 50 lines
- Modules <= 250 lines
- Directories <= 7 files

Validate with: `auzoom_validate(path=".", scope="project")`

---

## Credits

**Tools**: AuZoom + Orchestrator (built for this project), [Get Shit Done](https://github.com/glittercowboy/get-shit-done) by TACHES
**Built by**: Claude (Anthropic) for Dhiraj Daga
**Methodology**: GSD meta-prompting system
**License**: MIT

---

**Validated results** (V1 audit, 13 phases, 84+ tests):
- **71.3% token savings** via progressive disclosure (high confidence)
- **50.7% cost savings** via model routing (medium confidence)
- **71.1% file read reduction** via graph navigation (high confidence)
- **100% quality maintained** on simple tasks (medium confidence)

See [VALIDATION-SUMMARY.md](VALIDATION-SUMMARY.md) for detailed methodology and audit findings.
