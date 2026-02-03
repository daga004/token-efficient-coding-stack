#!/usr/bin/env python3
"""
Test harness for real Gemini Flash API execution.

Executes 8 representative validation tasks with real Gemini API to measure
actual token consumption and costs, replacing theoretical estimates from Phase 5.
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add orchestrator to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "orchestrator" / "src"))

from orchestrator.clients.gemini import GeminiClient


# Gemini 3 Flash pricing (as of January 2026)
GEMINI_PRICE_INPUT_PER_1M = 0.50  # $0.50 per 1M input tokens
GEMINI_PRICE_OUTPUT_PER_1M = 3.00  # $3.00 per 1M output tokens


# 8 representative validation tasks across difficulty levels
TEST_TASKS = [
    # Simple tasks (Tier 0-1)
    {
        "id": "simple-1",
        "difficulty": "Simple",
        "tier": 0,
        "description": "Add docstring to function",
        "prompt": "Add a docstring to this Python function:\n\ndef calculate_sum(a, b):\n    return a + b",
    },
    {
        "id": "simple-2",
        "difficulty": "Simple",
        "tier": 1,
        "description": "Fix typo in variable name",
        "prompt": "Fix the typo in this code (varialbe should be variable):\n\nvarilabe_name = 'example'\nprint(varilabe_name)",
    },
    {
        "id": "simple-3",
        "difficulty": "Simple",
        "tier": 1,
        "description": "Add type hint to function",
        "prompt": "Add type hints to this function:\n\ndef greet(name):\n    return f'Hello, {name}!'",
    },
    # Medium tasks (Tier 2-3)
    {
        "id": "medium-1",
        "difficulty": "Medium",
        "tier": 2,
        "description": "Create simple validation function",
        "prompt": "Write a Python function that validates an email address format. Return True if valid, False otherwise. Use regex.",
    },
    {
        "id": "medium-2",
        "difficulty": "Medium",
        "tier": 2,
        "description": "Add error handling to function",
        "prompt": "Add proper error handling to this function:\n\ndef read_json_file(filename):\n    with open(filename) as f:\n        return json.load(f)",
    },
    {
        "id": "medium-3",
        "difficulty": "Medium",
        "tier": 3,
        "description": "Refactor function for clarity",
        "prompt": "Refactor this function to be more readable:\n\ndef p(x,y,z):\n    r=x*2\n    if r>y:return r+z\n    else:return y-z",
    },
    # Complex tasks (Tier 4-5)
    {
        "id": "complex-1",
        "difficulty": "Complex",
        "tier": 4,
        "description": "Implement binary search algorithm",
        "prompt": "Implement a binary search function in Python that finds the index of a target value in a sorted list. Return -1 if not found. Include docstring and type hints.",
    },
    {
        "id": "complex-2",
        "difficulty": "Complex",
        "tier": 5,
        "description": "Debug async race condition",
        "prompt": "This async code has a race condition. Identify and fix it:\n\nimport asyncio\n\ndata = []\n\nasync def add_item(item):\n    await asyncio.sleep(0.1)\n    data.append(item)\n\nasync def process():\n    tasks = [add_item(i) for i in range(10)]\n    await asyncio.gather(*tasks)\n    print(f'Processed {len(data)} items')",
    },
]


def calculate_cost(tokens_input: int, tokens_output: int) -> float:
    """Calculate cost for Gemini Flash execution."""
    cost_input = (tokens_input / 1_000_000) * GEMINI_PRICE_INPUT_PER_1M
    cost_output = (tokens_output / 1_000_000) * GEMINI_PRICE_OUTPUT_PER_1M
    return cost_input + cost_output


async def execute_task(task: dict, client: GeminiClient, dry_run: bool = False) -> dict:
    """Execute a single task with Gemini client."""
    if dry_run:
        return {
            "task_id": task["id"],
            "difficulty": task["difficulty"],
            "tier": task["tier"],
            "description": task["description"],
            "success": None,
            "response": "[DRY RUN - No actual execution]",
            "tokens_input": 0,
            "tokens_output": 0,
            "tokens_total": 0,
            "latency_ms": 0,
            "cost": 0.0,
            "error": None,
        }

    # Execute with real API
    result = await client.execute(task["prompt"])

    tokens_total = result.tokens_input + result.tokens_output
    cost = calculate_cost(result.tokens_input, result.tokens_output)

    return {
        "task_id": task["id"],
        "difficulty": task["difficulty"],
        "tier": task["tier"],
        "description": task["description"],
        "success": result.success,
        "response": result.response[:200] if result.response else "",
        "tokens_input": result.tokens_input,
        "tokens_output": result.tokens_output,
        "tokens_total": tokens_total,
        "latency_ms": result.latency_ms,
        "cost": cost,
        "error": result.error,
    }


def write_evidence_file(results: list, evidence_path: Path, dry_run: bool = False):
    """Write execution results to evidence file in markdown format."""

    # Calculate summary stats
    total_tasks = len(results)
    successful_tasks = sum(1 for r in results if r["success"] is True)
    success_rate = (successful_tasks / total_tasks * 100) if total_tasks > 0 else 0
    total_tokens = sum(r["tokens_total"] for r in results)
    total_cost = sum(r["cost"] for r in results)
    avg_cost = total_cost / total_tasks if total_tasks > 0 else 0

    # Write markdown
    with open(evidence_path, "w") as f:
        f.write("# Gemini Real Execution Evidence\n\n")
        f.write(f"**Execution Date**: {datetime.now().isoformat()}\n")
        f.write(f"**Mode**: {'DRY RUN' if dry_run else 'REAL API EXECUTION'}\n\n")

        f.write("## Summary\n\n")
        f.write(f"- **Total tasks**: {total_tasks}\n")
        f.write(f"- **Successful**: {successful_tasks}/{total_tasks} ({success_rate:.1f}%)\n")
        f.write(f"- **Total tokens**: {total_tokens:,}\n")
        f.write(f"- **Total cost**: ${total_cost:.6f}\n")
        f.write(f"- **Average cost/task**: ${avg_cost:.6f}\n\n")

        f.write("## Pricing Reference\n\n")
        f.write(f"- **Input tokens**: ${GEMINI_PRICE_INPUT_PER_1M}/1M tokens\n")
        f.write(f"- **Output tokens**: ${GEMINI_PRICE_OUTPUT_PER_1M}/1M tokens\n")
        f.write(f"- **Model**: gemini-3-flash-preview\n\n")

        f.write("---\n\n")

        # Write individual task results
        for result in results:
            f.write(f"## Task {result['task_id']}: {result['description']}\n\n")
            f.write(f"**Difficulty**: {result['difficulty']} (Tier {result['tier']})\n\n")

            f.write("### Execution Result\n\n")
            f.write(f"- **Success**: {result['success']}\n")
            f.write(f"- **Response** (first 200 chars):\n  ```\n  {result['response']}\n  ```\n")
            f.write(f"- **Tokens**: {result['tokens_input']:,} in / {result['tokens_output']:,} out / {result['tokens_total']:,} total\n")
            f.write(f"- **Latency**: {result['latency_ms']}ms\n")
            f.write(f"- **Cost**: ${result['cost']:.6f}\n")

            if result["error"]:
                f.write(f"\n**Error**: {result['error']}\n")

            f.write("\n### Notes\n\n")
            if not dry_run and result["success"]:
                f.write("Execution completed successfully.\n")
            elif not dry_run and not result["success"]:
                f.write("Execution failed - see error above.\n")
            else:
                f.write("Dry run - no actual API call made.\n")

            f.write("\n---\n\n")


async def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Test Gemini real API execution")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print tasks without executing (no API calls)",
    )
    args = parser.parse_args()

    # Check for API key
    if not args.dry_run and "GEMINI_API_KEY" not in os.environ:
        print("ERROR: GEMINI_API_KEY environment variable not set")
        print("\nGet your API key from: https://aistudio.google.com/apikey")
        print("Then set it: export GEMINI_API_KEY='your-key-here'")

        # Write evidence file documenting the skip
        evidence_path = Path(__file__).parent.parent / "evidence" / "07-02-gemini-real-execution.md"
        with open(evidence_path, "w") as f:
            f.write("# Gemini Real Execution - API KEY NOT SET\n\n")
            f.write(f"**Attempted**: {datetime.now().isoformat()}\n\n")
            f.write("Execution could not proceed - GEMINI_API_KEY environment variable not set.\n\n")
            f.write("To execute:\n")
            f.write("1. Get API key from https://aistudio.google.com/apikey\n")
            f.write("2. Set: export GEMINI_API_KEY='your-key-here'\n")
            f.write("3. Run: python audit/scripts/test_gemini_real.py\n")

        print(f"\nDocumented in: {evidence_path}")
        sys.exit(1)

    # Initialize client
    client = GeminiClient(model="gemini-flash")

    # Print execution info
    mode = "DRY RUN" if args.dry_run else "REAL API EXECUTION"
    print(f"=== Gemini Test Harness - {mode} ===\n")
    print(f"Tasks to execute: {len(TEST_TASKS)}")
    print(f"Model: gemini-3-flash-preview")

    if not args.dry_run:
        print(f"Estimated cost: $0.50-2.00 (depends on response lengths)\n")

    # Execute tasks
    results = []
    for i, task in enumerate(TEST_TASKS, 1):
        print(f"\n[{i}/{len(TEST_TASKS)}] {task['id']}: {task['description']}")
        print(f"  Difficulty: {task['difficulty']} (Tier {task['tier']})")

        if args.dry_run:
            print("  Status: Skipped (dry run)")
            result = await execute_task(task, client, dry_run=True)
        else:
            print("  Status: Executing...")
            result = await execute_task(task, client, dry_run=False)

            if result["success"]:
                print(f"  ✓ Success - {result['tokens_total']} tokens, ${result['cost']:.6f}")
            else:
                print(f"  ✗ Failed - {result['error']}")

        results.append(result)

    # Write evidence file
    evidence_path = Path(__file__).parent.parent / "evidence" / "07-02-gemini-real-execution.md"
    write_evidence_file(results, evidence_path, dry_run=args.dry_run)

    print(f"\n=== Execution Complete ===")
    print(f"Evidence written to: {evidence_path}")

    if not args.dry_run:
        total_cost = sum(r["cost"] for r in results)
        success_count = sum(1 for r in results if r["success"] is True)
        print(f"\nSummary:")
        print(f"  Success rate: {success_count}/{len(results)}")
        print(f"  Total cost: ${total_cost:.6f}")


if __name__ == "__main__":
    asyncio.run(main())
