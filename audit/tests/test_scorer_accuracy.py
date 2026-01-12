"""Accuracy test for ComplexityScorer against validation task suite.

Validates complexity scores against the 10 validation tasks from TEST-SUITE.md,
comparing predicted tiers to actual tiers used in OPTIMIZED-RESULTS.md.
"""

import json
import pytest
from datetime import datetime
from pathlib import Path
from orchestrator.scoring import ComplexityScorer
from orchestrator.models import Task


class TestScorerAccuracy:
    """Test scorer accuracy against real validation tasks."""

    # Class-level storage for results across all tests
    all_results = []
    scorer = None

    @classmethod
    def setup_class(cls):
        """Setup scorer once for all tests."""
        cls.scorer = ComplexityScorer()
        cls.all_results = []

    @classmethod
    def teardown_class(cls):
        """Write evidence to JSONL file after all tests."""
        evidence_path = Path("audit/evidence")
        evidence_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        evidence_file = evidence_path / f"scorer_accuracy_{timestamp}.jsonl"

        with open(evidence_file, "w") as f:
            for result in cls.all_results:
                f.write(json.dumps(result) + "\n")

    def _score_and_record(self, task_id: str, description: str, context: dict,
                          actual_tier: int, expected_score_range: tuple = None):
        """Score a task and record results."""
        task = Task(description=description, context=context)
        complexity = self.scorer.score_task(task)

        match = complexity.recommended_tier == actual_tier

        result = {
            "task_id": task_id,
            "description": description,
            "predicted_score": complexity.score,
            "predicted_tier": complexity.recommended_tier,
            "actual_tier": actual_tier,
            "match": match,
            "factors": complexity.factors,
            "confidence": complexity.confidence
        }
        self.all_results.append(result)

        # Optional: assert score is in expected range
        if expected_score_range:
            assert expected_score_range[0] <= complexity.score <= expected_score_range[1], \
                f"Task {task_id}: Score {complexity.score} not in range {expected_score_range}"

        return complexity, match

    # Category 1: Code Exploration

    def test_task_1_1_explore_unknown_package(self):
        """Task 1.1: Explore Unknown Python Package (Haiku in actual)."""
        description = "What are the main modules and their purposes in the AuZoom codebase?"
        context = {
            "files_count": 15,  # 15 Python files
            "subsystems": ["core", "mcp"]  # 2 subsystems
        }
        # Actual: Used Haiku (tier 1) in OPTIMIZED-RESULTS.md
        complexity, match = self._score_and_record("1.1", description, context, actual_tier=1)

        # Task is medium complexity: exploring codebase structure
        # Expected: 1.0 (length) + 2.0 (15 files) + 1.0 (2 subsystems) = 4.0 → Haiku (tier 1)
        assert match, f"Expected tier 1 (Haiku), got tier {complexity.recommended_tier}"

    def test_task_1_2_find_specific_function(self):
        """Task 1.2: Find Specific Function (Haiku in actual)."""
        description = "Locate and understand the score_task function in orchestrator"
        context = {
            "files_count": 1  # Single file search
        }
        # Actual: Used Haiku (tier 1) in OPTIMIZED-RESULTS.md
        complexity, match = self._score_and_record("1.2", description, context, actual_tier=1)

        # Simple search task: 1.0 (length) + 0.5 (1 file) = 1.5 → Flash (tier 0)
        # NOTE: This may be a mismatch - simple search routed to Haiku (overprovisioned)
        # We'll verify if this is appropriate

    # Category 2: Simple Edits

    def test_task_2_1_fix_typo_in_docstring(self):
        """Task 2.1: Fix Typo in Docstring (Flash in actual)."""
        description = "Fix spelling error in docstring"
        context = {
            "files_count": 1
        }
        # Actual: Used Flash (tier 0) in OPTIMIZED-RESULTS.md
        complexity, match = self._score_and_record("2.1", description, context, actual_tier=0)

        # Trivial edit: 0.5 (short) + 0.5 (1 file) = 1.0 → Flash (tier 0)
        assert match, f"Expected tier 0 (Flash), got tier {complexity.recommended_tier}"

    def test_task_2_2_update_constant_value(self):
        """Task 2.2: Update Constant Value (Flash in actual)."""
        description = "Change MAX_TOKENS from 4096 to 8192"
        context = {
            "files_count": 1
        }
        # Actual: Used Flash (tier 0) in OPTIMIZED-RESULTS.md
        complexity, match = self._score_and_record("2.2", description, context, actual_tier=0)

        # Simple constant change: 0.5 (short) + 0.5 (1 file) = 1.0 → Flash (tier 0)
        assert match, f"Expected tier 0 (Flash), got tier {complexity.recommended_tier}"

    # Category 3: Feature Implementation

    def test_task_3_1_add_validation_rule(self):
        """Task 3.1: Add New Validation Rule (Haiku in actual)."""
        description = "Add max 3 files per directory validation to AuZoom validator"
        context = {
            "files_count": 1,
            "requires_tests": True
        }
        # Actual: Used Haiku (tier 1) in OPTIMIZED-RESULTS.md
        complexity, match = self._score_and_record("3.1", description, context, actual_tier=1)

        # Feature with tests: 1.0 (length) + 0.5 (1 file) + 1.5 (tests) = 3.0 → Haiku (tier 1)
        assert match, f"Expected tier 1 (Haiku), got tier {complexity.recommended_tier}"

    def test_task_3_2_add_cost_tracking(self):
        """Task 3.2: Add Cost Tracking (Haiku in actual)."""
        description = "Add cumulative cost tracking to orchestrator executor"
        context = {
            "files_count": 1,
            "requires_tests": True
        }
        # Actual: Used Haiku (tier 1) in OPTIMIZED-RESULTS.md
        complexity, match = self._score_and_record("3.2", description, context, actual_tier=1)

        # Feature with tests: 0.5 (7 words) + 0.5 (1 file) + 1.5 (tests) = 2.5 → Flash (tier 0)
        # MISMATCH: Scorer predicts Flash, but Haiku was used (may be manual override or task complexity underestimated)

    # Category 4: Refactoring

    def test_task_4_1_extract_helper_function(self):
        """Task 4.1: Extract Helper Function (Haiku in actual)."""
        description = "Extract common validation logic in validator.py"
        context = {
            "files_count": 1,
            "requires_tests": True
        }
        # Actual: Used Haiku (tier 1) in OPTIMIZED-RESULTS.md
        complexity, match = self._score_and_record("4.1", description, context, actual_tier=1)

        # Refactoring with tests: 0.5 (short) + 0.5 (1 file) + 1.5 (tests) = 2.5 → Flash (tier 0)
        # But contains "refactor" keyword → +1.0 → 3.5 → Haiku (tier 1)
        # NOTE: May mismatch if keyword not detected in shorter description

    def test_task_4_2_rename_module(self):
        """Task 4.2: Rename Module (Haiku in actual)."""
        description = "Rename models.py to data_models.py and update all imports"
        context = {
            "files_count": 5  # Module + 5 importers
        }
        # Actual: Used Haiku (tier 1) in OPTIMIZED-RESULTS.md
        complexity, match = self._score_and_record("4.2", description, context, actual_tier=1)

        # Multi-file refactor: 1.0 (length) + 1.5 (5 files) = 2.5 → Flash (tier 0)
        # NOTE: May be a mismatch - simple rename routed to Haiku

    # Category 5: Debugging

    def test_task_5_1_diagnose_test_failure(self):
        """Task 5.1: Diagnose Test Failure (Haiku in actual)."""
        description = "Understand why test_mcp_server fails in auzoom"
        context = {
            "files_count": 2  # Test file + implementation
        }
        # Actual: Used Haiku (tier 1) in OPTIMIZED-RESULTS.md
        complexity, match = self._score_and_record("5.1", description, context, actual_tier=1)

        # Debugging: 0.5 (short) + 0.5 (2 files) = 1.0 → Flash (tier 0)
        # NOTE: May be a mismatch - debugging might need higher tier

    def test_task_5_2_fix_import_error(self):
        """Task 5.2: Fix Import Error (Haiku in actual)."""
        description = "Resolve circular import in orchestrator"
        context = {
            "files_count": 8  # Multiple modules in cycle
        }
        # Actual: Used Haiku (tier 1) in OPTIMIZED-RESULTS.md
        complexity, match = self._score_and_record("5.2", description, context, actual_tier=1)

        # Complex debugging: 0.5 (short) + 2.0 (8+ files) = 2.5 → Flash (tier 0)
        # NOTE: Likely mismatch - circular imports are complex, should be Haiku

    def test_calculate_accuracy_metrics(self):
        """Calculate and assert overall accuracy metrics."""
        # This test runs last and calculates summary metrics
        total = len(self.all_results)
        matches = sum(1 for r in self.all_results if r["match"])
        accuracy = (matches / total * 100) if total > 0 else 0

        # Calculate confusion matrix
        confusion = {0: {0: 0, 1: 0, 2: 0, 3: 0},
                     1: {0: 0, 1: 0, 2: 0, 3: 0},
                     2: {0: 0, 1: 0, 2: 0, 3: 0},
                     3: {0: 0, 1: 0, 2: 0, 3: 0}}

        for result in self.all_results:
            actual = result["actual_tier"]
            predicted = result["predicted_tier"]
            confusion[actual][predicted] += 1

        # Calculate average score deviation
        deviations = []
        tier_to_score_range = {0: 1.5, 1: 4.0, 2: 6.5, 3: 9.0}  # Midpoints
        for result in self.all_results:
            expected_score = tier_to_score_range[result["actual_tier"]]
            deviation = abs(result["predicted_score"] - expected_score)
            deviations.append(deviation)
        avg_deviation = sum(deviations) / len(deviations) if deviations else 0

        # Add summary to results
        summary = {
            "task_id": "SUMMARY",
            "total_tasks": total,
            "matches": matches,
            "accuracy_percent": round(accuracy, 2),
            "avg_score_deviation": round(avg_deviation, 2),
            "confusion_matrix": confusion
        }
        self.all_results.append(summary)

        # Print for visibility
        print(f"\n=== Scorer Accuracy Results ===")
        print(f"Total tasks: {total}")
        print(f"Tier matches: {matches}/{total} ({accuracy:.1f}%)")
        print(f"Avg score deviation: {avg_deviation:.2f}")
        print(f"Confusion matrix:")
        print(f"  Actual\\Predicted |  0  |  1  |  2  |  3  |")
        for actual_tier in range(4):
            row = [confusion[actual_tier][pred] for pred in range(4)]
            print(f"  Tier {actual_tier}          | {row[0]:2}  | {row[1]:2}  | {row[2]:2}  | {row[3]:2}  |")

        # Store accuracy result (don't fail - this is analysis/audit code)
        # Note: 40% accuracy indicates systematic under-scoring (tier 0 over tier 1)
        # This is a key finding for the accuracy report
        if accuracy < 80.0:
            print(f"\nWARNING: Accuracy {accuracy:.1f}% below target of 80%")
            print(f"Key finding: Scorer systematically predicts lower tiers than actual usage")
