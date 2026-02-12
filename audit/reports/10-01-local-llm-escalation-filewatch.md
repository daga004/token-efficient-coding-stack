# Plan 10-01: Local LLM, Escalation Matrix, File Watching Assessment

**Date**: 2026-02-12
**Lens**: Portability, ease of use, Claude Code skill chainability

---

## Item 1: Local LLM Integration (Qwen3)

### Description
Integrate local LLMs (Qwen3 30B3A via LMStudio) into the orchestrator for cost-effective task execution. Includes multi-tier escalation (local → cloud), hardware-specific config (64GB M4 Mac Mini Pro).

### Current State
- Detailed plan exists (`.planning/LOCAL-LLM-INTEGRATION.md`)
- Phases 2.5-2.8 planned (~18 hours)
- Not implemented

### Assessment

**Portability Impact**: NEGATIVE
- Requires specific hardware (64GB M4 Mac Mini)
- Requires LMStudio installed and configured
- Requires specific local model weights downloaded
- SSH tunneling for remote access adds complexity
- **Cannot be packaged as a portable skill** - environment-specific

**Ease of Use Impact**: MIXED
- Potential for $0 cost execution (positive)
- Adds significant setup burden (negative)
- Requires model management (negative)
- Multiple failure points (connection, memory, model loading)

**Skill Chainability Impact**: NEUTRAL
- Architecturally separable from core orchestrator
- Could be added as optional backend without changing API
- Does not affect existing Claude Code integration

**Is it V1 Critical?**
- Does it break core assumptions? NO - model routing works without local LLMs
- Does it block the skill from working? NO - cloud-only routing is functional
- Does it affect portability? YES NEGATIVELY - ties to specific hardware

### Verdict

**Category**: V2-Enhancement
**Severity**: LOW
**Blocker**: NO
**Portability Rating**: 1/5 (hardware-dependent)

**Rationale**: Local LLM integration is the antithesis of portability. It requires specific hardware, software, and model management. The current cloud-based routing (Gemini Flash → Haiku → Sonnet → Opus) is universally portable and works out of the box. Local LLM should be an optional plugin for power users, not a V1 requirement.

**Recommendation**: Defer to V2. If added later, implement as optional backend that auto-detects LMStudio availability. Core skill must work without it.

---

## Item 2: Escalation Matrix

### Description
Multi-tier escalation chains per task type. Worker + checker pattern with retry logic and cost guards. Four task type categories (Quick Edits, Standard Dev, Complex Architecture, Critical Tasks).

### Current State
- Design documented in LOCAL-LLM-INTEGRATION.md (lines 76-110)
- Not implemented
- Currently: Simple complexity score → model tier mapping

### Assessment

**Portability Impact**: NEUTRAL to POSITIVE
- Pure logic (no hardware dependency)
- Could be configured via JSON/YAML
- Enhances the routing experience

**Ease of Use Impact**: MIXED
- More sophisticated routing (positive)
- More configuration complexity (negative)
- Retry logic adds latency for failures (negative)
- Worker+checker doubles token cost on validated tasks

**Skill Chainability Impact**: POSITIVE
- Could enhance GSD workflow integration
- Better error recovery for multi-step tasks
- Compatible with Claude Code Task tool's agent spawning

**Is it V1 Critical?**
- Does it break core assumptions? NO - basic routing works
- Does it block the skill from working? NO
- Does it improve skill quality? YES (better error recovery)

### Verdict

**Category**: V1.1-Important
**Severity**: LOW
**Blocker**: NO
**Portability Rating**: 4/5 (pure logic, configurable)

**Rationale**: The escalation matrix is architecturally sound and portable, but adds complexity beyond what V1 needs. The current simple scoring (complexity → tier) works for the skill's core value proposition. The worker+checker pattern is valuable for production use but not needed to prove the concept.

**Recommendation**: Defer to V1.1. Implement as configurable escalation rules (JSON config). Start with simple retry → escalate pattern. Worker+checker deferred to V2.

---

## Item 3: File Watching for Cache Invalidation

### Description
Use `watchdog` library for real-time file system monitoring to invalidate cache entries when files change. Currently uses passive SHA256-based content hashing.

### Current State
- Mentioned in Phase 1 summaries (01-02-SUMMARY.md)
- Not implemented
- Current approach: Content hash check on access (lazy validation)

### Assessment

**Portability Impact**: SLIGHTLY NEGATIVE
- `watchdog` has platform-specific backends (inotify, fsevents, kqueue)
- Works cross-platform but behavior differs
- Adds dependency (`pip install watchdog`)
- Background daemon adds resource usage

**Ease of Use Impact**: MARGINAL
- Users don't notice cache staleness (hash validation catches it)
- Real-time watching is invisible to user
- Current lazy validation is sufficient for interactive use
- File watching matters more for long-running servers

**Skill Chainability Impact**: NEUTRAL
- Doesn't affect skill interface
- Doesn't change how Claude Code interacts with AuZoom
- Background process management adds operational complexity

**Is it V1 Critical?**
- Does it break core assumptions? NO - hash-based validation ensures correctness
- Does it block the skill from working? NO
- Does it cause correctness issues? NO (hash check on every access)

### Verdict

**Category**: V2-Enhancement
**Severity**: VERY LOW
**Blocker**: NO
**Portability Rating**: 3/5 (cross-platform with caveats)

**Rationale**: The current SHA256 content hashing is both correct and simpler. Every file access validates the hash, so stale cache is impossible. File watching would provide marginal latency improvement (pre-invalidation vs lazy invalidation) at the cost of a background daemon, platform-specific behavior, and an additional dependency. For a portable skill, simpler is better.

**Recommendation**: Defer to V2 or later. Current approach is correct, simple, and portable. File watching adds complexity without meaningful user-facing benefit for a skill-based tool.

---

## Summary

| Item | Category | Severity | Blocker | Portability |
|------|----------|----------|---------|-------------|
| Local LLM (Qwen3) | V2-Enhancement | LOW | NO | 1/5 |
| Escalation Matrix | V1.1-Important | LOW | NO | 4/5 |
| File Watching | V2-Enhancement | VERY LOW | NO | 3/5 |

### Key Insight for Skill Design

**None of these items are needed for a portable, chainable Claude Code skill.** The core value (progressive disclosure + model routing) works today with:
- Cloud-only model routing (universally portable)
- Simple complexity scoring (no escalation needed for V1)
- Hash-based cache validation (correct and dependency-free)

### Portability Principles (from this assessment)

1. **No hardware assumptions**: Skill must work on any machine with Claude Code
2. **Minimal dependencies**: Stdlib > pip packages > system packages
3. **Simple > sophisticated**: Basic routing > escalation matrix for V1
4. **Correct > fast**: Hash validation > file watching for correctness
5. **Cloud-first**: Cloud APIs are universally available; local LLMs are not

---

**Assessment Date**: 2026-02-12
**Assessor Context**: V1 skill portability focus
