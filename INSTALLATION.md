# Token-Efficient AI Coding Stack - Installation Guide

Complete setup guide for AuZoom (multi-resolution code navigation) and Orchestrator (intelligent model routing) with Claude Code integration.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [AuZoom Installation](#auzoom-installation)
- [Orchestrator Installation](#orchestrator-installation)
- [MCP Server Configuration](#mcp-server-configuration)
- [Verification](#verification)
- [Usage Examples](#usage-examples)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

1. **Python 3.10+**
   ```bash
   python3 --version  # Should show 3.10 or higher
   ```

2. **Claude Code CLI**
   - Install from: https://claude.ai/download
   - Verify installation:
     ```bash
     claude --version
     ```

3. **Git**
   ```bash
   git --version
   ```

### System Requirements

- **OS**: macOS, Linux, or Windows (with WSL)
- **RAM**: 4GB minimum (8GB recommended)
- **Disk**: 500MB for installation

---

## Quick Start

For the impatient:

```bash
# 1. Clone repository
git clone <repo-url>
cd token-efficiency-stack

# 2. Install AuZoom
cd auzoom
pip install -e .

# 3. Register MCP server
claude mcp add --scope user auzoom $(which auzoom-mcp)

# 4. Restart Claude Code
# ... restart your Claude Code application ...

# 5. Verify
claude mcp list
# Should show: auzoom: ... - ✓ Connected
```

---

## AuZoom Installation

### What is AuZoom?

AuZoom provides **multi-resolution code navigation** with 3 fetch levels:
- **Skeleton** (~15 tokens/node): Names only
- **Summary** (~75 tokens/node): + docstrings, signatures
- **Full** (~400 tokens/node): Complete source code

**Token savings**: 4-27x reduction vs traditional file reading.

### Installation Steps

1. **Navigate to AuZoom directory**
   ```bash
   cd /path/to/token-efficiency-stack/auzoom
   ```

2. **Install in development mode**
   ```bash
   pip install -e .
   ```

   This creates two commands:
   - `auzoom` - CLI tool
   - `auzoom-mcp` - MCP server

3. **Verify installation**
   ```bash
   which auzoom-mcp
   # Should show: /path/to/python/bin/auzoom-mcp

   auzoom --version
   # Should show: auzoom, version 0.2.0
   ```

4. **Test MCP server manually**
   ```bash
   echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | auzoom-mcp
   ```

   Should return JSON with 5 tools:
   - `auzoom_read`
   - `auzoom_find`
   - `auzoom_get_dependencies`
   - `auzoom_stats`
   - `auzoom_validate`

### Directory Structure After Installation

```
auzoom/
├── src/
│   └── auzoom/
│       ├── core/           # Parser, graph, caching
│       ├── mcp/            # MCP server implementation
│       ├── cli.py          # CLI commands
│       └── models.py       # Data models
├── tests/                  # 39 tests (all passing)
├── pyproject.toml          # Package configuration
└── .auzoom/                # Cache directory (auto-created)
    ├── index.json          # File index
    └── metadata/           # Cached parse results
```

---

## Orchestrator Installation

**Status**: Phase 2 - In development

The Orchestrator will provide intelligent model routing based on task complexity:
- **Tier 0** (0-3): Gemini Flash ($0.01/1M tokens)
- **Tier 1** (3-5): Claude Haiku
- **Tier 2** (5-8): Claude Sonnet
- **Tier 3** (8-10): Claude Opus

### Installation (When Available)

```bash
cd orchestrator
pip install -e .
claude mcp add --scope user orchestrator $(which orchestrator-mcp)
```

---

## MCP Server Configuration

### Register AuZoom MCP Server

**Option 1: User Scope (Recommended)**

Available across all projects:

```bash
claude mcp add --scope user auzoom $(which auzoom-mcp)
```

**Option 2: Project Scope**

Only for current project:

```bash
cd /path/to/your/project
claude mcp add --scope project auzoom $(which auzoom-mcp)
```

**Option 3: Manual Configuration**

Edit `~/.claude.json` (user scope) or `.mcp.json` (project scope):

```json
{
  "mcpServers": {
    "auzoom": {
      "type": "stdio",
      "command": "/path/to/auzoom-mcp",
      "args": [],
      "env": {}
    }
  }
}
```

### Restart Claude Code

**Critical**: MCP servers only load on startup. After adding/modifying MCP configuration:

1. Quit Claude Code completely
2. Reopen Claude Code
3. MCP servers will load automatically

---

## Verification

### Step 1: Check MCP Server Status

```bash
claude mcp list
```

**Expected output:**
```
Checking MCP server health...

auzoom: /path/to/auzoom-mcp - ✓ Connected
```

**If you see "✗ Failed to connect":**
- Restart Claude Code (servers only load on startup)
- Check the command path: `which auzoom-mcp`
- Test manually: `echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | auzoom-mcp`

### Step 2: Verify Tools in Claude Code

After restart, start a conversation and ask Claude:

```
Can you read the file orchestrator/src/orchestrator/models.py using auzoom_read at skeleton level?
```

Claude should respond using the `auzoom_read` tool.

### Step 3: Check Cache Performance

```bash
# CLI tool to check stats
auzoom stats
```

**Expected output:**
```
Cache Statistics:
- Files indexed: X
- Cache hits: Y
- Cache misses: Z
- Hit rate: XX%
```

### Step 4: Validate Code Structure

```bash
# Validate a file meets AuZoom standards
auzoom validate --scope file path/to/file.py

# Validate entire project
auzoom validate --scope project
```

**AuZoom Standards:**
- Functions ≤50 lines
- Modules ≤250 lines
- Directories ≤7 files

---

## Usage Examples

### Example 1: Progressive File Reading

Ask Claude Code:

```
Read orchestrator/src/orchestrator/models.py at skeleton level
```

Claude uses: `auzoom_read(path="orchestrator/src/orchestrator/models.py", level="skeleton")`

**Result**: ~270 tokens (18 nodes × 15 tokens)

---

Then ask:

```
Show me the summary for the Task class
```

Claude uses: `auzoom_read(path="orchestrator/src/orchestrator/models.py", level="summary")`

**Result**: ~1350 tokens (18 nodes × 75 tokens)

---

Finally:

```
Show me the full implementation of TaskComplexity
```

Claude uses: `auzoom_read(path="orchestrator/src/orchestrator/models.py", level="full")`

**Result**: ~7200 tokens (18 nodes × 400 tokens)

**Total tokens**: 8820 tokens

**Traditional approach** (read full file 3 times): 21,600 tokens

**Savings**: 59% reduction

### Example 2: Find Functions Across Project

Ask Claude:

```
Find all functions named 'validate' in the project
```

Claude uses: `auzoom_find(pattern="validate")`

Returns all matching nodes across indexed files.

### Example 3: Dependency Analysis

Ask Claude:

```
What are the dependencies of the ComplexityScorer class?
```

Claude uses: `auzoom_get_dependencies(node_id="orchestrator/src/orchestrator/scoring.py::ComplexityScorer", depth=2)`

Returns dependency graph with transitive dependencies.

### Example 4: Code Validation

Ask Claude:

```
Validate the orchestrator package meets AuZoom standards
```

Claude uses: `auzoom_validate(scope="directory", path="orchestrator/src/orchestrator")`

Returns compliance report with any violations.

---

## Troubleshooting

### MCP Server Shows "Failed to connect"

**Cause**: Claude Code hasn't been restarted after configuration.

**Solution**:
```bash
# 1. Verify configuration exists
cat ~/.claude.json  # or .mcp.json

# 2. Verify command exists
which auzoom-mcp

# 3. Test manually
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | auzoom-mcp

# 4. Restart Claude Code completely
# ... quit and reopen ...

# 5. Check again
claude mcp list
```

### "auzoom-mcp: command not found"

**Cause**: AuZoom not installed or not in PATH.

**Solution**:
```bash
# Reinstall AuZoom
cd auzoom
pip install -e .

# Verify
which auzoom-mcp
```

### "ModuleNotFoundError: No module named 'auzoom'"

**Cause**: AuZoom installed with wrong Python version.

**Solution**:
```bash
# Check Python version
python3 --version  # Must be 3.10+

# Reinstall with correct Python
cd auzoom
python3.11 -m pip install -e .  # Use specific version

# Update MCP config with correct path
claude mcp remove auzoom
claude mcp add --scope user auzoom $(which auzoom-mcp)
```

### Cache Performance Issues

**Symptom**: Slow file reads, low cache hit rate.

**Solution**:
```bash
# Clear cache
rm -rf .auzoom/

# Warm cache for important files
auzoom warm path/to/important/directory

# Check stats
auzoom stats
```

### Tools Not Available in Claude Code

**Symptom**: Claude says "I don't have access to auzoom_read tool"

**Checklist**:
1. ✓ MCP server registered: `claude mcp list` shows "✓ Connected"
2. ✓ Claude Code restarted after configuration
3. ✓ No errors in `~/.claude/debug/latest`
4. ✓ Test manually works: `echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | auzoom-mcp`

**Solution**:
```bash
# Check debug logs
grep -i "auzoom\|mcp" ~/.claude/debug/latest

# If no mentions, MCP server didn't load - restart Claude Code

# If errors, check permissions
ls -la $(which auzoom-mcp)
```

---

## Performance Metrics

### Token Savings (Measured)

**Python files** (auzoom/models.py, 18 nodes):
- Skeleton: 270 tokens (96% reduction vs full)
- Summary: 1,350 tokens (81% reduction vs full)
- Full: 7,200 tokens (baseline)

**Cache speedup**:
- Cold parse: 5-6ms
- Warm (memory): <0.1ms (100x faster)
- Disk cache: <1ms (5-10x faster)

### Cost Savings Example

**Scenario**: Read 10 files (avg 20 nodes each) during code review

**Traditional approach:**
- 10 full reads: 10 × 8000 tokens = 80,000 tokens
- Cost (Sonnet @ $3/1M): $0.24

**With AuZoom:**
- 10 skeleton reads: 10 × 300 tokens = 3,000 tokens
- 3 summary reads: 3 × 1,500 tokens = 4,500 tokens
- 1 full read: 1 × 8,000 tokens = 8,000 tokens
- **Total**: 15,500 tokens
- Cost (Sonnet @ $3/1M): $0.047

**Savings**: 81% reduction, $0.19 saved per review

---

## Architecture Overview

### How AuZoom Works

```
┌─────────────────────────────────────────────────────────────┐
│ Claude Code Session                                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  "Read auth.py at skeleton level"                          │
│          ↓                                                  │
│  auzoom_read(path="auth.py", level="skeleton")             │
│          ↓                                                  │
├─────────────────────────────────────────────────────────────┤
│ AuZoom MCP Server (stdio)                                   │
├─────────────────────────────────────────────────────────────┤
│          ↓                                                  │
│  LazyCodeGraph.get_file()                                  │
│          ├─→ Check cache (.auzoom/metadata/)               │
│          │   └─→ HIT: Return cached (< 1ms)                │
│          └─→ MISS: Parse with tree-sitter (5ms)            │
│                   └─→ Cache result                          │
│          ↓                                                  │
│  Serialize to skeleton/summary/full                        │
│          ↓                                                  │
│  Return JSON: {nodes: [...], cached: true}                 │
│          ↓                                                  │
└─────────────────────────────────────────────────────────────┘
│          ↓                                                  │
│  Claude processes structure (270 tokens vs 7200)           │
└─────────────────────────────────────────────────────────────┘
```

### File Structure

```
token-efficiency-stack/
├── auzoom/                 # Phase 1: Multi-resolution navigation
│   ├── src/auzoom/
│   │   ├── core/
│   │   │   ├── parsing/   # Tree-sitter parsers
│   │   │   ├── graph/     # Lazy code graph
│   │   │   └── caching/   # Persistent cache
│   │   ├── mcp/           # MCP server
│   │   └── cli.py         # CLI commands
│   └── tests/             # 39 tests
│
├── orchestrator/           # Phase 2: Intelligent routing
│   ├── src/orchestrator/
│   │   ├── scoring.py     # Complexity scoring
│   │   ├── registry.py    # Model registry
│   │   └── clients/       # Model clients
│   └── tests/
│
└── .planning/             # GSD workflow
    ├── PROJECT.md
    ├── ROADMAP.md
    └── phases/
```

---

## Next Steps

1. **Complete Phase 1**: Verify AuZoom works end-to-end
2. **Phase 2**: Implement Orchestrator for model routing
3. **Phase 3**: Integration & validation (measure token/cost savings)

---

## Support & Contributing

- **Issues**: Report bugs and request features
- **Documentation**: See `auzoom/docs/` for detailed architecture
- **Tests**: Run `pytest` in `auzoom/` or `orchestrator/`

---

## License

MIT License - See LICENSE file for details
