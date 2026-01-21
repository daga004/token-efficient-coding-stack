#!/usr/bin/env python3
"""
Net Savings Calculator for Progressive vs Upfront Comparison

Compares progressive traversal (from Phase 6.5-01) against baseline upfront
full read to calculate net token savings accounting for all overhead.
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


class NetSavingsCalculator:
    """Calculate net savings between progressive and baseline approaches."""

    def __init__(self):
        self.evidence_path = Path("audit/evidence")

    def load_progressive_results(self) -> List[Dict[str, Any]]:
        """Load progressive traversal results from Phase 6.5-01."""
        filepath = self.evidence_path / "progressive_traversal_20260113_results.jsonl"

        results = []
        with open(filepath, 'r') as f:
            for line in f:
                if line.strip():
                    results.append(json.loads(line))

        return results

    def load_baseline_results(self) -> List[Dict[str, Any]]:
        """Load baseline upfront results from Task 1."""
        # Find most recent baseline file
        baseline_files = sorted(self.evidence_path.glob("baseline_upfront_*.jsonl"))
        if not baseline_files:
            raise FileNotFoundError("No baseline results found")

        filepath = baseline_files[-1]

        results = []
        with open(filepath, 'r') as f:
            for line in f:
                if line.strip():
                    results.append(json.loads(line))

        return results

    def calculate_task_net_savings(
        self, progressive: Dict[str, Any], baseline: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate net savings for a single task.

        Net savings = (baseline_tokens - progressive_total) / baseline_tokens × 100%

        Where progressive_total = read_tokens + conversation_overhead
        """
        prog_tokens = progressive.get("total_tokens", 0)
        prog_overhead = progressive.get("conversation_overhead", 0)
        prog_total = prog_tokens + prog_overhead

        base_tokens = baseline.get("total_tokens", 0)

        # Calculate net savings
        if base_tokens == 0:
            net_savings_pct = 0.0
        else:
            net_savings_pct = ((base_tokens - prog_total) / base_tokens) * 100

        # Determine verdict
        if net_savings_pct >= 20:
            verdict = "WIN"
        elif net_savings_pct >= 0:
            verdict = "MARGINAL"
        else:
            verdict = "LOSS"

        return {
            "task_id": progressive.get("task_id"),
            "description": progressive.get("description"),
            "task_type": progressive.get("task_type"),
            "progressive_tokens": prog_tokens,
            "conversation_overhead": prog_overhead,
            "progressive_total": prog_total,
            "baseline_tokens": base_tokens,
            "net_savings_pct": round(net_savings_pct, 1),
            "verdict": verdict,
            "overhead_impact_pct": round((prog_overhead / prog_total * 100), 1) if prog_total > 0 else 0,
        }

    def calculate_aggregate_metrics(self, comparisons: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate aggregate metrics across all tasks."""
        if not comparisons:
            return {}

        # Overall metrics
        total_progressive = sum(c["progressive_total"] for c in comparisons)
        total_baseline = sum(c["baseline_tokens"] for c in comparisons)
        avg_net_savings = sum(c["net_savings_pct"] for c in comparisons) / len(comparisons)

        # Win rate
        wins = sum(1 for c in comparisons if c["verdict"] == "WIN")
        losses = sum(1 for c in comparisons if c["verdict"] == "LOSS")
        marginal = sum(1 for c in comparisons if c["verdict"] == "MARGINAL")
        win_rate = wins / len(comparisons)

        # By task type
        by_type = {}
        for task_type in set(c["task_type"] for c in comparisons):
            tasks = [c for c in comparisons if c["task_type"] == task_type]
            avg_savings = sum(t["net_savings_pct"] for t in tasks) / len(tasks)
            type_wins = sum(1 for t in tasks if t["verdict"] == "WIN")
            type_win_rate = type_wins / len(tasks)

            by_type[task_type] = {
                "count": len(tasks),
                "avg_savings": round(avg_savings, 1),
                "win_rate": round(type_win_rate, 2),
            }

        return {
            "overall": {
                "tasks_analyzed": len(comparisons),
                "total_progressive_tokens": total_progressive,
                "total_baseline_tokens": total_baseline,
                "average_net_savings": round(avg_net_savings, 1),
                "win_rate": round(win_rate, 2),
                "tasks_with_savings": wins,
                "tasks_marginal": marginal,
                "tasks_with_overhead": losses,
            },
            "by_type": by_type,
        }

    def calculate_breakeven(self, comparisons: List[Dict[str, Any]]) -> int:
        """
        Estimate file size breakeven point.

        For now, use heuristic based on task results.
        Would need more data points for precise calculation.
        """
        # Tasks that saved tokens
        wins = [c for c in comparisons if c["verdict"] in ["WIN", "MARGINAL"]]
        losses = [c for c in comparisons if c["verdict"] == "LOSS"]

        if wins and losses:
            # Heuristic: shallow tasks (skeleton-only) typically win
            # Medium/deep tasks on small files typically lose
            # Breakeven is likely around file size where summary becomes beneficial

            # Based on Phase 5 findings: ~650 lines / ~2600 tokens
            return 2600
        elif wins:
            # All tasks saved tokens - progressive is beneficial
            return 0
        else:
            # All tasks lost tokens - progressive adds overhead
            # Would need larger files to be beneficial
            return 5000

    def generate_comparison_report(self) -> Dict[str, Any]:
        """Generate complete comparison with all metrics."""
        print("Loading progressive results from Phase 6.5-01...")
        progressive = self.load_progressive_results()
        print(f"  Found {len(progressive)} progressive task results")

        print("Loading baseline results from Task 1...")
        baseline = self.load_baseline_results()
        print(f"  Found {len(baseline)} baseline task results")

        print("\nCalculating net savings for each task...")
        comparisons = []

        for prog in progressive:
            task_id = prog["task_id"]
            base = next((b for b in baseline if b["task_id"] == task_id), None)

            if base:
                comparison = self.calculate_task_net_savings(prog, base)
                comparisons.append(comparison)
                print(f"  Task {task_id}: {comparison['net_savings_pct']:+.1f}% - {comparison['verdict']}")

        print("\nCalculating aggregate metrics...")
        aggregate = self.calculate_aggregate_metrics(comparisons)

        print("\nEstimating breakeven file size...")
        breakeven = self.calculate_breakeven(comparisons)

        report = {
            "metadata": {
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "progressive_source": "audit/evidence/progressive_traversal_20260113_results.jsonl",
                "baseline_source": "audit/evidence/baseline_upfront_20260121_125901.jsonl",
                "tasks_compared": len(comparisons),
            },
            "task_by_task": comparisons,
            "aggregate": aggregate,
            "breakeven_file_size_tokens": breakeven,
        }

        return report

    def save_report(self, report: Dict[str, Any]) -> str:
        """Save report to JSON file."""
        filepath = Path("audit/net_savings.json")

        with open(filepath, 'w') as f:
            json.dumps(report, f, indent=2)

        print(f"\n✅ Report saved to: {filepath}")
        return str(filepath)


def main():
    """Run net savings calculator."""
    calculator = NetSavingsCalculator()

    print("=" * 60)
    print("NET SAVINGS CALCULATOR")
    print("Progressive vs Upfront Comparison")
    print("=" * 60)
    print()

    report = calculator.generate_comparison_report()

    print("\n" + "=" * 60)
    print("AGGREGATE RESULTS")
    print("=" * 60)

    overall = report["aggregate"]["overall"]
    print(f"\nTasks analyzed: {overall['tasks_analyzed']}")
    print(f"Average net savings: {overall['average_net_savings']:+.1f}%")
    print(f"Win rate: {overall['win_rate'] * 100:.0f}%")
    print(f"  Wins: {overall['tasks_with_savings']}")
    print(f"  Marginal: {overall['tasks_marginal']}")
    print(f"  Losses: {overall['tasks_with_overhead']}")

    print("\nBy Task Type:")
    for task_type, metrics in report["aggregate"]["by_type"].items():
        print(f"  {task_type}: {metrics['avg_savings']:+.1f}% avg, {metrics['win_rate'] * 100:.0f}% win rate")

    print(f"\nBreakeven file size: ~{report['breakeven_file_size_tokens']} tokens")

    # Save to JSON
    filepath = Path("audit/net_savings.json")
    with open(filepath, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n✅ Full report saved to: {filepath}")


if __name__ == "__main__":
    main()
