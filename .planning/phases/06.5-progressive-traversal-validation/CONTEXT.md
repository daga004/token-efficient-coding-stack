# Phase 6.5 Context: Progressive Traversal & Graph Navigation Validation

**Created**: 2026-01-13 (inserted post-Phase 5 audit findings)
**Priority**: CRITICAL - Core feature validation gap identified

---

## User's Intent (Clarified 2026-01-13)

**What AuZoom should be**:
> "An interface which discloses when user pings only the top-level, and the tree is traversed based on the need and the request. In the initial case, the system only has a look at the map of the graph of the codebase which is relevant for the context."

**Progressive traversal workflow**:
```
User: "Find score_task function"
System: Reads skeleton (graph overview) → locates function
User: "What does it do?"
System: Reads summary (function signature + docstring)
User: "Show implementation"
System: Reads full code

Progressive: 150 + 1,125 + 450 = 1,725 tokens
vs. Upfront full read: 450 tokens
```

**Key insight**: May use MORE tokens but provide better **context control** and **UX**.

---

## Gap Identified in Phase 5

**What Phase 5 validated**:
- ✅ Skeleton vs full (static choice)
- ✅ Summary vs full (static choice)
- ✅ Cost savings from model routing

**What Phase 5 DID NOT validate**:
- ❌ **Progressive traversal** (skeleton → ask → summary → ask → full)
- ❌ **On-demand depth selection** (when to go deeper?)
- ❌ **Graph navigation** (traverse dependencies as needed)
- ❌ **Conversation overhead** (follow-up requests add tokens)
- ❌ **Context efficiency** (does progressive save tokens given overhead?)

**Critical finding**: Phase 5 measured static level requests, not interactive progressive traversal—the **core innovation**.

---

## Why This Phase is Critical

1. **Core feature unvalidated**: Progressive traversal is the key value proposition
2. **Phase 5 limitations**: Small file overhead (-655%) suggests static level selection insufficient
3. **User intent mismatch**: Current validation doesn't match described progressive workflow
4. **V1 blocker**: Can't certify V1 without validating core feature works as intended

**Without this validation**: We don't know if progressive traversal delivers value or just adds overhead.

---

## Validation Questions

### Question 1: Interaction Pattern Analysis
**Do agents naturally traverse progressively, or do they immediately request full depth?**

Hypothesis: Agents will start shallow (skeleton) and go deeper only when needed.

Success criteria:
- Average depth < 2.0 (most stay at skeleton/summary)
- ≥60% of tasks don't require full read
- Progressive saves tokens despite conversation overhead

---

### Question 2: Progressive vs Upfront Efficiency
**Does progressive traversal save tokens when accounting for conversation overhead?**

Hypothesis: Conversation overhead (follow-up requests) offsets single-level token savings.

Success criteria:
- Net savings ≥20% (progressive vs upfront full read)
- OR: Net savings ≥0% with measurably better UX (acceptable trade-off)

---

### Question 3: Graph Navigation Value
**Does dependency graph traversal reduce file reads vs. blind exploration?**

Hypothesis: Graph-guided navigation reads 30-50% fewer files than traditional grep-based search.

Success criteria:
- Files read reduced by ≥30%
- Quality maintained at 100% (no missed dependencies)
- Token savings ≥40% on multi-file tasks

---

### Question 4: Context-Aware Depth Selection
**Can the system correctly determine when to go deeper?**

Hypothesis: Orchestrator/agent can select appropriate depth with ≥80% accuracy.

Success criteria:
- Depth selection accuracy ≥80%
- False negatives ≤10% (stayed shallow when needed depth → quality loss)
- False positives ≤30% (went deeper than needed → wasted tokens)

---

## Methodology: Real Execution Required

**Critical difference from Phase 5**:
- Phase 5: File measurements with static level estimates
- Phase 6.5: **Real Claude Code Task tool execution** with actual MCP progressive reads

**What this means**:
1. Spawn agents via Task tool
2. Agents use auzoom_read MCP naturally (not simulated)
3. Measure actual token consumption from API usage
4. Log interaction patterns (how many follow-ups, depth progression)
5. Compare to baseline (traditional Read tool approach)

**Why real execution**:
- Progressive traversal is about **interaction patterns**
- Can't simulate "when agent decides to go deeper"
- Need actual conversation overhead measurements
- Need real graph navigation behavior

---

## Test Tasks

**Select 10 tasks covering different traversal patterns**:

1. **Shallow tasks** (skeleton sufficient):
   - "List all public functions in scorer.py"
   - "Show module structure of orchestrator/"

2. **Medium depth tasks** (summary sufficient):
   - "What does score_task function do?"
   - "Find all imports in auzoom_read.py"

3. **Deep tasks** (full read required):
   - "Fix bug in token counting logic"
   - "Implement retry with backoff in executor.py"

4. **Graph navigation tasks**:
   - "Find all callers of score_task"
   - "Fix circular import between scorer.py and executor.py"

5. **Multi-file tasks**:
   - "Rename orchestrator.py to router.py and update imports"
   - "Extract validation logic to separate module"

**Task distribution**:
- 2 shallow (20%)
- 3 medium (30%)
- 3 deep (30%)
- 2 graph navigation (20%)

---

## Success Criteria

**Phase 6.5 succeeds if**:
1. Progressive traversal delivers ≥20% net token savings vs upfront OR measurably better UX
2. Graph navigation reduces file reads by ≥30% vs baseline
3. Quality maintained at 100% (no regressions from progressive approach)
4. Depth selection accuracy ≥80%

**If Phase 6.5 fails**:
- Progressive traversal adds overhead without benefit
- Recommendation: Default to full read for small files, progressive only for large
- V1 revision: Change claims from "progressive disclosure" to "graph-based navigation"

---

## Dependencies

**Requires**:
- Phase 5 complete ✅ (methodology baseline established)
- Real Claude Code Task tool available ✅
- auzoom MCP server functional ✅

**Blocks**:
- Phase 7 (formerly Phase 6): Gemini Flash integration
- Phase 12: Final certification

**Rationale for insertion**: Must validate core feature before other enhancements. If progressive traversal doesn't work, other validations may be moot.

---

## References

- Phase 5 synthesis: Claims partially refuted, small file overhead identified
- User clarification (2026-01-13): Progressive on-demand traversal is intended design
- Phase 2 findings: Dependency tracking 100% accurate (graph navigation foundation solid)

---

**Phase 6.5 validates the CORE VALUE PROPOSITION**: Progressive on-demand depth traversal with graph-guided navigation.

Without this validation, V1 certification is incomplete.
