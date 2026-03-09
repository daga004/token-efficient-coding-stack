#!/usr/bin/env python3
"""
Token benchmark: compare three approaches for reading codebases.

Approaches:
  A (Naive)     : Read every file fully
  B (Baseline)  : Glob + Grep + targeted Read (structured, no tooling)
  C (AuZoom)    : Progressive disclosure via auzoom_read

Run: python3 benchmark/token_benchmark.py [path-to-repo]
Default: benchmarks the auzoom/ source itself
"""

import sys
import os
import re
import json
from pathlib import Path

# Adjust path to import AuZoom
sys.path.insert(0, str(Path(__file__).parent.parent / "auzoom" / "src"))

try:
    from auzoom.core.parsing.parser import PythonParser
    AUZOOM_AVAILABLE = True
except ImportError as e:
    print(f"Warning: AuZoom import failed ({e}). Approach C will be skipped.")
    AUZOOM_AVAILABLE = False

# MCP tool schema overhead (tokens added to context when AuZoom MCP is registered)
# 9 tools × ~117 tokens/schema average = ~1,050 tokens
# With MCP CLI mode enabled, this drops to ~0 (tools loaded on-demand)
MCP_SCHEMA_OVERHEAD = 1050
MCP_CLI_SCHEMA_OVERHEAD = 0

# Per-call overhead (JSON encoding of tool call + tool name in context)
MCP_CALL_OVERHEAD = 30

# Token estimation: ~4 characters per token (rough but reasonable for Python code)
CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    """Estimate token count from text (4 chars per token heuristic)."""
    return max(1, len(text) // CHARS_PER_TOKEN)


def get_py_files(path: Path, exclude_tests: bool = True) -> list[Path]:
    """Get all Python files in path, optionally excluding test files."""
    files = []
    for f in path.rglob("*.py"):
        if exclude_tests and ("test" in f.parts or f.name.startswith("test_")):
            continue
        files.append(f)
    return sorted(files)


def approach_a_naive(repo_path: Path) -> dict:
    """Read every file fully. Worst-case baseline."""
    files = get_py_files(repo_path)
    total_tokens = 0
    total_files = 0
    max_file_tokens = 0

    for f in files:
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            tokens = estimate_tokens(content)
            total_tokens += tokens
            total_files += 1
            max_file_tokens = max(max_file_tokens, tokens)
        except Exception:
            pass

    return {
        "approach": "A (Naive — Read all files)",
        "files_read": total_files,
        "tokens": total_tokens,
        "max_file_tokens": max_file_tokens,
        "notes": "Reads every file fully — unrealistic but shows worst case",
    }


def approach_b_structured(repo_path: Path) -> dict:
    """
    Structured Glob/Grep/Read baseline.

    Simulates the hierarchical reading pattern:
    1. Read DESIGN.md if exists (~200 tokens)
    2. Glob all .py files (~50 tokens for file list)
    3. Read __init__.py of each package (~100 tokens each)
    4. Grep for target function name (~30 tokens)
    5. Read just the target file (one file, full content)

    This is the 'free layer' — good structure + built-in tools.
    """
    files = get_py_files(repo_path)
    tokens = 0
    files_read = 0

    # Step 1: Read DESIGN.md or README (orientation)
    for design_file in ["DESIGN.md", "ARCHITECTURE.md", "README.md"]:
        df = repo_path / design_file
        if df.exists():
            content = df.read_text(encoding="utf-8", errors="ignore")
            # Cap at 500 tokens (we don't read the whole README, just the architecture section)
            tokens += min(estimate_tokens(content), 500)
            files_read += 1
            break
    else:
        # No design doc — cost of absence is that you need to read more files
        tokens += 100  # At least a basic Glob to orient

    # Step 2: Glob output (file path listing)
    glob_output = "\n".join(str(f.relative_to(repo_path)) for f in files)
    tokens += estimate_tokens(glob_output)

    # Step 3: Read __init__.py files (package summaries)
    init_files = [f for f in files if f.name == "__init__.py"]
    for init_f in init_files:
        try:
            content = init_f.read_text(encoding="utf-8", errors="ignore")
            tokens += estimate_tokens(content)
            files_read += 1
        except Exception:
            pass

    # Step 4: Grep result (find target function — ~30 tokens for the grep output)
    tokens += 30

    # Step 5: Read one target file (average file size for this repo)
    if files:
        file_sizes = []
        for f in files:
            if f.name != "__init__.py":
                try:
                    content = f.read_text(encoding="utf-8", errors="ignore")
                    file_sizes.append(estimate_tokens(content))
                except Exception:
                    pass

        if file_sizes:
            avg_file_tokens = sum(file_sizes) // len(file_sizes)
            tokens += avg_file_tokens
            files_read += 1

    return {
        "approach": "B (Structured baseline — Glob/Grep/Read)",
        "files_read": files_read,
        "tokens": tokens,
        "notes": "DESIGN.md + Glob + __init__.py reads + one full file read",
    }


def approach_c_auzoom(repo_path: Path) -> dict:
    """
    AuZoom progressive disclosure.

    Simulates:
    1. Schema overhead (MCP tool schemas always in context)
    2. auzoom_find (locate entry point)
    3. auzoom_read(skeleton) of all files in target module
    4. auzoom_read(summary) of one target file
    5. auzoom_read(full) only if editing (not counted here — read tasks)
    """
    if not AUZOOM_AVAILABLE:
        return {
            "approach": "C (AuZoom — progressive disclosure)",
            "files_read": 0,
            "tokens": -1,
            "notes": "AuZoom not available",
        }

    try:
        parser = PythonParser()
        py_files = get_py_files(repo_path)

        # Parse all files to measure skeleton vs full content sizes
        skeleton_tokens_total = 0
        summary_tokens_total = 0
        full_tokens_total = 0
        files_parsed = 0

        for f in py_files:
            try:
                nodes = parser.parse_file(str(f))
                if not nodes:
                    continue

                file_full_tokens = estimate_tokens(f.read_text(encoding="utf-8", errors="ignore"))
                full_tokens_total += file_full_tokens

                # Skeleton: just signatures/names (function defs without body)
                skeleton_parts = []
                summary_parts = []
                for node in nodes:
                    if node.signature:
                        skeleton_parts.append(node.signature)
                    elif node.name:
                        skeleton_parts.append(node.name)
                    # Summary adds docstrings
                    if node.docstring:
                        summary_parts.append(node.docstring)
                    if node.source:
                        summary_parts.append(node.source[:100])  # first 100 chars

                skeleton_content = "\n".join(skeleton_parts)
                skeleton_tokens_total += max(30, estimate_tokens(skeleton_content))

                summary_content = skeleton_content + "\n" + "\n".join(summary_parts)
                summary_tokens_total += max(50, estimate_tokens(summary_content))

                files_parsed += 1
            except Exception:
                pass

        # Scenario: Explore + Find + Understand (don't read full files)
        # 1. MCP schema overhead (always in context)
        schema_tokens = MCP_SCHEMA_OVERHEAD

        # 2. auzoom_find (~50 tokens output + 30 overhead per call)
        find_tokens = 50 + MCP_CALL_OVERHEAD

        # 3. auzoom_read(skeleton) of all files in one module (~5 files avg)
        # Use average skeleton size
        if files_parsed > 0:
            avg_skeleton = skeleton_tokens_total // files_parsed
            module_skeleton_tokens = avg_skeleton * 5  # explore ~5 files
        else:
            module_skeleton_tokens = 0
        explore_tokens = module_skeleton_tokens + MCP_CALL_OVERHEAD

        # 4. auzoom_read(summary) of one target file
        if files_parsed > 0:
            avg_summary = summary_tokens_total // files_parsed
        else:
            avg_summary = 0
        understand_tokens = avg_summary + MCP_CALL_OVERHEAD

        total = schema_tokens + find_tokens + explore_tokens + understand_tokens
        total_with_cli = (total - MCP_SCHEMA_OVERHEAD + MCP_CLI_SCHEMA_OVERHEAD)

        return {
            "approach": "C (AuZoom — progressive disclosure)",
            "files_read": 0,  # No full file reads
            "files_parsed": files_parsed,
            "tokens": total,
            "tokens_with_mcp_cli": total_with_cli,
            "breakdown": {
                "mcp_schema_overhead": schema_tokens,
                "find_call": find_tokens,
                "skeleton_explore_5_files": explore_tokens,
                "summary_understand_1_file": understand_tokens,
            },
            "notes": "Includes 1,050-token MCP schema overhead. MCP CLI mode drops this to ~0.",
        }

    except Exception as e:
        return {
            "approach": "C (AuZoom — progressive disclosure)",
            "files_read": 0,
            "tokens": -1,
            "notes": f"Error: {e}",
        }


def get_repo_stats(repo_path: Path) -> dict:
    """Get basic stats about a repo."""
    files = get_py_files(repo_path)

    total_lines = 0
    file_sizes = []
    violations = []

    for f in files:
        try:
            lines = f.read_text(encoding="utf-8", errors="ignore").count("\n")
            total_lines += lines
            file_sizes.append(lines)
            if lines > 250:
                violations.append((lines, f.name))
        except Exception:
            pass

    violations.sort(reverse=True)

    return {
        "path": str(repo_path),
        "py_files": len(files),
        "total_lines": total_lines,
        "avg_lines": total_lines // max(1, len(files)),
        "max_lines": max(file_sizes) if file_sizes else 0,
        "files_over_250_lines": len(violations),
        "top_violators": violations[:3],
    }


def run_benchmark(repo_path: Path, label: str) -> None:
    """Run all three approaches on a repo and print results."""
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"  Path: {repo_path}")
    print(f"{'='*60}")

    stats = get_repo_stats(repo_path)
    print(f"\n  Repo stats:")
    print(f"    Python files (excl. tests): {stats['py_files']}")
    print(f"    Total lines: {stats['total_lines']:,}")
    print(f"    Avg lines/file: {stats['avg_lines']}")
    print(f"    Files >250 lines: {stats['files_over_250_lines']}")
    if stats['top_violators']:
        print(f"    Top violators: {stats['top_violators']}")

    print(f"\n  Token comparison (scenario: find + understand one function):")
    print(f"  {'Approach':<45} {'Files':<8} {'Tokens':<10} {'vs Naive'}")
    print(f"  {'-'*75}")

    result_a = approach_a_naive(repo_path)
    result_b = approach_b_structured(repo_path)
    result_c = approach_c_auzoom(repo_path)

    naive_tokens = result_a["tokens"]

    for result in [result_a, result_b, result_c]:
        tokens = result["tokens"]
        if tokens > 0 and naive_tokens > 0:
            savings = (1 - tokens / naive_tokens) * 100
            savings_str = f"{savings:.0f}% savings"
        else:
            savings_str = "N/A"

        print(f"  {result['approach']:<45} {result.get('files_read', 0):<8} {tokens:<10,} {savings_str}")

    if result_c.get("tokens_with_mcp_cli", -1) > 0:
        cli_tokens = result_c["tokens_with_mcp_cli"]
        cli_savings = (1 - cli_tokens / naive_tokens) * 100
        print(f"  {'  + with MCP CLI mode enabled':<45} {'0':<8} {cli_tokens:<10,} {cli_savings:.0f}% savings")

    print(f"\n  Verdict:")
    c_tokens = result_c.get("tokens", -1)
    b_tokens = result_b["tokens"]

    if c_tokens <= 0:
        print(f"    AuZoom data unavailable")
    elif c_tokens < b_tokens:
        incremental = (1 - c_tokens / b_tokens) * 100
        print(f"    AuZoom saves {incremental:.0f}% vs structured baseline (net positive)")
    else:
        overhead = ((c_tokens - b_tokens) / b_tokens) * 100
        print(f"    AuZoom costs {overhead:.0f}% MORE than structured baseline (net negative)")
        print(f"    Reason: MCP schema overhead ({MCP_SCHEMA_OVERHEAD} tokens) exceeds progressive savings")
        print(f"    Enable MCP CLI mode to eliminate schema overhead")


def main():
    repos = []

    if len(sys.argv) > 1:
        # User-specified repo
        repos.append((Path(sys.argv[1]), sys.argv[1]))
    else:
        # Default: benchmark all four tiers
        stack_root = Path(__file__).parent.parent
        repos = [
            (stack_root / "auzoom" / "src", "Tiny: AuZoom source (24 files)"),
            (stack_root / "audit", "Small: Audit suite (39 files)"),
        ]

        # External repos (if cloned)
        external = [
            ("/tmp/bench-requests/src", "Small-Medium: requests library (~18 files)"),
            ("/tmp/bench-fastapi/fastapi", "Medium: FastAPI (~48 files)"),
            ("/tmp/bench-django/django", "Large: Django (~889 files)"),
        ]
        for path, label in external:
            if Path(path).exists():
                repos.append((Path(path), label))

    print("Token Benchmark: Naive vs Structured Baseline vs AuZoom")
    print("=========================================================")
    print(f"MCP schema overhead: {MCP_SCHEMA_OVERHEAD} tokens (always in context)")
    print(f"MCP CLI mode overhead: {MCP_CLI_SCHEMA_OVERHEAD} tokens (loads on-demand)")
    print(f"Token estimation: 1 token ≈ {CHARS_PER_TOKEN} characters")

    results = []
    for repo_path, label in repos:
        if not repo_path.exists():
            print(f"\nSkipping {label}: path not found ({repo_path})")
            continue

        run_benchmark(repo_path, label)

        # Collect for summary table
        stats = get_repo_stats(repo_path)
        result_b = approach_b_structured(repo_path)
        result_c = approach_c_auzoom(repo_path)

        results.append({
            "label": label,
            "files": stats["py_files"],
            "lines": stats["total_lines"],
            "baseline": result_b["tokens"],
            "auzoom": result_c.get("tokens", -1),
            "auzoom_cli": result_c.get("tokens_with_mcp_cli", -1),
        })

    # Summary breakeven analysis
    print(f"\n{'='*60}")
    print("SUMMARY: Breakeven Analysis")
    print(f"{'='*60}")
    print(f"\n{'Repo':<35} {'Files':<8} {'Baseline':<12} {'AuZoom':<12} {'Delta'}")
    print(f"{'-'*75}")

    for r in results:
        if r["auzoom"] > 0:
            delta = r["auzoom"] - r["baseline"]
            delta_str = f"+{delta:,} (worse)" if delta > 0 else f"{delta:,} (better)"
        else:
            delta_str = "N/A"
        print(f"{r['label']:<35} {r['files']:<8} {r['baseline']:<12,} {r['auzoom']:<12,} {delta_str}")

    print(f"\nBreakeven point:")
    for r in results:
        if r["auzoom"] > 0:
            if r["auzoom"] < r["baseline"]:
                print(f"  ✓ {r['label']}: AuZoom wins (positive ROI)")
            else:
                if r["auzoom_cli"] > 0 and r["auzoom_cli"] < r["baseline"]:
                    print(f"  ~ {r['label']}: AuZoom loses with schemas, WINS with MCP CLI mode")
                else:
                    print(f"  ✗ {r['label']}: AuZoom loses (overhead exceeds savings)")

    print(f"\nNote: This models a single 'find + understand one function' session.")
    print(f"For exploration-heavy sessions (reading many files), AuZoom scales better.")
    print(f"For edit-heavy sessions (few full reads), the baseline may be sufficient.")


if __name__ == "__main__":
    main()
