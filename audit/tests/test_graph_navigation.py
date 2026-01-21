"""
Test suite for graph navigation efficiency validation.

Compares graph-based navigation (auzoom tools) vs baseline search (grep + read)
to measure file read reduction while maintaining quality.

Tasks test:
- Direct dependency finding (callers/callees)
- Circular dependency detection
- Refactoring operations (rename, extract)
- Cross-module analysis

Target: ≥30% file read reduction with 100% quality parity.
"""

import pytest
from dataclasses import dataclass
from typing import List


@dataclass
class GraphTask:
    """Defines a graph navigation task with ground truth and expected file counts."""

    task_id: int
    description: str
    category: str
    ground_truth: List[str]  # Files that are actually relevant
    graph_approach: str  # Description of auzoom tool usage
    baseline_approach: str  # Description of traditional tool usage
    expected_graph_files: int  # Expected file reads with graph
    expected_baseline_files: int  # Expected file reads with baseline
    success_criteria: str


# Task 1: Find all callers of validate_file
TASK_1_FIND_CALLERS = GraphTask(
    task_id=1,
    description="Find all functions that call validate_file in auzoom/src/auzoom/",
    category="dependency_finding",
    ground_truth=[
        "auzoom/src/auzoom/core/validator.py",  # Contains validate_file definition
        "auzoom/src/auzoom/mcp/server.py",  # May call validate_file (via _tool_validate)
    ],
    graph_approach=(
        "1. auzoom_find('validate_file') to locate function\n"
        "2. auzoom_get_dependencies(node_id='...validate_file', reverse=True) to find callers\n"
        "3. auzoom_read only the caller files at skeleton level"
    ),
    baseline_approach=(
        "1. Grep 'validate_file' across all Python files\n"
        "2. Read all matching files to identify actual function calls vs definitions\n"
        "3. Manually inspect each to determine if it's a caller or just a definition"
    ),
    expected_graph_files=2,
    expected_baseline_files=6,
    success_criteria="Find 100% of callers, read ≤70% as many files as baseline"
)


# Task 2: Find all dependencies of _tool_read
TASK_2_FIND_DEPENDENCIES = GraphTask(
    task_id=2,
    description="Find all functions that _tool_read calls (its dependencies)",
    category="dependency_finding",
    ground_truth=[
        "auzoom/src/auzoom/mcp/server.py",  # Contains _tool_read
        "auzoom/src/auzoom/mcp/server.py",  # _read_python_file (called by _tool_read)
        "auzoom/src/auzoom/mcp/server.py",  # _read_non_python_file (called by _tool_read)
        "auzoom/src/auzoom/core/graph/lazy_graph.py",  # LazyCodeGraph (used in _read_python_file)
    ],
    graph_approach=(
        "1. auzoom_find('_tool_read') to locate function\n"
        "2. auzoom_get_dependencies(node_id='..._tool_read', depth=1) to get direct callees\n"
        "3. auzoom_read only dependency files at skeleton level"
    ),
    baseline_approach=(
        "1. Read server.py to find _tool_read implementation\n"
        "2. Manually identify each function call within _tool_read\n"
        "3. Read each dependency file to understand what it does\n"
        "4. May need to read additional files if imports are unclear"
    ),
    expected_graph_files=4,
    expected_baseline_files=8,
    success_criteria="Find 100% of dependencies, read ≤50% as many files as baseline"
)


# Task 3: Show call chain from handle_tool_call to PythonParser
TASK_3_CALL_CHAIN = GraphTask(
    task_id=3,
    description="Show the call chain from server.handle_tool_call to PythonParser",
    category="dependency_finding",
    ground_truth=[
        "auzoom/src/auzoom/mcp/server.py",  # handle_tool_call → _tool_read
        "auzoom/src/auzoom/mcp/server.py",  # _tool_read → _read_python_file
        "auzoom/src/auzoom/core/graph/lazy_graph.py",  # LazyCodeGraph used in _read_python_file
        "auzoom/src/auzoom/core/parsing/parser.py",  # PythonParser
    ],
    graph_approach=(
        "1. auzoom_find('handle_tool_call') and auzoom_find('PythonParser')\n"
        "2. auzoom_get_dependencies(depth=3) to trace call chain\n"
        "3. Read only files in the chain at skeleton level"
    ),
    baseline_approach=(
        "1. Read server.py to see what handle_tool_call calls\n"
        "2. Follow each call manually (may read 5-7 files exploring dead ends)\n"
        "3. Trace through to find PythonParser usage\n"
        "4. May need to read full files to understand complex call patterns"
    ),
    expected_graph_files=4,
    expected_baseline_files=9,
    success_criteria="Find correct call chain, read ≤50% as many files as baseline"
)


# Task 4: Identify circular imports
TASK_4_CIRCULAR_IMPORTS = GraphTask(
    task_id=4,
    description="Identify any circular imports in auzoom/src/auzoom/",
    category="circular_dependency",
    ground_truth=[
        # Based on actual codebase analysis - may be none
        # If none exist, ground_truth = [] and test verifies no false positives
    ],
    graph_approach=(
        "1. auzoom_get_dependencies(depth=3) for all modules\n"
        "2. Detect cycles in dependency graph (graph traversal, no file reads)\n"
        "3. Only read files if cycles found to verify"
    ),
    baseline_approach=(
        "1. Read all Python files in src/auzoom/\n"
        "2. Extract imports from each file manually\n"
        "3. Build import graph manually\n"
        "4. Check for cycles by manual inspection"
    ),
    expected_graph_files=0,  # Graph traversal only, no file reads unless cycles found
    expected_baseline_files=18,  # Must read all files to build import graph
    success_criteria="100% accuracy on cycle detection, massive file read reduction"
)


# Task 5: Fix circular import (if exists)
TASK_5_FIX_CIRCULAR = GraphTask(
    task_id=5,
    description="Fix circular import between validator.py and server.py (if exists)",
    category="circular_dependency",
    ground_truth=[
        "auzoom/src/auzoom/core/validator.py",
        "auzoom/src/auzoom/mcp/server.py",
    ],
    graph_approach=(
        "1. auzoom_get_dependencies to identify cycle (from Task 4)\n"
        "2. auzoom_read only the 2 files involved in the cycle\n"
        "3. Determine which import to break based on dependency direction"
    ),
    baseline_approach=(
        "1. Read both files plus their dependencies to understand structure\n"
        "2. Read import chain files to see what's actually needed\n"
        "3. May read 8-10 files to understand full context before fixing"
    ),
    expected_graph_files=2,
    expected_baseline_files=9,
    success_criteria="Fix correctly with minimal file reads"
)


# Task 6: Rename module cache_manager.py to caching_manager.py
TASK_6_RENAME_MODULE = GraphTask(
    task_id=6,
    description="Rename cache_manager.py to caching_manager.py and update all imports",
    category="refactoring",
    ground_truth=[
        "auzoom/src/auzoom/core/caching/cache_manager.py",  # The file to rename
        "auzoom/src/auzoom/core/caching/__init__.py",  # May import cache_manager
        "auzoom/src/auzoom/mcp/server.py",  # May import from caching
        # Plus any other files that import cache_manager
    ],
    graph_approach=(
        "1. auzoom_find('cache_manager.py') to locate module\n"
        "2. auzoom_get_dependencies(reverse=True) to find all importers\n"
        "3. auzoom_read only the importer files to update imports\n"
        "4. Rename file and update imports"
    ),
    baseline_approach=(
        "1. Grep 'cache_manager' across all files\n"
        "2. Read all matching files (including false positives like comments)\n"
        "3. Manually verify which are actual imports vs mentions\n"
        "4. Update imports and rename"
    ),
    expected_graph_files=6,
    expected_baseline_files=12,
    success_criteria="Find 100% of importers, read ≤50% as many files"
)


# Task 7: Extract validation logic to separate module
TASK_7_EXTRACT_VALIDATION = GraphTask(
    task_id=7,
    description="Extract validation functions from server.py into new validate_tools.py",
    category="refactoring",
    ground_truth=[
        "auzoom/src/auzoom/mcp/server.py",  # Source of validation logic
        "auzoom/src/auzoom/core/validator.py",  # Validation dependencies
        "auzoom/src/auzoom/tools.py",  # Tool definitions
    ],
    graph_approach=(
        "1. auzoom_read server.py at skeleton to identify validation functions\n"
        "2. auzoom_get_dependencies for those functions to find what they call\n"
        "3. auzoom_read only dependency files to understand what to move\n"
        "4. Extract and create new module"
    ),
    baseline_approach=(
        "1. Read server.py fully to find validation functions\n"
        "2. Read validator.py and related files to understand context\n"
        "3. May read 7-9 files to ensure all dependencies are understood\n"
        "4. Extract and create new module"
    ),
    expected_graph_files=4,
    expected_baseline_files=9,
    success_criteria="Identify correct functions to extract, read ≤50% as many files"
)


# Task 8: Analyze data flow from MCP request to response
TASK_8_DATA_FLOW = GraphTask(
    task_id=8,
    description="Trace data flow from MCP request through to final response",
    category="cross_module_analysis",
    ground_truth=[
        "auzoom/src/auzoom/mcp/server.py",  # Entry point (run → handle_tool_call)
        "auzoom/src/auzoom/mcp/jsonrpc_handler.py",  # JSON-RPC handling
        "auzoom/src/auzoom/core/graph/lazy_graph.py",  # Graph operations
        "auzoom/src/auzoom/core/parsing/parser.py",  # Parsing
        "auzoom/src/auzoom/tools.py",  # Response models
    ],
    graph_approach=(
        "1. auzoom_find('run') to locate entry point\n"
        "2. auzoom_get_dependencies(depth=5) to trace execution path\n"
        "3. auzoom_read only files in the critical path at skeleton level\n"
        "4. Progressively go deeper only for unclear parts"
    ),
    baseline_approach=(
        "1. Read server.py to understand entry point\n"
        "2. Manually trace each function call by reading files\n"
        "3. May read 12-15 files exploring different code paths\n"
        "4. Need full reads to understand data transformations"
    ),
    expected_graph_files=6,
    expected_baseline_files=15,
    success_criteria="Trace complete data flow, read ≤40% as many files"
)


# Test suite
ALL_TASKS = [
    TASK_1_FIND_CALLERS,
    TASK_2_FIND_DEPENDENCIES,
    TASK_3_CALL_CHAIN,
    TASK_4_CIRCULAR_IMPORTS,
    TASK_5_FIX_CIRCULAR,
    TASK_6_RENAME_MODULE,
    TASK_7_EXTRACT_VALIDATION,
    TASK_8_DATA_FLOW,
]


@pytest.mark.parametrize("task", ALL_TASKS, ids=lambda t: f"task_{t.task_id}")
def test_graph_navigation_task(task):
    """
    Validates graph navigation task definition.

    Actual execution happens in Task 2 via graph_executor.py.
    This test verifies task structure and expected values.
    """
    # Verify task has all required fields
    assert task.task_id > 0
    assert task.description
    assert task.category in [
        "dependency_finding",
        "circular_dependency",
        "refactoring",
        "cross_module_analysis"
    ]
    assert isinstance(task.ground_truth, list)
    assert task.graph_approach
    assert task.baseline_approach
    assert task.expected_graph_files >= 0
    assert task.expected_baseline_files > task.expected_graph_files  # Graph should read fewer
    assert task.success_criteria

    # Verify expected file reduction is ≥30%
    reduction = (task.expected_baseline_files - task.expected_graph_files) / task.expected_baseline_files * 100
    assert reduction >= 30, f"Task {task.task_id} expected reduction {reduction:.1f}% < 30% target"


def test_task_coverage():
    """Verify we have tasks covering all categories."""
    categories = [t.category for t in ALL_TASKS]
    assert "dependency_finding" in categories
    assert "circular_dependency" in categories
    assert "refactoring" in categories
    assert "cross_module_analysis" in categories


def test_total_expected_reduction():
    """Verify overall expected file reduction meets ≥30% target."""
    total_graph = sum(t.expected_graph_files for t in ALL_TASKS)
    total_baseline = sum(t.expected_baseline_files for t in ALL_TASKS)
    overall_reduction = (total_baseline - total_graph) / total_baseline * 100

    assert overall_reduction >= 30, f"Overall expected reduction {overall_reduction:.1f}% < 30% target"

    print(f"\nExpected metrics across 8 tasks:")
    print(f"  Graph files: {total_graph}")
    print(f"  Baseline files: {total_baseline}")
    print(f"  Reduction: {overall_reduction:.1f}%")
