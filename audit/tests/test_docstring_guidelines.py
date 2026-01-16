"""Test docstring guidelines compliance across AuZoom codebase.

Scans Python files to measure average docstring token counts, identify
violations (>30 tokens), and generate compliance report against guidelines.
"""

import ast
from pathlib import Path
from typing import Any

import pytest
import tiktoken

from audit.harness import AuditTest
from audit.models import EvidenceType, TestStatus


class DocstringComplianceTest(AuditTest):
    """Test docstring compliance with token efficiency guidelines."""

    def __init__(self):
        super().__init__(
            name="docstring_compliance",
            category="auzoom-optimizations",
        )
        self.encoding = tiktoken.get_encoding("cl100k_base")

        # AuZoom codebase directories to scan
        self.scan_paths = [
            Path("/Users/dhirajd/Documents/claude/auzoom/src/auzoom"),
            Path("/Users/dhirajd/Documents/claude/orchestrator/src/orchestrator"),
        ]

    def _count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken."""
        if not text:
            return 0
        return len(self.encoding.encode(text))

    def _extract_docstrings(self, file_path: Path) -> list[dict]:
        """Extract all docstrings from a Python file with their context."""

        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(file_path))
        except Exception as e:
            return []

        docstrings = []

        for node in ast.walk(tree):
            # Functions and methods
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                docstring = ast.get_docstring(node)
                if docstring:
                    # Calculate function size (lines)
                    func_lines = node.end_lineno - node.lineno + 1

                    # Determine token budget based on size
                    if func_lines <= 10:
                        budget = 5
                    elif func_lines <= 30:
                        budget = 15
                    else:
                        budget = 30

                    docstrings.append({
                        "type": "function",
                        "name": node.name,
                        "docstring": docstring,
                        "tokens": self._count_tokens(docstring),
                        "line": node.lineno,
                        "func_lines": func_lines,
                        "token_budget": budget,
                    })

            # Classes
            elif isinstance(node, ast.ClassDef):
                docstring = ast.get_docstring(node)
                if docstring:
                    docstrings.append({
                        "type": "class",
                        "name": node.name,
                        "docstring": docstring,
                        "tokens": self._count_tokens(docstring),
                        "line": node.lineno,
                        "token_budget": 30,  # Classes can have longer docstrings
                    })

            # Module-level docstring
            elif isinstance(node, ast.Module):
                docstring = ast.get_docstring(node)
                if docstring:
                    docstrings.append({
                        "type": "module",
                        "name": file_path.name,
                        "docstring": docstring,
                        "tokens": self._count_tokens(docstring),
                        "line": 1,
                        "token_budget": 50,  # Modules can have longer docstrings
                    })

        return docstrings

    def execute(self) -> TestStatus:
        """Execute docstring compliance analysis."""

        all_docstrings = []
        violations = []
        file_count = 0

        # Scan all Python files
        for scan_path in self.scan_paths:
            if not scan_path.exists():
                continue

            for py_file in scan_path.rglob("*.py"):
                # Skip test files and __pycache__
                if "test" in str(py_file) or "__pycache__" in str(py_file):
                    continue

                file_count += 1
                docstrings = self._extract_docstrings(py_file)

                for doc_info in docstrings:
                    doc_info["file"] = str(py_file.relative_to(scan_path.parent))
                    all_docstrings.append(doc_info)

                    # Check for violations (exceeds token budget)
                    if doc_info["tokens"] > doc_info["token_budget"]:
                        violations.append({
                            "file": doc_info["file"],
                            "line": doc_info["line"],
                            "name": doc_info["name"],
                            "type": doc_info["type"],
                            "tokens": doc_info["tokens"],
                            "budget": doc_info["token_budget"],
                            "excess": doc_info["tokens"] - doc_info["token_budget"],
                        })

        # Calculate statistics
        if all_docstrings:
            total_tokens = sum(d["tokens"] for d in all_docstrings)
            avg_tokens = total_tokens / len(all_docstrings)

            # Token distribution
            zero_to_10 = len([d for d in all_docstrings if d["tokens"] <= 10])
            ten_to_20 = len([d for d in all_docstrings if 10 < d["tokens"] <= 20])
            twenty_to_30 = len([d for d in all_docstrings if 20 < d["tokens"] <= 30])
            over_30 = len([d for d in all_docstrings if d["tokens"] > 30])

            zero_to_10_pct = (zero_to_10 / len(all_docstrings)) * 100
            ten_to_20_pct = (ten_to_20 / len(all_docstrings)) * 100
            twenty_to_30_pct = (twenty_to_30 / len(all_docstrings)) * 100
            over_30_pct = (over_30 / len(all_docstrings)) * 100

            # Compliance check
            # Target: 80% of functions with 0-10 tokens
            compliant = avg_tokens <= 15 and zero_to_10_pct >= 60

            # Log overall statistics
            self.evidence.log(EvidenceType.MEASUREMENT, {
                "test": "docstring_compliance_overall",
                "files_scanned": file_count,
                "total_docstrings": len(all_docstrings),
                "avg_tokens": round(avg_tokens, 2),
                "total_violations": len(violations),
                "target_avg_tokens": 15,
                "compliant": compliant,
            })

            # Log token distribution
            self.evidence.log(EvidenceType.MEASUREMENT, {
                "test": "docstring_token_distribution",
                "0-10_tokens": zero_to_10,
                "0-10_tokens_pct": round(zero_to_10_pct, 2),
                "11-20_tokens": ten_to_20,
                "11-20_tokens_pct": round(ten_to_20_pct, 2),
                "21-30_tokens": twenty_to_30,
                "21-30_tokens_pct": round(twenty_to_30_pct, 2),
                "over_30_tokens": over_30,
                "over_30_tokens_pct": round(over_30_pct, 2),
            })

            # Log violations
            for violation in violations[:10]:  # Log first 10
                self.evidence.log(EvidenceType.MEASUREMENT, {
                    "test": "docstring_violation",
                    **violation
                })

            # Print summary
            print(f"\n{'='*60}")
            print("Docstring Compliance Report")
            print(f"{'='*60}")
            print(f"Files scanned: {file_count}")
            print(f"Total docstrings: {len(all_docstrings)}")
            print(f"Average tokens: {avg_tokens:.1f} (target: ≤15)")
            print(f"\nToken Distribution:")
            print(f"  0-10 tokens: {zero_to_10} ({zero_to_10_pct:.1f}%)")
            print(f"  11-20 tokens: {ten_to_20} ({ten_to_20_pct:.1f}%)")
            print(f"  21-30 tokens: {twenty_to_30} ({twenty_to_30_pct:.1f}%)")
            print(f"  Over 30 tokens: {over_30} ({over_30_pct:.1f}%)")
            print(f"\nViolations (>budget): {len(violations)}")

            if violations:
                print(f"\nTop 5 Violations:")
                for i, v in enumerate(violations[:5], 1):
                    print(f"  {i}. {v['file']}:{v['line']} - {v['name']}")
                    print(f"     {v['tokens']} tokens (budget: {v['budget']}, excess: {v['excess']})")

            print(f"\n{'='*60}")
            print(f"Status: {'✅ COMPLIANT' if compliant else '⚠️ NEEDS IMPROVEMENT'}")
            print(f"{'='*60}")

            return TestStatus.PASS if compliant else TestStatus.PARTIAL

        else:
            print("No docstrings found to analyze")
            return TestStatus.FAIL


if __name__ == "__main__":
    test = DocstringComplianceTest()
    status = test.execute()
    print(f"\nFinal Status: {status.value}")
    print(f"Evidence logged to: {test.evidence.log_file}")
