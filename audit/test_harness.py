"""
Basic tests for audit harness functionality.

Verifies test execution, evidence collection, and reporting.
"""

import pytest

from audit.harness import AuditRunner, AuditTest
from audit.models import EvidenceType, TestStatus


class DummyPassTest(AuditTest):
    """Test that always passes."""

    def execute(self) -> TestStatus:
        self.evidence.log(EvidenceType.MEASUREMENT, {"result": "success"})
        return TestStatus.PASS


class DummyFailTest(AuditTest):
    """Test that always fails."""

    def execute(self) -> TestStatus:
        self.evidence.log(EvidenceType.MEASUREMENT, {"result": "failure"})
        return TestStatus.FAIL


def test_audit_runner_instantiation():
    """Verify AuditRunner can be instantiated."""
    runner = AuditRunner()
    assert runner is not None
    assert len(runner.tests) == 0


def test_audit_runner_register():
    """Verify tests can be registered."""
    runner = AuditRunner()
    test = DummyPassTest("test1", "unit")
    runner.register(test)
    assert len(runner.tests) == 1


def test_audit_runner_execution():
    """Verify tests can be executed and results collected."""
    runner = AuditRunner()
    runner.register(DummyPassTest("test_pass", "unit"))
    runner.register(DummyFailTest("test_fail", "unit"))

    report = runner.run_all()

    assert report.tests_run == 2
    assert report.passed == 1
    assert report.failed == 1
    assert len(report.results) == 2


def test_evidence_collection():
    """Verify evidence is collected during test execution."""
    test = DummyPassTest("evidence_test", "unit")
    test.execute()

    evidence_path = test.get_evidence_path()
    assert evidence_path is not None
    assert "evidence_test" in evidence_path
