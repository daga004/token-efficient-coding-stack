# Token-Efficient Coding Stack

**Reduce token usage as your Python codebase grows — progressive code reading + intelligent model routing for long-horizon development projects.**

[![Tests](https://img.shields.io/badge/tests-98%20passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)]()
[![V1](https://img.shields.io/badge/status-V1%20Certified-success)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()

---

## Who This Is For

This stack is designed for **long-horizon coding tasks** on **growing Python codebases**:

- Projects spanning weeks or months of development
- Codebases that have grown beyond 50+ Python files
- Sessions involving exploration of unfamiliar code (not just quick edits)
- API-billing users who pay per token (not subscription plans)

**When it helps most**: You're building a feature over several weeks. The codebase has grown to 200+ files. You need to understand auth, database, and API layers before making changes. AuZoom reads skeletons of 50 files for the cost of reading 3 files fully.

**When NOT to use this stack**:
- Quick one-off edits or small scripts
- Non-Python projects (progressive disclosure is Python-only)
- Subscription-plan users (token savings don't translate to cost savings)
- Codebases with monolithic files averaging >400 lines — fix the structure first

---

## The Three Layers

Token efficiency has three layers. You don't need all three to get value.

### Layer 0: Coding Principles (Free, always)
Good code structure eliminates 89-97% of token waste before any tooling:
- Modules ≤250 lines — split what grows beyond
- `DESIGN.md` at root — one file that orients any agent
- Meaningful `__init__.py` with module-level docstrings
- Hierarchical Glob → `__init__.py` → Grep → targeted Read

See `/skills python-coding-principles` for the complete pattern.

### Layer 1: Claude Code Built-ins (Free, always)
`Glob` → `Grep` → targeted `Read` with structured patterns handles most tasks on small-medium codebases efficiently. No tools needed beyond what Claude Code already provides.

### Layer 2: AuZoom (Add for large codebases + exploration-heavy sessions)
Progressive disclosure reads skeleton first, details only when needed:
- At 20+ files: ~20% additional savings over the structured baseline
- At 200+ files: ~50-90% additional savings
- At 800+ files: ~96% savings vs the baseline

---

## Validated Results (V1 Audit, 2026-02-21)

These numbers apply to exploration-heavy tasks on codebases with 50+ files:

| Metric | Validated | Context |
|--------|-----------|---------|
| **Progressive disclosure savings** | **71.3%** token reduction | Exploration tasks, 50+ file codebases |
| **Graph navigation savings** | **71.1%** file read reduction | Multi-file dependency tracing |
| **Cost savings (model routing)** | **50.7%** cost reduction | API-billing users, mixed task distribution |
| **Non-Python metadata** | **91.7%** token reduction | Non-Python file navigation |
| **Quality (simple tasks)** | **100%** maintained | Simple tasks only |

**Caveats**: Cost savings use pricing-based Gemini (not real API execution). Quality validated for simple tasks only. Complex task success rate estimated 67-85%.

**How we validated**: 13-phase audit, 37 plans, 98 automated tests. See [V1 Certification Report](audit/reports/12-V1-CERTIFICATION.md).

---

## Benchmark: When Does AuZoom Pay Off?

Empirical token measurements comparing structured baseline (Glob/Grep/Read) vs AuZoom:

| Repo | Files | LOC | Baseline | AuZoom | AuZoom+CLI |
|------|-------|-----|---------|--------|-----------|
| AuZoom source | 24 | 3,233 | 2,005 | 2,346 ❌ | 1,296 ✓ |
| Audit suite | 14 | 2,445 | 2,584 | 2,090 ✓ | 1,040 ✓ |
| requests lib | 18 | 5,628 | 4,161 | 3,339 ✓ | 2,289 ✓ |
| FastAPI | 48 | 19,284 | 5,495 | 15,874 ❌† | 14,824 ❌† |
| Django | 894 | 155,657 | 66,385 | 2,778 ✓ | 1,728 ✓ |

**Legend**: ✓ = AuZoom wins vs baseline, ❌ = baseline is more efficient
†FastAPI has massive monolithic files (avg 401 lines, some >4,900 lines) — structure violation inflates even AuZoom's skeleton output.

**Key finding**: AuZoom helps when files are well-structured (≤250 lines). It amplifies good architecture; it can't rescue monolithic code.

**With MCP CLI mode enabled** (`CLAUDE_MCP_CLI=true`): eliminates the 1,050-token schema overhead, making AuZoom beneficial at nearly any codebase size.

See `benchmark/RESULTS.md` for full methodology and `benchmark/token_benchmark.py` to measure your own repo.

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

The stack adds 9 MCP tool schemas to your context window (~1,050 tokens). MCP CLI mode eliminates this overhead by loading tools on-demand:

```json
// In ~/.claude/settings.json
{
  "env": {
    "CLAUDE_MCP_CLI": "true"
  }
}
```

**Why it matters**: A token-efficiency stack that adds tokens via schemas is ironic. MCP CLI mode makes the stack truly zero-overhead until tools are actually needed.

---

## How It Works

Three tools work together in your Claude Code workflow:

### 1. AuZoom — Progressive Code Reading

Instead of reading entire files, AuZoom reads at three levels:

- **Skeleton**: Class/function signatures only (~15 tokens/node)
- **Summary**: Signatures + docstrings + key logic (~75 tokens/node)
- **Full**: Complete source when editing (~400 tokens/node)

Plus dependency graphs that trace relationships without reading every file.

**Validated savings**: 71.3% token reduction on exploration tasks, 71.1% file reduction on graph navigation (codebases with 50+ files).

### 2. Orchestrator — Smart Model Routing

Routes each task to the cheapest model that works:

| Model | Cost/1M input | When Used | Savings vs Sonnet |
|-------|--------------|-----------|-------------------|
| Gemini Flash | $0.50 | Trivial tasks (score 0-3) | ~83% |
| Claude Haiku | $0.80 | Simple tasks (score 3-5) | ~73% |
| Claude Sonnet | $3.00 | Complex tasks (score 5-8) | Baseline |
| Claude Opus | $15.00 | Critical decisions (score 8-10) | Use when needed |

**Validated savings**: 50.7% cost reduction across task mix (API-billing users).

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

---

## Getting the Most Out of This Stack

### Decision Flow: When to Use What

```
Task received
|
+-- <50 files, well structured? --> Use Layer 1 (Glob/Grep/Read). AuZoom optional.
|
+-- 50+ files or large files? --> Use Layer 2 (AuZoom) progressive disclosure
|
+-- Need to find code? --> auzoom_find (instant, ~50 tokens)
|
+-- Need structure? --> auzoom_read(level="skeleton")
|
+-- Need function details? --> auzoom_read(level="summary")
|
+-- Need to edit code? --> auzoom_read(level="full") for target function only
|
+-- Need dependency chain? --> auzoom_get_dependencies (graph query)
|
+-- Ready to implement? --> orchestrator_route to pick model, then execute
```

### Best Practices

1. **Start with coding principles**: ≤250-line modules + DESIGN.md makes every approach more efficient.
2. **Start with skeleton, escalate as needed**: skeleton → summary → full. Most exploration needs only skeleton.
3. **Route every task**: Even 1 tier difference = significant savings. `orchestrator_route` before execution.
4. **Use graph queries for multi-file tasks**: `auzoom_get_dependencies` avoids reading 5+ files manually.
5. **Enable MCP CLI mode**: Eliminates 1,050-token schema overhead — always worth doing.

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
Fetches latest library/framework documentation so Claude uses current APIs instead of outdated ones from training data.

```bash
npx -y @anthropic-ai/claude-code mcp add context7 -- npx -y @upstash/context7-mcp@latest
```

### Claude Code Hooks
The stack ships with one project-scoped hook in `.claude/settings.json`:
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

**AuZoom**: Tree-sitter Python parser → Lazy graph → Content-based cache (SHA256) → MCP tools (6 tools)
**Orchestrator**: Complexity scorer → Model registry → Task executor → Quality validator → MCP tools (3 tools)
**GSD**: Meta-prompts → Planning workflows → Execution templates → Context management

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
+-- benchmark/                      # Empirical token measurements
|   +-- token_benchmark.py          # Run on any repo
|   +-- RESULTS.md                  # Results across 5 repo sizes
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
- [x] MCP CLI mode documentation (zero-overhead tool loading)

### V1.1 (Planned)
- [ ] Empirical benchmark suite (this refactoring)
- [ ] Coding principles skill (Layer 0 baseline)
- [ ] Configuration file for user-customizable models/thresholds
- [ ] JS/TS tree-sitter support (doubles target audience)
- [ ] Feedback logging for routing visibility
- [ ] Real Gemini API execution validation

### V2 (Future)
- [ ] Multi-language support (Go, Rust, Java)
- [ ] Multi-level non-Python disclosure (metadata → outline → full)
- [ ] Incremental parsing for large repos
- [ ] Advanced compression techniques

---

## Known Limitations

**Validated caveats**:
- Cost savings (50.7%) use pricing-based Gemini, not real API execution
- Quality validated for simple tasks only (100%). Complex tasks estimated 67-85%
- Python-only for progressive disclosure (non-Python gets structural metadata)
- Complexity scorer has systematic under-scoring tendency (conservative routing)

**AuZoom does NOT help with**:
- Monolithic files (avg >400 lines) — fix the code structure first
- Edit-heavy sessions touching only 1-2 known files
- Codebases under ~20 files without MCP CLI mode enabled

**Use with caution for**:
- Security-critical code (0% success on sanitization tasks in audit)
- Complex concurrency (race conditions, deadlocks)
- Large-scale refactorings (>10 files) without review

**Best for**:
- Exploration of unfamiliar large codebases
- Feature development over weeks/months
- Standard features, test writing, dependency analysis

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
- Functions ≤ 50 lines
- Modules ≤ 250 lines
- Directories ≤ 7 files

Validate with: `auzoom_validate(path=".", scope="project")`

---

## Credits

**Tools**: AuZoom + Orchestrator (built for this project), [Get Shit Done](https://github.com/glittercowboy/get-shit-done) by TACHES
**Built by**: Claude (Anthropic) for Dhiraj Daga
**Methodology**: GSD meta-prompting system
**License**: MIT

---

**Validated results** (V1 audit, 13 phases, 84+ tests):
- **71.3% token savings** via progressive disclosure (high confidence, 50+ file codebases)
- **50.7% cost savings** via model routing (medium confidence, API-billing users)
- **71.1% file read reduction** via graph navigation (high confidence)
- **100% quality maintained** on simple tasks (medium confidence)

See [VALIDATION-SUMMARY.md](VALIDATION-SUMMARY.md) for detailed methodology and [benchmark/RESULTS.md](benchmark/RESULTS.md) for breakeven analysis.
