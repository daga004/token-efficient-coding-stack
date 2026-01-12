# Test Report: {{test_name}}

**Status:** {{status}}
**Phase:** {{phase}}
**Duration:** {{duration_ms}}ms
**Timestamp:** {{timestamp}}

---

## Objective

{{objective}}

## Method

{{method}}

## Evidence

{{evidence_refs}}

Evidence files:
{{#evidence_files}}
- `{{path}}` - {{description}}
{{/evidence_files}}

## Result

**Status:** {{status}}

{{result_details}}

## Findings

### Summary

{{findings_summary}}

### Details

{{findings_details}}

## Severity

**Level:** {{severity}}
**Impact:** {{impact}}

## Recommendations

{{recommendations}}

---

## Example Usage

This template shows how to document audit test results. Replace placeholders with actual values:

- `{{test_name}}` - Name of the test (e.g., "verify_token_reduction")
- `{{status}}` - Test outcome (PASS, FAIL, PARTIAL, SKIP)
- `{{phase}}` - Audit phase identifier (e.g., "02-auzoom-core")
- `{{duration_ms}}` - Execution time in milliseconds
- `{{timestamp}}` - ISO 8601 timestamp
- `{{objective}}` - What the test aimed to verify
- `{{method}}` - How the test was conducted
- `{{evidence_refs}}` - Paths to evidence files
- `{{result_details}}` - Detailed results with measurements
- `{{findings_summary}}` - Brief findings statement
- `{{findings_details}}` - Comprehensive findings with evidence
- `{{severity}}` - Issue severity (CRITICAL, HIGH, MEDIUM, LOW, INFO)
- `{{impact}}` - Impact description
- `{{recommendations}}` - Suggested actions

---

## Example Filled Report

# Test Report: verify_token_reduction

**Status:** FAIL
**Phase:** 02-auzoom-core
**Duration:** 1250ms
**Timestamp:** 2026-01-12T08:00:00Z

---

## Objective

Verify that AuZoom reduces token usage by ≥50% for typical Python files.

## Method

1. Selected 10 representative Python files from codebase
2. Measured baseline tokens (full file content)
3. Processed files with AuZoom at "summary" level
4. Measured AuZoom tokens (hierarchical output)
5. Calculated reduction percentage per file
6. Compared against 50% threshold

## Evidence

- `audit/evidence/verify_token_reduction_20260112_080000.jsonl` - Test execution log
- `audit/results/token_measurements.json` - Raw token counts
- `audit/results/reduction_analysis.csv` - Per-file analysis

## Result

**Status:** FAIL

Target: ≥50% token reduction
Actual: 23% average reduction
Gap: 27 percentage points below target

Per-file results:
- Small files (<100 lines): -15% to +10% (WORSE than baseline)
- Medium files (100-250 lines): 20% to 35% reduction
- Large files (>250 lines): 45% to 60% reduction

## Findings

### Summary

AuZoom fails to meet the ≥50% token reduction promise. Small files show token INCREASES.

### Details

**Finding 1: Small file overhead**
- Files under 100 lines show 15% token increase
- Metadata overhead exceeds content savings
- Contradicts "reduces tokens" claim in WISHLIST.md

**Finding 2: Missing auto-threshold**
- No automatic detection of small files
- Users must manually avoid AuZoom for small files
- Feature deferred per WISHLIST-COMPLIANCE.md

**Finding 3: Realistic reduction is 23%**
- Across representative file distribution
- Far below promised ≥50%
- Documentation overstates capability

## Severity

**Level:** HIGH
**Impact:** Core value proposition misrepresented

## Recommendations

1. Update documentation to state "23% average reduction" with file size caveats
2. Implement auto-threshold detection for small files
3. Consider hybrid approach: bypass AuZoom for files <100 lines
4. Add warning in CLI when processing small files

---
