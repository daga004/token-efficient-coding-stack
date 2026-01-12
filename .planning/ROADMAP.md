# Roadmap: Token-Efficient AI Coding Stack - V1 Comprehensive Audit

## Overview

Systematic verification that the Token-Efficient AI Coding Stack implementation aligns with core assumptions (local code indexing with dependency tracking + dynamic model routing), validate all published metrics with real API execution, assess legitimacy of deferred work, and produce actionable gap analysis. The journey progresses from foundational traceability through component-level verification to integration testing and comprehensive reporting.

## Domain Expertise

- ~/.claude/skills/expertise/auzoom-structured-code/SKILL.md

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Audit Foundation & Traceability** - Reconstruct missing documentation and set up audit infrastructure (Complete: 2026-01-12)
- [x] **Phase 2: AuZoom Core Verification** - Verify progressive disclosure and dependency tracking (Complete: 2026-01-12)
- [ ] **Phase 3: AuZoom Structural Compliance** - Verify code follows structural constraints
- [ ] **Phase 4: Orchestrator Core Verification** - Test complexity scoring and model routing
- [ ] **Phase 5: Validation Metrics Re-execution** - Re-run 25 tasks with real APIs
- [ ] **Phase 6: Gemini Flash Real Integration** - Fix CLI and verify actual execution
- [ ] **Phase 7: Small File Overhead Assessment** - Test auto-detect threshold necessity
- [ ] **Phase 8: Non-Python File Handling Audit** - Verify metadata summaries adequacy
- [ ] **Phase 9: Deferred Work Legitimacy Assessment** - Evaluate V2 deferrals
- [ ] **Phase 10: Integration Testing** - End-to-end AuZoom + Orchestrator + GSD
- [ ] **Phase 11: Gap Analysis & Reporting** - Comprehensive findings with severity
- [ ] **Phase 12: Critical Fixes & V1.1 Roadmap** - Address critical gaps and plan next milestone

## Phase Details

### Phase 1: Audit Foundation & Traceability
**Goal**: Reconstruct WISHLIST-COMPLIANCE.md mapping promises to delivery, set up audit infrastructure, establish baseline for verification

**Depends on**: Nothing (first phase)

**Research**: Unlikely (document reconstruction from existing planning files)

**Plans**: 3 plans

Plans:
- [x] 01-01: Reconstruct WISHLIST-COMPLIANCE.md from phase plans and PROJECT.md references (2 min - ea70f96)
- [x] 01-02: Create audit test infrastructure (harness, logging, evidence collection) (4.5 min - 69cf1b6)
- [x] 01-03: Baseline metrics capture (current state before any changes) (8 min - 1a2ecd5, 0cf4baa)

### Phase 2: AuZoom Core Verification
**Goal**: Verify Assumption 1 - local code indexing with function-level dependency tracking reduces full-file reads

**Depends on**: Phase 1

**Research**: Unlikely (testing existing implementation)

**Plans**: 4 plans

Plans:
- [x] 02-01: Test progressive disclosure (skeleton → summary → full) token reduction (2 min - a96adbb, b13d505)
- [x] 02-02: Verify dependency tracking accuracy (auzoom_get_dependencies correctness) (7 min - df66c41, b0e75dd)
- [x] 02-03: Test for bypass behavior (are full reads used when not needed?) (3 min - 48a88ba, bc29ebb)
- [x] 02-04: Measure actual token savings vs claims on real codebases (6 min - 30a9437, 48ed3f4, 08f45c1)

### Phase 3: AuZoom Structural Compliance
**Goal**: Verify implementation follows AuZoom structural constraints (≤50 lines functions, ≤250 lines modules, ≤7 files per directory)

**Depends on**: Phase 2

**Research**: Unlikely (auditing existing code structure)

**Plans**: 3 plans (1/3 complete)

Plans:
- [x] 03-01: Run auzoom_validate on entire codebase, document violations (3 min - 19aa969, 8c1cfa6)
- [ ] 03-02: Assess if violations impact claimed benefits (does non-compliance hurt token savings?)
- [ ] 03-03: Create synthesis report with recommendations for critical fixes vs acceptable deviations

### Phase 4: Orchestrator Core Verification
**Goal**: Verify Assumption 2 - dynamic model routing based on task difficulty uses appropriate models

**Depends on**: Phase 1

**Research**: Unlikely (testing existing complexity scorer)

**Plans**: 3 plans

Plans:
- [ ] 04-01: Test complexity scorer accuracy (do scores match actual task difficulty?)
- [ ] 04-02: Verify model routing appropriateness (simple→Haiku, complex→Sonnet, critical→Opus)
- [ ] 04-03: Quality maintenance check (no degradation across model tiers)

### Phase 5: Validation Metrics Re-execution
**Goal**: Re-run all 25 validation tasks with real API calls to verify 79.5% savings and 100% quality claims

**Depends on**: Phase 2, Phase 4

**Research**: Unlikely (executing existing test suite)

**Plans**: 4 plans

Plans:
- [ ] 05-01: Re-execute 10 simple tasks (complexity 0.5-5.5) with actual Claude API
- [ ] 05-02: Re-execute 15 challenging tasks (complexity 4.5-8.5) with actual Claude API
- [ ] 05-03: Compare results to claimed metrics (79.5% cost savings, 100%/67% quality)
- [ ] 05-04: Identify measurement methodology errors or biases

### Phase 6: Gemini Flash Real Integration
**Goal**: Replace theoretical Gemini costs with actual CLI execution and recalculate savings

**Depends on**: Phase 5

**Research**: Likely (Gemini CLI integration patterns, current API)

**Research topics**: Gemini CLI command structure, model names (gemini-2.5-flash vs gemini-flash), authentication flow, token counting in CLI output

**Plans**: 3 plans

Plans:
- [ ] 06-01: Fix GeminiClient CLI command structure (replace non-existent "generate" subcommand)
- [ ] 06-02: Test actual Gemini execution with token/cost measurement
- [ ] 06-03: Recalculate validation savings with real Gemini data (update from theoretical)

### Phase 7: Small File Overhead Assessment
**Goal**: Verify if auto-detect file size threshold is critical for V1 or legitimately V2

**Depends on**: Phase 2, Phase 5

**Research**: Unlikely (analyzing existing validation results)

**Plans**: 2 plans

Plans:
- [ ] 07-01: Analyze tasks 2.1, 3.1, 4.1 where token increases occurred
- [ ] 07-02: Determine if file size heuristics are Critical (breaks assumptions) or Enhancement (optimization)

### Phase 8: Non-Python File Handling Audit
**Goal**: Verify metadata approach for non-Python files meets "progressive discovery of context" claim

**Depends on**: Phase 2

**Research**: Unlikely (testing existing FileSummarizer implementation)

**Plans**: 2 plans

Plans:
- [ ] 08-01: Test metadata summaries on real non-Python files (markdown, JSON, config)
- [ ] 08-02: Assess if metadata provides sufficient context reduction vs full reads

### Phase 9: Deferred Work Legitimacy Assessment
**Goal**: Evaluate all deferred V2 items to determine proper deferral vs missing critical functionality

**Depends on**: Phase 1

**Research**: Unlikely (analyzing planning decisions and rationale)

**Plans**: 3 plans

Plans:
- [ ] 09-01: Assess local LLM integration (Qwen3), escalation matrix, file watching
- [ ] 09-02: Assess multi-language support, cross-project learning, test generation
- [ ] 09-03: Categorize each: V1-Critical / V1.1-Important / V2-Enhancement

### Phase 10: Integration Testing
**Goal**: End-to-end testing of AuZoom + Orchestrator + GSD workflow for conflicts and correctness

**Depends on**: Phase 2, Phase 4

**Research**: Unlikely (testing existing integration)

**Plans**: 3 plans

Plans:
- [ ] 10-01: Test full workflow (GSD plan → AuZoom file read → Orchestrator route → execution)
- [ ] 10-02: Test for conflicts (caching, model selection, file access coordination)
- [ ] 10-03: Verify MCP protocol compliance (v2024-11-05) and error handling

### Phase 11: Gap Analysis & Reporting
**Goal**: Comprehensive findings report with evidence, severity classification, and proposed fixes

**Depends on**: All verification phases (2-10)

**Research**: Unlikely (synthesizing audit findings)

**Plans**: 2 plans

Plans:
- [ ] 11-01: Create gap report (Expected vs Actual, evidence, file/line references)
- [ ] 11-02: Classify gaps (Critical/Important/Enhancement) with proposed fixes

### Phase 12: Critical Fixes & V1.1 Roadmap
**Goal**: Address gaps classified as Critical and define V1.1 milestone based on Important gaps

**Depends on**: Phase 11

**Research**: Unlikely (implementing fixes for identified gaps)

**Plans**: 3 plans

Plans:
- [ ] 12-01: Implement Critical fixes (breaks core assumptions, must fix for V1)
- [ ] 12-02: Test fixes verify assumptions now hold
- [ ] 12-03: Define V1.1 roadmap with Important gaps and properly-deferred V2 items

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Audit Foundation & Traceability | 3/3 | Complete | 2026-01-12 |
| 2. AuZoom Core Verification | 4/4 | Complete | 2026-01-12 |
| 3. AuZoom Structural Compliance | 0/2 | Not started | - |
| 4. Orchestrator Core Verification | 0/3 | Not started | - |
| 5. Validation Metrics Re-execution | 0/4 | Not started | - |
| 6. Gemini Flash Real Integration | 0/3 | Not started | - |
| 7. Small File Overhead Assessment | 0/2 | Not started | - |
| 8. Non-Python File Handling Audit | 0/2 | Not started | - |
| 9. Deferred Work Legitimacy Assessment | 0/3 | Not started | - |
| 10. Integration Testing | 0/3 | Not started | - |
| 11. Gap Analysis & Reporting | 0/2 | Not started | - |
| 12. Critical Fixes & V1.1 Roadmap | 0/3 | Not started | - |
