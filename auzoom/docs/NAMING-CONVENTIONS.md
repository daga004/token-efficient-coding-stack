# AuZoom Naming Conventions

> If an agent can't understand a node from its name + dependencies, the name is wrong.

## The Test

Read the dependency graph. Does it tell the story?

```python
# ✅ PASS: Graph is documentation
OrderService.submit_order()
  → InventoryService.reserve_items()
  → PaymentGateway.charge_customer()
  → NotificationService.send_confirmation()

# ❌ FAIL: Graph is useless
Service.process() → Helper.do() → Manager.handle()
```

## Patterns

| Type | Pattern | Good | Bad |
|------|---------|------|-----|
| Module | `domain_responsibility.py` | `user_auth.py` | `utils.py` |
| Class | `EntityRole` | `UserRepository` | `Manager` |
| Function | `verb_object` | `validate_email` | `process` |
| Boolean | `is_/has_/can_` | `is_active` | `active` |
| Numeric | `_unit` suffix | `timeout_seconds` | `timeout` |
| Collection | plural | `users` | `user_list` |

## Banned Names

### Modules
`utils.py`, `helpers.py`, `common.py`, `misc.py`, `core.py`, `base.py`

### Functions (without qualifier)
`process`, `handle`, `run`, `do`, `execute`, `perform`, `manage`, `get`, `set`

### Classes (without entity prefix)
`Manager`, `Handler`, `Service`, `Helper`, `Processor`, `Controller`

### Variables
`data`, `info`, `items`, `result`, `temp`, `value`, `x`, `y` (except coordinates)

## Approved Patterns

### Verbs
| Verb | Returns | Example |
|------|---------|---------|
| `get_` | The value | `get_user_by_id` |
| `find_` | Value or None | `find_user_by_email` |
| `create_` | New entity | `create_order` |
| `validate_` | Bool/raises | `validate_input` |
| `calculate_` | Computed value | `calculate_total` |
| `send_` | None/status | `send_notification` |
| `is_/has_/can_` | Bool | `is_authenticated` |

### Role Suffixes
| Suffix | Meaning |
|--------|---------|
| `Repository` | Data access |
| `Service` | Business logic |
| `Gateway` | External system |
| `Validator` | Validation |
| `Factory` | Object creation |
| `Handler` | Event/request handling |

## Allowed Abbreviations

```
id, url, api, http, json, sql, db, io, os, env, config, auth, 
admin, max, min, num, src, dst, err, msg, req, res
```

## Never Abbreviate

```
usr→user, pwd→password, amt→amount, qty→quantity, calc→calculate,
val→value/validate, mgr→manager, svc→service, impl→implementation
```

## Validation

| Error | Trigger |
|-------|---------|
| `generic_module` | Module in banned list |
| `generic_function` | Banned verb without qualifier |
| `generic_class` | Banned class without entity prefix |
| `missing_bool_prefix` | Boolean without `is_/has_/can_` |
| `missing_units` | Numeric without unit suffix |
