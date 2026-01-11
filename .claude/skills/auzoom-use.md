# AuZoom Usage Patterns

**Loaded on-demand**. Return to main skill: `/skills token-efficient-coding`

---

## Progressive Disclosure Strategy

### Level Selection Guide

**Skeleton** (~15 tokens/node):
- First exploration of unknown code
- Finding specific functions/classes by name
- Understanding module structure
- Deciding what to explore next

**Summary** (~75 tokens/node):
- Understanding function purpose (docstrings)
- Checking function signatures
- Reviewing class interfaces
- Planning changes before implementation

**Full** (~400 tokens/node):
- Implementing changes (need exact code)
- Debugging logic errors
- Understanding complex algorithms
- Copying/adapting existing code

### Decision Tree
```
Start → skeleton
├─ Found what I need? → summary (that specific node)
│  └─ Need implementation? → full (just that node)
└─ Not found? → search with auzoom_find
```

---

## Common Workflows

### Workflow 1: "Find and modify function X"
```python
# 1. Locate the file
auzoom_find("function_name")  # Returns file path + node ID

# 2. Read skeleton to confirm location
auzoom_read("path/to/file.py", level="skeleton")

# 3. Read summary of target function only
# (Note: To read specific node, use full file read with summary level)
auzoom_read("path/to/file.py", level="summary")

# 4. Make changes with Edit tool

# 5. Validate structure compliance
auzoom_validate("path/to/file.py", scope="file")
```

### Workflow 2: "Understand module dependencies"
```python
# 1. Get module structure
result = auzoom_read("src/module.py", level="skeleton")

# 2. Pick interesting function, get its node_id from result
# Example: node_id = "/path/to/file.py::ClassName::method_name"

# 3. Explore dependencies
deps = auzoom_get_dependencies(node_id, depth=1)

# 4. Read summaries of dependent nodes
for dep in deps["dependencies"]:
    auzoom_read(dep["file_path"], level="summary")
```

### Workflow 3: "Explore unfamiliar codebase"
```python
# 1. List all Python files
# Use Glob or directory listing first

# 2. Read skeletons of main modules
auzoom_read("src/main.py", level="skeleton")
auzoom_read("src/core.py", level="skeleton")

# 3. Identify entry points, drill down
auzoom_read("src/main.py", level="summary")

# 4. Only read full when necessary for implementation
```

---

## Performance Tips

### Cache Utilization
- **First read**: Parses file (~5ms)
- **Subsequent reads**: From cache (<0.1ms)
- **Cache invalidation**: Automatic on file change (SHA256 hash)

**Tip**: Read skeleton first, then summary/full. Second read is free!

### Token Budget Management
```
File with 10 functions:
- Full read: 10 × 400 = 4,000 tokens
- Skeleton + selective summary: 10 × 15 + 2 × 75 = 300 tokens
- Savings: 13x reduction
```

**Strategy**: Skeleton entire file (cheap), summary only what you need (selective), full rarely (expensive).

---

## Advanced Features

### Search by Pattern
```python
# Find all classes matching pattern
auzoom_find("*Handler")  # Returns all nodes with "Handler" in name

# Find specific function
auzoom_find("process_payment")  # Exact match
```

### Structure Validation
```python
# Validate entire project
auzoom_validate(".", scope="project")
# Returns violations:
# - Functions >50 lines
# - Modules >250 lines
# - Directories >7 files

# Validate single file
auzoom_validate("src/main.py", scope="file")

# Validate directory
auzoom_validate("src/", scope="directory")
```

### Cache Statistics
```python
auzoom_stats()
# Returns:
# - Cache hit rate (aim for >90%)
# - Files indexed
# - Nodes in memory
# - Average parse time
```

---

## Troubleshooting

**Problem**: "File not found"
**Solution**: Use absolute paths or paths relative to project root

**Problem**: "Too many tokens even with skeleton"
**Solution**: File is too large (>250 lines). Validates structure with `auzoom_validate`

**Problem**: "Cache not hitting"
**Solution**: File is being modified between reads. This is expected during editing.

**Problem**: "Can't read non-Python file"
**Solution**: AuZoom generates summaries for non-Python files automatically (Markdown, JSON, etc.)

---

## Integration with Other Tools

### With Edit Tool
```python
# 1. Read skeleton to locate
auzoom_read("file.py", level="skeleton")

# 2. Read summary for context
auzoom_read("file.py", level="summary")

# 3. Edit (normal Edit tool)
Edit(file_path="file.py", old_string="...", new_string="...")

# 4. Validate structure
auzoom_validate("file.py")
```

### With Grep
```python
# AuZoom for structure, Grep for content
# Use auzoom_find for names, Grep for keywords in code

# Example: Find function by name
auzoom_find("authenticate_user")

# Example: Find usage pattern
Grep(pattern="authenticate_user\\(", output_mode="files_with_matches")
```

---

**Remember**: Start with skeleton, drill down progressively. Every token counts!
