# AuZoom Architecture v0.2

## Core Concept

```
Layer 0 (skeleton): Names + deps        → 15 tokens/node (always present)
Layer 1 (summary):  + docstrings        → 75 tokens/node (on request)
Layer 2 (full):     + source code       → 400 tokens/node (on request)
```

## System Design

```
┌─────────────────────────────────────────────────────────┐
│ MCP Interface: get_graph | find | deps | visualize     │
├─────────────────────────────────────────────────────────┤
│ Query Engine: traversal, tiered fetch, graph render    │
├─────────────────────────────────────────────────────────┤
│ Store (SQLite): nodes, edges, snapshots                │
├─────────────────────────────────────────────────────────┤
│ Parser (tree-sitter): AST extraction, deps detection   │
├─────────────────────────────────────────────────────────┤
│ File Watcher: auto-snapshot on change                  │
└─────────────────────────────────────────────────────────┘
```

## Data Model

```typescript
interface NodeSkeleton {  // Layer 0 - always present
  id: string;             // "src/auth/service.py::AuthService.login"
  name: string;           // "login"
  type: NodeType;         // module|class|function|method
  level: number;          // 0=root, 1=module, 2=class, 3=method
  parent_id: string;
  children_ids: string[];
  depends_on: Edge[];     // outgoing
  depended_by: Edge[];    // incoming
  file_path: string;
  line_start: number;
  line_end: number;
}

interface NodeSummary extends NodeSkeleton {  // Layer 1
  signature?: string;     // "def login(email: str) -> Result"
  summary?: string;       // first line of docstring
  description?: string;   // full docstring
}

interface NodeFull extends NodeSummary {  // Layer 2
  source?: string;        // actual code
}

interface Edge {
  target_id: string;
  target_name: string;
  edge_type: "calls" | "imports" | "inherits" | "uses";
}
```

## File Read Interception

All code reads go through AuZoom:

```python
def intercept_read(path: str) -> str:
    if path.suffix in CODE_EXTENSIONS:
        return auzoom.get_graph(path, level="skeleton")  # redirect
    return standard_read(path)  # allow

CODE_EXTENSIONS = {'.py', '.js', '.ts', '.go', '.rs', '.java', '.cpp'}
```

## MCP Tools

### auzoom_get_graph
```typescript
params: {
  node_id: string;          // or "root"
  depth_up: number;         // levels toward root
  depth_down: number;       // levels toward leaves
  fetch_level: "skeleton" | "summary" | "full";
  include_private: boolean;
}
returns: {
  center: Node;
  ancestors: Node[];
  descendants: Node[];
  edges: Edge[];
}
```

### auzoom_get_dependencies
```typescript
params: {
  node_id: string;
  direction: "incoming" | "outgoing" | "both";
  depth: number;
  fetch_level: FetchLevel;
}
returns: {
  center: NodeSkeleton;
  outgoing: DependencyChain[];
  incoming: DependencyChain[];
}
```

### auzoom_find
```typescript
params: { query: string; type_filter?: NodeType[]; limit: number; }
returns: { matches: Node[]; total_count: number; }
```

### auzoom_visualize
```typescript
params: {
  node_id: string;
  depth_down: number;
  format: "mermaid" | "ascii" | "svg";
  show_docstrings: boolean;
}
returns: { content: string; format: string; }
```

### auzoom_validate
```typescript
params: { scope: string; rules?: string[]; }
returns: {
  summary: { passed: number; warnings: number; errors: number; };
  violations: Violation[];
}
```

### History Tools
```typescript
auzoom_list_snapshots(limit, since?)
auzoom_get_snapshot(snapshot_id, node_id, fetch_level)
auzoom_diff_snapshots(from_snapshot, to_snapshot)
auzoom_visualize_diff(from_snapshot, to_snapshot, format)
auzoom_index(path, recursive?, force?)
```

## Validation Rules

### Naming (Errors)
| Rule | Trigger |
|------|---------|
| `generic_module` | `utils.py`, `helpers.py`, `common.py` |
| `generic_function` | `process()`, `handle()`, `run()` alone |
| `generic_class` | `Manager`, `Service` without prefix |

### Size (Warnings → Errors)
| Unit | Warn | Error |
|------|------|-------|
| Function | >40 | >50 |
| Module | >200 | >250 |
| Class | >150 | >200 |
| Directory | >7 | >10 |

## Storage Schema

```sql
CREATE TABLE nodes (
  id TEXT PRIMARY KEY,
  type TEXT, name TEXT, qualified_name TEXT, level INT,
  parent_id TEXT, signature TEXT, docstring TEXT,
  file_path TEXT, line_start INT, line_end INT
);

CREATE TABLE edges (
  source_id TEXT, target_id TEXT, edge_type TEXT,
  PRIMARY KEY (source_id, target_id, edge_type)
);

CREATE TABLE snapshots (
  id TEXT PRIMARY KEY, timestamp TEXT, trigger TEXT,
  files_changed TEXT, git_commit TEXT
);

CREATE TABLE snapshot_nodes (
  snapshot_id TEXT, node_id TEXT, state TEXT,
  PRIMARY KEY (snapshot_id, node_id)
);
```

## Snapshot System

```
File saved → debounce 2s → snapshot if stable
Snapshot = full AST state + edges + timestamp + git commit
Append-only log, latest = current state
```

## Implementation Phases

| Phase | Components | Duration |
|-------|------------|----------|
| 1 | Parser (tree-sitter) + Store (SQLite) | 1 week |
| 2 | Query engine + MCP server | 1 week |
| 3 | Validation + Visualization | 1 week |
| 4 | File watcher + Snapshots | 1 week |

## Dependencies

```toml
dependencies = [
  "tree-sitter>=0.21", "tree-sitter-python",
  "mcp", "watchdog", "click"
]
```
