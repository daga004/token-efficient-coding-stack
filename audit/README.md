# Audit Infrastructure

Systematic verification testing framework for the V1 Comprehensive Audit project.

## Overview

This infrastructure provides:
- **Test execution harness** - Base classes for writing audit tests
- **Evidence collection** - Automatic capture of test inputs/outputs
- **Structured logging** - Console + file logging with context injection
- **Report templates** - Standardized documentation format

## Quick Start

### 1. Write an Audit Test

```python
from audit import AuditTest, EvidenceType
from audit.models import TestStatus

class VerifyTokenReduction(AuditTest):
    """Test that AuZoom reduces tokens by ≥50%."""

    def __init__(self):
        super().__init__(
            name="verify_token_reduction",
            category="auzoom-core"
        )

    def execute(self) -> TestStatus:
        # Measure baseline
        baseline_tokens = self._measure_baseline()
        self.evidence.log(
            EvidenceType.MEASUREMENT,
            {"metric": "baseline_tokens", "value": baseline_tokens}
        )

        # Measure with AuZoom
        auzoom_tokens = self._measure_auzoom()
        self.evidence.log(
            EvidenceType.MEASUREMENT,
            {"metric": "auzoom_tokens", "value": auzoom_tokens}
        )

        # Calculate reduction
        reduction_pct = ((baseline_tokens - auzoom_tokens) / baseline_tokens) * 100
        self.evidence.log(
            EvidenceType.MEASUREMENT,
            {
                "metric": "token_reduction",
                "baseline": baseline_tokens,
                "actual": auzoom_tokens,
                "reduction_pct": reduction_pct
            }
        )

        # Verify against threshold
        if reduction_pct >= 50:
            return TestStatus.PASS
        elif reduction_pct >= 25:
            return TestStatus.PARTIAL
        else:
            return TestStatus.FAIL

    def _measure_baseline(self) -> int:
        # Implementation here
        pass

    def _measure_auzoom(self) -> int:
        # Implementation here
        pass
```

### 2. Run Tests

```python
from audit import AuditRunner, AuditLogger

# Set up logging
logger = AuditLogger(name="audit", console_level="INFO")

# Create runner
runner = AuditRunner()

# Register tests
runner.register(VerifyTokenReduction())
# ... register more tests

# Run all tests
report = runner.run_all()

# Check results
print(f"Tests run: {report.tests_run}")
print(f"Passed: {report.passed}")
print(f"Failed: {report.failed}")
```

### 3. Generate Report

Use the template at `audit/templates/test_report.md`:

```python
# Read template
with open("audit/templates/test_report.md") as f:
    template = f.read()

# Fill in values
report_content = template.replace("{{test_name}}", "verify_token_reduction")
report_content = report_content.replace("{{status}}", "FAIL")
# ... replace other placeholders

# Write report
with open(f"audit/reports/{test_name}_report.md", "w") as f:
    f.write(report_content)
```

## Directory Structure

```
audit/
├── __init__.py          # Package exports
├── harness.py           # Test execution framework
├── models.py            # Pydantic data models
├── logger.py            # Structured logging
├── README.md            # This file
├── evidence/            # Evidence files (*.jsonl)
├── logs/                # Log files (audit_*.log)
├── templates/           # Report templates
│   ├── test_report.md   # Markdown test report template
│   └── evidence_log.jsonl  # Evidence format examples
└── test_harness.py      # Framework tests
```

## Evidence Collection

Evidence is automatically logged in JSON Lines format:

```jsonl
{"test_name": "verify_token_reduction", "timestamp": "2026-01-12T08:00:00Z", "type": "measurement", "data": {"metric": "baseline_tokens", "value": 5000}, "metadata": {}}
{"test_name": "verify_token_reduction", "timestamp": "2026-01-12T08:00:05Z", "type": "measurement", "data": {"metric": "auzoom_tokens", "value": 3850}, "metadata": {}}
```

Evidence types:
- **file** - File operations (reads, writes, diffs)
- **api** - API calls (requests, responses, timing)
- **measurement** - Metrics and measurements
- **error** - Exceptions and errors

## Logging Levels

- **DEBUG** - All operations (file I/O, API calls, measurements)
- **INFO** - Test start/end, key milestones
- **ERROR** - Failures and exceptions

Console output is human-readable. File logs are JSON-structured for parsing.

## Test Categories

Organize tests by category for selective execution:

- `auzoom-core` - AuZoom functionality tests
- `orchestrator` - Orchestrator functionality tests
- `integration` - Integration tests
- `performance` - Performance benchmarks
- `compliance` - Compliance verification

Run specific category:
```python
report = runner.run_by_category("auzoom-core")
```

## Best Practices

1. **One concern per test** - Each test verifies one specific claim
2. **Evidence for everything** - Log all inputs, outputs, and measurements
3. **Clear pass/fail criteria** - Define thresholds explicitly
4. **Document findings** - Use templates for consistent reporting
5. **Non-destructive** - Never modify production code during tests

## AuZoom Structural Compliance

This infrastructure follows AuZoom constraints:
- ✓ Files ≤250 lines (harness.py: 172, logger.py: 106, models.py: 71)
- ✓ Functions ≤50 lines (all functions comply)
- ✓ Clear separation of concerns (harness, models, logger, templates)

## Example: Complete Test with Evidence

See `templates/test_report.md` for a filled example showing:
- Objective and method
- Evidence collection
- Result analysis
- Findings documentation
- Severity assessment
- Recommendations

## Next Steps

1. Write audit tests for Phase 2+ (AuZoom core verification)
2. Collect evidence systematically
3. Generate reports using templates
4. Track findings in audit documentation

---

For questions or issues, see `.planning/PROJECT.md` and `.planning/ROADMAP.md`.
