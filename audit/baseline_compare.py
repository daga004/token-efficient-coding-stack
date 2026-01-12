"""Baseline comparison utility for measuring audit impact.

This module provides tools to compare the current system state against
the baseline snapshot, enabling measurement of improvements from audit
fixes and verification.

Usage:
    python audit/baseline_compare.py

AuZoom compliance: All functions ≤50 lines, module ≤250 lines.
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional


def load_baseline(path: str = "audit/baseline/metrics.json") -> Dict[str, Any]:
    """Load baseline metrics from JSON snapshot.

    Args:
        path: Path to baseline metrics file

    Returns:
        Baseline metrics dictionary

    Raises:
        FileNotFoundError: If baseline file doesn't exist
        json.JSONDecodeError: If baseline file is invalid JSON
    """
    baseline_path = Path(path)
    if not baseline_path.exists():
        raise FileNotFoundError(f"Baseline not found: {path}")

    with open(baseline_path) as f:
        return json.load(f)


def capture_current() -> Dict[str, Any]:
    """Re-run baseline measurements on current state.

    Captures same metrics as Task 1 baseline for comparison.

    Returns:
        Current metrics dictionary matching baseline structure
    """
    # Git state
    commit_hash = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        text=True
    ).strip()

    branch = subprocess.check_output(
        ["git", "branch", "--show-current"],
        text=True
    ).strip()

    # File counts
    py_files = subprocess.check_output(
        ["find", ".", "-name", "*.py", "-not", "-path", "*/__pycache__/*"],
        text=True
    ).strip().split('\n')
    py_count = len([f for f in py_files if f])

    return {
        "git_state": {
            "commit_hash": commit_hash,
            "commit_short": commit_hash[:7],
            "branch": branch
        },
        "codebase_statistics": {
            "python_files_total": py_count
        }
    }


def compare(baseline: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
    """Compute deltas and improvements between baseline and current.

    Args:
        baseline: Baseline metrics from load_baseline()
        current: Current metrics from capture_current()

    Returns:
        Comparison report with deltas and improvement indicators
    """
    report = {
        "commits": {
            "baseline": baseline["git_state"]["commit_short"],
            "current": current["git_state"]["commit_short"],
            "changed": baseline["git_state"]["commit_hash"] !=
                      current["git_state"]["commit_hash"]
        },
        "files": {
            "baseline_count": baseline["codebase_statistics"]["python_files_total"],
            "current_count": current["codebase_statistics"]["python_files_total"],
            "delta": (current["codebase_statistics"]["python_files_total"] -
                     baseline["codebase_statistics"]["python_files_total"])
        }
    }

    # Add validation metrics comparison if available in current
    if "validation_metrics" in baseline:
        val_base = baseline["validation_metrics"]["overall"]
        report["validation"] = {
            "baseline_token_reduction": val_base["overall_token_reduction_pct"],
            "baseline_cost_reduction": val_base["overall_cost_reduction_pct"]
        }

    return report


def format_comparison(comparison: Dict[str, Any]) -> str:
    """Format comparison report for human readability.

    Args:
        comparison: Comparison dict from compare()

    Returns:
        Formatted markdown report string
    """
    lines = ["# Baseline Comparison Report\n"]

    # Git changes
    commits = comparison["commits"]
    if commits["changed"]:
        lines.append(f"**Commits**: {commits['baseline']} → {commits['current']}")
        lines.append("✅ **State changed** (expected after audit)\n")
    else:
        lines.append(f"**Commits**: {commits['baseline']} (unchanged)")
        lines.append("⚠️ **No changes** (smoke test)\n")

    # File count changes
    files = comparison["files"]
    delta = files["delta"]
    if delta > 0:
        lines.append(f"**Files**: {files['baseline_count']} → {files['current_count']} (+{delta} files)")
    elif delta < 0:
        lines.append(f"**Files**: {files['baseline_count']} → {files['current_count']} ({delta} files)")
    else:
        lines.append(f"**Files**: {files['baseline_count']} (no change)")

    return "\n".join(lines)


def main():
    """Run baseline comparison and display results."""
    try:
        baseline = load_baseline()
        current = capture_current()
        comparison = compare(baseline, current)
        report = format_comparison(comparison)

        print(report)

        # Save report
        output_path = Path("audit/baseline/comparison_report.md")
        output_path.write_text(report)
        print(f"\n✅ Report saved to: {output_path}")

    except Exception as e:
        print(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()
