"""
Phase 6.5 Plan 01: Progressive Traversal Interaction Pattern Tests

Tests to validate that agents naturally traverse progressively (skeleton → summary → full)
rather than immediately requesting full depth.

Each task has:
- task_id: Unique identifier
- description: Task prompt for the agent
- expected_depth: Expected max depth (1.0=skeleton, 2.0=summary, 3.0=full)
- success_criteria: What constitutes correct output
- task_type: shallow, medium, deep, or graph
"""

import pytest

# Task definitions for progressive traversal validation
PROGRESSIVE_TRAVERSAL_TASKS = [
    # SHALLOW TASKS (skeleton sufficient - 2 tasks)
    {
        "task_id": 1,
        "description": "List all public functions in auzoom/src/auzoom/server.py",
        "expected_depth": 1.0,
        "success_criteria": "Function list accurate, includes only public functions (no underscore prefix), no deeper reads needed",
        "task_type": "shallow",
        "expected_files": ["auzoom/src/auzoom/server.py"],
        "baseline_tokens": 450,  # Full read of server.py
    },
    {
        "task_id": 2,
        "description": "Show module structure of orchestrator/ directory",
        "expected_depth": 1.0,
        "success_criteria": "Complete file list with module names, basic structure overview",
        "task_type": "shallow",
        "expected_files": ["orchestrator/*.py"],  # Multiple skeleton reads
        "baseline_tokens": 800,  # Estimate for multiple files
    },

    # MEDIUM DEPTH TASKS (summary sufficient - 3 tasks)
    {
        "task_id": 3,
        "description": "What does auzoom_read function do in server.py?",
        "expected_depth": 2.0,
        "success_criteria": "Accurate description of function purpose, parameters, return value - without full implementation details",
        "task_type": "medium",
        "expected_files": ["auzoom/src/auzoom/server.py"],
        "baseline_tokens": 450,
    },
    {
        "task_id": 4,
        "description": "Find all MCP tools defined in server.py",
        "expected_depth": 2.0,
        "success_criteria": "Complete list of tool names with function signatures",
        "task_type": "medium",
        "expected_files": ["auzoom/src/auzoom/server.py"],
        "baseline_tokens": 450,
    },
    {
        "task_id": 5,
        "description": "Explain the caching strategy in auzoom/src/auzoom/cache.py",
        "expected_depth": 2.0,
        "success_criteria": "Correct explanation of cache strategy (LRU, TTL, etc.) without full implementation",
        "task_type": "medium",
        "expected_files": ["auzoom/src/auzoom/cache.py"],
        "baseline_tokens": 350,
    },

    # DEEP TASKS (full read required - 3 tasks)
    {
        "task_id": 6,
        "description": "Review token counting logic in auzoom/src/auzoom/parser.py and identify any potential bugs",
        "expected_depth": 3.0,
        "success_criteria": "Full code review with either bug identification or confirmation of correctness",
        "task_type": "deep",
        "expected_files": ["auzoom/src/auzoom/parser.py"],
        "baseline_tokens": 500,
    },
    {
        "task_id": 7,
        "description": "Add comprehensive error handling to auzoom_validate function",
        "expected_depth": 3.0,
        "success_criteria": "Error handling added correctly, handles edge cases, maintains function contract",
        "task_type": "deep",
        "expected_files": ["auzoom/src/auzoom/validate.py"],
        "baseline_tokens": 400,
    },
    {
        "task_id": 8,
        "description": "Optimize the dependency resolution algorithm in auzoom/src/auzoom/graph.py for better performance",
        "expected_depth": 3.0,
        "success_criteria": "Optimization implemented, performance improved, correctness maintained",
        "task_type": "deep",
        "expected_files": ["auzoom/src/auzoom/graph.py"],
        "baseline_tokens": 600,
    },

    # GRAPH NAVIGATION TASKS (dependency traversal - 2 tasks)
    {
        "task_id": 9,
        "description": "Find all functions that call validate_path in the auzoom codebase",
        "expected_depth": 1.5,
        "success_criteria": "Complete list of callers using dependency graph, no full file reads",
        "task_type": "graph",
        "expected_files": ["auzoom/src/auzoom/validate.py", "auzoom/src/auzoom/server.py"],
        "baseline_tokens": 850,  # Would need to read multiple files
    },
    {
        "task_id": 10,
        "description": "Show the call chain from auzoom_read to Python AST parsing",
        "expected_depth": 2.0,
        "success_criteria": "Accurate call chain with intermediate functions, no full implementation details needed",
        "task_type": "graph",
        "expected_files": ["auzoom/src/auzoom/server.py", "auzoom/src/auzoom/parser.py"],
        "baseline_tokens": 950,
    },
]


@pytest.mark.parametrize("task", PROGRESSIVE_TRAVERSAL_TASKS, ids=lambda t: f"task_{t['task_id']}_{t['task_type']}")
def test_progressive_traversal_task(task):
    """
    Test progressive traversal behavior for a single task.

    This test will be executed by the progressive_executor.py which spawns
    real Task agents and logs their interaction patterns.
    """
    # This is a test definition - actual execution happens in progressive_executor.py
    pass


def get_tasks_by_type(task_type):
    """Get all tasks of a specific type."""
    return [t for t in PROGRESSIVE_TRAVERSAL_TASKS if t["task_type"] == task_type]


def get_expected_depth_distribution():
    """Calculate expected depth distribution."""
    depths = [t["expected_depth"] for t in PROGRESSIVE_TRAVERSAL_TASKS]
    return {
        "avg_depth": sum(depths) / len(depths),
        "shallow_count": len([d for d in depths if d == 1.0]),
        "medium_count": len([d for d in depths if d == 2.0]),
        "deep_count": len([d for d in depths if d == 3.0]),
        "graph_count": len([d for d in depths if 1.0 < d < 2.0]),
    }


if __name__ == "__main__":
    # Print task summary
    print("Progressive Traversal Tasks Summary")
    print("=" * 60)

    for task_type in ["shallow", "medium", "deep", "graph"]:
        tasks = get_tasks_by_type(task_type)
        print(f"\n{task_type.upper()} tasks ({len(tasks)}):")
        for task in tasks:
            print(f"  {task['task_id']}. {task['description'][:60]}...")
            print(f"     Expected depth: {task['expected_depth']}, Baseline: {task['baseline_tokens']} tokens")

    print("\n" + "=" * 60)
    dist = get_expected_depth_distribution()
    print(f"Expected average depth: {dist['avg_depth']:.2f}")
    print(f"Distribution: {dist['shallow_count']} shallow, {dist['medium_count']} medium, {dist['deep_count']} deep, {dist['graph_count']} graph")
