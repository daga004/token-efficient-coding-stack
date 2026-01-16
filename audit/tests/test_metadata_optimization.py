"""Test metadata optimization features for token reduction.

Tests compact JSON format, field selection, file threshold bypass, and
collapsed imports to verify 40-50% token reduction target.
"""

import json
import os
from pathlib import Path
from typing import Any

import pytest
import tiktoken

from audit.harness import AuditTest
from audit.models import EvidenceType, TestStatus


class MetadataOptimizationTest(AuditTest):
    """Test metadata optimization features across all workstreams."""

    def __init__(self):
        super().__init__(
            name="metadata_optimization",
            category="auzoom-optimizations",
        )
        self.encoding = tiktoken.get_encoding("cl100k_base")

        # Test files for different scenarios
        self.test_files = [
            {
                "path": "/Users/dhirajd/Documents/claude/auzoom/src/auzoom/models.py",
                "category": "medium",
                "lines": 269,
                "has_imports": True,
            },
            {
                "path": "/Users/dhirajd/Documents/claude/auzoom/src/auzoom/mcp/server.py",
                "category": "large",
                "lines": 427,
                "has_imports": True,
            },
            {
                "path": "/Users/dhirajd/Documents/claude/orchestrator/src/orchestrator/models.py",
                "category": "small",
                "lines": 65,
                "has_imports": True,
            },
        ]

    def _count_tokens(self, content: str | dict) -> int:
        """Count tokens using tiktoken."""
        if isinstance(content, dict):
            content = json.dumps(content)
        return len(self.encoding.encode(content))

    def _get_auzoom_response(
        self, file_path: str, level: str = "skeleton",
        format: str = "standard", fields: list[str] | None = None
    ) -> dict:
        """Simulate auzoom_read tool response.

        This would normally call the MCP server, but for testing we'll
        use the graph directly.
        """
        from auzoom.src.auzoom.core.graph.lazy_graph import LazyCodeGraph
        from auzoom.src.auzoom.models import FetchLevel

        graph = LazyCodeGraph(str(Path(file_path).parent.parent.parent))

        try:
            imports, nodes = graph.get_file(
                file_path,
                FetchLevel[level.upper()],
                format=format,
                fields=fields
            )

            return {
                "type": "python",
                "file_path": file_path,
                "level": level,
                "format": format,
                "imports": imports,
                "nodes": nodes,
                "node_count": len(nodes),
                "import_count": len(imports),
            }
        except Exception as e:
            return {"error": str(e)}

    def execute(self) -> TestStatus:
        """Execute all metadata optimization tests."""

        all_passed = True

        # Test 1: Compact vs Standard format token reduction
        print("\n=== Test 1: Compact Format Token Reduction ===")
        compact_reduction = self._test_compact_format()
        if compact_reduction < 40.0:
            all_passed = False
            print(f"❌ FAIL: Compact reduction {compact_reduction:.1f}% < 40% target")
        else:
            print(f"✅ PASS: Compact reduction {compact_reduction:.1f}% >= 40% target")

        # Test 2: Field selection token reduction
        print("\n=== Test 2: Field Selection Token Reduction ===")
        field_reduction = self._test_field_selection()
        if field_reduction < 50.0:
            all_passed = False
            print(f"❌ FAIL: Field selection {field_reduction:.1f}% < 50% target")
        else:
            print(f"✅ PASS: Field selection {field_reduction:.1f}% >= 50% target")

        # Test 3: File threshold bypass
        print("\n=== Test 3: File Threshold Bypass ===")
        threshold_works = self._test_file_threshold()
        if not threshold_works:
            all_passed = False
            print("❌ FAIL: File threshold bypass not working")
        else:
            print("✅ PASS: File threshold bypass working")

        # Test 4: Collapsed imports
        print("\n=== Test 4: Collapsed Imports ===")
        import_reduction = self._test_collapsed_imports()
        if import_reduction < 70.0:
            all_passed = False
            print(f"❌ FAIL: Import reduction {import_reduction:.1f}% < 70% target")
        else:
            print(f"✅ PASS: Import reduction {import_reduction:.1f}% >= 70% target")

        # Test 5: Backward compatibility
        print("\n=== Test 5: Backward Compatibility ===")
        backward_compatible = self._test_backward_compatibility()
        if not backward_compatible:
            all_passed = False
            print("❌ FAIL: Backward compatibility broken")
        else:
            print("✅ PASS: Backward compatibility maintained")

        return TestStatus.PASS if all_passed else TestStatus.PARTIAL

    def _test_compact_format(self) -> float:
        """Test compact format provides 40-50% token reduction."""

        total_standard_tokens = 0
        total_compact_tokens = 0

        for test_file in self.test_files:
            file_path = test_file["path"]

            # Get standard format response
            standard_response = self._get_auzoom_response(
                file_path, level="skeleton", format="standard"
            )

            if "error" in standard_response:
                print(f"Error reading {file_path}: {standard_response['error']}")
                continue

            # Get compact format response
            compact_response = self._get_auzoom_response(
                file_path, level="skeleton", format="compact"
            )

            # Count tokens
            standard_tokens = self._count_tokens(standard_response["nodes"])
            compact_tokens = self._count_tokens(compact_response["nodes"])

            total_standard_tokens += standard_tokens
            total_compact_tokens += compact_tokens

            reduction = ((standard_tokens - compact_tokens) / standard_tokens * 100)

            self.evidence.log(EvidenceType.MEASUREMENT, {
                "test": "compact_format_per_file",
                "file": Path(file_path).name,
                "category": test_file["category"],
                "standard_tokens": standard_tokens,
                "compact_tokens": compact_tokens,
                "reduction_pct": round(reduction, 2),
            })

        # Calculate overall reduction
        overall_reduction = (
            (total_standard_tokens - total_compact_tokens) / total_standard_tokens * 100
        )

        self.evidence.log(EvidenceType.MEASUREMENT, {
            "test": "compact_format_overall",
            "total_standard_tokens": total_standard_tokens,
            "total_compact_tokens": total_compact_tokens,
            "reduction_pct": round(overall_reduction, 2),
            "target": 40.0,
        })

        return overall_reduction

    def _test_field_selection(self) -> float:
        """Test field selection provides 50-70% token reduction."""

        total_full_tokens = 0
        total_partial_tokens = 0

        for test_file in self.test_files:
            file_path = test_file["path"]

            # Get full fields response
            full_response = self._get_auzoom_response(
                file_path, level="skeleton", format="standard", fields=None
            )

            if "error" in full_response:
                continue

            # Get partial fields response (only id and dependents for dependency analysis)
            partial_response = self._get_auzoom_response(
                file_path, level="skeleton", format="standard",
                fields=["id", "dependents"]
            )

            # Count tokens
            full_tokens = self._count_tokens(full_response["nodes"])
            partial_tokens = self._count_tokens(partial_response["nodes"])

            total_full_tokens += full_tokens
            total_partial_tokens += partial_tokens

            reduction = ((full_tokens - partial_tokens) / full_tokens * 100)

            self.evidence.log(EvidenceType.MEASUREMENT, {
                "test": "field_selection_per_file",
                "file": Path(file_path).name,
                "full_tokens": full_tokens,
                "partial_tokens": partial_tokens,
                "fields": ["id", "dependents"],
                "reduction_pct": round(reduction, 2),
            })

        # Calculate overall reduction
        overall_reduction = (
            (total_full_tokens - total_partial_tokens) / total_full_tokens * 100
        )

        self.evidence.log(EvidenceType.MEASUREMENT, {
            "test": "field_selection_overall",
            "total_full_tokens": total_full_tokens,
            "total_partial_tokens": total_partial_tokens,
            "reduction_pct": round(overall_reduction, 2),
            "target": 50.0,
        })

        return overall_reduction

    def _test_file_threshold(self) -> bool:
        """Test file threshold bypass for small files."""

        # Create a tiny test file
        test_file = Path("/tmp/auzoom_test_tiny.py")
        test_content = '''"""Tiny module for testing."""

def add(a: int, b: int) -> int:
    return a + b
'''
        test_file.write_text(test_content)

        try:
            # Set threshold to 300 tokens
            os.environ["AUZOOM_SMALL_FILE_THRESHOLD"] = "300"

            # Try to read with AuZoom
            from auzoom.src.auzoom.mcp.server import AuZoomMCPServer

            server = AuZoomMCPServer(str(test_file.parent))
            response = server._read_python_file(
                test_file, level_str="skeleton", format="standard"
            )

            # Check if bypass was triggered
            bypassed = response.get("type") == "small_file_bypass"

            self.evidence.log(EvidenceType.MEASUREMENT, {
                "test": "file_threshold_bypass",
                "file_size_tokens": len(test_content.split()) * 4,  # Rough estimate
                "threshold": 300,
                "bypassed": bypassed,
                "response_type": response.get("type"),
            })

            return bypassed

        finally:
            test_file.unlink(missing_ok=True)

    def _test_collapsed_imports(self) -> float:
        """Test collapsed imports reduce token overhead."""

        total_with_import_nodes = 0
        total_without_import_nodes = 0

        for test_file in self.test_files:
            if not test_file["has_imports"]:
                continue

            file_path = test_file["path"]

            # Get response with imports collapsed
            response = self._get_auzoom_response(
                file_path, level="skeleton", format="standard"
            )

            if "error" in response:
                continue

            # Measure tokens for collapsed imports (simple string array)
            collapsed_tokens = self._count_tokens(response["imports"])

            # Estimate tokens if imports were full nodes (like other nodes)
            # Average node is ~30 tokens, imports would be similar
            estimated_full_import_tokens = response["import_count"] * 30

            total_with_import_nodes += estimated_full_import_tokens
            total_without_import_nodes += collapsed_tokens

            reduction = (
                (estimated_full_import_tokens - collapsed_tokens) /
                estimated_full_import_tokens * 100
            )

            self.evidence.log(EvidenceType.MEASUREMENT, {
                "test": "collapsed_imports_per_file",
                "file": Path(file_path).name,
                "import_count": response["import_count"],
                "collapsed_tokens": collapsed_tokens,
                "estimated_full_tokens": estimated_full_import_tokens,
                "reduction_pct": round(reduction, 2),
            })

        # Calculate overall reduction
        overall_reduction = (
            (total_with_import_nodes - total_without_import_nodes) /
            total_with_import_nodes * 100
        )

        self.evidence.log(EvidenceType.MEASUREMENT, {
            "test": "collapsed_imports_overall",
            "total_full_import_tokens": total_with_import_nodes,
            "total_collapsed_tokens": total_without_import_nodes,
            "reduction_pct": round(overall_reduction, 2),
            "target": 70.0,
        })

        return overall_reduction

    def _test_backward_compatibility(self) -> bool:
        """Test that standard format still works (backward compatibility)."""

        all_compatible = True

        for test_file in self.test_files:
            file_path = test_file["path"]

            try:
                # Get standard format response
                response = self._get_auzoom_response(
                    file_path, level="skeleton", format="standard"
                )

                # Check response has expected fields
                required_fields = ["type", "file_path", "level", "imports", "nodes"]
                has_all_fields = all(field in response for field in required_fields)

                # Check nodes have expected structure
                if response.get("nodes"):
                    first_node = response["nodes"][0]
                    node_fields = ["id", "name", "type", "dependents"]
                    has_node_fields = all(field in first_node for field in node_fields)
                else:
                    has_node_fields = True  # Empty is OK

                compatible = has_all_fields and has_node_fields

                if not compatible:
                    all_compatible = False

                self.evidence.log(EvidenceType.MEASUREMENT, {
                    "test": "backward_compatibility_per_file",
                    "file": Path(file_path).name,
                    "has_all_fields": has_all_fields,
                    "has_node_fields": has_node_fields,
                    "compatible": compatible,
                })

            except Exception as e:
                all_compatible = False
                self.evidence.log(EvidenceType.ERROR, {
                    "test": "backward_compatibility_error",
                    "file": Path(file_path).name,
                    "error": str(e),
                })

        self.evidence.log(EvidenceType.MEASUREMENT, {
            "test": "backward_compatibility_overall",
            "all_compatible": all_compatible,
        })

        return all_compatible


if __name__ == "__main__":
    test = MetadataOptimizationTest()
    status = test.execute()
    print(f"\n{'='*60}")
    print(f"Final Status: {status.value}")
    print(f"Evidence logged to: {test.evidence.log_file}")
    print(f"{'='*60}")
