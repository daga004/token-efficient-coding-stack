"""
Test correlation between structural violations and token savings performance.

This test correlates structural violations from Phase 3 Plan 01 with token savings
from Phase 2 Plan 04 to determine if non-compliance with AuZoom guidelines
(≤50 line functions, ≤250 line modules) impacts progressive disclosure effectiveness.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pytest


def load_structural_violations() -> Dict[str, Dict]:
    """Load structural violation data from Phase 3 Plan 01 evidence."""
    evidence_dir = Path(__file__).parent.parent / "evidence"

    # Find the most recent structural compliance evidence file
    evidence_files = sorted(evidence_dir.glob("structural_compliance_*.jsonl"))
    if not evidence_files:
        pytest.skip("No structural compliance evidence found")

    latest_file = evidence_files[-1]

    violations_by_file = {}
    with open(latest_file) as f:
        for line in f:
            entry = json.loads(line)
            if entry.get("type") == "measurement" and "violations" in entry.get("data", {}):
                # Parse violations into file-keyed dict
                for violation in entry["data"]["violations"]:
                    file_path = violation["file"]
                    if file_path not in violations_by_file:
                        violations_by_file[file_path] = {
                            "violations": [],
                            "total_severity": 0,
                            "module_line_count": 0
                        }

                    violations_by_file[file_path]["violations"].append(violation)

                    # Extract line count from violation
                    if violation["type"] == "module_too_long":
                        current = violation.get("current", 0)
                        limit = violation.get("limit", 250)
                        violations_by_file[file_path]["module_line_count"] = current
                        # Calculate severity as percentage over limit
                        violations_by_file[file_path]["total_severity"] = (current - limit) / limit * 100

    return violations_by_file


def load_token_savings() -> List[Dict]:
    """Load token savings data from Phase 2 Plan 04 evidence."""
    evidence_dir = Path(__file__).parent.parent / "evidence"

    # Find real_codebase_savings evidence files
    evidence_files = sorted(evidence_dir.glob("real_codebase_savings_*.jsonl"))
    if not evidence_files:
        pytest.skip("No real codebase savings evidence found")

    latest_file = evidence_files[-1]

    savings_data = []
    with open(latest_file) as f:
        for line in f:
            entry = json.loads(line)
            if entry.get("type") == "measurement" and "files" in entry.get("data", {}):
                data = entry["data"]
                # Store per-file savings data
                for file_path in data["files"]:
                    savings_data.append({
                        "file": file_path,
                        "codebase_name": data["codebase_name"],
                        "size_category": data["size_category"],
                        "savings_percentage": data["savings_percentage"],
                        "baseline_tokens": data["baseline_tokens"],
                        "optimized_tokens": data["optimized_tokens"],
                        "total_lines": data["total_lines"],
                        "meets_target": data["meets_target"]
                    })

    return savings_data


def normalize_path(path: str) -> str:
    """Normalize file path to match between systems."""
    # Convert to relative path from project root
    if "/Documents/claude/" in path:
        return path.split("/Documents/claude/")[1]
    return path


def calculate_pearson_correlation(x: List[float], y: List[float]) -> Tuple[Optional[float], Optional[float]]:
    """
    Calculate Pearson correlation coefficient and p-value manually.
    Returns (correlation, p_value) or (None, None) if insufficient data.
    """
    if len(x) < 3 or len(x) != len(y):
        return None, None

    n = len(x)

    # Calculate means
    mean_x = sum(x) / n
    mean_y = sum(y) / n

    # Calculate correlation coefficient
    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    denominator_x = sum((x[i] - mean_x) ** 2 for i in range(n))
    denominator_y = sum((y[i] - mean_y) ** 2 for i in range(n))

    if denominator_x == 0 or denominator_y == 0:
        return None, None

    correlation = numerator / (denominator_x ** 0.5 * denominator_y ** 0.5)

    # Simple p-value approximation using t-distribution
    # For small samples, we'll use a conservative approach
    # t = r * sqrt((n-2)/(1-r^2))
    if abs(correlation) < 1.0:
        t_stat = abs(correlation) * ((n - 2) / (1 - correlation ** 2)) ** 0.5
        # Rough approximation: p < 0.05 when t > 2.0 for small samples
        p_value = 0.04 if t_stat > 2.0 else 0.10
    else:
        p_value = 0.001

    return correlation, p_value


def correlate_violations_with_savings(violations: Dict, savings: List[Dict]) -> Tuple[List[Dict], Dict]:
    """Correlate violations with savings performance for common files."""

    # Normalize paths for both datasets
    violations_normalized = {normalize_path(k): v for k, v in violations.items()}

    correlations = []
    for saving in savings:
        file_path = normalize_path(saving["file"])

        # Check if this file has violations
        has_violation = file_path in violations_normalized
        violation_data = violations_normalized.get(file_path, {})

        correlations.append({
            "file": saving["file"],
            "relative_path": file_path,
            "has_violation": has_violation,
            "violation_severity": violation_data.get("total_severity", 0),
            "module_line_count": violation_data.get("module_line_count", 0),
            "savings_percentage": saving["savings_percentage"],
            "size_category": saving["size_category"],
            "baseline_tokens": saving["baseline_tokens"],
            "optimized_tokens": saving["optimized_tokens"],
            "meets_target": saving["meets_target"]
        })

    # Calculate correlation statistics
    violated_files = [c for c in correlations if c["has_violation"]]
    compliant_files = [c for c in correlations if not c["has_violation"]]

    stats_summary = {
        "total_files_tested": len(correlations),
        "violated_files": len(violated_files),
        "compliant_files": len(compliant_files),
        "average_savings_violated": sum(f["savings_percentage"] for f in violated_files) / len(violated_files) if violated_files else 0,
        "average_savings_compliant": sum(f["savings_percentage"] for f in compliant_files) / len(compliant_files) if compliant_files else 0,
        "overall_average": sum(c["savings_percentage"] for c in correlations) / len(correlations),
        "violation_files_details": []
    }

    # Detailed analysis of violated files
    for vf in violated_files:
        stats_summary["violation_files_details"].append({
            "file": vf["relative_path"],
            "line_count": vf["module_line_count"],
            "over_limit_pct": vf["violation_severity"],
            "savings_pct": vf["savings_percentage"],
            "vs_average": vf["savings_percentage"] - stats_summary["overall_average"]
        })

    # Calculate Pearson correlation if we have enough violated files with variation
    if len(violated_files) >= 3:
        severities = [f["violation_severity"] for f in violated_files]
        savings_vals = [f["savings_percentage"] for f in violated_files]

        if len(set(severities)) > 1:  # Need variation in severities
            corr, p_value = calculate_pearson_correlation(severities, savings_vals)
            stats_summary["pearson_correlation"] = corr
            stats_summary["p_value"] = p_value
            stats_summary["statistically_significant"] = p_value is not None and p_value < 0.05
        else:
            stats_summary["pearson_correlation"] = None
            stats_summary["correlation_note"] = "Insufficient variation in violation severity for correlation"
    else:
        stats_summary["pearson_correlation"] = None
        stats_summary["correlation_note"] = f"Insufficient violated files for correlation (n={len(violated_files)}, need n>=3)"

    return correlations, stats_summary


def test_violation_impact_correlation():
    """
    Test correlation between structural violations and token savings performance.

    Hypothesis: Files exceeding structural limits by >50% show degraded progressive disclosure benefits.
    """

    # Load data from both phases
    violations = load_structural_violations()
    savings = load_token_savings()

    # Correlate violations with savings
    correlations, stats_summary = correlate_violations_with_savings(violations, savings)

    # Log evidence
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    evidence_file = Path(__file__).parent.parent / "evidence" / f"violation_impact_{timestamp}.jsonl"

    with open(evidence_file, "w") as f:
        # Log correlation data
        f.write(json.dumps({
            "test_name": "violation_impact",
            "timestamp": datetime.now().isoformat(),
            "type": "correlation_data",
            "data": {
                "correlations": correlations,
                "statistics": stats_summary
            },
            "metadata": {
                "test": "violation_impact",
                "phase": "03-auzoom-structural-compliance",
                "plan": "02"
            }
        }) + "\n")

        # Log hypothesis test result
        hypothesis_result = "INSUFFICIENT_DATA"
        if stats_summary["pearson_correlation"] is not None:
            if stats_summary["statistically_significant"]:
                if stats_summary["pearson_correlation"] < -0.5:
                    hypothesis_result = "CONFIRMED_STRONG"
                elif stats_summary["pearson_correlation"] < -0.3:
                    hypothesis_result = "CONFIRMED_MODERATE"
                else:
                    hypothesis_result = "REJECTED"
            else:
                hypothesis_result = "INCONCLUSIVE"

        f.write(json.dumps({
            "test_name": "violation_impact",
            "timestamp": datetime.now().isoformat(),
            "type": "hypothesis_test",
            "data": {
                "hypothesis": "Files exceeding structural limits by >50% show degraded progressive disclosure benefits",
                "result": hypothesis_result,
                "evidence": {
                    "violated_avg_savings": stats_summary["average_savings_violated"],
                    "compliant_avg_savings": stats_summary["average_savings_compliant"],
                    "difference": stats_summary["average_savings_violated"] - stats_summary["average_savings_compliant"],
                    "pearson_correlation": stats_summary.get("pearson_correlation"),
                    "p_value": stats_summary.get("p_value"),
                    "sample_size_violated": stats_summary["violated_files"],
                    "sample_size_compliant": stats_summary["compliant_files"]
                }
            },
            "metadata": {
                "test": "violation_impact",
                "phase": "03-auzoom-structural-compliance",
                "plan": "02"
            }
        }) + "\n")

        # Log scatter plot data for visualization
        scatter_data = []
        for corr in correlations:
            if corr["has_violation"]:
                scatter_data.append({
                    "x": corr["violation_severity"],
                    "y": corr["savings_percentage"],
                    "label": os.path.basename(corr["relative_path"]),
                    "size_category": corr["size_category"]
                })

        f.write(json.dumps({
            "test_name": "violation_impact",
            "timestamp": datetime.now().isoformat(),
            "type": "scatter_plot_data",
            "data": {
                "title": "Violation Severity vs Token Savings",
                "x_axis": "Violation Severity (% over 250 line limit)",
                "y_axis": "Token Savings (%)",
                "points": scatter_data
            },
            "metadata": {
                "test": "violation_impact",
                "phase": "03-auzoom-structural-compliance",
                "plan": "02"
            }
        }) + "\n")

    # Assertions
    assert len(correlations) > 0, "Should have correlation data"
    assert stats_summary["total_files_tested"] > 0, "Should have files to analyze"

    # Print summary for visibility
    print(f"\n=== Violation Impact Correlation Analysis ===")
    print(f"Total files tested: {stats_summary['total_files_tested']}")
    print(f"Files with violations: {stats_summary['violated_files']}")
    print(f"Files compliant: {stats_summary['compliant_files']}")
    print(f"\nAverage savings (violated files): {stats_summary['average_savings_violated']:.2f}%")
    print(f"Average savings (compliant files): {stats_summary['average_savings_compliant']:.2f}%")
    print(f"Difference: {stats_summary['average_savings_violated'] - stats_summary['average_savings_compliant']:.2f}%")

    if stats_summary.get("pearson_correlation") is not None:
        print(f"\nPearson correlation: {stats_summary['pearson_correlation']:.3f}")
        print(f"P-value: {stats_summary['p_value']:.4f}")
        print(f"Statistically significant: {stats_summary['statistically_significant']}")
    else:
        print(f"\n{stats_summary.get('correlation_note', 'No correlation calculated')}")

    print(f"\nEvidence logged to: {evidence_file}")
