# PROJECT BRIEF: Token-Efficient AI Coding Stack

## Vision

Build a unified system that dramatically reduces Claude Code token costs (~82%) while maintaining or improving code quality through three integrated layers:

1. **GSD** (existing) — Workflow orchestration, task decomposition, state management
2. **AuZoom** (to build) — Context compression via hierarchical code navigation
3. **Hierarchical Orchestrator** (to build) — Intelligent model routing based on task complexity

## Success Criteria

- [ ] AuZoom MCP server running, intercepting code file reads
- [ ] Orchestrator routing simple tasks to Haiku/local, complex to Sonnet
- [ ] Both tools integrated with GSD's `/run-plan` execution flow
- [ ] Measured token reduction ≥50% on real coding tasks
- [ ] Measured cost reduction ≥70% vs all-Sonnet baseline

## Constraints

- **Environment:** Mac M4 mini, 64GB RAM
- **Local models:** Qwen3-30B-A3B, Qwen2.5-Coder-32B available via Ollama
- **API access:** Anthropic (Haiku/Sonnet/Opus), Cerebras (GLM 4.7)
- **Framework:** MCP (Model Context Protocol) for tool integration
- **Workflow:** GSD methodology—atomic plans, fresh subagent contexts

## Core Principles

### Documentation Minimization
- Minimize documentation creation—it's token-intensive
- Only create summary documents when explicitly necessary
- Update existing docs over creating new files
- No proactive/automatic documentation unless requested
- Ask before creating comprehensive documentation files

**Preferred approach:**
1. Check if existing docs can be updated/extended
2. Keep summaries concise and focused
3. Write documentation only when explicitly asked
4. Prefer brief, actionable information over lengthy explanations

### Token Efficiency First
- Every file read is a cost decision
- Skeleton before summary before full
- Cheap models for simple tasks, expensive for validation
- Fresh contexts over accumulated state

## Non-Goals (V1)

- Evolving-memory integration (deferred to V2)
- Cross-project learning (deferred to V2)
- Automatic test generation (deferred to V2)
- UI/dashboard for monitoring (deferred to V2)

## Technical Approach

### AuZoom Core
- Python MCP server using Tree-sitter for parsing
- Three fetch levels: skeleton (names+deps), summary (+docstrings), full (source)
- File read interception for code files (.py, .js, .ts, etc.)
- Mandatory navigation—no bypass to full file reads

### Orchestrator Core
- Rule-based complexity scoring (0-10 scale)
- Model dispatch based on score thresholds
- Sonnet validation checkpoint (input-heavy, max 100 token output)
- Feedback logging to file (later: memory system)

### Integration Points
- AuZoom intercepts `@file` references in GSD PLAN.md
- Orchestrator wraps GSD's subagent execution
- Both expose MCP tools to Claude Code

## Current State

- AuZoom: Complete specification, data models, agent skill docs (from prior conversation)
- Orchestrator: Complete design doc, routing algorithm, validation protocol (from prior conversation)
- GSD: Installed and functional
- Integration: Not started

## Definition of Done

V1 is complete when:
1. `auzoom_get_graph` returns skeleton/summary/full for any Python file
2. `orchestrator_route` returns model recommendation for any task description
3. `orchestrator_execute` successfully dispatches to Haiku and local Qwen
4. Running `/gsd:execute-plan` on a real plan uses both tools
5. Before/after token counts show measurable improvement
