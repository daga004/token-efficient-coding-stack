# ROADMAP: Token-Efficient AI Coding Stack

## Milestone: V1.0 — Core Integration

### Phase 1: AuZoom Parser Foundation
**Objective:** Build the code parsing layer that extracts skeleton/summary/full views

**Deliverables:**
- Tree-sitter Python bindings configured
- CodeNode data model implemented
- Parser extracts: functions, classes, methods, imports, dependencies
- Three fetch levels working for Python files

**Verification:** Parse a 500-line Python file, confirm skeleton <50 tokens, summary <200 tokens

**Status:** [ ] Not Started

---

### Phase 2: AuZoom MCP Server
**Objective:** Expose AuZoom as MCP tools Claude Code can call

**Deliverables:**
- MCP server with `auzoom_get_graph`, `auzoom_find`, `auzoom_get_dependencies`
- File read interception for code extensions
- Caching layer for parsed ASTs
- Error handling for unparseable files

**Verification:** Claude Code can call `auzoom_get_graph("src/example.py", "skeleton")` and get response

**Status:** [ ] Not Started

**Depends on:** Phase 1

---

### Phase 3: Orchestrator Core
**Objective:** Build model routing and validation layer

**Deliverables:**
- Complexity scoring function (rule-based, 0-10 scale)
- Model dispatch to: local Ollama, Haiku API, Sonnet API
- Validation checkpoint function (Sonnet, max 100 tokens out)
- Feedback logging to `.orchestrator/feedback.jsonl`

**Verification:** Route 10 sample tasks, confirm scoring matches expected complexity

**Status:** [ ] Not Started

---

### Phase 4: Orchestrator MCP Server
**Objective:** Expose orchestrator as MCP tools

**Deliverables:**
- MCP server with `orchestrator_route`, `orchestrator_execute`, `orchestrator_validate`
- Configuration file for model endpoints and thresholds
- Timeout and fallback handling

**Verification:** Claude Code can call `orchestrator_route("add logging to function")` and get model recommendation

**Status:** [ ] Not Started

**Depends on:** Phase 3

---

### Phase 5: GSD Integration
**Objective:** Wire AuZoom and Orchestrator into GSD's execution flow

**Deliverables:**
- Modified `/run-plan` that uses orchestrator for model selection
- `@file` reference handler that routes through AuZoom
- Context budget calculator based on target model
- SUMMARY.md includes token/cost metrics

**Verification:** Execute a real GSD plan, confirm both tools are invoked

**Status:** [ ] Not Started

**Depends on:** Phase 2, Phase 4

---

### Phase 6: Testing & Tuning
**Objective:** Validate token savings on real workloads, tune thresholds

**Deliverables:**
- Test suite of 10 representative coding tasks
- Before/after token measurements
- Tuned complexity thresholds based on observed quality
- Documented failure cases and mitigations

**Verification:** Achieve ≥50% token reduction, ≥70% cost reduction vs baseline

**Status:** [ ] Not Started

**Depends on:** Phase 5

---

## Phase Summary

| Phase | Name | Est. Plans | Dependencies |
|-------|------|------------|--------------|
| 1 | AuZoom Parser | 3-4 | None |
| 2 | AuZoom MCP | 2-3 | Phase 1 |
| 3 | Orchestrator Core | 2-3 | None |
| 4 | Orchestrator MCP | 2 | Phase 3 |
| 5 | GSD Integration | 2-3 | Phase 2, 4 |
| 6 | Testing & Tuning | 2-3 | Phase 5 |

**Total estimated plans:** 13-18 (at 2-3 tasks each = 26-54 atomic tasks)

## Parallel Tracks

Phases 1-2 (AuZoom) and Phases 3-4 (Orchestrator) can run in parallel:

```
Week 1:  [Phase 1: Parser]     [Phase 3: Orchestrator Core]
Week 2:  [Phase 2: AuZoom MCP] [Phase 4: Orchestrator MCP]
Week 3:  [        Phase 5: Integration        ]
Week 4:  [        Phase 6: Testing & Tuning   ]
```

## Learning Capture

After each phase, document in STATE.md:
- What worked / what didn't
- Threshold adjustments made
- Unexpected issues encountered
- Token/cost measurements

This feeds V2 planning (evolving-memory integration).
