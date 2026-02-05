#!/usr/bin/env python3
"""Test FileSummarizer metadata generation on real files."""

import sys
from pathlib import Path

# Add auzoom to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "auzoom" / "src"))

from auzoom.mcp.file_summarizer import FileSummarizer


# Test cases - real files from this repository
TEST_FILES = [
    ("README.md", "markdown"),
    ("VALIDATION-SUMMARY.md", "markdown"),
    (".planning/config.json", "json"),
    ("orchestrator/pyproject.toml", "toml"),
    (".planning/ROADMAP.md", "markdown"),
    (".planning/PROJECT.md", "markdown"),
]


def test_file_summarizer():
    """Test metadata generation on real files."""
    summarizer = FileSummarizer(cache_dir=Path("/tmp/auzoom-test-cache"))

    results = []
    repo_root = Path(__file__).parent.parent.parent

    for file_path, file_type in TEST_FILES:
        path = repo_root / file_path
        if not path.exists():
            print(f"Warning: {file_path} not found, skipping")
            continue

        try:
            content = path.read_text()
            lines = content.splitlines()

            # Generate metadata
            metadata = summarizer._generate_summary_text(path, lines, content)

            # Calculate metrics
            full_size = len(content)
            metadata_size = len(metadata)
            reduction_pct = (1 - metadata_size / full_size) * 100

            # Estimate tokens (4 char per token)
            full_tokens = max(1, full_size // 4)
            metadata_tokens = max(1, metadata_size // 4)
            token_reduction = (1 - metadata_tokens / full_tokens) * 100

            # Calculate cost savings (Sonnet pricing: $3 input, $15 output per 1M)
            # Assume reading is input cost
            full_cost = (full_tokens / 1_000_000) * 3.0
            metadata_cost = (metadata_tokens / 1_000_000) * 3.0
            cost_savings = full_cost - metadata_cost

            results.append({
                "file": file_path,
                "type": file_type,
                "full_size": full_size,
                "full_tokens": full_tokens,
                "metadata_size": metadata_size,
                "metadata_tokens": metadata_tokens,
                "byte_reduction": f"{reduction_pct:.1f}%",
                "token_reduction": f"{token_reduction:.1f}%",
                "cost_savings": f"${cost_savings:.6f}",
                "metadata": metadata,
                "lines": len(lines)
            })

        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue

    return results


def print_results(results):
    """Print results in human-readable format."""
    print(f"\n{'='*80}")
    print(f"FileSummarizer Test Results")
    print(f"{'='*80}\n")
    print(f"Files tested: {len(results)}\n")

    for r in results:
        print(f"\n{'='*80}")
        print(f"File: {r['file']}")
        print(f"Type: {r['type']}")
        print(f"{'='*80}")
        print(f"Full size: {r['full_size']:,} bytes ({r['full_tokens']:,} tokens)")
        print(f"Metadata size: {r['metadata_size']:,} bytes ({r['metadata_tokens']:,} tokens)")
        print(f"Byte reduction: {r['byte_reduction']}")
        print(f"Token reduction: {r['token_reduction']}")
        print(f"Cost savings: {r['cost_savings']}")
        print(f"\nMetadata content:")
        print("-" * 80)
        print(r['metadata'])
        print("-" * 80)

    # Summary statistics
    print(f"\n{'='*80}")
    print("SUMMARY STATISTICS")
    print(f"{'='*80}")

    total_full_tokens = sum(r['full_tokens'] for r in results)
    total_metadata_tokens = sum(r['metadata_tokens'] for r in results)
    avg_token_reduction = (1 - total_metadata_tokens / total_full_tokens) * 100

    total_full_cost = sum(r['full_tokens'] for r in results) / 1_000_000 * 3.0
    total_metadata_cost = sum(r['metadata_tokens'] for r in results) / 1_000_000 * 3.0
    total_cost_savings = total_full_cost - total_metadata_cost

    print(f"Total files: {len(results)}")
    print(f"Total full tokens: {total_full_tokens:,}")
    print(f"Total metadata tokens: {total_metadata_tokens:,}")
    print(f"Average token reduction: {avg_token_reduction:.1f}%")
    print(f"Total cost savings: ${total_cost_savings:.6f}")
    print(f"Average cost savings per file: ${total_cost_savings / len(results):.6f}")


def write_evidence_file(results):
    """Write evidence file in markdown format."""
    repo_root = Path(__file__).parent.parent.parent
    evidence_file = repo_root / "audit" / "evidence" / "09-01-metadata-tests.md"

    with open(evidence_file, "w") as f:
        f.write("# Non-Python File Metadata Tests\n\n")
        f.write(f"**Test Execution Date**: {Path(__file__).stat().st_mtime}\n")
        f.write(f"**Files Tested**: {len(results)}\n\n")

        # Summary statistics
        total_full_tokens = sum(r['full_tokens'] for r in results)
        total_metadata_tokens = sum(r['metadata_tokens'] for r in results)
        avg_token_reduction = (1 - total_metadata_tokens / total_full_tokens) * 100

        f.write("## Summary Statistics\n\n")
        f.write(f"- **Total files**: {len(results)}\n")
        f.write(f"- **Total full tokens**: {total_full_tokens:,}\n")
        f.write(f"- **Total metadata tokens**: {total_metadata_tokens:,}\n")
        f.write(f"- **Average token reduction**: {avg_token_reduction:.1f}%\n")
        f.write(f"- **File types tested**: {', '.join(set(r['type'] for r in results))}\n\n")

        f.write("---\n\n")

        # Results by file type
        f.write("## Results by File Type\n\n")

        for file_type in sorted(set(r['type'] for r in results)):
            f.write(f"### {file_type.capitalize()} Files\n\n")

            type_results = [r for r in results if r['type'] == file_type]
            for r in type_results:
                f.write(f"#### {r['file']}\n\n")
                f.write(f"- **Full size**: {r['full_size']:,} bytes ({r['full_tokens']:,} tokens)\n")
                f.write(f"- **Metadata size**: {r['metadata_size']:,} bytes ({r['metadata_tokens']:,} tokens)\n")
                f.write(f"- **Token reduction**: {r['token_reduction']}\n")
                f.write(f"- **Cost savings**: {r['cost_savings']}\n")
                f.write(f"- **Lines**: {r['lines']}\n\n")

                f.write("**Metadata content:**\n```\n")
                f.write(r['metadata'])
                f.write("\n```\n\n")

                # Assessment
                f.write("**Assessment:**\n")
                token_pct = float(r['token_reduction'].rstrip('%'))
                if token_pct >= 95:
                    f.write("- ✅ Excellent reduction (≥95%)\n")
                    usefulness = "4/5"
                elif token_pct >= 90:
                    f.write("- ✅ Good reduction (90-95%)\n")
                    usefulness = "3/5"
                elif token_pct >= 80:
                    f.write("- ⚠️ Moderate reduction (80-90%)\n")
                    usefulness = "3/5"
                else:
                    f.write("- ❌ Poor reduction (<80%)\n")
                    usefulness = "2/5"

                # Assess metadata usefulness
                metadata_lines = r['metadata'].split('\n')
                if len(metadata_lines) <= 4:
                    f.write("- Information density: MINIMAL (basic stats only)\n")
                elif "Headers:" in r['metadata'] and "No headers" not in r['metadata']:
                    f.write("- Information density: MEDIUM (includes structural info)\n")
                    usefulness = "3/5"
                else:
                    f.write("- Information density: LOW (name, size, type only)\n")

                f.write(f"- **Usefulness score**: {usefulness}\n\n")
                f.write("---\n\n")

    print(f"\nEvidence file written to: {evidence_file}")


if __name__ == "__main__":
    print("Testing FileSummarizer metadata generation...")
    results = test_file_summarizer()

    if not results:
        print("No files could be tested!")
        sys.exit(1)

    print_results(results)
    write_evidence_file(results)

    print(f"\n{'='*80}")
    print("Test complete!")
    print(f"{'='*80}\n")
