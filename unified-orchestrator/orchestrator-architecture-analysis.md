# Orchestrator Architecture: MCP Tools vs Direct Switching + AuZoom Integration

## The Core Question

Should other LLMs be exposed as MCP tools to Claude Code, or should an external orchestrator handle switching?

---

## Option A: LLMs as MCP Tools

```
┌─────────────────────────────────────────────────────────────┐
│                      CLAUDE CODE                             │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Available Tools:                                        ││
│  │  • auzoom_get_graph()     - Code navigation             ││
│  │  • call_haiku()           - Simple generation           ││
│  │  • call_qwen_local()      - Local model                 ││
│  │  • call_glm()             - Fast Cerebras               ││
│  │  • validate_with_sonnet() - Validation checkpoint       ││
│  │  • read_file(), write_file(), bash(), etc.             ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  Claude Code decides: "This looks simple, I'll use Haiku"   │
│  → tool_call: call_haiku(prompt="Write a sort function")    │
└─────────────────────────────────────────────────────────────┘
```

### Pros
- Claude Code sees full context, makes informed decisions
- Can combine models mid-task (Haiku drafts, Sonnet reviews)
- Natural integration with existing tool ecosystem
- Claude Code can override routing when it knows better

### Cons
- Claude Code consumes tokens just to DECIDE which tool to call
- Every model switch requires Claude Code round-trip
- Claude Code's judgment may not be cost-optimal
- Slower: decision → tool call → wait → process response → next decision

---

## Option B: External Orchestrator (Pre-Router)

```
┌─────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR LAYER                        │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 1. Receive task                                         ││
│  │ 2. Score complexity (rule-based, no LLM needed)         ││
│  │ 3. Route to appropriate model                           ││
│  │ 4. If simple (complexity ≤ 2): Haiku/Local handles ALL  ││
│  │ 5. If complex: Pass to Claude Code                      ││
│  └─────────────────────────────────────────────────────────┘│
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
   ┌─────────┐      ┌───────────┐      ┌───────────┐
   │  LOCAL  │      │   HAIKU   │      │ CLAUDE    │
   │  Qwen   │      │           │      │  CODE     │
   └─────────┘      └───────────┘      │ (Sonnet)  │
                                       └───────────┘
```

### Pros
- Zero LLM tokens for routing decision
- Simple tasks never touch expensive models
- Faster: direct routing without deliberation
- Predictable costs based on complexity rules

### Cons
- Loses Claude Code's contextual judgment
- Rule-based routing can't adapt to nuance
- May misroute edge cases
- Another service to maintain

---

## Option C: Hybrid (RECOMMENDED)

**Key Insight**: Use BOTH. Orchestrator handles mechanical routing, Claude Code can override.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATOR MCP SERVER                      │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    orchestrator_route()                         ││
│  │  - Scores complexity (rule-based)                               ││
│  │  - Returns: {model, reason, confidence}                         ││
│  │  - Does NOT execute, just recommends                            ││
│  └─────────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    orchestrator_execute()                       ││
│  │  - Takes: {model, prompt, context}                              ││
│  │  - Routes to specified model                                    ││
│  │  - Returns: {response, tokens_used, latency}                    ││
│  └─────────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                    orchestrator_validate()                      ││
│  │  - Always uses Sonnet (input-heavy mode)                        ││
│  │  - Returns: {pass, issues, confidence, escalate}                ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           CLAUDE CODE                                │
│                                                                      │
│  Workflow:                                                          │
│  1. Get routing recommendation: orchestrator_route(task)            │
│  2. Accept or override: "Orchestrator says Haiku, but I see this    │
│     involves auth code, I'll use Sonnet"                            │
│  3. Execute: orchestrator_execute(model="sonnet", prompt=...)       │
│  4. Optionally validate: orchestrator_validate(output)              │
│                                                                      │
│  Claude Code DELEGATES generation but RETAINS judgment              │
└─────────────────────────────────────────────────────────────────────┘
```

### Why This Works

1. **Cost Optimization**: Orchestrator's routing costs 0 LLM tokens
2. **Judgment Preserved**: Claude Code can override with full context
3. **Flexibility**: Can run in "auto" mode (trust orchestrator) or "manual" (always decide)
4. **Observability**: All routing decisions logged for learning

---

## AuZoom Integration: The Compound Effect

AuZoom reduces **input tokens** (what gets sent to models).
Hierarchical routing reduces **output cost** (which model generates).

**Combined effect is multiplicative, not additive.**

### Without AuZoom + Without Routing (Baseline)

```
Task: "Fix the login bug in auth/service.py"

Claude Code (Sonnet):
  Input:  auth/service.py (800 lines, 3,200 tokens)
        + auth/repository.py (400 lines, 1,600 tokens)
        + auth/models.py (300 lines, 1,200 tokens)
        + system prompt (500 tokens)
  = 6,500 input tokens × $3/1M = $0.0195

  Output: Fix + explanation (800 tokens)
  = 800 output tokens × $15/1M = $0.012

  Total: $0.0315 per task
```

### With AuZoom Only

```
Task: "Fix the login bug in auth/service.py"

Claude Code (Sonnet):
  Input:  auzoom skeleton (all auth/, 400 tokens)
        + auzoom summary (login function, 80 tokens)
        + auzoom full (login function only, 300 tokens)
        + system prompt (500 tokens)
  = 1,280 input tokens × $3/1M = $0.00384

  Output: Fix + explanation (800 tokens)
  = 800 output tokens × $15/1M = $0.012

  Total: $0.01584 per task (50% reduction)
```

### With Routing Only

```
Task: "Fix the login bug in auth/service.py"

Haiku generates fix (no AuZoom):
  Input:  6,500 tokens × $0.25/1M = $0.001625
  Output: 800 tokens × $1.25/1M = $0.001
  Subtotal: $0.002625

Sonnet validates (input-heavy):
  Input:  fix + context (2,000 tokens) × $3/1M = $0.006
  Output: validation (100 tokens) × $15/1M = $0.0015
  Subtotal: $0.0075

  Total: $0.010125 per task (68% reduction)
```

### With BOTH AuZoom + Routing (Compound Effect)

```
Task: "Fix the login bug in auth/service.py"

Step 1: Orchestrator routes to Haiku (0 tokens, rule-based)

Step 2: AuZoom navigation
  auzoom_get_graph(node="auth", level="skeleton", depth=2)
  → 400 tokens, identifies login() needs fixing

Step 3: Haiku generates fix (with minimal context)
  Input:  skeleton (400) + login summary (80) + login full (300) = 780 tokens
  × $0.25/1M = $0.000195
  Output: 500 tokens × $1.25/1M = $0.000625
  Subtotal: $0.00082

Step 4: Sonnet validates (input-heavy, AuZoom-optimized context)
  Input:  fix (500) + relevant context via AuZoom (600) = 1,100 tokens
  × $3/1M = $0.0033
  Output: 100 tokens × $15/1M = $0.0015
  Subtotal: $0.0048

  Total: $0.00562 per task (82% reduction from baseline!)
```

### Cost Comparison Summary

| Approach | Cost/Task | Reduction |
|----------|-----------|-----------|
| Baseline (Sonnet, full files) | $0.0315 | - |
| AuZoom only | $0.0158 | 50% |
| Routing only | $0.0101 | 68% |
| **AuZoom + Routing** | **$0.0056** | **82%** |

---

## Integrated Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           MCP SERVER BUNDLE                              │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                         🐱 AuZoom                                  │ │
│  │  auzoom_get_graph(node, level, depth)                              │ │
│  │  auzoom_find(query, scope)                                         │ │
│  │  auzoom_get_dependencies(node, direction)                          │ │
│  │                                                                    │ │
│  │  Returns: Multi-resolution code view (skeleton/summary/full)       │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│                                    ▼                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                    🎭 Orchestrator                                 │ │
│  │  orchestrator_route(task, context) → {model, confidence}           │ │
│  │  orchestrator_execute(model, prompt, auzoom_context) → response    │ │
│  │  orchestrator_validate(output, context) → {pass, issues}           │ │
│  │                                                                    │ │
│  │  Routing Rules:                                                    │ │
│  │  • complexity ≤ 2 → local/qwen3-30b                               │ │
│  │  • complexity ≤ 4, code → cerebras/glm-4.7                        │ │
│  │  • complexity ≤ 4, other → haiku                                  │ │
│  │  • complexity ≤ 7 → sonnet                                        │ │
│  │  • complexity > 7 → opus                                          │ │
│  │  • validation checkpoint → sonnet (max 100 tokens out)            │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                    │                                     │
│                                    ▼                                     │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                    📊 Memory                                       │ │
│  │  memory_retrieve(query) → relevant past experiences                │ │
│  │  memory_store(task, model, outcome) → logged                       │ │
│  │  memory_get_profile(model) → task affinities                       │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLAUDE CODE                                    │
│                                                                          │
│  System prompt includes:                                                │
│  "You have access to AuZoom for efficient code navigation and          │
│   Orchestrator for model routing. ALWAYS use auzoom_get_graph          │
│   before reading full files. PREFER orchestrator_execute over          │
│   direct generation for delegatable tasks."                            │
│                                                                          │
│  Typical workflow:                                                      │
│  1. auzoom_get_graph(node="root", level="skeleton", depth=2)           │
│     → Understand codebase structure (400 tokens)                       │
│  2. Identify relevant nodes from skeleton                              │
│  3. auzoom_get_graph(node="target", level="summary")                   │
│     → Get signatures/docstrings (80 tokens)                            │
│  4. orchestrator_route(task_description)                               │
│     → Get model recommendation                                         │
│  5. orchestrator_execute(model, prompt_with_auzoom_context)            │
│     → Delegate to optimal model                                        │
│  6. If validation_required:                                            │
│     orchestrator_validate(output, auzoom_context)                      │
│     → Sonnet reviews (input-heavy)                                     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## AuZoom-Aware Context Building

The orchestrator should build context using AuZoom levels based on the target model:

```python
class AuZoomContextBuilder:
    """Build optimal context for each model tier"""
    
    def build_context(self, task: str, target_model: str) -> str:
        if target_model in ["local/qwen3-30b", "haiku"]:
            # Minimal context for simple models
            return self._build_minimal_context(task)
        elif target_model in ["cerebras/glm-4.7", "sonnet"]:
            # Medium context with summaries
            return self._build_medium_context(task)
        else:  # opus
            # Full context for complex reasoning
            return self._build_full_context(task)
    
    def _build_minimal_context(self, task: str) -> str:
        """Skeleton + target function full only"""
        relevant_nodes = self.auzoom.find(task)
        
        context_parts = [
            # Skeleton for navigation
            self.auzoom.get_graph("root", level="skeleton", depth=2),
            # Full code only for the specific target
            self.auzoom.get_graph(relevant_nodes[0], level="full")
        ]
        return self._format(context_parts)
    
    def _build_medium_context(self, task: str) -> str:
        """Skeleton + summaries for dependencies + target full"""
        relevant = self.auzoom.find(task)
        deps = self.auzoom.get_dependencies(relevant[0], depth=1)
        
        context_parts = [
            self.auzoom.get_graph("root", level="skeleton", depth=2),
            # Summaries for dependencies (understand interfaces)
            *[self.auzoom.get_graph(d, level="summary") for d in deps],
            # Full for target
            self.auzoom.get_graph(relevant[0], level="full")
        ]
        return self._format(context_parts)
    
    def _build_full_context(self, task: str) -> str:
        """Full code for target and immediate dependencies"""
        relevant = self.auzoom.find(task)
        deps = self.auzoom.get_dependencies(relevant[0], depth=1)
        
        context_parts = [
            self.auzoom.get_graph("root", level="skeleton", depth=3),
            *[self.auzoom.get_graph(d, level="full") for d in deps[:3]],
            self.auzoom.get_graph(relevant[0], level="full")
        ]
        return self._format(context_parts)
```

---

## Model-Specific Prompt Templates

Different models need different prompt structures:

```python
PROMPT_TEMPLATES = {
    "local/qwen3-30b": """
<task>{task}</task>
<code_context>
{auzoom_skeleton}
</code_context>
<target_code>
{target_full}
</target_code>
Output only the modified code, no explanation.
""",
    
    "cerebras/glm-4.7": """
<task>{task}</task>
<navigation>
{auzoom_skeleton}
</navigation>
<dependencies>
{dependency_summaries}
</dependencies>
<modify>
{target_full}
</modify>
Think step by step. Output the fix.
""",
    
    "haiku": """
Task: {task}

Context (skeleton):
{auzoom_skeleton}

Code to modify:
{target_full}

Provide the corrected code.
""",
    
    "sonnet_validation": """
<context>{task_and_requirements}</context>
<code_structure>{auzoom_skeleton}</code_structure>
<output_to_validate>{generated_code}</output_to_validate>

Validate. JSON only (max 100 tokens):
{{"pass": bool, "issues": ["..."], "confidence": 0-1, "escalate": bool}}
"""
}
```

---

## Recommendation: Single MCP Server

Bundle everything into ONE MCP server with multiple tools:

```typescript
// claude_mcp_config.json
{
  "mcpServers": {
    "ai-orchestrator": {
      "command": "python",
      "args": ["-m", "ai_orchestrator.server"],
      "env": {
        "ANTHROPIC_API_KEY": "...",
        "CEREBRAS_API_KEY": "...",
        "OLLAMA_HOST": "http://localhost:11434",
        "QDRANT_HOST": "localhost:6333"
      }
    }
  }
}
```

Tools exposed:
```
auzoom_get_graph      - Multi-resolution code navigation
auzoom_find           - Semantic search in codebase
auzoom_dependencies   - Dependency analysis
orchestrator_route    - Get routing recommendation
orchestrator_execute  - Execute on specified model
orchestrator_validate - Input-heavy validation
memory_retrieve       - Get relevant past experiences
memory_store          - Log outcome for learning
```

This keeps Claude Code's tool list clean while providing full orchestration capability.
