"""
Audit test harness for systematic verification.

Provides base classes for test execution, evidence collection, and result tracking.
"""

import json
import traceback
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from time import time
from typing import Any, Optional

from audit.models import AuditReport, EvidenceType, TestResult, TestStatus


class Evidence:
    """Evidence collection for audit tests."""

    def __init__(self, test_name: str, evidence_dir: str = "audit/evidence"):
        self.test_name = test_name
        self.evidence_dir = Path(evidence_dir)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self.evidence_file = (
            self.evidence_dir / f"{test_name}_{self.timestamp}.jsonl"
        )

    def log(
        self,
        evidence_type: EvidenceType,
        data: Any,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Log evidence entry to JSON Lines file."""
        entry = {
            "test_name": self.test_name,
            "timestamp": datetime.utcnow().isoformat(),
            "type": evidence_type.value,
            "data": data,
            "metadata": metadata or {},
        }
        with open(self.evidence_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def get_path(self) -> str:
        """Get path to evidence file."""
        return str(self.evidence_file)


class AuditTest(ABC):
    """Base class for audit tests."""

    def __init__(self, name: str, category: str):
        self.name = name
        self.category = category
        self.evidence = Evidence(name)

    @abstractmethod
    def execute(self) -> TestStatus:
        """Execute the test and return status."""
        pass

    def verify(self) -> bool:
        """Verify test prerequisites. Override if needed."""
        return True

    def get_evidence_path(self) -> str:
        """Get path to evidence file for this test."""
        return self.evidence.get_path()


class AuditRunner:
    """Test runner for executing audit tests."""

    def __init__(self):
        self.tests: list[AuditTest] = []
        self.results: list[TestResult] = []

    def register(self, test: AuditTest) -> None:
        """Register a test for execution."""
        self.tests.append(test)

    def run_all(self) -> AuditReport:
        """Run all registered tests."""
        return self._run_tests(self.tests)

    def run_by_category(self, category: str) -> AuditReport:
        """Run tests matching a specific category."""
        filtered = [t for t in self.tests if t.category == category]
        return self._run_tests(filtered)

    def _run_tests(self, tests: list[AuditTest]) -> AuditReport:
        """Execute a list of tests and collect results."""
        self.results = []
        passed = 0
        failed = 0
        partial = 0
        skipped = 0

        for test in tests:
            start_time = time()
            status = TestStatus.SKIP
            error_msg = None

            try:
                # Verify prerequisites
                if not test.verify():
                    status = TestStatus.SKIP
                    skipped += 1
                else:
                    # Execute test
                    status = test.execute()

                    # Count results
                    if status == TestStatus.PASS:
                        passed += 1
                    elif status == TestStatus.FAIL:
                        failed += 1
                    elif status == TestStatus.PARTIAL:
                        partial += 1
                    elif status == TestStatus.SKIP:
                        skipped += 1

            except Exception as e:
                status = TestStatus.FAIL
                failed += 1
                error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
                test.evidence.log(
                    EvidenceType.ERROR, {"exception": str(e), "traceback": error_msg}
                )

            duration_ms = (time() - start_time) * 1000

            result = TestResult(
                name=test.name,
                status=status,
                duration_ms=duration_ms,
                evidence_refs=[test.get_evidence_path()],
                error_msg=error_msg,
            )
            self.results.append(result)

        # Generate report
        report = AuditReport(
            phase="unknown",
            tests_run=len(tests),
            passed=passed,
            failed=failed,
            partial=partial,
            skipped=skipped,
            evidence_dir="audit/evidence",
            results=self.results,
        )

        return report
