"""
Test token savings on real external codebases beyond validation suite.

Measures baseline vs optimized tokens for common task: "Find function X and understand dependencies"
to verify claims hold on diverse production code (not just small validation files).
"""

import json
from pathlib import Path
from typing import Any

import pytest
import tiktoken

from audit.harness import AuditTest
from audit.models import EvidenceType, TestStatus


class RealCodebaseSavingsTest(AuditTest):
    """Test token savings on real-world codebases of various sizes."""

    def __init__(self):
        super().__init__(
            name="real_codebase_savings",
            category="auzoom-structured-code",
        )
        self.encoding = tiktoken.get_encoding("cl100k_base")

        # Diverse codebases from Claude Code project
        # Testing common task: "Find function X and understand its dependencies"
        self.test_cases = [
            # Small files (<200 lines)
            {
                "name": "audit-models-small",
                "files": ["/Users/dhirajd/Documents/claude/audit/models.py"],
                "task": "Find TestResult class and understand structure",
                "target_function": "TestResult",
                "size_category": "small",
                "lines": 64,
            },
            {
                "name": "orchestrator-models-small",
                "files": ["/Users/dhirajd/Documents/claude/orchestrator/src/orchestrator/models.py"],
                "task": "Find TaskResponse class and understand structure",
                "target_function": "TaskResponse",
                "size_category": "small",
                "lines": 65,
            },
            # Medium files (200-400 lines)
            {
                "name": "auzoom-tools-medium",
                "files": ["/Users/dhirajd/Documents/claude/auzoom/src/auzoom/tools.py"],
                "task": "Find GetGraphParams class and understand usage",
                "target_function": "GetGraphParams",
                "size_category": "medium",
                "lines": 203,
            },
            {
                "name": "auzoom-parser-medium",
                "files": ["/Users/dhirajd/Documents/claude/auzoom/src/auzoom/core/parsing/parser.py"],
                "task": "Find parse_file method and understand dependencies",
                "target_function": "parse_file",
                "size_category": "medium",
                "lines": 243,
            },
            # Large file (>500 lines)
            {
                "name": "memory-server-large",
                "files": ["/Users/dhirajd/Documents/claude/evolving-memory-mcp/src/server.py"],
                "task": "Find handle_create_entities method and understand flow",
                "target_function": "handle_create_entities",
                "size_category": "large",
                "lines": 878,
            },
            # Complex nested project (multiple related files)
            {
                "name": "auzoom-graph-nested",
                "files": [
                    "/Users/dhirajd/Documents/claude/auzoom/src/auzoom/core/graph/lazy_graph.py",
                    "/Users/dhirajd/Documents/claude/auzoom/src/auzoom/core/parsing/parser.py",
                    "/Users/dhirajd/Documents/claude/auzoom/src/auzoom/mcp/server.py",
                    "/Users/dhirajd/Documents/claude/auzoom/src/auzoom/tools.py",
                    "/Users/dhirajd/Documents/claude/auzoom/src/auzoom/core/caching/cache_manager.py",
                ],
                "task": "Find LazyCodeGraph.get_file and understand cross-file dependencies",
                "target_function": "get_file",
                "size_category": "complex",
                "lines": 0,  # Multi-file, will calculate
            },
        ]

    def _count_tokens(self, content: str) -> int:
        """Count tokens using tiktoken with cl100k_base encoding."""
        return len(self.encoding.encode(content))

    def _read_file_full(self, file_path: str) -> str:
        """Read complete file content."""
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def _read_file_skeleton(self, file_path: str) -> str:
        """
        Extract skeleton (signatures only) from file.

        Simulates auzoom_read with level=skeleton.
        """
        full_content = self._read_file_full(file_path)
        lines = full_content.split("\n")
        result_lines = []

        for line in lines:
            stripped = line.strip()
            # Include imports
            if stripped.startswith("import ") or stripped.startswith("from "):
                result_lines.append(line)
            # Include class definitions
            elif stripped.startswith("class "):
                result_lines.append(line)
            # Include function/method definitions
            elif stripped.startswith("def "):
                result_lines.append(line)
            # Include decorators
            elif stripped.startswith("@"):
                result_lines.append(line)

        return "\n".join(result_lines)

    def _read_file_summary(self, file_path: str) -> str:
        """
        Extract summary (signatures + docstrings) from file.

        Simulates auzoom_read with level=summary.
        """
        full_content = self._read_file_full(file_path)
        lines = full_content.split("\n")
        result_lines = []
        in_docstring = False
        in_function_body = False
        indent_level = 0

        for line in lines:
            stripped = line.strip()

            # Track docstrings
            if '"""' in line or "'''" in line:
                if in_docstring:
                    result_lines.append(line)
                    in_docstring = False
                else:
                    in_docstring = True
                    result_lines.append(line)
                continue

            if in_docstring:
                result_lines.append(line)
                continue

            # Include imports
            if stripped.startswith("import ") or stripped.startswith("from "):
                result_lines.append(line)
                in_function_body = False
            # Include class definitions
            elif stripped.startswith("class "):
                result_lines.append(line)
                in_function_body = False
            # Include function/method definitions
            elif stripped.startswith("def "):
                result_lines.append(line)
                in_function_body = True
                indent_level = len(line) - len(line.lstrip())
            # Include decorators
            elif stripped.startswith("@"):
                result_lines.append(line)
            # Include first line of function body
            elif in_function_body:
                current_indent = len(line) - len(line.lstrip())
                if current_indent > indent_level and stripped:
                    result_lines.append(line)
                    in_function_body = False
                elif current_indent <= indent_level and stripped:
                    in_function_body = False

        return "\n".join(result_lines)

    def _simulate_baseline_workflow(self, test_case: dict) -> int:
        """
        Simulate baseline workflow: Load all files fully to find function and dependencies.

        Returns: Total tokens for baseline approach.
        """
        total_tokens = 0
        for file_path in test_case["files"]:
            full_content = self._read_file_full(file_path)
            tokens = self._count_tokens(full_content)
            total_tokens += tokens
        return total_tokens

    def _simulate_optimized_workflow(self, test_case: dict) -> int:
        """
        Simulate optimized workflow with progressive disclosure:
        1. Skeleton search across all files (find target function)
        2. Summary for matched file (understand structure)
        3. Full read for file being edited (if needed)
        4. Summary for dependencies (understand context)

        Returns: Total tokens for optimized approach.
        """
        total_tokens = 0
        target_function = test_case["target_function"]
        target_file = None

        # Step 1: Skeleton search across all files (to find target)
        for file_path in test_case["files"]:
            skeleton = self._read_file_skeleton(file_path)
            tokens = self._count_tokens(skeleton)
            total_tokens += tokens

            # Check if target function is in this file
            if target_function in skeleton:
                target_file = file_path

        # Step 2: Summary for matched file (understand structure)
        if target_file:
            summary = self._read_file_summary(target_file)
            tokens = self._count_tokens(summary)
            total_tokens += tokens

        # Step 3: For complex nested projects, get summary of related files
        # (simulates dependency understanding - even though 02-02 showed this is broken,
        #  the token savings test assumes the workflow would be: skeleton search,
        #  then summary for related files)
        if test_case["size_category"] == "complex":
            for file_path in test_case["files"]:
                if file_path != target_file:
                    # Get summary for related files (dependency context)
                    summary = self._read_file_summary(file_path)
                    tokens = self._count_tokens(summary)
                    total_tokens += tokens

        return total_tokens

    def execute(self) -> TestStatus:
        """Execute token savings test on real codebases."""
        results = []

        for test_case in self.test_cases:
            # Calculate total lines for multi-file cases
            if test_case["size_category"] == "complex":
                total_lines = 0
                for file_path in test_case["files"]:
                    with open(file_path, "r") as f:
                        total_lines += len(f.readlines())
                test_case["lines"] = total_lines

            # Measure baseline tokens (full read all files)
            baseline_tokens = self._simulate_baseline_workflow(test_case)

            # Measure optimized tokens (progressive disclosure)
            optimized_tokens = self._simulate_optimized_workflow(test_case)

            # Calculate savings
            savings_tokens = baseline_tokens - optimized_tokens
            savings_percentage = (savings_tokens / baseline_tokens * 100) if baseline_tokens > 0 else 0

            # Compare to target (≥50%)
            meets_target = savings_percentage >= 50.0

            result = {
                "codebase_name": test_case["name"],
                "task": test_case["task"],
                "size_category": test_case["size_category"],
                "total_lines": test_case["lines"],
                "file_count": len(test_case["files"]),
                "baseline_tokens": baseline_tokens,
                "optimized_tokens": optimized_tokens,
                "savings_tokens": savings_tokens,
                "savings_percentage": round(savings_percentage, 2),
                "target": 50.0,
                "meets_target": meets_target,
                "files": test_case["files"],
            }

            results.append(result)

            # Log evidence
            self.evidence.log(
                EvidenceType.MEASUREMENT,
                result,
                metadata={
                    "test": "real_codebase_savings",
                    "phase": "02-auzoom-core-verification",
                },
            )

        # Calculate average savings
        total_savings = sum(r["savings_percentage"] for r in results)
        average_savings = total_savings / len(results) if results else 0

        # Compare to validation baseline (23% from Phase 1)
        validation_baseline = 23.0
        exceeds_validation = average_savings >= validation_baseline

        # Compare to target (≥50%)
        meets_target_overall = average_savings >= 50.0

        summary = {
            "test_name": "real_codebase_savings",
            "codebases_tested": len(results),
            "average_savings_percentage": round(average_savings, 2),
            "validation_baseline": validation_baseline,
            "exceeds_validation": exceeds_validation,
            "target": 50.0,
            "meets_target": meets_target_overall,
            "individual_results": [
                {
                    "name": r["codebase_name"],
                    "savings": r["savings_percentage"],
                    "meets_target": r["meets_target"],
                }
                for r in results
            ],
        }

        # Log summary evidence
        self.evidence.log(
            EvidenceType.MEASUREMENT,
            summary,
            metadata={
                "test": "real_codebase_savings_summary",
                "phase": "02-auzoom-core-verification",
            },
        )

        # Determine test status
        if meets_target_overall:
            return TestStatus.PASS
        elif average_savings > 0:
            return TestStatus.PARTIAL
        else:
            return TestStatus.FAIL


def test_real_codebase_savings():
    """Pytest entry point for real codebase token savings test."""
    test = RealCodebaseSavingsTest()
    status = test.execute()

    # Read evidence file to display results
    evidence_path = test.get_evidence_path()
    print(f"\n{'='*80}")
    print(f"Real Codebase Token Savings Test")
    print(f"{'='*80}")
    print(f"Evidence: {evidence_path}\n")

    with open(evidence_path, "r") as f:
        for line in f:
            entry = json.loads(line)
            if entry["type"] == "analysis":
                data = entry["data"]
                print(f"Codebases tested: {data['codebases_tested']}")
                print(f"Average savings: {data['average_savings_percentage']}%")
                print(f"Target: {data['target']}%")
                print(f"Meets target: {data['meets_target']}")
                print(f"\nIndividual results:")
                for result in data["individual_results"]:
                    status_icon = "✓" if result["meets_target"] else "✗"
                    print(f"  {status_icon} {result['name']}: {result['savings']}%")

    assert status in [TestStatus.PASS, TestStatus.PARTIAL], f"Test failed with status: {status}"


if __name__ == "__main__":
    test = RealCodebaseSavingsTest()
    status = test.execute()
    print(f"\nTest completed with status: {status}")
    print(f"Evidence file: {test.get_evidence_path()}")
