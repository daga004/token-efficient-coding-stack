# Token-Efficient AI Coding Stack

## What This Is

A unified system that dramatically reduces Claude Code token costs (~82%) while maintaining code quality through three integrated layers: GSD (workflow orchestration), AuZoom (context compression via hierarchical code navigation), and Hierarchical Orchestrator (intelligent model routing based on task complexity). The system intercepts code file reads and intelligently routes tasks between local models, Haiku, and Sonnet.

## Core Value

AuZoom working end-to-end: code compression via skeleton/summary/full views integrated with GSD's execution flow.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] AuZoom MCP server intercepting code file reads
- [ ] Three fetch levels (skeleton/summary/full) working for Python files
- [ ] Orchestrator routing simple tasks to Haiku/local, complex to Sonnet
- [ ] Both tools integrated with GSD's execution flow
- [ ] Measured token reduction ≥50% on real coding tasks
- [ ] Measured cost reduction ≥70% vs all-Sonnet baseline
- [ ] Tree-sitter Python parser extracting functions, classes, methods, imports, dependencies
- [ ] MCP tools exposed: `auzoom_get_graph`, `auzoom_find`, `auzoom_get_dependencies`
- [ ] Orchestrator complexity scoring and model dispatch
- [ ] Validation checkpoint using Sonnet (max 100 token output)
- [ ] Feedback logging to `.orchestrator/feedback.jsonl`

### Out of Scope

- Evolving-memory integration — deferred to V2, focus on core compression and routing first
- Cross-language support beyond Python — start with Python-only, expand once validated
- Cross-project learning — deferred to V2
- Automatic test generation — deferred to V2
- UI/dashboard for monitoring — command-line only for V1

## Context

### Prior Work
- AuZoom specification completed in prior Claude.ai conversation: "Reducing AI agent token usage through selective code parsing"
- Orchestrator design completed in prior Claude.ai conversation: "Adaptive model selection framework for cost-optimized AI agents"
- GSD methodology installed and functional
- Existing documentation: BRIEF.md, ROADMAP.md, STATE.md, and initial phase plans in token-efficiency-stack folder

### Technical Approach
- **AuZoom Core**: Python MCP server using Tree-sitter for parsing, three fetch levels with mandatory navigation (no bypass to full file reads)
- **Orchestrator Core**: Rule-based complexity scoring (0-10 scale), model dispatch to local Ollama/Haiku/Sonnet, Sonnet validation checkpoint
- **Integration**: AuZoom intercepts `@file` references in GSD PLAN.md, Orchestrator wraps GSD's subagent execution

### Documentation Philosophy
- Minimize documentation creation (token-intensive)
- Update existing docs over creating new files
- No proactive/automatic documentation unless requested
- Keep summaries concise and actionable

### Token Efficiency Principles
- Every file read is a cost decision
- Skeleton before summary before full
- Cheap models for simple tasks, expensive for validation
- Fresh contexts over accumulated state

## Constraints

- **Environment**: Mac M4 mini, 64GB RAM
- **Local models**: LM Studio available on dhiraj@dhirajs-mac-min, Qwen3-30B-A3B and Qwen2.5-Coder-32B via Ollama
- **API access**: Anthropic (Haiku/Sonnet/Opus), Cerebras (GLM 4.7)
- **Framework**: MCP (Model Context Protocol) for tool integration
- **Workflow**: GSD methodology — atomic plans (2-3 tasks each), fresh subagent contexts
- **Language focus**: Python-only for V1

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Start with Python-only for AuZoom | Validate core concept before multi-language complexity | — Pending |
| Tree-sitter over ast module | Multi-language support path, even if starting with Python | — Pending |
| MCP as integration layer | Standard protocol for Claude Code tool integration | — Pending |
| Rule-based complexity scoring | Simpler than ML, good enough for V1 validation | — Pending |
| AuZoom as top priority | Core value - compression enables everything else | — Pending |

---
*Last updated: 2026-01-08 after initialization*
