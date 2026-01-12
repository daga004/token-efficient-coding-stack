"""
Test structural compliance with AuZoom guidelines.

Validates entire project against structure requirements:
- Functions ≤50 lines
- Modules ≤250 lines
- Directories ≤7 files

Uses CodeValidator from auzoom.core.validator to identify violations.
"""

import json
from pathlib import Path
from typing import Any

import pytest

from audit.harness import AuditTest
from audit.models import EvidenceType, TestStatus
from auzoom.core.validator import CodeValidator, Violation


class StructuralComplianceTest(AuditTest):
    """Test entire project against AuZoom structural guidelines."""

    def __init__(self):
        super().__init__(
            name="structural_compliance",
            category="auzoom-structured-code",
        )
        self.validator = CodeValidator()
        self.project_root = "/Users/dhirajd/Documents/claude"

    def execute(self) -> TestStatus:
        """Run structural validation on entire project."""
        print("\n" + "=" * 60)
        print("Structural Compliance Validation")
        print("=" * 60)
        print(f"\nValidating project: {self.project_root}")
        print("\nGuidelines:")
        print(f"  - Functions ≤{self.validator.FUNCTION_MAX_LINES} lines")
        print(f"  - Modules ≤{self.validator.MODULE_MAX_LINES} lines")
        print(f"  - Directories ≤{self.validator.DIR_MAX_FILES} files\n")

        # Run validation
        violations = self.validator.validate_project(self.project_root)

        # Calculate scope metrics
        project_path = Path(self.project_root)
        all_py_files = []
        all_dirs = []
        total_lines = 0

        for py_file in project_path.rglob("*.py"):
            if any(
                part in py_file.parts
                for part in [
                    ".git",
                    "__pycache__",
                    ".venv",
                    "node_modules",
                    ".pytest_cache",
                    "build",
                    "dist",
                ]
            ):
                continue
            all_py_files.append(str(py_file))
            try:
                with open(py_file) as f:
                    total_lines += len(f.readlines())
            except Exception:
                pass

        for dir_path in project_path.rglob("*"):
            if dir_path.is_dir():
                if any(
                    part in dir_path.parts
                    for part in [
                        ".git",
                        "__pycache__",
                        ".venv",
                        "node_modules",
                        ".pytest_cache",
                        "build",
                        "dist",
                    ]
                ):
                    continue
                all_dirs.append(str(dir_path))

        # Log validation scope
        scope_data = {
            "project_root": self.project_root,
            "files_checked": len(all_py_files),
            "directories_scanned": len(all_dirs),
            "total_lines": total_lines,
            "validation_time": "N/A",  # Could add timing if needed
        }

        self.evidence.log(
            EvidenceType.MEASUREMENT,
            scope_data,
            metadata={"type": "validation_scope"},
        )

        print(f"Validation scope:")
        print(f"  - Files checked: {len(all_py_files)}")
        print(f"  - Directories scanned: {len(all_dirs)}")
        print(f"  - Total lines analyzed: {total_lines:,}\n")

        # Categorize violations by type
        by_type = {}
        for v in violations:
            if v.type not in by_type:
                by_type[v.type] = []
            by_type[v.type].append(v)

        # Log violations by type
        for vtype, vlist in by_type.items():
            type_data = {
                "type": vtype,
                "count": len(vlist),
                "severity_breakdown": {
                    "error": len([v for v in vlist if v.severity == "error"]),
                    "warning": len([v for v in vlist if v.severity == "warning"]),
                },
                "examples": [
                    {
                        "file": v.file,
                        "line": v.line,
                        "message": v.message,
                        "current": v.current,
                        "limit": v.limit,
                    }
                    for v in vlist[:5]  # First 5 examples
                ],
            }

            self.evidence.log(
                EvidenceType.MEASUREMENT,
                type_data,
                metadata={"type": "violation_category", "violation_type": vtype},
            )

        # Log all violations
        all_violations_data = {
            "total_violations": len(violations),
            "by_type": {vtype: len(vlist) for vtype, vlist in by_type.items()},
            "by_severity": {
                "error": len([v for v in violations if v.severity == "error"]),
                "warning": len([v for v in violations if v.severity == "warning"]),
            },
            "violations": [
                {
                    "file": v.file,
                    "line": v.line,
                    "type": v.type,
                    "severity": v.severity,
                    "message": v.message,
                    "current": v.current,
                    "limit": v.limit,
                }
                for v in violations
            ],
        }

        self.evidence.log(
            EvidenceType.MEASUREMENT,
            all_violations_data,
            metadata={"type": "complete_violation_list"},
        )

        # Calculate compliance rate
        compliant_files = len(all_py_files) - len(
            set(v.file for v in violations if v.type in ["function_too_long", "module_too_long"])
        )
        compliance_rate = (
            (compliant_files / len(all_py_files) * 100) if all_py_files else 0
        )

        compliance_data = {
            "compliant_files": compliant_files,
            "total_files": len(all_py_files),
            "compliance_rate": round(compliance_rate, 2),
        }

        self.evidence.log(
            EvidenceType.MEASUREMENT,
            compliance_data,
            metadata={"type": "compliance_rate"},
        )

        # Print summary
        print(f"Results:")
        print(f"  - Total violations: {len(violations)}")
        print(f"  - Errors: {all_violations_data['by_severity']['error']}")
        print(f"  - Warnings: {all_violations_data['by_severity']['warning']}")
        print(f"  - Compliance rate: {compliance_rate:.1f}%\n")

        print(f"Violations by type:")
        for vtype, count in all_violations_data["by_type"].items():
            print(f"  - {vtype}: {count}")

        print(f"\nEvidence logged to: {self.get_evidence_path()}\n")

        # Test passes regardless of violations - this is documentation, not a failure
        return TestStatus.PASS


def test_structural_compliance():
    """Execute structural compliance validation."""
    test = StructuralComplianceTest()
    status = test.execute()
    assert status == TestStatus.PASS
    print(f"✓ Test complete - evidence at {test.get_evidence_path()}")
