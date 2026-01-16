# Self-Optimizing GSD Orchestrator: Token-Efficient Plan Execution

## Executive Summary

GSD plans can evolve from sequential task execution (current model: main agent executes all tasks linearly) into self-optimizing orchestrators that:

1. **Annotate tasks with execution metadata** (subagent type, model selection, parallelization hints)
2. **Auto-spawn parallel subagents** for independent segments based on dependency graphs
3. **Route tasks to optimal models** (Haiku for simple, Sonnet for complex, Opus for planning)
4. **Track token costs** per task type and learn execution patterns
5. **Minimize main context usage** to 10-20% by pushing autonomous work to fresh-context subagents

**Result**: Plans that handle 50M+ token codebases with higher quality and lower cost than possible with single-agent linear execution.

---

## Part 1: Current State Analysis

### 1.1 Current GSD Execution Model

**PLAN.md Structure** (from plan-format.md):
```xml
<tasks>
  <task type="auto">
    <name>Task 1: [Name]</name>
    <files>[paths]</files>
    <action>[what to do]</action>
    <verify>[command/check]</verify>
    <done>[criteria]</done>
  </task>

  <task type="checkpoint:human-verify">
    <what-built>[what Claude automated]</what-built>
    <how-to-verify>[numbered verification steps]</how-to-verify>
    <resume-signal>[how to continue]</resume-signal>
  </task>
</tasks>
```

**Execution Pattern** (from execute-phase.md):
- Parse plan into segments by checkpoints
- For fully autonomous plans: spawn single subagent for entire plan
- For segmented plans with verify-only checkpoints: subagent per segment, main context only for checkpoints
- Task commits created per-task during execution

**Constraints**:
- Each task commits independently (`feat({phase}-{plan}): [task description]`)
- No explicit model selection metadata in tasks
- No parallelization hints beyond implicit checkpoint-based segmentation
- No token tracking per task type
- Main context orchestration only for checkpoints

### 1.2 Token Efficiency Insights from Blog

From "Launching 3+ Haiku sub-agents for exploration reduces latency":

1. **Model Tiering**:
   - Haiku: Simple code review, file reads, straightforward implementations
   - Sonnet: 90% of production tasks, complex features, medium-to-large refactors
   - Opus: Planning, architecture, complex decision-making

2. **Parallelization Patterns**:
   - 3+ Haiku agents in parallel cost less than 1 Sonnet
   - Each fresh context starts at 0% (no accumulated context)
   - Parallel execution multiplies throughput without multiplicative cost

3. **Context Separation**:
   - Fresh subagent context: ~5% usage for reading initial files
   - Accumulated main context: 50-70% after executing multiple tasks
   - Quality degrades after 70% context usage

4. **Token Efficiency Strategy**:
   - Push autonomous work to fresh-context subagents (Haiku or Sonnet)
   - Keep main context for checkpoints and decisions only
   - Spawn parallel subagents for independent work

---

## Part 2: Enhanced Task Schema with Execution Metadata

### 2.1 Extended Task XML Structure

```xml
<task type="auto"
      subagent="general-purpose|explore|plan|bash"
      model="haiku|sonnet|opus"
      parallel="sequential|can-parallelize"
      estimated-complexity="1-10"
      depends-on="task-numbers"
      context-mode="fresh|inherited">
  <name>Task N: [Action-oriented name]</name>
  <files>[paths modified]</files>
  <action>[Specific implementation instructions]</action>
  <verify>[Verification command/check]</verify>
  <done>[Acceptance criteria]</done>
  <metrics>
    <estimated-tokens>5000-8000</estimated-tokens>
    <estimated-duration>15-30min</estimated-duration>
  </metrics>
</task>
```

### 2.2 Attribute Definitions

#### `subagent` (Execution Context Type)
Determines which specialized subagent handles this task:

| Value | Use Case | Context | When |
|-------|----------|---------|------|
| `general-purpose` | Standard implementation tasks | Fresh | Default for most `type="auto"` |
| `explore` | Codebase analysis, dependency discovery, research | Fresh | Large codebases, file structure learning |
| `plan` | Creating execution plans, architecture | Fresh + loaded context | Complex phase planning |
| `bash` | Infrastructure, deployments, CLI operations | Inherited | Depends on prior task results |

**Decision Framework**:
- Is this a code implementation task? → `general-purpose`
- Is this exploring/mapping the codebase? → `explore`
- Is this creating next-phase plans? → `plan`
- Does this depend on prior task state (built files, configs)? → `bash` (inherit context)

#### `model` (LLM Selection)
Route task to appropriate model based on complexity and token budget:

| Model | Cost | Complexity Range | Task Examples |
|-------|------|------------------|----------------|
| `haiku` | Lowest | 1-4 | File reads, simple fixes, straightforward tests, code review, basic refactoring |
| `sonnet` | Medium | 5-8 | Most production features, API implementations, medium refactors, business logic |
| `opus` | Highest | 9-10 | Architecture decisions, planning, complex coordination, risk-critical code |

**Heuristics for Model Selection**:
- Start at Sonnet (90% of tasks)
- Use Haiku if: "task involves straightforward implementation without complex logic"
- Use Opus if: "task requires planning, architecture, or novel problem-solving"

**Complexity Scoring** (0-10 scale):
```
1-3:   Trivial         → Haiku
       - Add field to model
       - Fix syntax error
       - Add import statement

4-6:   Standard        → Sonnet (default)
       - Implement API endpoint
       - Create validation logic
       - Refactor module structure

7-9:   Complex         → Sonnet
       - Complex state management
       - Distributed system coordination
       - Novel algorithm

10:    Critical/Novel  → Opus
       - Architecture decision
       - Security-critical code
       - New paradigm adoption
```

#### `parallel` (Dependency & Execution Strategy)
Indicates whether task can run in parallel with others:

| Value | Meaning | Implications |
|-------|---------|--------------|
| `sequential` | Must run after prior task completes | Depends on files from previous task |
| `can-parallelize` | Can run alongside other `can-parallelize` tasks | No data dependencies between tasks |

**Used for**: Building task groups for parallel subagent spawning.

#### `depends-on` (Explicit Dependency Graph)
List task numbers this task depends on:
```xml
<task ... depends-on="1,2">
  <!-- Runs only after tasks 1 and 2 complete -->
</task>
```

#### `context-mode` (Context Management)
How subagent loads context:

| Mode | Behavior | When |
|------|----------|------|
| `fresh` | Read only required files, 0% context start | Default for most work |
| `inherited` | Subagent gets accumulated context from main | For sequential tasks depending on prior work |

---

## Part 3: Parallel Dependency Graph Notation

### 3.1 Graph Representation in PLAN.md

```markdown
<task_dependency_graph>
## Execution Graph

### Sequential Path (blocking)
Task 1: Setup → Task 2: Implement → Task 3: Test

### Parallel Groups

**Group 1 (Batch 1 - can run in parallel):**
- Task 4: Feature A (depends-on: 3)
- Task 5: Feature B (depends-on: 3)
- Task 6: Feature C (depends-on: 3)

All three can spawn parallel subagents since they have same dependencies.

**Group 2 (After Group 1):**
- Task 7: Integration test (depends-on: 4,5,6)

### Routing Decision

```
Task 1 (sequential)
  ↓
Task 2 (sequential)
  ↓
Task 3 (sequential, merge point)
  ↓
┌─────────────────────┐
│ Parallel batch 1    │ ← spawn 3 subagents simultaneously
├─────────────────────┤
│ Task 4 (Haiku)      │
│ Task 5 (Sonnet)     │
│ Task 6 (Haiku)      │
└─────────────────────┘
  ↓ (all complete)
Task 7 (sequential)
```

</task_dependency_graph>
```

### 3.2 Building the Graph Algorithmically

**Input**: Task list with `depends-on` attributes
**Output**: Execution batches (sequential groups that can run in parallel within batch)

```python
def build_execution_graph(tasks):
    """
    Build parallel execution batches from task dependency graph.

    Tasks can run in parallel if:
    1. They have the same set of dependencies
    2. None depend on each other
    3. All their dependencies are complete
    """

    graph = {
        "batches": [],      # Sequential list of parallel batches
        "dependencies": {}  # task_id -> list of task_ids
    }

    # Build reverse index: task -> what depends on it
    reverse_deps = {}
    for task in tasks:
        task_id = task.number
        for dep in task.depends_on:
            if dep not in reverse_deps:
                reverse_deps[dep] = []
            reverse_deps[dep].append(task_id)

    completed = set()
    batch_num = 1

    while len(completed) < len(tasks):
        # Find all tasks whose dependencies are satisfied
        ready = [
            t for t in tasks
            if t.number not in completed
            and all(dep in completed for dep in t.depends_on)
        ]

        if not ready:
            raise Exception("Circular dependency detected")

        # Group ready tasks by dependency signature
        dep_groups = {}
        for task in ready:
            sig = tuple(sorted(task.depends_on))
            if sig not in dep_groups:
                dep_groups[sig] = []
            dep_groups[sig].append(task)

        # Each dependency group can run in parallel
        for sig, group in dep_groups.items():
            batch = {
                "batch_number": batch_num,
                "depends_on": list(sig),
                "tasks": [t.number for t in group],
                "can_parallelize": len(group) > 1,
                "subagent_model_assignments": assign_models(group)
            }
            graph["batches"].append(batch)
            batch_num += 1

            for task in group:
                completed.add(task.number)

    return graph
```

---

## Part 4: Model Selection Heuristics

### 4.1 Complexity Scorer Implementation

```python
class ComplexityScorer:
    """Score task complexity 0-10 to determine model routing."""

    def score(self, task) -> int:
        """Analyze task action/files to predict complexity."""

        score = 5  # Default: Sonnet

        # Reduce score (toward Haiku) for simple indicators
        if self._is_file_read_task(task):
            score -= 2
        if self._is_simple_fix(task):
            score -= 2
        if self._is_straightforward_feature(task):
            score -= 1

        # Increase score (toward Opus) for complex indicators
        if self._requires_architecture_decision(task):
            score += 3
        if self._is_complex_refactoring(task):
            score += 2
        if self._involves_novel_problem(task):
            score += 2

        return max(1, min(10, score))  # Clamp 1-10

    def _is_file_read_task(self, task) -> bool:
        """Check if task is mainly file reading."""
        action_lower = task.action.lower()
        return (
            "read" in action_lower or
            "understand" in action_lower or
            "review" in action_lower
        ) and "implement" not in action_lower

    def _is_simple_fix(self, task) -> bool:
        """Check for simple bug fixes."""
        done_lower = task.done.lower()
        return (
            "fix" in task.name.lower() and
            len(task.files.split(",")) == 1 and  # Single file
            "regex" not in done_lower and
            "algorithm" not in done_lower
        )

    def _is_straightforward_feature(self, task) -> bool:
        """Check for straightforward feature additions."""
        action = task.action
        # Simple additions: add field, add import, add route
        return (
            "add" in action.lower() and
            "complex" not in action.lower() and
            "state management" not in action.lower()
        )

    def _requires_architecture_decision(self, task) -> bool:
        """Check if task requires architecture choices."""
        keywords = [
            "architecture", "design", "pattern",
            "refactor" if "large-scale" in task.action.lower() else None,
            "new service", "new table", "new layer"
        ]
        return any(
            k and k.lower() in task.action.lower()
            for k in keywords
        )

    def _is_complex_refactoring(self, task) -> bool:
        """Check for complex refactoring."""
        return (
            "refactor" in task.name.lower() and
            len(task.files.split(",")) > 2  # Multiple files
        )

    def _involves_novel_problem(self, task) -> bool:
        """Check for novel/uncertain problems."""
        keywords = [
            "research", "investigate", "validate",
            "security", "performance optimization"
        ]
        return any(
            k.lower() in task.action.lower()
            for k in keywords
        )

    @property
    def model_for_score(self) -> dict:
        """Map score ranges to model selection."""
        return {
            range(1, 4): "haiku",      # 1-3: Haiku
            range(4, 9): "sonnet",     # 4-8: Sonnet
            range(9, 11): "opus"       # 9-10: Opus
        }
```

### 4.2 Cost-Aware Routing

```python
class TokenAwareCostRouter:
    """Route tasks to models based on token budget and complexity."""

    def __init__(self, total_budget_tokens=200000):
        self.total_budget = total_budget_tokens
        self.remaining = total_budget_tokens

        # Cost multipliers (relative to Haiku=1)
        self.cost_multipliers = {
            "haiku": 1.0,
            "sonnet": 5.0,
            "opus": 15.0
        }

    def select_model(self, task, complexity_score):
        """Select model, accounting for budget constraints."""

        # Primary model from complexity
        primary_model = self._model_from_complexity(complexity_score)

        # Check if we can afford it
        estimated_cost = self._estimate_cost(task, primary_model)

        if estimated_cost > self.remaining * 0.15:
            # Can't afford primary model without exceeding 15% of remaining
            # Try fallback to cheaper model
            if primary_model != "haiku":
                fallback = self._find_fallback(primary_model)
                fallback_cost = self._estimate_cost(task, fallback)

                if fallback_cost <= self.remaining * 0.15:
                    return fallback

        return primary_model

    def _model_from_complexity(self, score) -> str:
        """Pure complexity-based model selection."""
        if score <= 3:
            return "haiku"
        elif score <= 8:
            return "sonnet"
        else:
            return "opus"

    def _estimate_cost(self, task, model) -> int:
        """Estimate token cost for task with given model."""
        # Use task's estimated_tokens if available
        base_estimate = task.metrics.get("estimated_tokens", 5000)

        # Adjust for model (larger models may be more efficient)
        if model == "haiku":
            return base_estimate * 1.2  # Haiku might need more tokens
        elif model == "sonnet":
            return base_estimate  # Baseline
        else:  # opus
            return base_estimate * 0.8  # Opus is more efficient

    def _find_fallback(self, model) -> str:
        """Find cheaper fallback model."""
        if model == "opus":
            return "sonnet"
        elif model == "sonnet":
            return "haiku"
        return "haiku"

    def record_actual_tokens(self, task_result):
        """Update remaining budget with actual execution."""
        self.remaining -= task_result.actual_tokens

```

---

## Part 5: Automated Subagent Spawning

### 5.1 Parallel Batch Execution Strategy

**Current Implementation** (from execute-phase.md):
```
1. Parse plan segments by checkpoints
2. For autonomous segment: spawn one subagent with all tasks
3. For segmented plans: spawn one subagent per autonomous segment
4. For decision-dependent: execute in main context (no subagent)
```

**Enhanced Implementation** (Token-Optimized):
```
1. Parse plan into task dependency graph
2. Identify execution batches (parallel groups)
3. For each batch:
   - Assign models (Haiku/Sonnet/Opus) per task
   - Spawn up to N parallel subagents (same cost < 1 Sonnet)
   - Each subagent handles 1-3 tasks from batch
4. Merge results, update context
5. Proceed to next batch
```

### 5.2 Subagent Spawning Protocol

```python
class ParallelSubagentOrchestrator:
    """Manage parallel subagent execution with token tracking."""

    MAX_PARALLEL_SUBAGENTS = 5

    def execute_plan(self, plan_path):
        """Execute plan with automatic parallelization."""

        # Step 1: Parse and build execution graph
        plan = parse_plan_file(plan_path)
        graph = build_execution_graph(plan.tasks)

        # Step 2: Assign models to all tasks
        for task in plan.tasks:
            complexity = ComplexityScorer().score(task)
            task.assigned_model = TokenAwareCostRouter().select_model(
                task, complexity
            )

        # Step 3: Execute batches sequentially, tasks in parallel
        results = []

        for batch_num, batch in enumerate(graph["batches"]):
            print(f"\nBatch {batch_num + 1}/{len(graph['batches'])}")
            print(f"Tasks: {batch['tasks']}")
            print(f"Can parallelize: {batch['can_parallelize']}")

            if batch["can_parallelize"] and len(batch["tasks"]) > 1:
                # Spawn parallel subagents
                batch_results = self._execute_batch_parallel(
                    plan, batch, max_workers=min(
                        len(batch["tasks"]),
                        self.MAX_PARALLEL_SUBAGENTS
                    )
                )
            else:
                # Sequential execution
                batch_results = self._execute_batch_sequential(plan, batch)

            results.extend(batch_results)

            # Verify batch completion before proceeding
            if not all(r["success"] for r in batch_results):
                raise Exception(f"Batch {batch_num} failed")

        # Step 4: Create SUMMARY.md with execution metrics
        self._create_summary(plan, results)

        return results

    def _execute_batch_parallel(self, plan, batch, max_workers):
        """Execute multiple tasks in parallel via subagents."""

        subagent_configs = []

        # Distribute tasks across subagents
        for task_num in batch["tasks"]:
            task = next(t for t in plan.tasks if t.number == task_num)

            config = {
                "task_number": task_num,
                "task_name": task.name,
                "model": task.assigned_model,
                "subagent_type": task.subagent,
                "files": task.files,
                "action": task.action,
                "verify": task.verify,
                "done": task.done
            }
            subagent_configs.append(config)

        # Spawn subagents in parallel
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    self._spawn_subagent,
                    config
                ): config["task_number"]
                for config in subagent_configs
            }

            for future in as_completed(futures):
                task_num = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    print(f"  ✓ Task {task_num} complete ({result['tokens']} tokens)")
                except Exception as e:
                    print(f"  ✗ Task {task_num} failed: {e}")
                    results.append({
                        "task_number": task_num,
                        "success": False,
                        "error": str(e),
                        "tokens": 0
                    })

        return results

    def _spawn_subagent(self, config):
        """Spawn single subagent for one task."""

        prompt = self._build_subagent_prompt(config)

        # Route to appropriate subagent
        if config["subagent_type"] == "explore":
            model = "haiku"  # Exploration is cheap
        else:
            model = config["model"]

        # Execute subagent (pseudo-code)
        response = call_model(
            prompt=prompt,
            model=model,
            temperature=0,
            max_tokens=config.get("max_tokens", 20000)
        )

        return {
            "task_number": config["task_number"],
            "success": self._parse_completion(response),
            "output": response.content,
            "tokens": response.usage.output_tokens,
            "model_used": model,
            "commit_hash": self._extract_commit(response)
        }

    def _build_subagent_prompt(self, config) -> str:
        """Build focused prompt for subagent."""

        return f"""Execute this task from a GSD plan:

**Task {config['task_number']}: {config['task_name']}**

**Files**: {config['files']}

**Action**: {config['action']}

**Verify**: {config['verify']}

**Done when**: {config['done']}

**Important**:
- Execute ONLY this task (not entire plan)
- Follow all verification checks
- DO NOT create SUMMARY.md or commit
- Report results with task number, files modified, commit hash, any issues

After completion, create atomic commit: `feat({phase}-{plan}): {config['task_name']}`
"""

    def _execute_batch_sequential(self, plan, batch):
        """Execute batch tasks sequentially in main context."""

        results = []
        for task_num in batch["tasks"]:
            task = next(t for t in plan.tasks if t.number == task_num)
            result = self._execute_task_inline(task)
            results.append(result)

        return results

    def _execute_task_inline(self, task):
        """Execute single task in main context."""
        # Standard task execution (current GSD flow)
        pass

    def _create_summary(self, plan, results):
        """Create SUMMARY.md with execution metrics."""

        total_tokens = sum(r.get("tokens", 0) for r in results)
        parallel_multiplier = self._calculate_parallelization_factor(results)

        summary = f"""# {plan.phase}: {plan.objective} Summary

**Token Efficiency Metrics**:
- Total tokens: {total_tokens}
- Main context usage: {self._estimate_main_context_percent(results)}%
- Parallel batches: {self._count_parallel_batches(results)}
- Subagent spawns: {self._count_subagent_spawns(results)}
- Cost multiplier for parallelization: {parallel_multiplier:.2f}x

## Task Execution

{self._format_task_results(results)}

## Files Modified

{self._list_files_modified(results)}
"""

        write_summary(summary)
```

---

## Part 6: Token Cost Tracking Per Task Type

### 6.1 Token Metrics Schema

```xml
<task ... estimated-complexity="6">
  <!-- ... task definition ... -->

  <metrics>
    <estimated-tokens>8000-12000</estimated-tokens>
    <estimated-duration>20-30min</estimated-duration>
    <token-budget>15000</token-budget>
    <complexity-breakdown>
      <file-reading>2000</file-reading>
      <implementation>5000</implementation>
      <testing>2000</testing>
      <debugging>1000</debugging>
    </complexity-breakdown>
  </metrics>
</task>
```

### 6.2 Token Tracking and Learning

```python
class TokenCostLearner:
    """Track and learn token costs for task types."""

    def __init__(self, stats_file=".planning/.token-stats.json"):
        self.stats_file = stats_file
        self.stats = self._load_stats()

    def record_task_execution(self, task_result):
        """Record actual tokens used for future estimation."""

        task_type = task_result["type"]  # "file-read", "api-impl", "test", etc.
        actual_tokens = task_result["tokens_used"]
        complexity = task_result["complexity_score"]
        model = task_result["model_used"]
        duration_sec = task_result["duration"]

        key = (task_type, complexity, model)

        if key not in self.stats:
            self.stats[key] = {
                "count": 0,
                "total_tokens": 0,
                "min_tokens": float('inf'),
                "max_tokens": 0,
                "avg_duration": 0,
                "success_rate": 0
            }

        stats = self.stats[key]
        stats["count"] += 1
        stats["total_tokens"] += actual_tokens
        stats["min_tokens"] = min(stats["min_tokens"], actual_tokens)
        stats["max_tokens"] = max(stats["max_tokens"], actual_tokens)
        stats["avg_duration"] = (
            (stats["avg_duration"] * (stats["count"] - 1) + duration_sec)
            / stats["count"]
        )
        stats["success_rate"] = (
            (stats["success_rate"] * (stats["count"] - 1) +
             (1.0 if task_result["success"] else 0.0))
            / stats["count"]
        )

        self._save_stats()

    def estimate_tokens(self, task_type, complexity, model):
        """Estimate tokens for task based on historical data."""

        key = (task_type, complexity, model)

        if key in self.stats:
            stats = self.stats[key]
            return {
                "estimate": stats["total_tokens"] / stats["count"],
                "confidence": min(0.95, stats["count"] / 10),  # More data = higher confidence
                "range": (stats["min_tokens"], stats["max_tokens"]),
                "success_rate": stats["success_rate"]
            }

        # Fallback to model-based estimate if no historical data
        return self._fallback_estimate(task_type, complexity, model)

    def _fallback_estimate(self, task_type, complexity, model):
        """Estimate when no historical data available."""

        base_costs = {
            "file-read": 2000,
            "simple-impl": 3000,
            "api-impl": 8000,
            "complex-refactor": 15000,
            "test-write": 5000,
            "architecture": 10000
        }

        base = base_costs.get(task_type, 5000)

        # Adjust for complexity
        complexity_multiplier = 1.0 + (complexity - 5) * 0.15

        # Adjust for model efficiency
        model_multipliers = {
            "haiku": 1.2,   # Haiku may need more tokens
            "sonnet": 1.0,  # Baseline
            "opus": 0.85    # Opus is more efficient
        }

        estimated = int(
            base * complexity_multiplier *
            model_multipliers.get(model, 1.0)
        )

        return {
            "estimate": estimated,
            "confidence": 0.3,  # Low confidence without data
            "range": (int(estimated * 0.7), int(estimated * 1.3)),
            "success_rate": 0.85  # Conservative
        }

    def _load_stats(self):
        """Load historical token statistics."""
        if Path(self.stats_file).exists():
            with open(self.stats_file) as f:
                return json.load(f)
        return {}

    def _save_stats(self):
        """Persist token statistics."""
        with open(self.stats_file, "w") as f:
            json.dump(self.stats, f, indent=2)

    def generate_report(self):
        """Generate token efficiency report."""

        print("\n=== Token Cost Analysis ===\n")

        for (task_type, complexity, model), stats in sorted(self.stats.items()):
            print(f"{task_type} (complexity {complexity}, {model}):")
            print(f"  Executions: {stats['count']}")
            print(f"  Avg tokens: {stats['total_tokens'] // stats['count']}")
            print(f"  Range: {stats['min_tokens']} - {stats['max_tokens']}")
            print(f"  Success rate: {stats['success_rate']*100:.1f}%")
            print(f"  Avg duration: {stats['avg_duration']:.1f}s\n")

```

---

## Part 7: Enhanced Plan Format Example

### 7.1 Complete Example: Multi-Feature Implementation Phase

```markdown
---
phase: 08-features
plan: 02
type: execute
domain: next-js
---

<objective>
Implement three independent API features (user profile, notifications, analytics).

Purpose: Ship core API functionality for MVP launch
Output: Three new API endpoints with tests, token-efficient parallel execution
</objective>

<execution_context>
~/.claude/get-shit-done/workflows/execute-phase.md
./summary.md
~/.claude/get-shit-done/references/checkpoints.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/phases/08-features/08-01-SUMMARY.md
@src/app/api/
@src/lib/db.ts
@src/types/
</context>

<task_dependency_graph>
## Execution Strategy

Sequential setup (shared) → Parallel features (independent) → Integration test

```
Task 1 (Setup)          [Sonnet]
     ↓
Task 2 (Schema)         [Haiku]
     ↓
Task 3 (Common utils)   [Haiku]
     ↓
┌──────────────────────────┐
│ PARALLEL BATCH 1         │  ← spawn 3 subagents
├──────────────────────────┤
│ Task 4: Profile API      │  [Haiku] - straightforward CRUD
│ Task 5: Notifications    │  [Sonnet] - medium complexity
│ Task 6: Analytics        │  [Sonnet] - complex aggregation
└──────────────────────────┘
     ↓ (all complete)
Task 7: Integration test    [Haiku]
```

**Parallelization**: Tasks 4-6 can spawn simultaneously (all depend on tasks 1-3)

</task_dependency_graph>

<tasks>

<task type="auto"
      subagent="general-purpose"
      model="sonnet"
      parallel="sequential"
      depends-on=""
      context-mode="inherited">
  <name>Task 1: Create API routes structure</name>
  <files>src/app/api/users/profile/route.ts, src/app/api/notifications/route.ts, src/app/api/analytics/route.ts</files>
  <action>Create three route directories and skeleton files with proper TypeScript types and request handling structure. Each route should have GET/POST handlers scaffolded. Avoid implementation details—just structure.</action>
  <verify>ls -la src/app/api/{users,notifications,analytics}/ and check route.ts files exist with proper exports</verify>
  <done>All three route files exist with skeleton structure, no TypeScript errors</done>
  <metrics>
    <estimated-tokens>3000-5000</estimated-tokens>
    <estimated-duration>8-12min</estimated-duration>
  </metrics>
</task>

<task type="auto"
      subagent="general-purpose"
      model="haiku"
      parallel="sequential"
      depends-on="1"
      context-mode="inherited">
  <name>Task 2: Extend database schema</name>
  <files>prisma/schema.prisma</files>
  <action>Add three models to Prisma schema: UserProfile (extends User), NotificationPreference, AnalyticsEvent. Add appropriate relations and indices. Use @db.VarChar for string fields to prevent Postgres issues.</action>
  <verify>npx prisma validate passes without errors</verify>
  <done>Schema valid, all three models defined with relations, prisma generate succeeds</done>
  <metrics>
    <estimated-tokens>2000-3000</estimated-tokens>
    <estimated-duration>5-8min</estimated-duration>
  </metrics>
</task>

<task type="auto"
      subagent="general-purpose"
      model="haiku"
      parallel="sequential"
      depends-on="1,2"
      context-mode="inherited">
  <name>Task 3: Create shared API utilities</name>
  <files>src/lib/api-utils.ts</files>
  <action>Extract common patterns: error response handler, auth guard middleware, response wrapper, pagination helper. All three feature endpoints will use these. Keep functions small (<20 lines each).</action>
  <verify>npm run typecheck passes, imports resolve, no unused functions</verify>
  <done>Utilities exported and imported by placeholder routes (task 1) without errors</done>
  <metrics>
    <estimated-tokens>3000-4000</estimated-tokens>
    <estimated-duration>10-15min</estimated-duration>
  </metrics>
</task>

<!-- Parallel batch starts here -->

<task type="auto"
      subagent="general-purpose"
      model="haiku"
      parallel="can-parallelize"
      depends-on="1,2,3"
      context-mode="fresh"
      estimated-complexity="3">
  <name>Task 4: Implement user profile API</name>
  <files>src/app/api/users/profile/route.ts, src/lib/profile-service.ts</files>
  <action>GET /api/users/profile returns user profile from UserProfile table. POST /api/users/profile updates profile fields (bio, avatar, preferences). Use shared utilities from task 3. No complex logic—straightforward CRUD mapping.</action>
  <verify>curl -X GET /api/users/profile returns 200 with profile object; POST with valid data returns 200; invalid token returns 401</verify>
  <done>Both GET and POST work correctly, tests pass, token validation enforced</done>
  <metrics>
    <estimated-tokens>5000-7000</estimated-tokens>
    <estimated-duration>15-20min</estimated-duration>
    <token-budget>8000</token-budget>
  </metrics>
</task>

<task type="auto"
      subagent="general-purpose"
      model="sonnet"
      parallel="can-parallelize"
      depends-on="1,2,3"
      context-mode="fresh"
      estimated-complexity="6">
  <name>Task 5: Implement notifications API</name>
  <files>src/app/api/notifications/route.ts, src/lib/notification-service.ts</files>
  <action>GET /api/notifications returns paginated list (use pagination helper). POST /api/notifications/preferences updates preferences. Handle subscription logic: check NotificationPreference table for opt-ins. Medium complexity: notification routing, preference checking.</action>
  <verify>GET returns paginated list with count; POST updates preferences correctly; unsubscribed users don't receive notifications (verify in follow-up test)</verify>
  <done>Pagination works, preferences stored, notification filtering functional</done>
  <metrics>
    <estimated-tokens>8000-12000</estimated-tokens>
    <estimated-duration>20-30min</estimated-duration>
    <token-budget>15000</token-budget>
  </metrics>
</task>

<task type="auto"
      subagent="general-purpose"
      model="sonnet"
      parallel="can-parallelize"
      depends-on="1,2,3"
      context-mode="fresh"
      estimated-complexity="7">
  <name>Task 6: Implement analytics API</name>
  <files>src/app/api/analytics/route.ts, src/lib/analytics-service.ts</files>
  <action>GET /api/analytics/{event-name} aggregates analytics events by time period (day/week/month from query param). Returns event count, unique users, top values. Complex: time-series aggregation, performance-aware querying. Create index on AnalyticsEvent(event_name, created_at) for performance.</action>
  <verify>GET /api/analytics/page-views?period=day returns aggregated counts; query executes in <200ms even with 100k events; proper caching headers set</verify>
  <done>Aggregation works correctly, performance acceptable (indexed), caching headers present</done>
  <metrics>
    <estimated-tokens>10000-15000</estimated-tokens>
    <estimated-duration>30-40min</estimated-duration>
    <token-budget>18000</token-budget>
  </metrics>
</task>

<task type="auto"
      subagent="general-purpose"
      model="haiku"
      parallel="sequential"
      depends-on="4,5,6"
      context-mode="fresh"
      estimated-complexity="4">
  <name>Task 7: Create integration test for all three endpoints</name>
  <files>__tests__/api/features.integration.test.ts</files>
  <action>Write integration test hitting all three endpoints in sequence: create user → set notification preferences → trigger analytics event → query analytics. Verify data flows correctly across features.</action>
  <verify>npm test passes all integration tests</verify>
  <done>Integration test passes, proves all three features work together</done>
  <metrics>
    <estimated-tokens>4000-6000</estimated-tokens>
    <estimated-duration>12-18min</estimated-duration>
  </metrics>
</task>

</tasks>

<verification>
Before declaring phase complete:
- [ ] All three API endpoints return correct responses
- [ ] Integration test passes
- [ ] npm run build succeeds without TypeScript errors
- [ ] No N+1 queries (check database logs)
- [ ] Proper error handling on all endpoints (invalid auth, missing fields, etc.)
</verification>

<success_criteria>
- All 7 tasks completed (3 sequential + 3 parallel + 1 integration)
- Three new API endpoints deployed and tested
- Parallel batch executed with 3 subagents simultaneously
- Total tokens used < estimated budget (tracking actual vs estimated)
- Integration test passing proves feature coordination
</success_criteria>

<output>
After completion, create `.planning/phases/08-features/08-02-SUMMARY.md` with:

- **Performance**: Duration, start/end times, tokens used
- **Parallelization**: Batch execution results (spawned 3 subagents, task completion order)
- **Token Efficiency**: Actual vs estimated tokens per task, subagent spawn cost vs main context
- **Accomplishments**: Three endpoints shipped with tests
- **Deviations**: Any auto-fixes applied (bugs, missing error handling, etc.)
- **Next Phase Readiness**: Database ready for analytics queries, notification system ready for background jobs
</output>
```

---

## Part 8: Integration with GSD Workflow

### 8.1 Modified plan-phase.md (Planning Step)

**New step in `<step name="break_into_tasks">`**:

```markdown
<step name="analyze_task_dependencies">
After breaking into tasks, analyze dependencies:

1. For each task, identify:
   - Can it run independently? (parallel: can-parallelize)
   - Does it depend on prior tasks? (depends-on: [numbers])
   - Is it a file-read task? (low complexity)
   - Is it implementing features? (medium complexity)
   - Is it architecture/decision task? (high complexity)

2. Estimate complexity (1-10) and assign initial model:
   - Score 1-3: likely Haiku
   - Score 4-8: likely Sonnet
   - Score 9-10: likely Opus

3. Build execution graph (use algorithm from Part 3)
   - Identify sequential path (blocking tasks)
   - Identify parallel groups (tasks with same dependencies)
   - Document in <task_dependency_graph> section

4. Annotate each task with:
   - subagent attribute (general-purpose, explore, plan, bash)
   - model attribute (haiku, sonnet, opus)
   - parallel attribute (sequential, can-parallelize)
   - depends-on numbers
   - context-mode (fresh for most, inherited for sequential)
   - estimated-tokens in <metrics>
</step>
```

### 8.2 Modified execute-phase.md (Execution Step)

**New step in `<step name="parse_segments">`**:

```markdown
<enhanced_routing>
**NEW: Complexity-aware parallel subagent spawning**

1. Build execution graph from task dependencies
2. For each batch in graph:
   - If batch is parallel AND all tasks are autonomous (type="auto"):
     * Assign models per task (from task.model attribute)
     * Spawn up to 5 parallel subagents (one per task group)
     * Wait for all to complete before next batch
   - If batch is sequential OR has checkpoints:
     * Execute in main context
     * Follow existing checkpoint protocol

3. Benefits:
   - Main context: 10-20% (orchestration + checkpoints only)
   - Each subagent: fresh 0-30% (independent tasks)
   - Parallel multiplier: 3 Haiku agents < 1 Sonnet
   - Higher quality throughout execution
</enhanced_routing>
```

### 8.3 Summary.md Enhancement

**New frontmatter field**:

```yaml
---
# ... existing fields ...

# Parallelization metrics
execution:
  parallel_batches: 2
  subagent_spawns: 5
  total_subagent_tokens: 45000
  main_context_tokens: 8000
  parallelization_efficiency: 0.92  # (sequential cost) / (parallel cost)
  token_savings_vs_sequential: 35000
---
```

---

## Part 9: Practical Implementation Guide

### 9.1 Phase 1: Annotation Only (No Execution Changes)

**Goal**: Add execution metadata to existing plans without changing execution behavior

**Changes**:
1. Add `subagent`, `model`, `parallel`, `depends-on`, `context-mode` attributes to all tasks
2. Add `<metrics>` section with `<estimated-tokens>` and `<estimated-duration>`
3. Add `<task_dependency_graph>` section to plan (visualization only)
4. Update PLAN.md template with new attributes
5. Create `.planning/.token-stats.json` for baseline tracking

**Effort**: Low (documentation update, no execution changes)

**Validation**:
- All existing plans updated with metadata
- No changes to actual execution yet
- Teams can see proposed parallelization without implementing it

### 9.2 Phase 2: Implement Parallel Subagent Spawning

**Goal**: Auto-spawn subagents for parallel task batches

**Changes**:
1. Implement `ParallelSubagentOrchestrator` (from Part 5.2)
2. Build task dependency graph from annotated plans
3. Modify `execute_segments` step to use parallel batches
4. Update subagent prompt builder to support per-task instructions
5. Implement `TokenCostLearner` for tracking (Part 6.2)

**Execution Pattern**:
```
Before (sequential, main context 70%):
Task 1 → Task 2 → Task 3 → Task 4 → Task 5

After (parallel batch, main context 15%):
Task 1 (main)
  ↓
Tasks 2,3,4 (3 parallel subagents, fresh contexts)
  ↓
Task 5 (main)
```

**Effort**: Medium (implementation of orchestrator)

### 9.3 Phase 3: Model Routing and Cost Optimization

**Goal**: Route tasks to Haiku/Sonnet/Opus based on complexity

**Changes**:
1. Implement `ComplexityScorer` (from Part 4.1)
2. Implement `TokenAwareCostRouter` (from Part 4.2)
3. Integrate model selection into `ParallelSubagentOrchestrator`
4. Track actual vs estimated tokens per task type
5. Monthly learning cycles to refine complexity heuristics

**Execution Pattern**:
```
Complexity 1-3 (Haiku, ~$0.01):
- File reads
- Simple fixes
- Straightforward tests

Complexity 4-8 (Sonnet, ~$0.05):
- Most features
- API implementations
- Medium refactoring

Complexity 9-10 (Opus, ~$0.15):
- Architecture decisions
- Critical algorithms
- Novel problems
```

**Effort**: Medium-High (model routing, learning integration)

### 9.4 Phase 4: Advanced Features (Future)

- Auto-detect file size thresholds (skip AuZoom overhead on small files)
- Context inheritance chains for related sequential tasks
- Escalation matrix: Haiku→Sonnet→Opus on failure
- Cross-project learning: share token stats across codebases
- Adaptive complexity scoring based on recent history

---

## Part 10: Metrics and ROI

### 10.1 Cost Reduction (Token-Efficient Execution)

**Current Model** (Sequential, main context dominates):
- Main context: 70% of 200k tokens = 140k tokens
- Task execution: 60k tokens (subagents already used)
- Total: 200k tokens per plan
- Cost: ~$2.40 (Sonnet average)

**Enhanced Model** (Parallel batches, mixed models):
- Main context: 15% of 200k = 30k tokens (orchestration only)
- Task execution:
  - 40% Haiku: 48k tokens × $0.0008/k = $0.04
  - 40% Sonnet: 48k tokens × $0.003/k = $0.14
  - 20% Opus: 24k tokens × $0.015/k = $0.36
- Parallel multiplier: 3 Haiku in parallel costs less than 1 Sonnet
- Total: 102k tokens, ~$0.60

**ROI**:
- Cost reduction: 75% ($1.80 saved per plan)
- 10 plans/month: $18/month savings
- 100 plans/month: $180/month savings
- Quality: Same or higher (fresh context per task)

### 10.2 Context Quality Preservation

**Current Model**:
- Context at task 1: 0% (fresh)
- Context at task 5: 35% (accumulated)
- Context at task 10: 70% (degrading quality)

**Enhanced Model**:
- Sequential tasks: Main context accumulates normally
- Parallel batches: Fresh context per subagent (0% start)
- After parallel batch: Reset to 5% (just checkpoint results)
- Maintains quality throughout

---

## Part 11: Design Document Summary

### Core Principles

1. **Declarative Execution Metadata**: Tasks annotate their execution requirements (model, parallelization) enabling auto-optimization
2. **Dependency Graph-Based Orchestration**: Build explicit dependency graphs from task annotations, identify parallel groups automatically
3. **Cost-Aware Model Routing**: Route tasks to optimal models (Haiku/Sonnet/Opus) based on complexity scoring
4. **Token Learning**: Track actual token usage per task type, refine estimates over time
5. **Fresh Context Preservation**: Spawn parallel subagents with fresh context to avoid quality degradation
6. **Transparent Accounting**: Track and report token usage, parallelization efficiency, cost savings

### Implementation Roadmap

**Phase 1 (Annotation)**: Add metadata to plans—1 week
**Phase 2 (Parallelization)**: Implement subagent orchestration—2 weeks
**Phase 3 (Routing)**: Add model selection—1 week
**Phase 4 (Learning)**: Integrate token tracking and analytics—ongoing

### Expected Outcomes

- **75% cost reduction** on token-heavy plans through parallelization + model routing
- **Higher quality** execution through fresh context per task
- **Transparent accounting** of costs and efficiency gains
- **Automated optimization** without manual intervention
- **Scaling capability** to 50M+ token codebases with fresh-context subagents

---

## File Locations and References

**Current GSD Implementation**:
- `/Users/dhirajd/.claude/get-shit-done/templates/phase-prompt.md` - PLAN.md template
- `/Users/dhirajd/.claude/get-shit-done/templates/summary.md` - SUMMARY.md template
- `/Users/dhirajd/.claude/get-shit-done/workflows/plan-phase.md` - Planning process
- `/Users/dhirajd/.claude/get-shit-done/workflows/execute-phase.md` - Execution process
- `/Users/dhirajd/.claude/get-shit-done/references/checkpoints.md` - Checkpoint protocol

**Proposed Changes**:
1. Update plan-prompt.md template with new task attributes
2. Add `<task_dependency_graph>` section to phase-prompt.md
3. Create new orchestrator component for parallel execution
4. Implement ComplexityScorer and TokenAwareCostRouter
5. Extend execute-phase.md with ParallelSubagentOrchestrator step
6. Add token tracking and learning system

---

**Document Version**: 1.0
**Last Updated**: 2026-01-15
**Status**: Design Document (Ready for Implementation)
