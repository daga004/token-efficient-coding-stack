"""
Challenging task validation suite using real Claude Code execution.

Tests 15 challenging development tasks across complexity spectrum (4.5-8.0).
Uses Task tool to spawn agents for real API execution and token measurement.
"""

import json
import pytest
from datetime import datetime
from pathlib import Path

# Task definitions for challenging validation
CHALLENGING_TASKS = [
    # Previously tested (5 tasks)
    {
        "id": "11",
        "name": "Add type hints to executor.py",
        "complexity": 4.5,
        "expected_model": "claude-3-5-haiku-20241022",
        "description": "Add complete type hints to orchestrator/src/orchestrator/executor.py",
        "files": ["orchestrator/src/orchestrator/executor.py"],
        "requirements": [
            "Add type hints to all function signatures",
            "Add type hints to all class attributes",
            "Import necessary types from typing module",
            "Ensure mypy --strict passes",
        ],
        "success_criteria": [
            "All functions have return type annotations",
            "All parameters have type annotations",
            "No 'Any' types unless necessary",
            "Code runs without errors",
        ],
    },
    {
        "id": "6",
        "name": "Add memoization to token counting",
        "complexity": 5.0,
        "expected_model": "claude-3-5-sonnet-20241022",
        "description": "Add memoization to token counting in auzoom to avoid redundant calculations",
        "files": ["auzoom/src/auzoom/core/parser.py"],
        "requirements": [
            "Add @lru_cache decorator to token counting function",
            "Ensure cached results are used for same inputs",
            "Add cache_info() reporting for diagnostics",
            "Update tests to verify caching behavior",
        ],
        "success_criteria": [
            "Token counting function has caching",
            "Repeated calls return cached results",
            "Tests pass",
            "Performance improvement measurable",
        ],
    },
    {
        "id": "9",
        "name": "Write integration test for routing",
        "complexity": 5.5,
        "expected_model": "claude-3-5-sonnet-20241022",
        "description": "Create integration test for orchestrator model routing logic",
        "files": ["orchestrator/tests/test_routing.py"],
        "requirements": [
            "Test Flash routing for complexity 0-3",
            "Test Haiku routing for complexity 3-5",
            "Test Sonnet routing for complexity 5-8",
            "Test edge cases (boundary values)",
            "Verify model selection matches complexity score",
        ],
        "success_criteria": [
            "Integration test file created",
            "All routing tiers tested",
            "Boundary conditions tested",
            "Tests pass",
        ],
    },
    {
        "id": "7",
        "name": "Add error handling to MCP server",
        "complexity": 6.5,
        "expected_model": "claude-3-5-sonnet-20241022",
        "description": "Add comprehensive error handling to auzoom MCP server",
        "files": ["auzoom/src/auzoom/mcp/server.py"],
        "requirements": [
            "Handle file not found errors gracefully",
            "Handle invalid path errors",
            "Handle parsing errors with clear messages",
            "Add try/except around tool calls",
            "Return structured error responses",
        ],
        "success_criteria": [
            "All MCP tool methods have error handling",
            "Errors return structured JSON responses",
            "Edge cases tested (missing files, invalid paths)",
            "No unhandled exceptions",
        ],
    },
    {
        "id": "13",
        "name": "Implement input sanitization",
        "complexity": 7.0,
        "expected_model": "claude-opus-4-20250514",
        "description": "Add input sanitization to MCP server to prevent path traversal attacks",
        "files": ["auzoom/src/auzoom/mcp/server.py"],
        "requirements": [
            "Validate file paths to prevent directory traversal",
            "Sanitize path inputs (remove .., //, etc.)",
            "Whitelist allowed file extensions",
            "Reject paths outside project root",
            "Add security tests for attack vectors",
        ],
        "success_criteria": [
            "Path traversal attacks blocked (../, /etc/passwd)",
            "Only project files accessible",
            "Security tests pass",
            "No false positives (legitimate paths work)",
        ],
    },
    # Never tested (10 tasks)
    {
        "id": "8",
        "name": "Refactor scoring.py for extensibility",
        "complexity": 6.0,
        "expected_model": "claude-3-5-sonnet-20241022",
        "description": "Refactor orchestrator scoring module to support pluggable scoring strategies",
        "files": ["orchestrator/src/orchestrator/scoring.py"],
        "requirements": [
            "Extract scoring logic into base ScoringStrategy class",
            "Implement ComplexityScorer as concrete strategy",
            "Add strategy registration mechanism",
            "Support multiple scoring strategies",
            "Maintain backward compatibility",
        ],
        "success_criteria": [
            "Strategy pattern implemented",
            "Multiple strategies supported",
            "Existing functionality preserved",
            "Tests pass",
        ],
    },
    {
        "id": "10",
        "name": "Add caching to dependency resolution",
        "complexity": 5.5,
        "expected_model": "claude-3-5-sonnet-20241022",
        "description": "Add caching to auzoom dependency graph traversal",
        "files": ["auzoom/src/auzoom/core/graph.py"],
        "requirements": [
            "Cache resolved dependency graphs",
            "Invalidate cache on file changes",
            "Add TTL for cache entries",
            "Expose cache statistics",
        ],
        "success_criteria": [
            "Dependency resolution cached",
            "Cache hit rate measurable",
            "Stale data avoided",
            "Tests pass",
        ],
    },
    {
        "id": "12",
        "name": "Implement retry logic with exponential backoff",
        "complexity": 6.5,
        "expected_model": "claude-3-5-sonnet-20241022",
        "description": "Add retry logic to orchestrator API calls with exponential backoff",
        "files": ["orchestrator/src/orchestrator/executor.py"],
        "requirements": [
            "Retry failed API calls up to 3 times",
            "Use exponential backoff (1s, 2s, 4s)",
            "Handle rate limiting (429 errors)",
            "Log retry attempts",
            "Make retry config configurable",
        ],
        "success_criteria": [
            "Transient failures recovered",
            "Backoff timing correct",
            "Rate limits respected",
            "Tests pass",
        ],
    },
    {
        "id": "14",
        "name": "Add comprehensive logging",
        "complexity": 5.0,
        "expected_model": "claude-3-5-sonnet-20241022",
        "description": "Add structured logging throughout orchestrator",
        "files": ["orchestrator/src/orchestrator/"],
        "requirements": [
            "Use Python logging module",
            "Log all API calls with timestamps",
            "Log model selection decisions",
            "Log errors with context",
            "Support log levels (DEBUG, INFO, ERROR)",
        ],
        "success_criteria": [
            "Logging configured throughout",
            "Log output structured (JSON)",
            "Log levels work correctly",
            "Performance not impacted",
        ],
    },
    {
        "id": "15",
        "name": "Create benchmark suite",
        "complexity": 6.0,
        "expected_model": "claude-3-5-sonnet-20241022",
        "description": "Create performance benchmark suite for orchestrator",
        "files": ["orchestrator/benchmarks/"],
        "requirements": [
            "Benchmark token counting performance",
            "Benchmark model routing speed",
            "Benchmark cache hit rates",
            "Compare baseline vs optimized",
            "Generate performance report",
        ],
        "success_criteria": [
            "Benchmark suite runnable",
            "Metrics tracked over time",
            "Report generated",
            "CI/CD integration possible",
        ],
    },
    {
        "id": "16",
        "name": "Implement rate limiting",
        "complexity": 6.5,
        "expected_model": "claude-3-5-sonnet-20241022",
        "description": "Add rate limiting to orchestrator to prevent API throttling",
        "files": ["orchestrator/src/orchestrator/rate_limiter.py"],
        "requirements": [
            "Implement token bucket algorithm",
            "Configure different limits per model tier",
            "Queue requests when limit hit",
            "Expose rate limit metrics",
            "Handle burst traffic gracefully",
        ],
        "success_criteria": [
            "Rate limiting enforced",
            "Requests queued appropriately",
            "No API 429 errors",
            "Tests pass",
        ],
    },
    {
        "id": "17",
        "name": "Add metrics collection",
        "complexity": 5.5,
        "expected_model": "claude-3-5-sonnet-20241022",
        "description": "Add metrics collection for orchestrator operations",
        "files": ["orchestrator/src/orchestrator/metrics.py"],
        "requirements": [
            "Track API call counts by model",
            "Track token consumption",
            "Track cost per task",
            "Track success/failure rates",
            "Export to Prometheus format",
        ],
        "success_criteria": [
            "Metrics tracked accurately",
            "Prometheus endpoint works",
            "Metrics queryable",
            "Dashboard displayable",
        ],
    },
    {
        "id": "18",
        "name": "Optimize graph traversal",
        "complexity": 7.5,
        "expected_model": "claude-opus-4-20250514",
        "description": "Optimize auzoom dependency graph traversal for large codebases",
        "files": ["auzoom/src/auzoom/core/graph.py"],
        "requirements": [
            "Implement incremental graph updates",
            "Use efficient graph representation (adjacency list)",
            "Add cycle detection optimization",
            "Profile and optimize hot paths",
            "Benchmark with 1000+ node graphs",
        ],
        "success_criteria": [
            "O(V+E) traversal complexity",
            "Large graphs handled efficiently",
            "Memory usage optimized",
            "Tests pass",
        ],
    },
    {
        "id": "19",
        "name": "Add streaming support",
        "complexity": 7.0,
        "expected_model": "claude-opus-4-20250514",
        "description": "Add streaming API support to orchestrator for real-time responses",
        "files": ["orchestrator/src/orchestrator/executor.py"],
        "requirements": [
            "Implement async streaming API",
            "Stream tokens as they arrive",
            "Handle partial responses",
            "Add streaming cost tracking",
            "Support cancellation",
        ],
        "success_criteria": [
            "Streaming works end-to-end",
            "Tokens streamed incrementally",
            "Cancellation works",
            "Tests pass",
        ],
    },
    {
        "id": "20",
        "name": "Implement transaction support",
        "complexity": 8.0,
        "expected_model": "claude-opus-4-20250514",
        "description": "Add transaction support for multi-step operations in orchestrator",
        "files": ["orchestrator/src/orchestrator/transaction.py"],
        "requirements": [
            "Implement begin/commit/rollback",
            "Track state changes across operations",
            "Support nested transactions",
            "Add transaction logging",
            "Handle failures gracefully",
        ],
        "success_criteria": [
            "Transactions maintain ACID properties",
            "Rollback works correctly",
            "Nested transactions supported",
            "Tests pass",
        ],
    },
]


class ChallengiingTaskValidator:
    """Validator for challenging development tasks using real execution."""

    def __init__(self):
        self.evidence_dir = Path("audit/evidence")
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self.evidence_file = self.evidence_dir / f"challenging_validation_{self.timestamp}.jsonl"

    def log_evidence(self, task_id: str, data: dict) -> None:
        """Log validation evidence to JSONL file."""
        entry = {
            "task_id": task_id,
            "timestamp": datetime.utcnow().isoformat(),
            **data,
        }
        with open(self.evidence_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def score_quality(self, task: dict, baseline_result: str, optimized_result: str) -> dict:
        """
        Score quality of optimized execution vs baseline.

        Returns:
            dict with quality_score (0-100), issues found, and rationale
        """
        # Quality scoring criteria:
        # 100%: Perfect - all requirements met, tests pass, no issues
        # 75%: Mostly working - minor issues, most tests pass
        # 50%: Partial - some functionality works, significant gaps
        # 25%: Broken - major failures, few tests pass
        # 0%: Failure - doesn't work, tests fail

        # This is a placeholder - real scoring would analyze actual code output
        # For this validation, we need to manually inspect results

        return {
            "quality_score": 0,  # To be scored after execution
            "issues": [],
            "rationale": "Manual scoring required after execution",
        }


@pytest.fixture
def validator():
    """Create validator instance."""
    return ChallengiingTaskValidator()


# Generate test cases for all 15 challenging tasks
@pytest.mark.parametrize("task", CHALLENGING_TASKS, ids=lambda t: f"Task{t['id']}")
def test_challenging_task(validator, task):
    """
    Execute challenging task with baseline and optimized approaches.

    This is a PLACEHOLDER test that documents the task structure.
    Real execution requires:
    1. Spawning Task agents for baseline execution (full file reads)
    2. Spawning Task agents for optimized execution (progressive disclosure)
    3. Measuring actual token consumption from agent execution
    4. Analyzing output quality based on success criteria
    5. Scoring quality objectively (not theoretically)

    NOTE: This test is meant to be executed manually or with real API calls.
    Automated execution would be expensive and time-consuming.
    """

    # Log task definition
    validator.log_evidence(
        task["id"],
        {
            "phase": "definition",
            "task_name": task["name"],
            "complexity": task["complexity"],
            "expected_model": task["expected_model"],
            "requirements": task["requirements"],
            "success_criteria": task["success_criteria"],
        },
    )

    print(f"\nTask {task['id']}: {task['name']}")
    print(f"  Complexity: {task['complexity']} → {task['expected_model']}")
    print(f"  Files: {', '.join(task['files'])}")
    print(f"  Requirements: {len(task['requirements'])} items")

    # PLACEHOLDER: Real execution would:
    # 1. Use Task tool to spawn baseline agent
    # 2. Use Task tool to spawn optimized agent
    # 3. Measure tokens from agent execution
    # 4. Score quality based on actual output

    # For now, mark as skipped with documentation
    pytest.skip(
        f"Task {task['id']} definition documented. "
        f"Real execution requires spawning agents with Task tool and measuring actual consumption."
    )


def test_evidence_file_created(validator):
    """Verify evidence file is created."""
    assert validator.evidence_file.exists()

    # Verify all 15 tasks logged
    with open(validator.evidence_file) as f:
        lines = f.readlines()
        assert len(lines) >= 15, f"Expected 15+ evidence entries, got {len(lines)}"


if __name__ == "__main__":
    # When run directly, just show task summary
    print("=" * 80)
    print("CHALLENGING TASK VALIDATION SUITE")
    print("=" * 80)
    print(f"\nTotal tasks: {len(CHALLENGING_TASKS)}")
    print("\nComplexity distribution:")
    for tier in [(4.5, 5.0), (5.0, 6.0), (6.0, 7.0), (7.0, 8.5)]:
        count = sum(1 for t in CHALLENGING_TASKS if tier[0] <= t["complexity"] < tier[1])
        models = set(t["expected_model"] for t in CHALLENGING_TASKS if tier[0] <= t["complexity"] < tier[1])
        print(f"  {tier[0]}-{tier[1]}: {count} tasks ({', '.join(models)})")

    print("\nTasks:")
    for task in CHALLENGING_TASKS:
        print(f"  {task['id']:>2}. {task['name']:<45} (complexity: {task['complexity']})")

    print("\n" + "=" * 80)
    print("Run with: pytest audit/tests/test_challenging_validation.py -v")
    print("=" * 80)
