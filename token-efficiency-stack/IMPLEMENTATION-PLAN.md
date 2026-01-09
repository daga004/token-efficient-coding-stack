# IMPLEMENTATION PLAN: Token-Efficient AI Coding Stack

## Quick Reference

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXECUTION SEQUENCE                           │
│                                                                 │
│  PARALLEL TRACK A          PARALLEL TRACK B                     │
│  ───────────────          ────────────────                      │
│  Phase 1: Parser    ←→    Phase 3: Scoring                      │
│      ↓                        ↓                                 │
│  Phase 2: AuZoom MCP  ←→  Phase 4: Orchestrator MCP             │
│      └────────────┬───────────┘                                 │
│                   ↓                                             │
│           Phase 5: Integration                                  │
│                   ↓                                             │
│           Phase 6: Testing & Tuning                             │
└─────────────────────────────────────────────────────────────────┘
```

## Phase Details

### Phase 1: AuZoom Parser Foundation (3 plans)

| Plan | Focus | Key Deliverable |
|------|-------|-----------------|
| 01-01 | Data models + Tree-sitter | CodeNode model, Python parser |
| 01-02 | Graph navigation | CodeGraph with fetch levels |
| 01-03 | Multi-file indexing | Index entire directory, handle imports |

**Exit criteria:** Parse 500-line file, skeleton uses <10% of full tokens

---

### Phase 2: AuZoom MCP Server (2 plans)

| Plan | Focus | Key Deliverable |
|------|-------|-----------------|
| 02-01 | MCP server scaffold | Server responds to tool calls |
| 02-02 | File interception | Code file reads redirected to AuZoom |

**Exit criteria:** Claude Code calls `auzoom_get_graph`, gets skeleton response

---

### Phase 3: Orchestrator Core (2 plans)

| Plan | Focus | Key Deliverable |
|------|-------|-----------------|
| 03-01 | Scoring + registry | Complexity 0-10, model selection |
| 03-02 | Execution + validation | Dispatch to models, Sonnet validation |

**Exit criteria:** Route 10 tasks to expected models, validation returns structured feedback

---

### Phase 4: Orchestrator MCP Server (2 plans)

| Plan | Focus | Key Deliverable |
|------|-------|-----------------|
| 04-01 | MCP server scaffold | Server with route/execute/validate tools |
| 04-02 | Fallback + timeout | Handle model failures gracefully |

**Exit criteria:** Claude Code calls `orchestrator_execute`, gets response from routed model

---

### Phase 5: GSD Integration (3 plans)

| Plan | Focus | Key Deliverable |
|------|-------|-----------------|
| 05-01 | @file interception | PLAN.md file refs route through AuZoom |
| 05-02 | Model-aware context | Context budget varies by target model |
| 05-03 | Metrics in SUMMARY | Token/cost tracking in plan outcomes |

**Exit criteria:** `/run-plan` uses both tools, SUMMARY shows token savings

---

### Phase 6: Testing & Tuning (2 plans)

| Plan | Focus | Key Deliverable |
|------|-------|-----------------|
| 06-01 | Benchmark suite | 10 representative tasks, before/after |
| 06-02 | Threshold tuning | Adjust scoring based on quality observations |

**Exit criteria:** ≥50% token reduction, ≥70% cost reduction documented

---

## Execution Commands

```bash
# Start Phase 1
cd /path/to/token-efficiency-stack
# Open in Claude Code, then:
/gsd:execute-plan phases/01-auzoom-parser/01-01-PLAN.md

# After completion, continue:
/gsd:execute-plan phases/01-auzoom-parser/01-02-PLAN.md

# Parallel: Start Phase 3 in separate session
/gsd:execute-plan phases/03-orchestrator-core/03-01-PLAN.md
```

## Learning Capture Protocol

**Principle: Minimal documentation overhead.** Don't create docs proactively—update STATE.md only.

After each plan completion:

1. **Update STATE.md** (append, don't create new files):
   - Decisions made (1-2 lines each)
   - Issues encountered (brief)
   - Threshold adjustments (if any)
   - Token/cost metric (one row in table)

2. **Skip SUMMARY.md unless**:
   - Plan explicitly requires it
   - Major unexpected outcome needs recording
   - You're stopping mid-phase (handoff)

3. **No README, no CHANGELOG, no separate docs** until V1 complete

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Tree-sitter grammar issues | Fall back to Python ast module for Python-only |
| MCP connection failures | Implement retry + fallback to direct file read |
| Local model too slow | Have Haiku as fallback for "local" tier |
| Orchestrator misroutes | Log all routing decisions, tune thresholds in Phase 6 |
| Token estimates inaccurate | Use tiktoken for accurate Claude tokenization |

## V2 Backlog (Post-V1)

Items explicitly deferred:

- [ ] Evolving-memory integration (semantic retrieval of past experiences)
- [ ] Cross-project learning (unified memory across repos)
- [ ] Automatic test generation from usage patterns
- [ ] TypeScript/JavaScript parser (extend AuZoom)
- [ ] Dashboard for token/cost monitoring
- [ ] Weekly learning checkpoint automation

## File Structure After V1

```
token-efficiency-stack/
├── BRIEF.md
├── ROADMAP.md
├── STATE.md
├── phases/
│   ├── 01-auzoom-parser/
│   │   ├── 01-01-PLAN.md
│   │   ├── 01-01-SUMMARY.md  ← created on completion
│   │   ├── 01-02-PLAN.md
│   │   └── ...
│   ├── 02-auzoom-mcp/
│   ├── 03-orchestrator-core/
│   ├── 04-orchestrator-mcp/
│   ├── 05-integration/
│   └── 06-testing/
├── auzoom/                    ← Python package
│   ├── __init__.py
│   ├── models.py
│   ├── parser.py
│   ├── graph.py
│   ├── formatter.py
│   └── mcp_server.py
├── orchestrator/              ← Python package
│   ├── __init__.py
│   ├── scoring.py
│   ├── registry.py
│   ├── executor.py
│   ├── validator.py
│   └── mcp_server.py
└── tests/
    ├── test_auzoom_core.py
    ├── test_orchestrator.py
    └── benchmarks/
```

## Getting Started

1. **Copy this directory** to your working location
2. **Initialize git**: `git init && git add . && git commit -m "Initial planning structure"`
3. **Open in Claude Code**
4. **Execute first plan**: Review `phases/01-auzoom-parser/01-01-PLAN.md`, then `/gsd:execute-plan`
5. **After completion**: Check SUMMARY, update STATE.md, commit, proceed to next plan

The system is designed to be self-documenting. Each plan execution produces a SUMMARY that feeds the next plan's context.
