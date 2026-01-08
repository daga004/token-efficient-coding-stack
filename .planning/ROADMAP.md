# Roadmap: Token-Efficient AI Coding Stack

## Overview

Build a unified system that reduces Claude Code token costs through three integrated layers: AuZoom (context compression via hierarchical code navigation), Hierarchical Orchestrator (intelligent model routing), and GSD integration. The journey starts with AuZoom's parser and MCP server, adds the orchestrator for smart routing, then integrates both into GSD's execution flow with measurable validation.

## Domain Expertise

None

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: AuZoom Implementation** - Build parser foundation + MCP server for hierarchical code navigation
- [ ] **Phase 2: Orchestrator Implementation** - Build routing core + MCP server for intelligent model selection
- [ ] **Phase 3: Integration & Validation** - Wire both into GSD and measure token/cost savings

## Phase Details

### Phase 1: AuZoom Implementation
**Goal**: Build and deploy AuZoom MCP server with tree-sitter parser that provides skeleton/summary/full views of Python code files

**Depends on**: Nothing (first phase)

**Research**: Likely (new technology integration)

**Research topics**: Tree-sitter Python bindings setup, MCP server implementation patterns, AST caching strategies, file read interception

**Plans**: 3 plans

Plans:
- [ ] 01-01: Tree-sitter parser foundation (CodeNode model, extract functions/classes/imports)
- [ ] 01-02: Three fetch levels (skeleton <50 tokens, summary <200 tokens, full source)
- [ ] 01-03: MCP server with tools (auzoom_get_graph, auzoom_find, auzoom_get_dependencies)

### Phase 2: Orchestrator Implementation
**Goal**: Build and deploy Orchestrator MCP server that routes tasks to appropriate models (local/Haiku/Sonnet) based on complexity

**Depends on**: Nothing (parallel with Phase 1)

**Research**: Likely (multiple model APIs)

**Research topics**: Ollama API integration, LM Studio on dhiraj@dhirajs-mac-min, Cerebras API, complexity scoring heuristics, validation checkpoint patterns

**Plans**: 3 plans

Plans:
- [ ] 02-01: Complexity scoring function (rule-based 0-10 scale)
- [ ] 02-02: Model dispatch layer (Ollama, Anthropic Haiku/Sonnet APIs)
- [ ] 02-03: MCP server with tools (orchestrator_route, orchestrator_execute, orchestrator_validate)

### Phase 3: Integration & Validation
**Goal**: Integrate AuZoom and Orchestrator into GSD execution flow and validate ≥50% token reduction, ≥70% cost reduction

**Depends on**: Phase 1, Phase 2

**Research**: Unlikely (combining existing components)

**Plans**: 2 plans

Plans:
- [ ] 03-01: GSD integration (modify /run-plan, @file routing, context budgeting)
- [ ] 03-02: Testing & measurement (10 representative tasks, before/after metrics, threshold tuning)

## Progress

**Execution Order:**
Phases 1 and 2 can run in parallel, then Phase 3 integrates both.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. AuZoom Implementation | 0/3 | Not started | - |
| 2. Orchestrator Implementation | 0/3 | Not started | - |
| 3. Integration & Validation | 0/2 | Not started | - |
