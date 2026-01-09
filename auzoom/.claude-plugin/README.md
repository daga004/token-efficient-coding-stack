# AuZoom MCP Server

Multi-resolution code navigation that replaces file reading with hierarchical views.

## Installation

```bash
cd auzoom
pip install -e .
```

## Configuration

Add to your Claude Code MCP settings (~/.claude/config.json or project settings):

```json
{
  "mcpServers": {
    "auzoom": {
      "command": "auzoom-mcp"
    }
  }
}
```

Or for development:

```json
{
  "mcpServers": {
    "auzoom": {
      "command": "python3",
      "args": ["-m", "auzoom.mcp_server"],
      "env": {
        "PYTHONPATH": "/path/to/auzoom/src"
      }
    }
  }
}
```

## Tools

### auzoom_read
**Replaces the Read tool** with hierarchical navigation.

**Parameters:**
- `path` (required): File path to read
- `level` (optional): Detail level - "skeleton" (default), "summary", or "full"
- `offset` (optional): Line offset for partial reads
- `limit` (optional): Line limit for partial reads

**Python files:**
- `skeleton`: Function/class names and signatures (~15 tokens/node)
- `summary`: + docstrings and metadata (~75 tokens/node)
- `full`: Complete source code (~400 tokens/node)

**Non-Python files (lazy indexing):**
- First access: Returns full content + caches summary in background
- Subsequent access: Returns cached summary (at skeleton/summary level)
- Use `level="full"` to always get complete content

**Usage:**
```json
{
  "name": "auzoom_read",
  "arguments": {
    "path": "src/auth.py"
  }
}
// Returns skeleton view

{
  "name": "auzoom_read",
  "arguments": {
    "path": "src/auth.py",
    "level": "full"
  }
}
// Returns full source

{
  "name": "auzoom_read",
  "arguments": {
    "path": "README.md",
    "level": "skeleton"
  }
}
// Returns cached summary (or full if first access)
```

### auzoom_find
Search for code by name pattern across indexed files.

**Parameters:**
- `pattern` (required): Name pattern to search for

**Returns:** List of matching nodes with IDs

### auzoom_get_dependencies
Get dependency graph for a code node.

**Parameters:**
- `node_id` (required): Node ID from auzoom_read or auzoom_find
- `depth` (optional): Dependency depth to traverse (default: 1)

### auzoom_stats
Get cache performance statistics.

**Returns:** Cache hits, misses, hit rate, files indexed, etc.

## How It Works

### Lazy Indexing

**All files are indexed lazily on first access:**

1. **Python files:**
   - Parsed with tree-sitter on first read
   - Structure cached to `.auzoom/metadata/`
   - Subsequent reads served from cache (instant)

2. **Non-Python files:**
   - First access at skeleton/summary: Returns full content + generates summary in background
   - First access at full: Returns full content + generates summary in background
   - Subsequent access: Returns cached summary (can request full explicitly)
   - Summary cached to `.auzoom/summaries/`

### Progressive Disclosure

Start with minimal information, drill down only when needed:

```
1. auzoom_read("auth.py")                    # Skeleton: see function names
2. auzoom_read("auth.py", level="summary")   # See docstrings
3. auzoom_read("auth.py", level="full")      # Get full source
```

Saves ~80% tokens on average.

### Cache Strategy

- **Content hashing**: File changes detected via SHA256
- **Persistent**: Cache survives restarts
- **Fast**: 100x+ speedup vs parsing

## Benefits

- **Zero workflow changes**: Works transparently with Claude Code
- **Automatic optimization**: Every file read gets token savings
- **Scalable**: Handles million-line codebases (only parses accessed files)
- **Progressive**: Start small, expand as needed

## File Structure

```
.auzoom/
  index.json                    # File metadata index
  metadata/
    src_auth_py_a3f2b1.json    # Parsed Python file cache
  summaries/
    README_md_8c4d9e.json      # Non-Python file summaries
```

Add to `.gitignore`:
```
.auzoom/
```

## Development

Run tests:
```bash
cd auzoom
PYTHONPATH=src pytest tests/test_mcp_server.py -v
```

Start server manually:
```bash
PYTHONPATH=src python3 -m auzoom.mcp_server
```

## Troubleshooting

**Server not starting:**
- Check `auzoom-mcp` is in PATH: `which auzoom-mcp`
- Try absolute path in config: `"command": "/path/to/auzoom-mcp"`

**Cache issues:**
- Clear cache: `rm -rf .auzoom`
- Check permissions: `.auzoom` directory should be writable

**Parse errors:**
- Python files fall back to full content if parse fails
- Check logs in stderr
