# Structural Compliance Validation Report

**Phase 3, Plan 1** — AuZoom Structural Compliance Audit

Generated: 2026-01-12

---

## Executive Summary

**Overall Compliance Rate: 87.32%**

- **Files Checked:** 71
- **Directories Scanned:** 95
- **Total Lines Analyzed:** 10,545
- **Total Violations:** 9
- **Compliant Files:** 62/71

**Violations by Severity:**

- ❌ **Errors:** 9
- ⚠️  **Warnings:** 0

**Violations by Type:**

- `module_too_long`: 9

---

## Detailed Findings

### Module Too Long

**Count:** 9 violations

**Examples:**

- `unified-orchestrator/hierarchical-orchestrator/scripts/unified_mcp_server.py:1`
  - Current: 798 lines | Limit: 250 lines
  - Over limit by: 548 lines (219.2%)

- `unified-orchestrator/hierarchical-orchestrator/scripts/memory.py:1`
  - Current: 346 lines | Limit: 250 lines
  - Over limit by: 96 lines (38.4%)

- `evolving-memory-mcp/src/server.py:1`
  - Current: 878 lines | Limit: 250 lines
  - Over limit by: 628 lines (251.2%)

- `audit/tests/test_real_codebase_savings.py:1`
  - Current: 376 lines | Limit: 250 lines
  - Over limit by: 126 lines (50.4%)

- `audit/tests/test_progressive_disclosure.py:1`
  - Current: 296 lines | Limit: 250 lines
  - Over limit by: 46 lines (18.4%)

*...and 4 more*

---

## Worst Offenders

Top 10 files with largest violations relative to limits:

| File | Line | Type | Current | Limit | Over Limit | % Over |
|------|------|------|---------|-------|------------|--------|
| evolving-memory-mcp/src/server.py | 1 | module | 878 | 250 | 628 | 251.2% |
| .../scripts/unified_mcp_server.py | 1 | module | 798 | 250 | 548 | 219.2% |
| audit/tests/test_bypass_behavior.py | 1 | module | 388 | 250 | 138 | 55.2% |
| audit/tests/test_dependency_tracking.py | 1 | module | 385 | 250 | 135 | 54.0% |
| audit/tests/test_real_codebase_savings.py | 1 | module | 376 | 250 | 126 | 50.4% |
| .../scripts/memory.py | 1 | module | 346 | 250 | 96 | 38.4% |
| auzoom/tests/test_mcp_server.py | 1 | module | 321 | 250 | 71 | 28.4% |
| audit/tests/test_progressive_disclosure.py | 1 | module | 296 | 250 | 46 | 18.4% |
| auzoom/src/auzoom/core/parsing/parser.py | 1 | module | 289 | 250 | 39 | 15.6% |

---

## Compliance by Area

Violations segmented by codebase subsystem:

### Audit

- **Violations:** 4
- **Affected Files:** 4

**By Type:**
- module_too_long: 4

### Auzoom

- **Violations:** 2
- **Affected Files:** 2

**By Type:**
- module_too_long: 2

### Other

- **Violations:** 3
- **Affected Files:** 3

**By Type:**
- module_too_long: 3

---

## Appendix: Complete Violation List

<details>
<summary>Click to expand all violations</summary>

### module_too_long

- `audit/tests/test_bypass_behavior.py:1`
  - Module exceeds 250 lines
  - Current: 388 | Limit: 250

- `audit/tests/test_dependency_tracking.py:1`
  - Module exceeds 250 lines
  - Current: 385 | Limit: 250

- `audit/tests/test_progressive_disclosure.py:1`
  - Module exceeds 250 lines
  - Current: 296 | Limit: 250

- `audit/tests/test_real_codebase_savings.py:1`
  - Module exceeds 250 lines
  - Current: 376 | Limit: 250

- `auzoom/src/auzoom/core/parsing/parser.py:1`
  - Module exceeds 250 lines
  - Current: 289 | Limit: 250

- `auzoom/tests/test_mcp_server.py:1`
  - Module exceeds 250 lines
  - Current: 321 | Limit: 250

- `evolving-memory-mcp/src/server.py:1`
  - Module exceeds 250 lines
  - Current: 878 | Limit: 250

- `unified-orchestrator/hierarchical-orchestrator/scripts/memory.py:1`
  - Module exceeds 250 lines
  - Current: 346 | Limit: 250

- `unified-orchestrator/hierarchical-orchestrator/scripts/unified_mcp_server.py:1`
  - Module exceeds 250 lines
  - Current: 798 | Limit: 250

</details>
