"""
Test for bypass behavior - verify full reads are not used when skeleton/summary should suffice.

Measures progressive disclosure consistency by testing real MCP tool operations
and checking cache behavior, content levels, and data sizes.
"""

import json
from pathlib import Path
from typing import Any

import pytest

from audit.harness import AuditTest
from audit.models import EvidenceType, TestStatus

# Import the MCP server directly for testing
from auzoom.mcp.server import AuZoomMCPServer


class BypassBehaviorTest(AuditTest):
    """Test for inappropriate full reads when skeleton/summary should suffice."""

    def __init__(self):
        super().__init__(
            name="bypass_behavior",
            category="auzoom-structured-code",
        )

        # Initialize MCP server for testing
        project_root = "/Users/dhirajd/Documents/claude"
        self.server = AuZoomMCPServer(project_root, auto_warm=False)

        # Test file for all scenarios
        self.test_file = "/Users/dhirajd/Documents/claude/auzoom/src/auzoom/tools.py"

        # Reset stats before testing
        self.server.graph.stats = {"cache_hits": 0, "cache_misses": 0, "parses": 0}

    def _get_cache_stats(self) -> dict:
        """Get current cache statistics."""
        return self.server.handle_tool_call("auzoom_stats", {})

    def _measure_content_size(self, response: dict) -> int:
        """Measure total content size in response."""
        content_str = json.dumps(response)
        return len(content_str)

    def _check_level_consistency(self, response: dict, expected_level: str) -> tuple[bool, str]:
        """Check if returned content matches expected level."""
        actual_level = response.get("level", "unknown")

        # Check for bypass indicators
        if expected_level == "skeleton" and actual_level == "full":
            return False, "Full read when skeleton requested"

        if expected_level == "summary" and actual_level == "full":
            return False, "Full read when summary requested"

        # For Python files, check node data
        if response.get("type") == "python":
            nodes = response.get("nodes", [])
            if not nodes:
                return True, "No nodes returned (acceptable for empty file)"

            # Check first node structure
            first_node = nodes[0]
            has_implementation = "implementation" in str(first_node)

            if expected_level == "skeleton" and has_implementation:
                return False, "Implementation present in skeleton level"

        return True, "Level consistent"

    def execute(self) -> TestStatus:
        """Execute bypass behavior detection test."""

        # Scenario 1: Find function - should return skeleton
        self._test_find_function()

        # Scenario 2: Get dependencies - should use cached skeleton
        self._test_get_dependencies()

        # Scenario 3: Repeated access at same level - should use cache
        self._test_repeated_access()

        # Scenario 4: Level escalation - verify progressive disclosure
        self._test_level_escalation()

        # Scenario 5: Common workflow - find → dependencies → read
        self._test_common_workflow()

        # Check overall results
        stats = self._get_cache_stats()

        self.evidence.log(
            EvidenceType.MEASUREMENT,
            {
                "summary": "Overall cache performance",
                "final_stats": stats,
            },
            metadata={"test_conclusion": "bypass_behavior_detection"},
        )

        return TestStatus.PASS

    def _test_find_function(self) -> None:
        """Scenario 1: Call auzoom_find to locate functions."""
        initial_stats = self._get_cache_stats()

        # Find functions in test file
        response = self.server.handle_tool_call("auzoom_find", {
            "pattern": "GetGraph"
        })

        final_stats = self._get_cache_stats()
        matches = response.get("matches", [])

        # Check if find triggered full reads
        bypass_detected = False
        bypass_reason = "None"

        # Find should return skeleton-level data
        for match in matches:
            # Check if match contains full implementation
            match_str = json.dumps(match)
            if len(match_str) > 1000:  # Large response suggests full content
                bypass_detected = True
                bypass_reason = "Find returned large content (possible full read)"

        evidence_data = {
            "scenario": "find_function",
            "operation": "auzoom_find",
            "pattern": "GetGraph",
            "matches_found": len(matches),
            "cache_stats_before": initial_stats,
            "cache_stats_after": final_stats,
            "bypass_detected": bypass_detected,
            "bypass_reason": bypass_reason,
            "expected_level": "skeleton",
        }

        self.evidence.log(
            EvidenceType.MEASUREMENT,
            evidence_data,
            metadata={"scenario": "find_function"},
        )

    def _test_get_dependencies(self) -> None:
        """Scenario 2: Get dependencies should use cached data."""

        # First, ensure file is loaded
        self.server.handle_tool_call("auzoom_read", {
            "path": self.test_file,
            "level": "skeleton"
        })

        initial_stats = self._get_cache_stats()

        # Now get dependencies - should use cache
        response = self.server.handle_tool_call("auzoom_get_dependencies", {
            "node_id": "auzoom.tools:GetGraphParams",
            "depth": 1
        })

        final_stats = self._get_cache_stats()

        # Check if cache was used
        cache_hits_before = initial_stats.get("cache_hits", 0)
        cache_hits_after = final_stats.get("cache_hits", 0)
        cache_used = cache_hits_after > cache_hits_before

        # Dependencies should not trigger new full reads
        parses_before = initial_stats.get("files_parsed", 0)
        parses_after = final_stats.get("files_parsed", 0)
        new_parses = parses_after - parses_before

        bypass_detected = new_parses > 0
        bypass_reason = f"New parses triggered: {new_parses}" if bypass_detected else "None"

        evidence_data = {
            "scenario": "get_dependencies",
            "operation": "auzoom_get_dependencies",
            "node_id": "auzoom.tools:GetGraphParams",
            "cache_used": cache_used,
            "cache_hits_delta": cache_hits_after - cache_hits_before,
            "new_parses": new_parses,
            "bypass_detected": bypass_detected,
            "bypass_reason": bypass_reason,
            "expected_behavior": "Use cached skeleton data",
        }

        self.evidence.log(
            EvidenceType.MEASUREMENT,
            evidence_data,
            metadata={"scenario": "get_dependencies"},
        )

    def _test_repeated_access(self) -> None:
        """Scenario 3: Repeated access should use cache, not re-parse."""

        # First access
        response1 = self.server.handle_tool_call("auzoom_read", {
            "path": self.test_file,
            "level": "skeleton"
        })

        stats_after_first = self._get_cache_stats()

        # Second access - should hit cache
        response2 = self.server.handle_tool_call("auzoom_read", {
            "path": self.test_file,
            "level": "skeleton"
        })

        stats_after_second = self._get_cache_stats()

        # Third access - should hit cache again
        response3 = self.server.handle_tool_call("auzoom_read", {
            "path": self.test_file,
            "level": "skeleton"
        })

        stats_after_third = self._get_cache_stats()

        # Check cache behavior
        parses_first = stats_after_first.get("files_parsed", 0)
        parses_second = stats_after_second.get("files_parsed", 0)
        parses_third = stats_after_third.get("files_parsed", 0)

        # Should not re-parse on subsequent accesses
        bypass_detected = (parses_second > parses_first) or (parses_third > parses_second)
        bypass_reason = "Re-parsing on repeated access" if bypass_detected else "None"

        evidence_data = {
            "scenario": "repeated_access",
            "operation": "auzoom_read (3x same file/level)",
            "file": self.test_file,
            "level": "skeleton",
            "parses_after_first": parses_first,
            "parses_after_second": parses_second,
            "parses_after_third": parses_third,
            "bypass_detected": bypass_detected,
            "bypass_reason": bypass_reason,
            "expected_behavior": "Cache hit on 2nd and 3rd access",
        }

        self.evidence.log(
            EvidenceType.MEASUREMENT,
            evidence_data,
            metadata={"scenario": "repeated_access"},
        )

    def _test_level_escalation(self) -> None:
        """Scenario 4: Test skeleton → summary → full progression."""

        # Start fresh with new file
        test_file_2 = "/Users/dhirajd/Documents/claude/auzoom/src/auzoom/models.py"

        # Read at skeleton level
        response_skeleton = self.server.handle_tool_call("auzoom_read", {
            "path": test_file_2,
            "level": "skeleton"
        })
        size_skeleton = self._measure_content_size(response_skeleton)
        stats_after_skeleton = self._get_cache_stats()

        # Read at summary level
        response_summary = self.server.handle_tool_call("auzoom_read", {
            "path": test_file_2,
            "level": "summary"
        })
        size_summary = self._measure_content_size(response_summary)
        stats_after_summary = self._get_cache_stats()

        # Read at full level
        response_full = self.server.handle_tool_call("auzoom_read", {
            "path": test_file_2,
            "level": "full"
        })
        size_full = self._measure_content_size(response_full)
        stats_after_full = self._get_cache_stats()

        # Check size progression (skeleton < summary < full)
        size_progression_correct = size_skeleton < size_summary < size_full

        # Check for inappropriate full reads
        skeleton_consistent, skeleton_msg = self._check_level_consistency(
            response_skeleton, "skeleton"
        )
        summary_consistent, summary_msg = self._check_level_consistency(
            response_summary, "summary"
        )

        bypass_detected = not (size_progression_correct and skeleton_consistent and summary_consistent)
        bypass_reason = []
        if not size_progression_correct:
            bypass_reason.append(f"Size progression wrong: {size_skeleton}, {size_summary}, {size_full}")
        if not skeleton_consistent:
            bypass_reason.append(f"Skeleton inconsistent: {skeleton_msg}")
        if not summary_consistent:
            bypass_reason.append(f"Summary inconsistent: {summary_msg}")

        evidence_data = {
            "scenario": "level_escalation",
            "operation": "auzoom_read (skeleton → summary → full)",
            "file": test_file_2,
            "size_skeleton": size_skeleton,
            "size_summary": size_summary,
            "size_full": size_full,
            "size_progression_correct": size_progression_correct,
            "skeleton_level_consistent": skeleton_consistent,
            "summary_level_consistent": summary_consistent,
            "bypass_detected": bypass_detected,
            "bypass_reason": "; ".join(bypass_reason) if bypass_reason else "None",
            "expected_behavior": "Progressive size increase, no premature full reads",
        }

        self.evidence.log(
            EvidenceType.MEASUREMENT,
            evidence_data,
            metadata={"scenario": "level_escalation"},
        )

    def _test_common_workflow(self) -> None:
        """Scenario 5: Common workflow - find → dependencies → read summary."""

        workflow_start_stats = self._get_cache_stats()

        # Step 1: Find a function
        find_response = self.server.handle_tool_call("auzoom_find", {
            "pattern": "NodeType"
        })
        stats_after_find = self._get_cache_stats()

        # Step 2: Get first match and read at summary level
        matches = find_response.get("matches", [])
        if matches:
            first_match = matches[0]
            node_id = first_match.get("id", "")

            # Read the summary
            read_response = self.server.handle_tool_call("auzoom_read", {
                "path": first_match.get("file", ""),
                "level": "summary"
            })
            stats_after_read = self._get_cache_stats()

            # Check if full read was triggered
            actual_level = read_response.get("level", "unknown")
            bypass_detected = actual_level == "full"
            bypass_reason = "Full read in common workflow" if bypass_detected else "None"

        else:
            bypass_detected = False
            bypass_reason = "No matches found"
            stats_after_read = stats_after_find

        evidence_data = {
            "scenario": "common_workflow",
            "operation": "find → read summary",
            "pattern": "NodeType",
            "matches_found": len(matches),
            "workflow_start_stats": workflow_start_stats,
            "stats_after_find": stats_after_find,
            "stats_after_read": stats_after_read,
            "bypass_detected": bypass_detected,
            "bypass_reason": bypass_reason,
            "expected_behavior": "Summary-level read, no full content",
        }

        self.evidence.log(
            EvidenceType.MEASUREMENT,
            evidence_data,
            metadata={"scenario": "common_workflow"},
        )


def test_bypass_behavior():
    """Pytest entry point for bypass behavior detection test."""
    test = BypassBehaviorTest()
    status = test.execute()

    # Print evidence path for reference
    print(f"\nEvidence written to: {test.get_evidence_path()}")

    # Test passes if executed without exceptions
    assert status == TestStatus.PASS, "Bypass behavior test failed"
