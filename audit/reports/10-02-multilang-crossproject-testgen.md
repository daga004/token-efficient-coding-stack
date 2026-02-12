# Plan 10-02: Multi-Language, Cross-Project Learning, Test Generation Assessment

**Date**: 2026-02-12
**Lens**: Portability, ease of use, Claude Code skill chainability

---

## Item 4: Multi-Language Tree-Sitter Support

### Description
Extend tree-sitter parsing beyond Python to JavaScript/TypeScript, Go, Rust, Java, etc. Enable progressive disclosure (skeleton/summary/full) for all languages.

### Current State
- Python: Full tree-sitter parsing (skeleton/summary/full levels)
- Non-Python: Enhanced metadata extraction (Phase 9 - regex-based imports/exports)
- tree-sitter grammars available for most languages

### Assessment

**Portability Impact**: POSITIVE (with caveats)
- tree-sitter grammars are installable via pip
- Each language adds ~5-10MB binary grammar
- Python-only limits usefulness for JS/TS/Go/Rust projects
- **Critical for universal skill adoption**

**Ease of Use Impact**: HIGH POSITIVE
- Users working in JS/TS/Go/Rust get same progressive disclosure
- Currently these users get regex-based metadata only (4.0/5 usefulness)
- Full tree-sitter would give 4.5-5.0/5 usefulness
- **Most requested feature for non-Python developers**

**Skill Chainability Impact**: HIGH POSITIVE
- Claude Code is used across all languages
- A skill that only works well for Python limits adoption
- Multi-language support makes the skill universally valuable

**Is it V1 Critical?**
- Does it break core assumptions? NO - Python progressive disclosure works
- Does it block the skill from working? PARTIALLY - limits value for non-Python projects
- Does it affect adoption? YES - language coverage drives skill adoption

### Verdict

**Category**: V1.1-Important
**Severity**: MEDIUM
**Blocker**: NO (but limits adoption)
**Portability Rating**: 4/5 (pip-installable grammars)

**Rationale**: Multi-language support is the single most impactful enhancement for making this a universally useful skill. The Phase 9 regex-based extraction provides adequate metadata (4.0/5) as a bridge. Full tree-sitter parsing for JS/TS (the most common non-Python languages in Claude Code use) should be V1.1 priority. Go/Rust/Java can follow in V2.

**Recommendation**:
- V1: Python tree-sitter + regex metadata for others (current state) ✅
- V1.1: Add tree-sitter for JavaScript/TypeScript (highest impact)
- V2: Add tree-sitter for Go, Rust, Java, C/C++, Ruby

**Effort**: V1.1 JS/TS: ~3-5 days. V2 full: ~2-3 weeks.

---

## Item 5: Cross-Project Learning

### Description
Unified memory across projects for consistent context and preferences. Share patterns, conventions, and learnings between separate codebases.

### Current State
- Not implemented
- Origin unclear (not found in original planning artifacts)
- `evolving-memory-mcp` exists as separate MCP server in repo (submodule)
- Claude Code has its own memory system (`CLAUDE.md`, auto-memory)

### Assessment

**Portability Impact**: COMPLEX
- Requires persistent storage across projects
- Claude Code already has per-project memory (`.claude/` directory)
- Would need shared storage location (filesystem or API)
- Could conflict with Claude Code's own memory management

**Ease of Use Impact**: MARGINAL to NEGATIVE
- Claude Code already handles cross-session memory via `CLAUDE.md`
- Adding another memory system creates confusion
- Users would need to understand two memory systems
- Potential for conflicting recommendations

**Skill Chainability Impact**: NEGATIVE
- Conflicts with Claude Code's built-in memory
- Over-engineers what Claude Code already provides
- Adds state management complexity to a skill that should be stateless

**Is it V1 Critical?**
- Does it break core assumptions? NO
- Does it block the skill from working? NO
- Is it even the right approach? QUESTIONABLE - Claude Code has memory

### Verdict

**Category**: V2-Enhancement (possibly NEVER)
**Severity**: VERY LOW
**Blocker**: NO
**Portability Rating**: 2/5 (state management adds complexity)

**Rationale**: Cross-project learning conflicts with Claude Code's built-in memory system (`CLAUDE.md`, auto-memory directory). Instead of building a separate memory system, the skill should leverage Claude Code's native memory. If cross-project patterns are needed, they belong in `~/.claude/` global memory, not in a separate MCP-managed store.

**Recommendation**: Do not implement as a separate feature. Instead, use Claude Code's built-in memory for cross-project conventions. The `evolving-memory-mcp` submodule should be evaluated separately as an independent tool, not as part of this skill.

---

## Item 6: Automatic Test Generation

### Description
Automatically generate tests from usage patterns. Origin unclear - mentioned in IMPLEMENTATION-PLAN.md and BRIEF.md but not traced to specific requirement.

### Current State
- Not implemented
- Referenced in `token-efficiency-stack/IMPLEMENTATION-PLAN.md` line 142
- Referenced in `token-efficiency-stack/BRIEF.md` line 52
- No design or architecture exists

### Assessment

**Portability Impact**: NEUTRAL
- Test generation is a pure software task
- Would use existing tree-sitter parsing
- No hardware or platform dependencies

**Ease of Use Impact**: POSITIVE (if done well)
- Could be a standalone skill or command
- "Generate tests for this function" is a clear use case
- But this is a SEPARATE feature from progressive disclosure + routing

**Skill Chainability Impact**: SEPARATE CONCERN
- This is a separate skill/capability, not part of progressive disclosure
- Better as a standalone GSD skill or Claude Code command
- Should not be bundled into AuZoom/Orchestrator

**Is it V1 Critical?**
- Does it break core assumptions? NO
- Does it block the skill from working? NO
- Is it even part of this skill? NO - separate concern

### Verdict

**Category**: V2-Enhancement (separate skill)
**Severity**: VERY LOW (for this skill)
**Blocker**: NO
**Portability Rating**: 4/5 (software-only)

**Rationale**: Test generation is a valuable capability but it's a completely separate concern from progressive disclosure and model routing. It should not be bundled into this skill. If implemented, it should be a separate GSD skill (like `/gsd:generate-tests`) that can leverage AuZoom's code understanding but operates independently.

**Recommendation**: Remove from this skill's roadmap entirely. If desired, create as a separate skill. Test generation can use AuZoom's tree-sitter parsing as input but should be its own independent, chainable command.

---

## Additional Items Assessed

### Item 7: Evolving Memory MCP Integration

**Current State**: Submodule in repo (`evolving-memory-mcp/`)
**Category**: V2-Enhancement (possibly NEVER for this skill)
**Rationale**: Same as cross-project learning - conflicts with Claude Code's native memory. Should remain a standalone tool.
**Portability**: 3/5
**Recommendation**: Keep as separate tool. Do not integrate into this skill.

### Item 8: UI/Dashboard for Monitoring

**Current State**: Not implemented, mentioned in WISHLIST-COMPLIANCE.md
**Category**: V2-Enhancement
**Rationale**: A skill should work in the terminal/CLI. Dashboards are nice-to-have but not core. Cost tracking can be done via log files or simple summary commands.
**Portability**: 2/5 (requires web server or desktop app)
**Recommendation**: Defer. Provide simple cost summary via MCP tool instead (e.g., `orchestrator_get_stats`).

### Item 9: Feedback Logging

**Current State**: Not implemented
**Category**: V1.1-Important
**Rationale**: Logging routing decisions to `.orchestrator/feedback.jsonl` is simple, portable, and enables future optimization. Low effort, high value for debugging and iteration.
**Portability**: 5/5 (just file writes)
**Recommendation**: Implement in V1.1. Simple file-based logging, no dependencies.

### Item 10: Configuration File for Orchestrator

**Current State**: Hardcoded thresholds
**Category**: V1.1-Important
**Rationale**: For a portable skill, users need to customize thresholds (e.g., available models, cost limits). Hardcoded values break portability when users have different model access.
**Portability**: 5/5 (JSON/TOML config)
**Recommendation**: Implement in V1.1. Simple config file (JSON or TOML) for model tiers, thresholds, cost limits. Critical for portability across different API subscriptions.

---

## Summary

| Item | Category | Severity | Blocker | Portability | Skill Relevance |
|------|----------|----------|---------|-------------|-----------------|
| Multi-Language Tree-Sitter | V1.1-Important | MEDIUM | NO | 4/5 | HIGH (universal adoption) |
| Cross-Project Learning | V2 (possibly NEVER) | VERY LOW | NO | 2/5 | LOW (conflicts w/ Claude Code) |
| Test Generation | V2 (separate skill) | VERY LOW | NO | 4/5 | NONE (separate concern) |
| Evolving Memory | V2 (possibly NEVER) | VERY LOW | NO | 3/5 | LOW (conflicts w/ Claude Code) |
| UI/Dashboard | V2-Enhancement | VERY LOW | NO | 2/5 | LOW (CLI-first) |
| Feedback Logging | V1.1-Important | LOW | NO | 5/5 | MEDIUM (debugging) |
| Config File | V1.1-Important | LOW | NO | 5/5 | HIGH (portability) |

### Key Insight for Skill Design

**The most impactful V1.1 items are the most boring ones:**
1. **Config file** (portability across environments)
2. **Multi-language JS/TS** (universal adoption)
3. **Feedback logging** (debugging and iteration)

The flashy features (cross-project learning, test generation, UI dashboards) are either separate concerns, conflicts with Claude Code's built-in capabilities, or anti-portable.

### Design Principle: Skill = Focused + Portable + Chainable

A great Claude Code skill:
- Does ONE thing well (progressive disclosure + routing)
- Works everywhere (no hardware assumptions)
- Chains with other tools (GSD, Claude Code memory, MCP)
- Has minimal configuration (sensible defaults, optional config)

---

**Assessment Date**: 2026-02-12
**Assessor Context**: V1 skill portability and chainability focus
