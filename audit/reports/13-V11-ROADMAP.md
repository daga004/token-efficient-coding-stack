# V1.1 Roadmap: Token-Efficient AI Coding Stack

**Phase:** 13 - Critical Fixes & V1.1 Roadmap
**Plan:** 13-03
**Date:** 2026-02-19
**Scope:** Post-V1 roadmap synthesized from audit gaps and deferred feature items

---

## 1. V1 Ship Summary

The V1 audit executed **37 plans across 13 phases** (2 superseded), producing **84+ automated tests** and **60+ evidence records**. The V1 Certification Report (Phase 12-02) issued a **CONDITIONAL GO** verdict with three conditions:

1. Fix GAP-023: Add MCP initialize handshake to AuZoom
2. Fix GAP-024: Add auzoom_get_calls to tool manifest
3. Fix GAP-025: Catch Pydantic ValidationError in Orchestrator

All three conditions were satisfied in **Phase 13-01** (3 min, ~39 lines) and verified in **Phase 13-02** (84/84 tests pass, 0 regressions). V1 is now **CERTIFIED** with the following validated claims:

| Claim | Value | Confidence |
|-------|-------|------------|
| Progressive disclosure token savings | 71.3% | High |
| Graph navigation file read reduction | 71.1% | High |
| Combined token savings (graph + progressive) | 97.6% | High |
| Cost savings vs always-Sonnet | 50.7% | Medium |
| Quality maintenance (simple tasks) | 100% | Medium |
| Non-Python metadata token reduction | 91.7% | High |

---

## 2. V1.1 Scope

V1.1 addresses two tracks of work identified during the V1 audit:

### Track A: Audit Gap Resolution (7 Important Gaps)

These are gaps classified as Important in the V1 Certification Report that affect accuracy, confidence, or documentation quality.

| GAP-ID | Description | Effort |
|--------|-------------|--------|
| GAP-007 | Complexity scorer keyword expansion (40% tier match vs 80% target) | 45 min |
| GAP-008 | Haiku boundary adjustment (3-5 to 3-6, depends on GAP-007) | 10 min |
| GAP-012 | Realistic test suite distribution (70/30 vs current 40/60) | 2 hours |
| GAP-013 | Real Gemini Flash API execution (pricing-based currently) | 1 hour + API costs |
| GAP-014 | Quality validation framework with objective scoring | 15-30 hours |
| GAP-026 | Document cost contribution breakdown (3.0% disclosure + 47.7% routing) | 15 min |
| GAP-027 | Real Claude Code Task execution for definitive validation | 15-30 hours (overlaps GAP-014) |

### Track B: Feature Development (4 V1.1 Items from Phase 10)

These are deferred items assessed in Phase 10 as V1.1-Important for portability and adoption.

| # | Item | Impact | Effort |
|---|------|--------|--------|
| 1 | Configuration file | Users customize models, thresholds, and behavior | 1 day |
| 2 | Multi-language JS/TS tree-sitter | Doubles target audience beyond Python-only | 3-5 days |
| 3 | Feedback logging | Routing decision visibility via .jsonl logs | 0.5 days |
| 4 | Basic escalation matrix | Retry-then-escalate error recovery | 1 day |

---

## 3. Proposed V1.1 Phases

### Phase 1: Quick Wins (1 day)

Low-effort gaps that improve documentation accuracy and scorer precision.

| Task | GAP-ID | Description | Effort | Files |
|------|--------|-------------|--------|-------|
| 1.1 | GAP-026 | Document cost contribution breakdown (disclosure 3.0% + routing 47.7%) | 15 min | README, claims docs |
| 1.2 | GAP-007 | Expand scorer keyword dictionaries (add "diagnose", "extract", "rename", "circular"); lower tier 1 threshold 3.0 to 2.5; boost file_count weight | 45 min | `orchestrator/src/orchestrator/scoring.py` |
| 1.3 | GAP-008 | Adjust Haiku boundary from score range 3-5 to 3-6 based on Phase 4 empirical data | 10 min | `orchestrator/src/orchestrator/registry.py` |

**Success criteria:** GAP-026 documentation published, scorer tier match improved from 40% toward 70%+, Haiku boundary handles scores up to 6.0.

### Phase 2: Configuration & Portability (2 days)

Core portability features that let users customize the skill for their environment.

| Task | Source | Description | Effort | Files |
|------|--------|-------------|--------|-------|
| 2.1 | Phase 10 | Configuration file (`auzoom.toml` or similar) for model names, tier boundaries, cost thresholds, and API keys | 1 day | New config module |
| 2.2 | Phase 10 | Feedback logging (`.jsonl` log of routing decisions, model selections, token counts) | 0.5 days | New logging module |

**Success criteria:** Zero-config startup with sensible defaults; config file overrides all hardcoded values; routing decisions logged to inspectable file.

### Phase 3: Multi-Language Support (3-5 days)

Extend progressive disclosure beyond Python-only.

| Task | Source | Description | Effort | Files |
|------|--------|-------------|--------|-------|
| 3.1 | Phase 10 | Add tree-sitter-javascript and tree-sitter-typescript grammars | 1-2 days | `auzoom/src/auzoom/core/parser.py` |
| 3.2 | Phase 10 | Implement skeleton/summary extraction for JS/TS (function signatures, class outlines, imports/exports) | 2-3 days | New JS/TS parser module |

**Success criteria:** JS/TS files get skeleton/summary/full progressive disclosure levels equivalent to Python; tree-sitter grammars pip-installable.

### Phase 4: Escalation & Routing (1 day)

Improve routing reliability with retry-then-escalate behavior.

| Task | Source | Description | Effort | Files |
|------|--------|-------------|--------|-------|
| 4.1 | Phase 10 | Basic escalation matrix: Flash failure -> retry -> Haiku; Haiku failure -> retry -> Sonnet | 1 day | `orchestrator/src/orchestrator/` |

**Success criteria:** Failed model calls trigger automatic escalation to next tier; escalation logged via feedback logging (Phase 2); max 2 retries per task.

### Phase 5: Validation (2-4 days + API costs)

Strengthen confidence in published claims with real execution data.

| Task | GAP-ID | Description | Effort | Files |
|------|--------|-------------|--------|-------|
| 5.1 | GAP-012 | Create realistic test suite with 70/30 simple/challenging distribution; add tasks where traditional approach excels | 2 hours | `audit/tests/` |
| 5.2 | GAP-013 | Execute real Gemini Flash API tests; measure actual token counts vs 4-char approximation | 1 hour + API costs | `audit/scripts/test_gemini_real.py` |
| 5.3 | GAP-014 + GAP-027 | Real Claude Code Task execution harness for all 25 tasks with objective quality scoring (ISS-002, ISS-003) | 2-4 days + $2-10 API costs | `audit/scripts/`, `audit/tests/` |

**Success criteria:** Test suite matches realistic workload distribution; Gemini costs validated with real API; all 25 tasks executed with real MCP server responses; objective pass/fail quality criteria established.

**Note:** GAP-014 and GAP-027 share the ISS-002 real execution framework. Combined effort is 2-4 days, not 30-60 hours as estimated individually.

### Total V1.1 Effort Estimate

| Phase | Effort | Calendar |
|-------|--------|----------|
| Phase 1: Quick Wins | ~1.5 hours | 1 day |
| Phase 2: Configuration & Portability | ~1.5 days | 2 days |
| Phase 3: Multi-Language Support | ~3-5 days | 5 days |
| Phase 4: Escalation & Routing | ~1 day | 1 day |
| Phase 5: Validation | ~2-4 days | 4 days |
| **Total** | **~10-15 days** | **~13 days** |

---

## 4. V1.1 Success Criteria

V1.1 certification requires:

1. **All 7 Important audit gaps resolved** (GAP-007, GAP-008, GAP-012, GAP-013, GAP-014, GAP-026, GAP-027)
2. **All 4 V1.1 feature items implemented** (config file, JS/TS, feedback logging, escalation)
3. **Scorer tier match accuracy >= 70%** (up from 40%)
4. **Real Gemini API execution validates 50.7% cost savings** (or revises with evidence)
5. **Real Claude Code Task execution validates token savings** (or revises with evidence)
6. **Realistic test suite with 70/30 distribution** passes all claims
7. **JS/TS progressive disclosure** achieves >= 50% token reduction
8. **Configuration file** allows model customization without code changes
9. **All existing 84 tests continue to pass** (no regressions)

---

## 5. V2 Parking Lot

The following Enhancement gaps are deferred to V2 or beyond. None affect V1.1 certification.

| GAP-ID | Description | Effort | Rationale for Deferral |
|--------|-------------|--------|------------------------|
| GAP-003 | Cache hit rate optimization (75% to 90%) | 30 min | Performance optimization; correctness unaffected |
| GAP-006 | Update structural compliance guidelines | 5 min | Documentation clarification only |
| GAP-017 | Update graph ground truth definitions | 15 min | Test data improvement; graph already better than baseline |
| GAP-018 | Re-execute Gemini test harness with fresh quota | 30 min | Subsumed by GAP-013 in V1.1 |
| GAP-020 | Multi-level non-Python disclosure (outline mode) | 2 hours | Current 91.7% reduction is sufficient |
| GAP-028 | Execute all 15 challenging tasks | 15-30 hours | Simple task quality (100%) covers majority use case |
| GAP-029 | Fix parser anomaly for Pydantic model files | 1 hour | Single file affected; edge case |
| GAP-030 | LazyCodeGraph module import resolution | 30 min | Test setup issue only; not production |

### V2 Feature Items (from Phase 10)

| Item | Effort | Notes |
|------|--------|-------|
| Multi-language Go/Rust/Java | 1-2 weeks | After JS/TS proven in V1.1 |
| Multi-level non-Python disclosure | 2-3 days | metadata -> outline -> full |
| Incremental parsing | 1 week | Only re-parse changed nodes |
| Cache compression | 1-2 days | gzip for large caches |
| Advanced query language | 1 week | Search across metadata |

### Deferred Indefinitely (from Phase 10)

Items explicitly excluded from the skill's scope:

- Local LLM integration (hardware-specific, anti-portable)
- Cross-project learning (conflicts with Claude Code memory)
- Evolving memory integration (conflicts with Claude Code memory)
- Test generation (separate concern, separate skill)
- UI/Dashboard (CLI-first, anti-portable)
- File watching (hash validation sufficient)
- Smart warming (over-engineering)
- Distributed cache (team feature, separate concern)

---

## 6. Design Principles

Carried forward from Phase 10-03, these principles guide V1.1 development:

### 1. Cloud-First, Local-Optional
The skill must work with cloud APIs (universally available). Local LLMs are optional for power users.

### 2. Language-Progressive
Start with Python (V1), add JS/TS (V1.1), then other languages (V2). Each addition should be a pip-installable tree-sitter grammar, not a new architecture.

### 3. Configuration over Convention
Users configure available models, cost thresholds, and escalation behavior via a config file. Sensible defaults enable zero-config startup.

### 4. Leverage Claude Code, Don't Compete
Don't build memory systems, UI dashboards, or features that Claude Code already provides. The skill complements Claude Code.

### 5. Focused Scope
Progressive disclosure + model routing. That's it. Test generation, cross-project learning, and dashboards are separate tools. A great skill does one thing well.

### 6. Minimal Dependencies
Stdlib preferred. tree-sitter for parsing. No watchdog, no Redis, no web frameworks. Every dependency is a portability risk.

---

*V1.1 Roadmap generated from V1 audit findings (30 gaps assessed, 84+ tests, 13 phases).*
*V1 Certification: 2026-02-19 | V1.1 Target: ~2 weeks from start*
