"""
Aggregate Metrics Calculator

Processes all evidence files from simple + challenging validation
and computes aggregate statistics for comparison to claimed metrics.
"""

import json
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, asdict


@dataclass
class TaskMetrics:
    """Metrics for a single task execution."""
    task_id: str
    approach: str  # "baseline" or "optimized"
    description: str
    tokens: int
    model: str
    cost: float
    notes: str = ""


@dataclass
class AggregateMetrics:
    """Aggregated metrics across all tasks."""
    # Totals
    total_tasks: int
    baseline_total_tokens: int
    optimized_total_tokens: int
    baseline_total_cost: float
    optimized_total_cost: float

    # Savings
    token_savings_pct: float
    cost_savings_pct: float

    # By task category
    simple_tasks_count: int
    simple_cost_savings_pct: float
    simple_token_savings_pct: float

    challenging_tasks_count: int
    challenging_cost_savings_pct: float
    challenging_token_savings_pct: float

    # Quality (from evidence, if available)
    simple_success_rate: float
    challenging_success_rate: float
    overall_success_rate: float

    # By-tier performance
    tier_performance: Dict[str, Dict[str, Any]]

    # Task-level details
    task_details: List[Dict[str, Any]]


class AggregateMetricsCalculator:
    """Calculate aggregate metrics from evidence files."""

    def __init__(self, evidence_dir: str = "audit/evidence"):
        self.evidence_dir = Path(evidence_dir)
        self.simple_tasks: List[TaskMetrics] = []
        self.challenging_tasks: List[TaskMetrics] = []

    def load_evidence(self):
        """Load all validation evidence from JSONL files."""
        # Load simple validation (has execution data)
        simple_files = list(self.evidence_dir.glob("simple_validation_*.jsonl"))
        for file in simple_files:
            with open(file) as f:
                for line in f:
                    entry = json.loads(line.strip())
                    self.simple_tasks.append(TaskMetrics(
                        task_id=entry["task_id"],
                        approach=entry["approach"],
                        description=entry["description"],
                        tokens=entry["tokens_estimate"],
                        model=entry["model"],
                        cost=entry["cost_estimate"],
                        notes=entry.get("notes", "")
                    ))

        # Load challenging validation (only task definitions, no execution)
        challenging_files = list(self.evidence_dir.glob("challenging_validation_*.jsonl"))
        # Note: Challenging tasks have no execution data, only definitions
        # We'll note this in the report

        print(f"Loaded {len(self.simple_tasks)} simple task measurements")
        print(f"Found {len(list(challenging_files))} challenging task definition files")

    def calculate_aggregates(self) -> AggregateMetrics:
        """Calculate aggregate metrics from loaded evidence."""
        # Separate baseline and optimized
        simple_baseline = [t for t in self.simple_tasks if t.approach == "baseline"]
        simple_optimized = [t for t in self.simple_tasks if t.approach == "optimized"]

        # Calculate simple task totals
        simple_baseline_tokens = sum(t.tokens for t in simple_baseline)
        simple_optimized_tokens = sum(t.tokens for t in simple_optimized)
        simple_baseline_cost = sum(t.cost for t in simple_baseline)
        simple_optimized_cost = sum(t.cost for t in simple_optimized)

        # Calculate savings
        simple_token_savings = (simple_baseline_tokens - simple_optimized_tokens) / simple_baseline_tokens * 100 if simple_baseline_tokens > 0 else 0
        simple_cost_savings = (simple_baseline_cost - simple_optimized_cost) / simple_baseline_cost * 100 if simple_baseline_cost > 0 else 0

        # Overall metrics (simple only, since challenging has no execution data)
        overall_tokens_baseline = simple_baseline_tokens
        overall_tokens_optimized = simple_optimized_tokens
        overall_cost_baseline = simple_baseline_cost
        overall_cost_optimized = simple_optimized_cost

        overall_token_savings = simple_token_savings
        overall_cost_savings = simple_cost_savings

        # Quality metrics (not available in file measurements)
        # Note: These would come from actual execution validation
        simple_success_rate = 0.0  # Unknown - file measurements don't include quality
        challenging_success_rate = 0.0  # Unknown - tasks defined but not executed
        overall_success_rate = 0.0  # Unknown

        # By-tier performance (extract from task details)
        tier_performance = self._calculate_tier_performance(simple_baseline, simple_optimized)

        # Task-level details
        task_details = self._build_task_details(simple_baseline, simple_optimized)

        return AggregateMetrics(
            total_tasks=len(simple_baseline),  # 10 simple tasks
            baseline_total_tokens=overall_tokens_baseline,
            optimized_total_tokens=overall_tokens_optimized,
            baseline_total_cost=overall_cost_baseline,
            optimized_total_cost=overall_cost_optimized,
            token_savings_pct=overall_token_savings,
            cost_savings_pct=overall_cost_savings,
            simple_tasks_count=len(simple_baseline),
            simple_cost_savings_pct=simple_cost_savings,
            simple_token_savings_pct=simple_token_savings,
            challenging_tasks_count=0,  # Not executed
            challenging_cost_savings_pct=0.0,  # Not executed
            challenging_token_savings_pct=0.0,  # Not executed
            simple_success_rate=simple_success_rate,
            challenging_success_rate=challenging_success_rate,
            overall_success_rate=overall_success_rate,
            tier_performance=tier_performance,
            task_details=task_details
        )

    def _calculate_tier_performance(self, baseline: List[TaskMetrics], optimized: List[TaskMetrics]) -> Dict[str, Dict[str, Any]]:
        """Calculate performance by model tier."""
        # Map models to tiers
        tier_map = {
            "claude-3-5-haiku-20241022": "Flash/Haiku",
            "claude-3-5-sonnet-20241022": "Sonnet",
            "claude-opus-4-5-20251101": "Opus"
        }

        # Group by tier
        tier_data = {}
        for opt_task in optimized:
            tier = tier_map.get(opt_task.model, "Unknown")
            if tier not in tier_data:
                tier_data[tier] = {
                    "tasks": [],
                    "baseline_costs": [],
                    "optimized_costs": [],
                    "baseline_tokens": [],
                    "optimized_tokens": []
                }

            # Find corresponding baseline
            baseline_task = next((b for b in baseline if b.task_id == opt_task.task_id), None)
            if baseline_task:
                tier_data[tier]["tasks"].append(opt_task.task_id)
                tier_data[tier]["baseline_costs"].append(baseline_task.cost)
                tier_data[tier]["optimized_costs"].append(opt_task.cost)
                tier_data[tier]["baseline_tokens"].append(baseline_task.tokens)
                tier_data[tier]["optimized_tokens"].append(opt_task.tokens)

        # Calculate averages
        tier_performance = {}
        for tier, data in tier_data.items():
            baseline_cost = sum(data["baseline_costs"])
            optimized_cost = sum(data["optimized_costs"])
            baseline_tokens = sum(data["baseline_tokens"])
            optimized_tokens = sum(data["optimized_tokens"])

            tier_performance[tier] = {
                "task_count": len(data["tasks"]),
                "tasks": data["tasks"],
                "avg_cost_savings_pct": (baseline_cost - optimized_cost) / baseline_cost * 100 if baseline_cost > 0 else 0,
                "avg_token_savings_pct": (baseline_tokens - optimized_tokens) / baseline_tokens * 100 if baseline_tokens > 0 else 0,
                "baseline_cost": baseline_cost,
                "optimized_cost": optimized_cost,
                "baseline_tokens": baseline_tokens,
                "optimized_tokens": optimized_tokens
            }

        return tier_performance

    def _build_task_details(self, baseline: List[TaskMetrics], optimized: List[TaskMetrics]) -> List[Dict[str, Any]]:
        """Build task-level detail list."""
        details = []
        for base_task in baseline:
            opt_task = next((o for o in optimized if o.task_id == base_task.task_id), None)
            if opt_task:
                token_savings = (base_task.tokens - opt_task.tokens) / base_task.tokens * 100 if base_task.tokens > 0 else 0
                cost_savings = (base_task.cost - opt_task.cost) / base_task.cost * 100 if base_task.cost > 0 else 0

                details.append({
                    "task_id": base_task.task_id,
                    "description": base_task.description,
                    "baseline_tokens": base_task.tokens,
                    "optimized_tokens": opt_task.tokens,
                    "token_savings_pct": token_savings,
                    "baseline_cost": base_task.cost,
                    "optimized_cost": opt_task.cost,
                    "cost_savings_pct": cost_savings,
                    "model": opt_task.model
                })

        return details

    def generate_report(self, metrics: AggregateMetrics) -> str:
        """Generate human-readable report."""
        report = []
        report.append("=" * 80)
        report.append("AGGREGATE METRICS REPORT")
        report.append("=" * 80)
        report.append("")

        report.append("## Overall Metrics")
        report.append(f"Total tasks measured: {metrics.total_tasks}")
        report.append(f"Baseline total tokens: {metrics.baseline_total_tokens:,}")
        report.append(f"Optimized total tokens: {metrics.optimized_total_tokens:,}")
        report.append(f"Token savings: {metrics.token_savings_pct:.1f}%")
        report.append(f"")
        report.append(f"Baseline total cost: ${metrics.baseline_total_cost:.6f}")
        report.append(f"Optimized total cost: ${metrics.optimized_total_cost:.6f}")
        report.append(f"Cost savings: {metrics.cost_savings_pct:.1f}%")
        report.append("")

        report.append("## Simple Tasks (10 tasks)")
        report.append(f"Token savings: {metrics.simple_token_savings_pct:.1f}%")
        report.append(f"Cost savings: {metrics.simple_cost_savings_pct:.1f}%")
        report.append("")

        report.append("## Challenging Tasks")
        report.append(f"Note: Challenging tasks defined but not executed (cost/time constraints)")
        report.append(f"Task definitions: 15 tasks")
        report.append(f"Execution data: None available")
        report.append("")

        report.append("## By-Tier Performance")
        for tier, perf in metrics.tier_performance.items():
            report.append(f"\n### {tier}")
            report.append(f"Tasks: {perf['task_count']} ({', '.join(perf['tasks'])})")
            report.append(f"Token savings: {perf['avg_token_savings_pct']:.1f}%")
            report.append(f"Cost savings: {perf['avg_cost_savings_pct']:.1f}%")

        report.append("")
        report.append("## Task-Level Details")
        for detail in metrics.task_details:
            report.append(f"\nTask {detail['task_id']}: {detail['description']}")
            report.append(f"  Tokens: {detail['baseline_tokens']} → {detail['optimized_tokens']} ({detail['token_savings_pct']:+.1f}%)")
            report.append(f"  Cost: ${detail['baseline_cost']:.6f} → ${detail['optimized_cost']:.6f} ({detail['cost_savings_pct']:+.1f}%)")
            report.append(f"  Model: {detail['model']}")

        return "\n".join(report)


if __name__ == "__main__":
    calc = AggregateMetricsCalculator()
    calc.load_evidence()
    metrics = calc.calculate_aggregates()

    # Print report
    print(calc.generate_report(metrics))

    # Save JSON
    output_file = Path("audit/aggregate_metrics.json")
    with open(output_file, "w") as f:
        json.dump(asdict(metrics), f, indent=2)

    print(f"\n\nJSON output saved to: {output_file}")
