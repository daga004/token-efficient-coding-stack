"""Code structure validation for AuZoom compatibility."""

from dataclasses import dataclass
from typing import List
from pathlib import Path


@dataclass
class Violation:
    """A structural code violation."""
    file: str
    line: int
    type: str  # "function_too_long", "module_too_long", "dir_too_many_files"
    severity: str  # "error", "warning"
    message: str
    current: int
    limit: int


class CodeValidator:
    """Validate code structure for AuZoom compatibility."""

    FUNCTION_MAX_LINES = 50
    MODULE_MAX_LINES = 250
    DIR_MAX_FILES = 7

    def __init__(self):
        self.violations: List[Violation] = []

    def validate_file(self, file_path: str) -> List[Violation]:
        """Check a single Python file for violations."""
        violations = []

        with open(file_path) as f:
            lines = f.readlines()

        # Check module length
        module_lines = len(lines)
        if module_lines > self.MODULE_MAX_LINES:
            violations.append(Violation(
                file=file_path,
                line=1,
                type="module_too_long",
                severity="error",
                message=f"Module exceeds {self.MODULE_MAX_LINES} lines",
                current=module_lines,
                limit=self.MODULE_MAX_LINES
            ))

        # Parse with tree-sitter to check function lengths
        try:
            from .parser import PythonParser
            parser = PythonParser()
            nodes = parser.parse_file(file_path)

            for node in nodes:
                if node.node_type.value in ['function', 'method']:
                    func_lines = node.line_end - node.line_start + 1
                    if func_lines > self.FUNCTION_MAX_LINES:
                        violations.append(Violation(
                            file=file_path,
                            line=node.line_start,
                            type="function_too_long",
                            severity="error",
                            message=f"Function '{node.name}' exceeds {self.FUNCTION_MAX_LINES} lines",
                            current=func_lines,
                            limit=self.FUNCTION_MAX_LINES
                        ))
        except Exception as e:
            # If parsing fails, skip function-level validation
            pass

        return violations

    def validate_directory(self, dir_path: str) -> List[Violation]:
        """Check directory for too many files."""
        violations = []
        path = Path(dir_path)

        if not path.is_dir():
            return violations

        # Count Python files (not subdirectories)
        py_files = list(path.glob("*.py"))
        file_count = len(py_files)

        if file_count > self.DIR_MAX_FILES:
            violations.append(Violation(
                file=str(path),
                line=0,
                type="dir_too_many_files",
                severity="warning",
                message=f"Directory has {file_count} files (limit: {self.DIR_MAX_FILES})",
                current=file_count,
                limit=self.DIR_MAX_FILES
            ))

        return violations

    def validate_project(self, project_root: str) -> List[Violation]:
        """Validate entire project."""
        violations = []
        root = Path(project_root)

        for py_file in root.rglob("*.py"):
            # Skip common ignore patterns
            if any(part in py_file.parts for part in ['.git', '__pycache__', '.venv', 'node_modules', '.pytest_cache', 'build', 'dist']):
                continue

            violations.extend(self.validate_file(str(py_file)))

        # Check directories
        for dir_path in root.rglob("*"):
            if dir_path.is_dir():
                if any(part in dir_path.parts for part in ['.git', '__pycache__', '.venv', 'node_modules', '.pytest_cache', 'build', 'dist']):
                    continue
                violations.extend(self.validate_directory(str(dir_path)))

        return violations

    def format_report(self, violations: List[Violation]) -> str:
        """Format violations as readable report."""
        if not violations:
            return "✓ All files comply with AuZoom structure guidelines"

        errors = [v for v in violations if v.severity == "error"]
        warnings = [v for v in violations if v.severity == "warning"]

        report = []
        report.append(f"\n{'='*60}")
        report.append(f"AuZoom Structure Validation Report")
        report.append(f"{'='*60}\n")

        if errors:
            report.append(f"❌ Errors ({len(errors)}):\n")
            for v in errors:
                report.append(f"  {v.file}:{v.line}")
                report.append(f"    {v.message}")
                report.append(f"    Current: {v.current} lines | Limit: {v.limit} lines")
                report.append("")

        if warnings:
            report.append(f"⚠️  Warnings ({len(warnings)}):\n")
            for v in warnings:
                report.append(f"  {v.file}")
                report.append(f"    {v.message}")
                report.append("")

        return "\n".join(report)
