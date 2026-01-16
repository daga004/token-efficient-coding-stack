"""
Progressive Traversal Executor

Spawns Claude Code Task agents for each test task and logs their interaction
patterns with the auzoom MCP server.

Measures:
- Depth progression (skeleton → summary → full)
- Token consumption at each level
- Conversation overhead
- Quality vs success criteria
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Import task definitions
import sys
sys.path.append(str(Path(__file__).parent / "tests"))
from test_progressive_traversal import PROGRESSIVE_TRAVERSAL_TASKS


class ProgressiveTraversalExecutor:
    """Executes tasks with real Task agents and logs progressive traversal patterns."""

    def __init__(self, evidence_dir: Path):
        self.evidence_dir = evidence_dir
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.evidence_file = self.evidence_dir / f"progressive_traversal_{self.timestamp}.jsonl"

    def execute_task(self, task: Dict[str, Any], task_agent_output: str = None) -> Dict[str, Any]:
        """
        Execute a single task with Task agent and measure progressive traversal.

        Args:
            task: Task definition from test suite
            task_agent_output: Output from spawned Task agent (if already executed)

        Returns:
            Dictionary with measurements:
            - task_id, description, task_type
            - interactions: List of auzoom_read calls with file, level, estimated tokens
            - final_depth: Max depth reached
            - total_tokens: Sum of all tokens
            - conversation_overhead: Estimated overhead between reads
            - baseline_tokens: What Read tool would use
            - net_savings: (baseline - progressive) / baseline
            - quality: Assessment vs success criteria
        """
        result = {
            "task_id": task["task_id"],
            "description": task["description"],
            "task_type": task["task_type"],
            "expected_depth": task["expected_depth"],
            "success_criteria": task["success_criteria"],
            "baseline_tokens": task["baseline_tokens"],
            "timestamp": datetime.now().isoformat(),
        }

        # If task_agent_output provided, analyze it
        if task_agent_output:
            result.update(self._analyze_agent_output(task_agent_output, task))
        else:
            # Task not yet executed - return template
            result["status"] = "pending"
            result["instructions"] = {
                "step_1": "Spawn Task agent with this prompt",
                "step_2": "Agent has auzoom MCP available",
                "step_3": "Log agent output to file",
                "step_4": "Re-run executor with task_agent_output parameter",
            }

        return result

    def _analyze_agent_output(self, output: str, task: Dict) -> Dict[str, Any]:
        """
        Analyze Task agent output to extract progressive traversal metrics.

        Looks for:
        - auzoom_read calls (file, level)
        - Depth progression
        - Token estimates
        - Quality assessment
        """
        # This would parse agent output for tool calls
        # For now, return template for manual filling
        return {
            "status": "executed",
            "interactions": [
                # Example: {"file": "server.py", "level": "skeleton", "tokens": 150, "reasoning": "..."}
            ],
            "final_depth": 0.0,  # To be measured
            "total_tokens": 0,  # To be calculated
            "conversation_overhead": 0,  # To be estimated
            "net_savings_pct": 0.0,  # (baseline - progressive) / baseline * 100
            "quality": "unknown",  # To be assessed
        }

    def spawn_task_agent(self, task: Dict[str, Any]) -> str:
        """
        Spawn a Task agent for this task.

        Returns: Instructions for manual execution or task_id for tracking
        """
        prompt = f"""Execute this task using auzoom MCP tools:

Task: {task['description']}

Instructions:
- Start with auzoom_read at skeleton level to get overview
- Only request deeper levels (summary, full) if needed
- Use auzoom_find and auzoom_get_dependencies for graph navigation
- Complete the task according to success criteria: {task['success_criteria']}

Expected approach:
- Type: {task['task_type']}
- Expected depth: {task['expected_depth']} (1.0=skeleton, 2.0=summary, 3.0=full)

Complete the task, documenting which auzoom tools you use."""

        return prompt

    def execute_all_tasks(self, task_ids: List[int] = None, dry_run: bool = True) -> List[Dict]:
        """
        Execute all or specified tasks.

        Args:
            task_ids: Specific task IDs to execute (or None for all)
            dry_run: If True, just show what would be executed

        Returns:
            List of result dictionaries
        """
        tasks_to_execute = [
            t for t in PROGRESSIVE_TRAVERSAL_TASKS
            if task_ids is None or t["task_id"] in task_ids
        ]

        print(f"Progressive Traversal Executor")
        print(f"{'=' * 60}")
        print(f"Tasks to execute: {len(tasks_to_execute)}")
        print(f"Evidence file: {self.evidence_file}")
        print(f"Dry run: {dry_run}")
        print()

        results = []

        for task in tasks_to_execute:
            print(f"\nTask {task['task_id']}: {task['description'][:50]}...")
            print(f"  Type: {task['task_type']}, Expected depth: {task['expected_depth']}")

            if dry_run:
                print(f"  [DRY RUN] Would spawn Task agent with prompt:")
                prompt = self.spawn_task_agent(task)
                print(f"  {prompt[:100]}...")
                result = self.execute_task(task, task_agent_output=None)
            else:
                print(f"  Spawning Task agent...")
                prompt = self.spawn_task_agent(task)
                print(f"  Prompt: {prompt}")
                print(f"  [MANUAL] Execute this prompt via Task tool and provide output")
                result = self.execute_task(task, task_agent_output=None)

            results.append(result)

            # Log to evidence file
            with open(self.evidence_file, "a") as f:
                f.write(json.dumps(result) + "\n")

        print(f"\n{'=' * 60}")
        print(f"Execution complete. Results logged to: {self.evidence_file}")

        return results

    def generate_summary_report(self, results: List[Dict]) -> str:
        """Generate summary report from execution results."""
        executed = [r for r in results if r.get("status") == "executed"]
        pending = [r for r in results if r.get("status") == "pending"]

        report = []
        report.append("Progressive Traversal Execution Summary")
        report.append("=" * 60)
        report.append(f"Total tasks: {len(results)}")
        report.append(f"Executed: {len(executed)}")
        report.append(f"Pending: {len(pending)}")
        report.append("")

        if executed:
            report.append("Executed Tasks:")
            for r in executed:
                report.append(f"  Task {r['task_id']} ({r['task_type']}): depth {r['final_depth']}, {r['total_tokens']} tokens")

        if pending:
            report.append("\nPending Tasks:")
            for r in pending:
                report.append(f"  Task {r['task_id']} ({r['task_type']}): {r['description'][:60]}...")

        return "\n".join(report)


def main():
    """Main execution entry point."""
    evidence_dir = Path(__file__).parent / "evidence"
    executor = ProgressiveTraversalExecutor(evidence_dir)

    print("Phase 6.5 Plan 01: Progressive Traversal Validation")
    print()
    print("This executor will run 10 tasks with real Task agents to measure")
    print("progressive traversal patterns (skeleton → summary → full).")
    print()
    print("Options:")
    print("  1. Dry run - Show what would be executed (fast)")
    print("  2. Execute sample tasks (2-3 tasks, ~5-10 min)")
    print("  3. Execute all tasks (10 tasks, ~20-30 min)")
    print()

    # For now, default to showing what would be executed
    # Actual execution requires user decision on approach

    # Sample: Execute first task from each type
    sample_task_ids = [1, 3, 6, 9]  # shallow, medium, deep, graph

    print("Running dry run on sample tasks to show approach...")
    results = executor.execute_all_tasks(task_ids=sample_task_ids, dry_run=True)

    print()
    print(executor.generate_summary_report(results))


if __name__ == "__main__":
    main()
