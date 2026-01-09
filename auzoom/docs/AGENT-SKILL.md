# 🐱 AuZoom Agent Skill

## 🚨 Rule 1: No Direct File Reads

**All code file reads go through AuZoom.**

| Blocked | Required |
|---------|----------|
| `view()`, `cat`, `read_file` | `auzoom_get_graph()` |
| `grep` | `auzoom_find()` |

```python
# ❌ NEVER
view("src/auth/service.py")

# ✅ ALWAYS
auzoom_get_graph("src/auth/service.py", fetch_level="skeleton")
```

**Scope:** `.py`, `.js`, `.ts`, `.go`, `.rs`, `.java` → AuZoom
**Exempt:** `.json`, `.yaml`, `.md`, `.txt`, config files → Standard read

---

## Rule 2: Start at Skeleton, Zoom Only When Needed

| Level | Tokens | When |
|-------|--------|------|
| `skeleton` | ~15/node | Exploring, finding, tracing deps |
| `summary` | ~75/node | Name unclear, need params |
| `full` | ~400/node | Ready to modify |

```python
# Step 1: See structure
auzoom_get_graph(node_id="root", depth_down=2, fetch_level="skeleton")

# Step 2: Check impact before changes
auzoom_get_dependencies(node_id="target", direction="incoming")

# Step 3: Get code ONLY for what you'll modify
auzoom_get_graph(node_id="target", fetch_level="full")
```

---

## Rule 3: Enforce Standards When Writing

You are the quality gate. Bad code = useless AuZoom.

### Banned Names

| Type | Banned | Required |
|------|--------|----------|
| Module | `utils.py`, `helpers.py`, `common.py` | `string_utils.py`, `date_helpers.py` |
| Function | `process()`, `handle()`, `run()` | `process_payment()`, `handle_webhook()` |
| Class | `Manager`, `Service`, `Handler` | `OrderManager`, `PaymentService` |
| Variable | `data`, `temp`, `result`, `x` | `user_data`, `cached_value` |

### Size Limits

| Unit | Warning | Error |
|------|---------|-------|
| Function | >40 lines | >50 lines |
| Module | >200 lines | >250 lines |
| Class | >150 lines | >200 lines |
| Directory | >7 modules | >10 modules |

### After Every Change

```python
auzoom_validate(scope="changed/files")  # Fix violations before commit
```

---

## Navigation Patterns

### Find Relevant Code
```python
auzoom_find(query="auth.*login", fetch_level="skeleton")
```

### Trace Dependencies
```python
auzoom_get_dependencies(node_id="func", direction="incoming", depth=2)
```

### Visualize Structure
```python
auzoom_visualize(node_id="module/", depth_down=2, format="mermaid")
```

### Debug Changes
```python
auzoom_list_snapshots(limit=5)
auzoom_visualize_diff(from_snapshot="previous", to_snapshot="latest")
```

---

## Token Budget

| Task | Cost |
|------|------|
| Explore codebase | 300-500 |
| Find relevant code | 200-400 |
| Understand function | 50-100 |
| Modify function | 300-600 |
| **Typical task** | **700-1500** |
| Without AuZoom | 10,000-20,000 |

---

## Migrating Legacy Code

**Test-driven restructuring:**

1. **Capture** - Write tests for all current behaviors
2. **Analyze** - `auzoom_validate(scope="all")` → find violations
3. **Restructure** - AI rewrite to AuZoom standards, one module at a time
4. **Verify** - Tests pass after each change

### Migration Prompt Template
```
Migrate this code to AuZoom standards:
[code]

Requirements:
- Preserve behavior (tests must pass)
- verb_object function names
- EntityRole class names  
- domain_responsibility module names
- Functions ≤50 lines, modules ≤250 lines
```

---

## Anti-Patterns

| ❌ Don't | ✅ Do |
|----------|-------|
| Fetch full file to "understand" | Use skeleton, read deps |
| Modify without checking callers | `get_dependencies(direction="incoming")` first |
| Search then read all results | Search skeleton, pick one, then full |
| Write generic names | Write self-documenting names |

---

## Quick Reference

```python
# Navigate
auzoom_get_graph(node_id, depth_up, depth_down, fetch_level)
auzoom_get_dependencies(node_id, direction, depth, fetch_level)
auzoom_find(query, fetch_level, limit)

# Visualize
auzoom_visualize(node_id, depth_down, format)
auzoom_visualize_diff(from_snapshot, to_snapshot)

# History
auzoom_list_snapshots(limit)
auzoom_diff_snapshots(from_snapshot, to_snapshot)

# Validate
auzoom_validate(scope)
auzoom_index(path)
```

---

## Philosophy

```
Names = Documentation
Dependencies = Architecture
Code = Implementation detail (fetch last)
Your code quality = Future token savings
```

*🐱 "Because curiosity shouldn't cost you 10,000 tokens"*
