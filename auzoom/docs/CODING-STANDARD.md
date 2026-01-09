# AuZoom Coding Standard

> Every code unit should be navigable by description alone.

## Size Limits

| Unit | Warning | Error | Why |
|------|---------|-------|-----|
| Function | >40 lines | >50 lines | Single fetch ~400 tokens |
| Class | >150 lines | >200 lines | Methods individually fetchable |
| Module | >200 lines | >250 lines | Fits in context if needed |
| Directory | >7 modules | >10 modules | Working memory limit |
| Nesting | - | >3 levels | Graph complexity |

## Structure

### Module Template
```python
"""One-line purpose.

Extended description. When would you import this?

Exports: ClassName, function_name
Dependencies: external_lib, sibling_module
"""
# Imports: stdlib, external, internal (absolute only)
# Constants
# Types/dataclasses  
# Public exports
# Private helpers (_prefixed)
```

### Class Template
```python
class UserService:
    """Manages user lifecycle.
    
    Collaborators: UserRepository, EmailService
    State: Stateless (all in DB)
    Thread Safety: Safe
    """
```

### Function Template
```python
def validate_credentials(email: str, password: str) -> bool:
    """Verify user login credentials.
    
    Args: email, password
    Returns: True if valid
    Raises: ValidationError
    Depends-on: UserRepository.find_by_email, PasswordHasher.verify
    Called-by: LoginController.handle_login
    """
```

## Naming Rules

### Patterns
| Type | Pattern | Example |
|------|---------|---------|
| Module | `domain_responsibility.py` | `user_authentication.py` |
| Class | `EntityRole` | `UserRepository`, `PaymentGateway` |
| Function | `verb_object` | `validate_user`, `send_email` |
| Boolean | `is_/has_/can_` prefix | `is_active`, `has_permission` |
| Numeric | unit suffix | `timeout_seconds`, `size_bytes` |

### Banned (Generic)
```
Modules:  utils.py, helpers.py, common.py, core.py, base.py
Functions: process(), handle(), run(), do(), execute(), manage()
Classes:  Manager, Handler, Service, Helper (without entity prefix)
Variables: data, items, result, temp, x, y (at module scope)
```

## Validation Errors

| Rule | Trigger |
|------|---------|
| `generic_module` | Module in banned list |
| `generic_function` | Function in banned list (no qualifier) |
| `generic_class` | Class in banned list (no entity prefix) |
| `function_length` | >50 lines |
| `module_length` | >250 lines |
| `nesting_depth` | >3 levels |
| `missing_docstring` | Public function/class without docstring |

## Dependency Documentation

Always include in docstrings:
```python
"""
Depends-on: what this calls
Called-by: what calls this
"""
```

The dependency graph should read like architecture docs:
```
OrderService.submit_order()
  → InventoryService.reserve_items()
  → PaymentGateway.charge_customer()
  → NotificationService.send_confirmation()
```

## Migration Priority

| Priority | Criteria |
|----------|----------|
| P0 | High churn + many violations |
| P1 | High churn OR many violations |
| P2 | Low churn, some violations |
| P3 | Rarely touched |

## Validation

Check compliance via CLI:
```bash
auzoom validate --scope project .
```

Or via MCP server:
```json
{
  "name": "auzoom_validate",
  "arguments": {
    "scope": "project",
    "path": "."
  }
}
```

## Progressive Disclosure Workflow

AuZoom works **alongside** standard tools (Read, Edit, Write):

1. **Explore** - `auzoom_read(path, level="skeleton")` to see structure (~15 tokens/node)
2. **Understand** - `auzoom_read(path, level="summary")` for signatures and docs (~75 tokens/node)
3. **Modify** - `auzoom_read(path, level="full")` when editing (~400 tokens/node)
4. **Edit** - Use standard `Edit` tool to modify code
5. **Validate** - `auzoom_validate(scope="project")` to check compliance

## Quick Checklist

Before commit:
- [ ] Function names are verb_object
- [ ] Class names are EntityRole
- [ ] No generic names
- [ ] Functions ≤50 lines
- [ ] Module ≤250 lines
- [ ] `auzoom_validate()` passes
