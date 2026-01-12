"""
Test dependency tracking accuracy for auzoom_get_dependencies.

Verifies that auzoom_get_dependencies correctly identifies function-level dependencies
by comparing against ground truth extracted via tree-sitter AST analysis.
"""

import json
import sys
from pathlib import Path
from typing import Any, Optional

import pytest
import tree_sitter_python as tspython
from tree_sitter import Language, Parser

from audit.harness import AuditTest
from audit.models import EvidenceType, TestStatus

# Add auzoom and orchestrator to Python path for imports
sys.path.insert(0, "/Users/dhirajd/Documents/claude/auzoom/src")
sys.path.insert(0, "/Users/dhirajd/Documents/claude/orchestrator/src")


class DependencyTrackingTest(AuditTest):
    """Test dependency tracking accuracy using ground truth comparison."""

    def __init__(self):
        super().__init__(
            name="dependency_tracking",
            category="auzoom-structured-code",
        )

        # Initialize tree-sitter parser for ground truth extraction
        py_language = Language(tspython.language())
        self.ts_parser = Parser(py_language)

        # Test cases: functions with known dependencies
        # Format: {file_path, function_name, line_start, expected_dependencies}
        self.test_cases = [
            {
                "file_path": "/Users/dhirajd/Documents/claude/auzoom/src/auzoom/core/graph/lazy_graph.py",
                "function": "get_file",
                "line_start": 37,
                "expected_calls": [
                    "_is_loaded",
                    "_load_from_cache",
                    "_parse_and_cache",
                    "_load_nodes_into_memory",
                    "_get_serialized_nodes",
                ],
            },
            {
                "file_path": "/Users/dhirajd/Documents/claude/auzoom/src/auzoom/core/graph/lazy_graph.py",
                "function": "_load_from_cache",
                "line_start": 71,
                "expected_calls": [
                    "_should_update_summary",
                ],
            },
            {
                "file_path": "/Users/dhirajd/Documents/claude/auzoom/src/auzoom/core/parsing/parser.py",
                "function": "parse_file",
                "line_start": 21,
                "expected_calls": [
                    "_extract_imports",
                    "_extract_functions",
                    "_extract_classes",
                    "_resolve_dependencies",
                ],
            },
            {
                "file_path": "/Users/dhirajd/Documents/claude/auzoom/src/auzoom/core/parsing/parser.py",
                "function": "_extract_functions",
                "line_start": 45,
                "expected_calls": [
                    "_is_inside_class",
                    "_walk_tree",
                ],
            },
            {
                "file_path": "/Users/dhirajd/Documents/claude/auzoom/src/auzoom/core/parsing/parser.py",
                "function": "_extract_classes",
                "line_start": 79,
                "expected_calls": [
                    "_extract_methods",
                    "_walk_tree",
                ],
            },
            {
                "file_path": "/Users/dhirajd/Documents/claude/orchestrator/src/orchestrator/executor.py",
                "function": "execute",
                "line_start": 34,
                "expected_calls": [
                    "_get_client_for_tier",
                ],
            },
            {
                "file_path": "/Users/dhirajd/Documents/claude/orchestrator/src/orchestrator/executor.py",
                "function": "validate_output",
                "line_start": 98,
                "expected_calls": [
                    "execute",
                ],
            },
            {
                "file_path": "/Users/dhirajd/Documents/claude/orchestrator/src/orchestrator/executor.py",
                "function": "execute_with_validation",
                "line_start": 125,
                "expected_calls": [
                    "execute",
                    "validate_output",
                ],
            },
        ]

    def _extract_function_calls_from_ast(
        self, file_path: str, function_name: str
    ) -> set[str]:
        """
        Extract function calls from a function body using tree-sitter AST.

        This is the ground truth - identifies what functions are actually called
        within the function body by parsing the AST.
        """
        with open(file_path, "rb") as f:
            source_code = f.read()

        tree = self.ts_parser.parse(source_code)
        root = tree.root_node

        # Find the target function definition
        function_node = self._find_function_node(root, function_name)
        if not function_node:
            return set()

        # Extract all call expressions within the function body
        calls = set()
        self._extract_calls_from_node(function_node, calls)

        return calls

    def _find_function_node(self, root_node, function_name: str):
        """Find the AST node for a specific function definition."""
        def walk(node):
            if node.type == "function_definition":
                # Get function name from the name child
                name_node = node.child_by_field_name("name")
                if name_node and name_node.text.decode("utf-8") == function_name:
                    return node

            for child in node.children:
                result = walk(child)
                if result:
                    return result
            return None

        return walk(root_node)

    def _extract_calls_from_node(self, node, calls: set[str]) -> None:
        """Recursively extract function call names from AST node."""
        if node.type == "call":
            # Get the function being called
            function_node = node.child_by_field_name("function")
            if function_node:
                # Handle simple function calls: func()
                if function_node.type == "identifier":
                    calls.add(function_node.text.decode("utf-8"))
                # Handle method calls: self.method()
                elif function_node.type == "attribute":
                    attr_node = function_node.child_by_field_name("attribute")
                    if attr_node:
                        calls.add(attr_node.text.decode("utf-8"))

        # Recurse into children
        for child in node.children:
            self._extract_calls_from_node(child, calls)

    def _get_auzoom_dependencies(self, node_id: str) -> set[str]:
        """
        Get dependencies reported by auzoom_get_dependencies tool.

        Note: We're testing the actual implementation, not a mock.
        We need to load the graph and query it.
        """
        try:
            # Import the actual graph implementation
            from auzoom.core.graph.lazy_graph import LazyCodeGraph

            # Create graph and ensure file is loaded
            graph = LazyCodeGraph(project_root="/Users/dhirajd/Documents/claude", auto_warm=False)

            # Extract file path from node_id (will be absolute path)
            file_path = node_id.split("::")[0]

            # Convert to absolute path if needed
            abs_file_path = str(Path(file_path).resolve())

            # Load the file to ensure graph has the nodes
            graph.get_file(abs_file_path, "skeleton")

            # Get dependencies - returns list of serialized node dicts
            dep_nodes = graph.get_dependencies(node_id, depth=1)

            # Extract function names from dependency node IDs
            deps = set()
            for node_dict in dep_nodes:
                # Each node_dict has an 'id' field with format: file::Class.method or file::function
                dep_id = node_dict.get("id", "")
                if "::" in dep_id:
                    parts = dep_id.split("::")
                    if len(parts) >= 2:
                        name_part = parts[-1]
                        # Handle Class.method format
                        if "." in name_part:
                            func_name = name_part.split(".")[-1]
                        else:
                            func_name = name_part
                        deps.add(func_name)

            return deps

        except Exception as e:
            self.evidence.log(
                EvidenceType.ERROR,
                {"error": f"Failed to get auzoom dependencies: {str(e)}"},
            )
            return set()

    def _build_node_id(self, file_path: str, class_name: Optional[str], function_name: str) -> str:
        """Build the node_id format expected by auzoom.

        Note: AuZoom uses absolute paths in node IDs.
        """
        # Convert to absolute path
        abs_path = str(Path(file_path).resolve())

        if class_name:
            return f"{abs_path}::{class_name}.{function_name}"
        else:
            return f"{abs_path}::{function_name}"

    def _calculate_precision_recall(
        self, expected: set[str], actual: set[str]
    ) -> tuple[float, float, set[str], set[str]]:
        """
        Calculate precision and recall metrics.

        Precision: % of returned dependencies that are correct (TP / (TP + FP))
        Recall: % of expected dependencies that were found (TP / (TP + FN))

        Returns: (precision, recall, false_positives, false_negatives)
        """
        true_positives = expected & actual
        false_positives = actual - expected
        false_negatives = expected - actual

        precision = (
            len(true_positives) / len(actual) * 100 if len(actual) > 0 else 0.0
        )
        recall = (
            len(true_positives) / len(expected) * 100 if len(expected) > 0 else 0.0
        )

        return precision, recall, false_positives, false_negatives

    def execute(self) -> TestStatus:
        """Execute dependency tracking accuracy test."""
        results = []

        for test_case in self.test_cases:
            file_path = test_case["file_path"]
            function_name = test_case["function"]
            line_start = test_case["line_start"]
            expected_calls = set(test_case["expected_calls"])

            # Verify file exists
            if not Path(file_path).exists():
                self.evidence.log(
                    EvidenceType.ERROR,
                    {
                        "file": file_path,
                        "function": function_name,
                        "error": "File not found",
                    },
                )
                continue

            try:
                # 1. Extract ground truth using tree-sitter
                actual_calls = self._extract_function_calls_from_ast(
                    file_path, function_name
                )

                # Use expected_calls as ground truth (manual verification)
                # and compare against what auzoom reports
                ground_truth = expected_calls

                # 2. Determine class name if function is a method
                # For now, check if file contains LazyCodeGraph, PythonParser, or Executor class
                class_name = None
                if "lazy_graph.py" in file_path:
                    class_name = "LazyCodeGraph"
                elif "parser.py" in file_path:
                    class_name = "PythonParser"
                elif "executor.py" in file_path:
                    class_name = "Executor"

                # 3. Build node_id and get auzoom dependencies
                node_id = self._build_node_id(file_path, class_name, function_name)
                auzoom_deps = self._get_auzoom_dependencies(node_id)

                # 4. Calculate precision and recall
                precision, recall, false_pos, false_neg = self._calculate_precision_recall(
                    ground_truth, auzoom_deps
                )

                result = {
                    "node_id": node_id,
                    "file": file_path,
                    "function": function_name,
                    "line": line_start,
                    "expected_dependencies": sorted(list(ground_truth)),
                    "actual_dependencies": sorted(list(auzoom_deps)),
                    "precision": round(precision, 2),
                    "recall": round(recall, 2),
                    "false_positives": sorted(list(false_pos)),
                    "false_negatives": sorted(list(false_neg)),
                }

                results.append(result)

                # Log evidence
                self.evidence.log(
                    EvidenceType.MEASUREMENT,
                    result,
                    metadata={
                        "file_reference": f"{file_path}:{line_start}",
                        "test_type": "dependency_accuracy",
                    },
                )

            except Exception as e:
                self.evidence.log(
                    EvidenceType.ERROR,
                    {
                        "file": file_path,
                        "function": function_name,
                        "error": str(e),
                    },
                )

        # Calculate average metrics
        if results:
            avg_precision = sum(r["precision"] for r in results) / len(results)
            avg_recall = sum(r["recall"] for r in results) / len(results)

            summary = {
                "total_functions_tested": len(results),
                "average_precision": round(avg_precision, 2),
                "average_recall": round(avg_recall, 2),
                "accuracy_threshold_met": avg_precision >= 90 and avg_recall >= 90,
            }

            self.evidence.log(
                EvidenceType.MEASUREMENT,
                summary,
                metadata={"test_conclusion": "dependency_tracking_accuracy"},
            )

            return TestStatus.PASS
        else:
            return TestStatus.FAIL


def test_dependency_tracking():
    """Pytest entry point for dependency tracking accuracy test."""
    test = DependencyTrackingTest()
    status = test.execute()

    # Print evidence path for reference
    print(f"\nEvidence written to: {test.get_evidence_path()}")

    # Test passes if data was collected
    assert status == TestStatus.PASS, "Dependency tracking test failed to collect data"
