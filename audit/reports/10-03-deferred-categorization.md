# Plan 10-03: Deferred Work Final Categorization

**Date**: 2026-02-12
**Assessment Lens**: Portability, ease of use, Claude Code skill chainability

---

## Complete Deferred Item Inventory

### 21 Items Assessed, 3 Categories

---

## Category 1: V1-Critical (Must Fix for V1)

### NONE

No deferred items are V1 blockers. All core functionality works:
- ✅ Progressive disclosure (Python: tree-sitter, Non-Python: enhanced metadata)
- ✅ Model routing (complexity scoring → tier selection)
- ✅ MCP server integration (AuZoom + Orchestrator)
- ✅ GSD workflow compatibility

**Implication**: V1 can ship as a portable skill without implementing any deferred items.

---

## Category 2: V1.1-Important (Enhance for Adoption)

### Priority Order (by impact on portability and adoption):

| # | Item | Impact | Effort | Portability |
|---|------|--------|--------|-------------|
| 1 | **Configuration File** | Users can customize models/thresholds | 1 day | 5/5 |
| 2 | **Multi-Language JS/TS** | Doubles target audience | 3-5 days | 4/5 |
| 3 | **Feedback Logging** | Enables debugging and iteration | 0.5 days | 5/5 |
| 4 | **Escalation Matrix** | Better error recovery | 2-3 days | 4/5 |

**Total V1.1 Effort**: ~7-10 days

**Why These Matter**:

1. **Configuration File**: A portable skill MUST let users configure which models they have access to. Not everyone has Gemini Flash or Opus access. Hardcoded tiers break portability.

2. **Multi-Language JS/TS**: Claude Code users work in JavaScript/TypeScript as much as Python. Adding tree-sitter-javascript/typescript doubles the skill's value.

3. **Feedback Logging**: Simple `.jsonl` logging of routing decisions enables users to understand and trust the tool. Essential for a production skill.

4. **Escalation Matrix**: Retry → escalate is a natural extension that improves reliability. Pure logic, no dependencies.

---

## Category 3: V2-Enhancement (Future Quality Improvements)

### Priority Order:

| # | Item | Impact | Effort | Portability | Notes |
|---|------|--------|--------|-------------|-------|
| 5 | Multi-Language Go/Rust/Java | Broader language coverage | 1-2 weeks | 4/5 | After JS/TS proven |
| 6 | Multi-Level Non-Python Disclosure | Outline mode for non-Python | 2-3 days | 5/5 | metadata → outline → full |
| 7 | Incremental Parsing | Performance optimization | 1 week | 5/5 | Only changed nodes |
| 8 | Compression | Cache efficiency | 1-2 days | 5/5 | gzip for large caches |
| 9 | Advanced Query Language | Power user feature | 1 week | 5/5 | Search across metadata |

### Deferred Indefinitely / Separate Concern:

| # | Item | Reason | Recommendation |
|---|------|--------|----------------|
| 10 | Local LLM Integration | Hardware-specific, anti-portable | Optional plugin if ever |
| 11 | Cross-Project Learning | Conflicts with Claude Code memory | Use Claude Code's built-in |
| 12 | Evolving Memory Integration | Conflicts with Claude Code memory | Keep as separate tool |
| 13 | Test Generation | Separate concern entirely | Separate skill if desired |
| 14 | UI/Dashboard | CLI-first, anti-portable | Simple stats command instead |
| 15 | File Watching | Marginal benefit, adds complexity | Hash validation sufficient |
| 16 | Smart Warming | ML prediction, over-engineering | Not needed for skill |
| 17 | Distributed Cache | Team feature, separate concern | Separate tool if needed |
| 18 | Weekly Learning Checkpoints | Automation, separate concern | Separate tool |
| 19 | Gemini Real Execution | API limitation, not feature gap | V1.1 when quota available |
| 20 | Worker+Checker Pattern | Complex, doubles cost | Part of escalation V2 |
| 21 | ASG Visualization | Requires UI, anti-portable | Separate tool if desired |

---

## Legitimacy Assessment

### Properly Deferred (Legitimate V2 items): 15/21

These items are legitimately V2 because:
- They are architecturally separable from core functionality
- Core assumptions work without them
- They would add complexity to an otherwise portable skill
- They are enhancement, not requirement

### Should Have Been V1.1 (Missed but not blocking): 4/21

These items (config file, JS/TS support, feedback logging, escalation matrix) would significantly improve the skill's portability and adoption. They are not blockers but represent the gap between "working tool" and "great portable skill."

### Incorrectly Scoped (Wrong approach entirely): 2/21

- **Cross-project learning**: Should use Claude Code's native memory, not a separate system
- **Test generation**: Should be a separate skill, not bundled

---

## Design Principles for Portable Skill

Based on this assessment, the following principles emerge:

### 1. Cloud-First, Local-Optional
The skill must work with cloud APIs (universally available). Local LLMs are optional for power users who want zero-cost execution.

### 2. Language-Progressive
Start with Python (best support), add JS/TS (V1.1), then other languages (V2). Each addition should be pip-installable tree-sitter grammar, not a new architecture.

### 3. Configuration over Convention
Users should be able to configure available models, cost thresholds, and escalation behavior via a simple config file. Sensible defaults for zero-config startup.

### 4. Leverage Claude Code, Don't Compete
Don't build memory systems, UI dashboards, or features that Claude Code already provides. The skill should complement Claude Code, not duplicate it.

### 5. Focused Scope
Progressive disclosure + model routing. That's it. Test generation, cross-project learning, and dashboards are separate tools. A great skill does one thing well.

### 6. Minimal Dependencies
Stdlib preferred. tree-sitter for parsing. No watchdog, no Redis, no web frameworks. Every dependency is a portability risk.

---

## V1 Skill Readiness Assessment

### What V1 Has (Sufficient for Ship)

| Capability | Status | Quality |
|------------|--------|---------|
| Python progressive disclosure | ✅ Working | 95.1% reduction |
| Non-Python enhanced metadata | ✅ Working | 91.7% reduction |
| Complexity scoring | ✅ Working | Validated |
| Model routing | ✅ Working | 50.7% cost savings |
| MCP server | ✅ Working | Protocol compliant |
| Caching | ✅ Working | Hash-based validation |
| GSD integration | ✅ Working | Skill-chainable |

### What V1 is Missing (Not Blocking)

| Capability | Impact | When |
|------------|--------|------|
| Config file | Users can't customize models | V1.1 |
| JS/TS parsing | Limited to Python projects | V1.1 |
| Feedback logging | No visibility into routing | V1.1 |
| Escalation | No retry on failure | V1.1 |

### Ship Decision

**V1 CAN SHIP** as a portable Claude Code skill with the following scope:
- Python-focused progressive disclosure
- Cloud-based model routing
- Enhanced non-Python metadata
- GSD workflow integration

**V1.1 SHOULD ADD** within 1-2 weeks:
- Configuration file
- JS/TS tree-sitter support
- Feedback logging
- Basic escalation

---

**Assessment Date**: 2026-02-12
