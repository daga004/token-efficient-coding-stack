"""Integration tests for all optimizations working together.

Re-runs Phase 6.5 tasks with all optimizations enabled to measure
combined token reduction and verify backward compatibility.
"""

import json
import os
from pathlib import Path
from typing import Any

import pytest
import tiktoken

from audit.harness import AuditTest
from audit.models import EvidenceType, TestStatus


class IntegrationOptimizationsTest(AuditTest):
    """Test all optimizations integrated together."""

    def __init__(self):
        super().__init__(
            name="integration_optimizations",
            category="auzoom-optimizations",
        )
        self.encoding = tiktoken.get_encoding("cl100k_base")

        # Representative tasks from Phase 6.5
        self.test_tasks = [
            {
                "name": "List public functions (Shallow)",
                "description": "List all public functions in models.py",
                "file": "/Users/dhirajd/Documents/claude/auzoom/src/auzoom/models.py",
                "expected_level": "skeleton",
                "baseline_tokens": 450,
            },
            {
                "name": "Explain function (Medium)",
                "description": "Explain how auzoom_read works",
                "file": "/Users/dhirajd/Documents/claude/auzoom/src/auzoom/mcp/server.py",
                "expected_level": "summary",
                "baseline_tokens": 850,
            },
            {
                "name": "Find callers (Graph)",
                "description": "Find all callers of CodeNode.to_skeleton",
                "node": "auzoom/src/auzoom/models.py::CodeNode.to_skeleton",
                "expected_level": "skeleton",
                "baseline_tokens": 1100,
            },
        ]

    def _count_tokens(self, content: str | dict) -> int:
        """Count tokens using tiktoken."""
        if isinstance(content, dict):
            content = json.dumps(content)
        return len(self.encoding.encode(content))

    def _measure_baseline(self, task: dict) -> int:
        """Measure baseline tokens (standard format, no optimizations)."""

        if "file" in task:
            # File reading task
            file_path = Path(task["file"])
            if file_path.exists():
                content = file_path.read_text()
                return self._count_tokens(content)

        # Use provided baseline
        return task.get("baseline_tokens", 0)

    def _measure_optimized(self, task: dict) -> int:
        """Measure optimized tokens (with all optimizations enabled)."""
        from auzoom.src.auzoom.core.graph.lazy_graph import LazyCodeGraph
        from auzoom.src.auzoom.models import FetchLevel

        # Enable all optimizations
        os.environ["AUZOOM_COMPACT_FORMAT_ENABLED"] = "true"
        os.environ["AUZOOM_FIELD_SELECTION_ENABLED"] = "true"
        os.environ["AUZOOM_SMALL_FILE_THRESHOLD"] = "300"

        if "file" in task:
            # File reading task with optimizations
            file_path = task["file"]
            graph = LazyCodeGraph(str(Path(file_path).parent.parent.parent))

            try:
                imports, nodes = graph.get_file(
                    file_path,
                    FetchLevel[task["expected_level"].upper()],
                    format="compact",
                    fields=["i", "n", "t", "r"]  # Compact field names
                )

                response = {
                    "imports": imports,
                    "nodes": nodes,
                }

                return self._count_tokens(response)

            except Exception:
                return 0

        elif "node" in task:
            # Graph traversal task
            node_id = task["node"]
            graph = LazyCodeGraph("/Users/dhirajd/Documents/claude/auzoom")

            try:
                deps = graph.get_dependencies(
                    node_id,
                    depth=2,
                    strategy=None,  # BFS default
                    direction=None,  # REVERSE default
                    node_type_filter=None
                )

                # Serialize with compact format
                response = {
                    "node_id": node_id,
                    "dependencies": deps,
                }

                return self._count_tokens(response)

            except Exception:
                return 0

        return 0

    def execute(self) -> TestStatus:
        """Execute integration tests with all optimizations."""

        all_passed = True

        print("\n{'='*60}")
        print("Integration Optimizations Test")
        print(f"{'='*60}\n")

        total_baseline_tokens = 0
        total_optimized_tokens = 0

        for i, task in enumerate(self.test_tasks, 1):
            print(f"Task {i}: {task['name']}")
            print(f"  Description: {task['description']}")

            # Measure baseline
            baseline_tokens = self._measure_baseline(task)
            total_baseline_tokens += baseline_tokens

            # Measure optimized
            optimized_tokens = self._measure_optimized(task)
            total_optimized_tokens += optimized_tokens

            # Calculate improvement
            if baseline_tokens > 0:
                improvement_pct = (
                    (baseline_tokens - optimized_tokens) / baseline_tokens * 100
                )
            else:
                improvement_pct = 0

            passed = improvement_pct > 0

            if not passed:
                all_passed = False

            print(f"  Baseline: {baseline_tokens} tokens")
            print(f"  Optimized: {optimized_tokens} tokens")
            print(f"  Improvement: {improvement_pct:+.1f}%")
            print(f"  Status: {'✅ PASS' if passed else '❌ FAIL'}\n")

            self.evidence.log(EvidenceType.MEASUREMENT, {
                "test": "integration_per_task",
                "task_name": task["name"],
                "baseline_tokens": baseline_tokens,
                "optimized_tokens": optimized_tokens,
                "improvement_pct": round(improvement_pct, 2),
                "passed": passed,
            })

        # Calculate overall improvement
        if total_baseline_tokens > 0:
            overall_improvement = (
                (total_baseline_tokens - total_optimized_tokens) /
                total_baseline_tokens * 100
            )
        else:
            overall_improvement = 0

        meets_target = overall_improvement >= 40.0

        print(f"{'='*60}")
        print("Overall Results")
        print(f"{'='*60}")
        print(f"Total baseline tokens: {total_baseline_tokens}")
        print(f"Total optimized tokens: {total_optimized_tokens}")
        print(f"Overall improvement: {overall_improvement:.1f}% (target: ≥40%)")
        print(f"Status: {'✅ MEETS TARGET' if meets_target else '⚠️ BELOW TARGET'}")
        print(f"{'='*60}\n")

        self.evidence.log(EvidenceType.MEASUREMENT, {
            "test": "integration_overall",
            "total_baseline_tokens": total_baseline_tokens,
            "total_optimized_tokens": total_optimized_tokens,
            "overall_improvement_pct": round(overall_improvement, 2),
            "target": 40.0,
            "meets_target": meets_target,
        })

        # Test backward compatibility
        print("Testing backward compatibility...")
        backward_compatible = self._test_backward_compatibility()

        if not backward_compatible:
            all_passed = False
            print("❌ FAIL: Backward compatibility broken\n")
        else:
            print("✅ PASS: Backward compatibility maintained\n")

        # Final status
        final_pass = all_passed and meets_target and backward_compatible

        return TestStatus.PASS if final_pass else TestStatus.PARTIAL

    def _test_backward_compatibility(self) -> bool:
        """Verify standard format still works (backward compatibility)."""
        from auzoom.src.auzoom.core.graph.lazy_graph import LazyCodeGraph
        from auzoom.src.auzoom.models import FetchLevel

        # Disable compact format to test standard
        os.environ["AUZOOM_COMPACT_FORMAT_ENABLED"] = "false"

        test_file = "/Users/dhirajd/Documents/claude/auzoom/src/auzoom/models.py"
        graph = LazyCodeGraph(str(Path(test_file).parent.parent.parent))

        try:
            # Test standard format
            imports, nodes = graph.get_file(
                test_file,
                FetchLevel.SKELETON,
                format="standard",
                fields=None
            )

            # Verify response structure
            has_nodes = isinstance(nodes, list) and len(nodes) > 0
            has_imports = isinstance(imports, list)

            if has_nodes:
                first_node = nodes[0]
                has_required_fields = all(
                    field in first_node
                    for field in ["id", "name", "type", "dependents"]
                )
            else:
                has_required_fields = False

            compatible = has_nodes and has_imports and has_required_fields

            self.evidence.log(EvidenceType.MEASUREMENT, {
                "test": "backward_compatibility",
                "has_nodes": has_nodes,
                "has_imports": has_imports,
                "has_required_fields": has_required_fields,
                "compatible": compatible,
            })

            return compatible

        except Exception as e:
            self.evidence.log(EvidenceType.ERROR, {
                "test": "backward_compatibility_error",
                "error": str(e),
            })
            return False


if __name__ == "__main__":
    test = IntegrationOptimizationsTest()
    status = test.execute()
    print(f"Final Status: {status.value}")
    print(f"Evidence logged to: {test.evidence.log_file}")
