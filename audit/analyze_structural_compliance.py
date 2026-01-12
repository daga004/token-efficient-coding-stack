#!/usr/bin/env python3
"""
Analyze structural compliance evidence and generate report.
"""

import json
from collections import defaultdict
from pathlib import Path

# Read evidence file
evidence_file = "audit/evidence/structural_compliance_20260112_103537.jsonl"
entries = []
with open(evidence_file) as f:
    for line in f:
        entries.append(json.loads(line))

# Extract data from entries
scope = None
violations_data = None
compliance = None

for entry in entries:
    mtype = entry["metadata"].get("type")
    if mtype == "validation_scope":
        scope = entry["data"]
    elif mtype == "complete_violation_list":
        violations_data = entry["data"]
    elif mtype == "compliance_rate":
        compliance = entry["data"]

if not all([scope, violations_data, compliance]):
    print("Error: Missing required evidence entries")
    exit(1)

violations = violations_data["violations"]

# Analysis: Group by subsystem
by_subsystem = defaultdict(list)
for v in violations:
    file_path = v["file"]
    if "/auzoom/" in file_path:
        subsystem = "auzoom"
    elif "/orchestrator/" in file_path:
        subsystem = "orchestrator"
    elif "/audit/" in file_path:
        subsystem = "audit"
    else:
        subsystem = "other"
    by_subsystem[subsystem].append(v)

# Find worst offenders
worst_offenders = sorted(
    violations, key=lambda v: (v["current"] - v["limit"]) / v["limit"], reverse=True
)[:10]

# Generate markdown report
report = []
report.append("# Structural Compliance Validation Report")
report.append("")
report.append("**Phase 3, Plan 1** — AuZoom Structural Compliance Audit")
report.append("")
report.append("Generated: 2026-01-12")
report.append("")
report.append("---")
report.append("")
report.append("## Executive Summary")
report.append("")
report.append(f"**Overall Compliance Rate: {compliance['compliance_rate']}%**")
report.append("")
report.append(f"- **Files Checked:** {scope['files_checked']}")
report.append(f"- **Directories Scanned:** {scope['directories_scanned']}")
report.append(f"- **Total Lines Analyzed:** {scope['total_lines']:,}")
report.append(f"- **Total Violations:** {violations_data['total_violations']}")
report.append(f"- **Compliant Files:** {compliance['compliant_files']}/{compliance['total_files']}")
report.append("")

# Severity breakdown
report.append("**Violations by Severity:**")
report.append("")
report.append(f"- ❌ **Errors:** {violations_data['by_severity']['error']}")
report.append(f"- ⚠️  **Warnings:** {violations_data['by_severity']['warning']}")
report.append("")

# Type breakdown
report.append("**Violations by Type:**")
report.append("")
for vtype, count in violations_data["by_type"].items():
    report.append(f"- `{vtype}`: {count}")
report.append("")
report.append("---")
report.append("")

# Detailed Findings
report.append("## Detailed Findings")
report.append("")

for vtype, count in violations_data["by_type"].items():
    report.append(f"### {vtype.replace('_', ' ').title()}")
    report.append("")
    report.append(f"**Count:** {count} violations")
    report.append("")

    type_violations = [v for v in violations if v["type"] == vtype]

    report.append("**Examples:**")
    report.append("")
    for v in type_violations[:5]:
        rel_path = v["file"].replace("/Users/dhirajd/Documents/claude/", "")
        over_pct = ((v["current"] - v["limit"]) / v["limit"] * 100)
        report.append(f"- `{rel_path}:{v['line']}`")
        report.append(f"  - Current: {v['current']} lines | Limit: {v['limit']} lines")
        report.append(f"  - Over limit by: {v['current'] - v['limit']} lines ({over_pct:.1f}%)")
        report.append("")

    if len(type_violations) > 5:
        report.append(f"*...and {len(type_violations) - 5} more*")
        report.append("")

report.append("---")
report.append("")

# Worst Offenders
report.append("## Worst Offenders")
report.append("")
report.append("Top 10 files with largest violations relative to limits:")
report.append("")
report.append("| File | Line | Type | Current | Limit | Over Limit | % Over |")
report.append("|------|------|------|---------|-------|------------|--------|")

for v in worst_offenders:
    rel_path = v["file"].replace("/Users/dhirajd/Documents/claude/", "")
    over = v["current"] - v["limit"]
    over_pct = (over / v["limit"] * 100)

    # Truncate path for table
    if len(rel_path) > 50:
        parts = rel_path.split("/")
        rel_path = f".../{'/'.join(parts[-2:])}"

    vtype_short = v["type"].replace("_too_long", "").replace("dir_too_many_files", "dir")
    report.append(
        f"| {rel_path} | {v['line']} | {vtype_short} | {v['current']} | {v['limit']} | {over} | {over_pct:.1f}% |"
    )

report.append("")
report.append("---")
report.append("")

# Compliance by Area
report.append("## Compliance by Area")
report.append("")
report.append("Violations segmented by codebase subsystem:")
report.append("")

for subsystem in sorted(by_subsystem.keys()):
    sub_violations = by_subsystem[subsystem]
    # Count unique files in this subsystem
    sub_files = set(v["file"] for v in sub_violations if v["type"] in ["function_too_long", "module_too_long"])

    report.append(f"### {subsystem.title()}")
    report.append("")
    report.append(f"- **Violations:** {len(sub_violations)}")
    report.append(f"- **Affected Files:** {len(sub_files)}")
    report.append("")

    # Breakdown by type
    sub_by_type = defaultdict(int)
    for v in sub_violations:
        sub_by_type[v["type"]] += 1

    if sub_by_type:
        report.append("**By Type:**")
        for vtype, count in sub_by_type.items():
            report.append(f"- {vtype}: {count}")
        report.append("")

report.append("---")
report.append("")

# Appendix: Full Violation List
report.append("## Appendix: Complete Violation List")
report.append("")
report.append("<details>")
report.append("<summary>Click to expand all violations</summary>")
report.append("")

for vtype in sorted(violations_data["by_type"].keys()):
    type_violations = [v for v in violations if v["type"] == vtype]
    report.append(f"### {vtype}")
    report.append("")

    for v in sorted(type_violations, key=lambda x: x["file"]):
        rel_path = v["file"].replace("/Users/dhirajd/Documents/claude/", "")
        report.append(f"- `{rel_path}:{v['line']}`")
        report.append(f"  - {v['message']}")
        report.append(f"  - Current: {v['current']} | Limit: {v['limit']}")
        report.append("")

report.append("</details>")
report.append("")

# Write report
report_path = "audit/reports/03-01-structural-compliance.md"
Path(report_path).parent.mkdir(parents=True, exist_ok=True)
with open(report_path, "w") as f:
    f.write("\n".join(report))

print(f"✓ Report generated: {report_path}")
print(f"  - Total violations: {violations_data['total_violations']}")
print(f"  - Compliance rate: {compliance['compliance_rate']}%")
print(f"  - Worst offenders: {len(worst_offenders)}")
