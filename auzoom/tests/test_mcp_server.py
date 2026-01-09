import pytest
import json
import time
import shutil
from pathlib import Path
from auzoom import AuZoomMCPServer


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear .auzoom cache before each test."""
    cache_dir = Path('.auzoom')
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
    yield
    # Cleanup after test
    if cache_dir.exists():
        shutil.rmtree(cache_dir)


@pytest.fixture
def server():
    """Create server instance for testing."""
    return AuZoomMCPServer('.', auto_warm=False)


def test_server_initialization():
    """Test server initializes correctly."""
    server = AuZoomMCPServer('.', auto_warm=False)
    assert server.project_root is not None
    assert server.graph is not None
    assert server.summarizer is not None


def test_tools_manifest(server):
    """Test tools manifest structure."""
    from auzoom.mcp.tools_schema import get_tools_manifest
    manifest = get_tools_manifest()

    assert "tools" in manifest
    assert len(manifest["tools"]) == 5  # read, find, dependencies, stats, validate

    # Check auzoom_read tool
    read_tool = next(t for t in manifest["tools"] if t["name"] == "auzoom_read")
    assert "inputSchema" in read_tool
    assert "path" in read_tool["inputSchema"]["properties"]
    assert "level" in read_tool["inputSchema"]["properties"]


def test_read_python_file_skeleton(server):
    """Test reading Python file at skeleton level."""
    result = server.handle_tool_call("auzoom_read", {
        "path": "src/auzoom/models.py",
        "level": "skeleton"
    })

    assert result["type"] == "python"
    assert result["level"] == "skeleton"
    assert "nodes" in result
    assert len(result["nodes"]) > 0

    # Skeleton should be compact
    node = result["nodes"][0]
    assert "id" in node
    assert "name" in node
    assert "type" in node


def test_read_python_file_summary(server):
    """Test reading Python file at summary level."""
    result = server.handle_tool_call("auzoom_read", {
        "path": "src/auzoom/models.py",
        "level": "summary"
    })

    assert result["type"] == "python"
    assert result["level"] == "summary"
    assert "nodes" in result

    # Summary should include more detail than skeleton
    node = result["nodes"][0]
    assert "id" in node
    assert "line_start" in node or node.get("type") == "import"


def test_read_python_file_full(server):
    """Test reading Python file at full level."""
    result = server.handle_tool_call("auzoom_read", {
        "path": "src/auzoom/models.py",
        "level": "full"
    })

    assert result["type"] == "python"
    assert result["level"] == "full"
    assert "nodes" in result

    # Full should include source
    node = result["nodes"][0]
    if node.get("type") != "import":
        assert "source" in node or "children" in node


def test_read_non_python_file_first_access(server):
    """Test reading non-Python file for first time."""
    # Create a test file
    test_file = Path("test_readme.md")
    test_file.write_text("# Test\n\nThis is a test file.\nWith multiple lines.\n")

    try:
        result = server.handle_tool_call("auzoom_read", {
            "path": str(test_file),
            "level": "skeleton"
        })

        # First read at skeleton level: should return full (not cached yet)
        assert result["type"] == "full_content_first_access"
        assert "content" in result
        assert "# Test" in result["content"]
        assert result["cached"] == False

        # Wait for background summarization
        time.sleep(0.5)

    finally:
        test_file.unlink()


def test_read_non_python_file_cached_summary(server):
    """Test reading non-Python file with cached summary."""
    # Create a test file
    test_file = Path("test_doc.txt")
    test_content = "Line 1\nLine 2\nLine 3\n"
    test_file.write_text(test_content)

    try:
        # First access at full level - triggers summarization
        result1 = server.handle_tool_call("auzoom_read", {
            "path": str(test_file),
            "level": "full"
        })

        assert result1["type"] == "full_content"
        assert result1["level"] == "full"

        # Wait for background summarization
        time.sleep(0.5)

        # Second access at skeleton level - should return cached summary
        result2 = server.handle_tool_call("auzoom_read", {
            "path": str(test_file),
            "level": "skeleton"
        })

        assert result2["type"] == "cached_summary"
        assert result2["cached"] == True
        assert "summary" in result2
        assert result2["level"] == "skeleton"

    finally:
        test_file.unlink()


def test_find_tool(server):
    """Test auzoom_find tool."""
    result = server.handle_tool_call("auzoom_find", {
        "pattern": "CodeNode"
    })

    assert "matches" in result
    assert "count" in result
    # May or may not find matches depending on what's indexed


def test_get_dependencies_tool(server):
    """Test auzoom_get_dependencies tool."""
    # First load a file to index it
    server.handle_tool_call("auzoom_read", {
        "path": "src/auzoom/models.py"
    })

    # Find a node
    find_result = server.handle_tool_call("auzoom_find", {
        "pattern": "CodeNode"
    })

    if find_result["matches"]:
        node_id = find_result["matches"][0]["id"]

        result = server.handle_tool_call("auzoom_get_dependencies", {
            "node_id": node_id,
            "depth": 1
        })

        assert "node_id" in result
        assert "dependencies" in result
        assert "count" in result


def test_stats_tool(server):
    """Test auzoom_stats tool."""
    # Do some reads first
    server.handle_tool_call("auzoom_read", {
        "path": "src/auzoom/models.py"
    })

    result = server.handle_tool_call("auzoom_stats", {})

    assert "cache_hits" in result
    assert "cache_misses" in result
    assert "hit_rate" in result
    assert "files_parsed" in result
    assert "non_python_summaries_cached" in result


def test_error_handling(server):
    """Test error handling for invalid requests."""
    # Missing path
    result = server.handle_tool_call("auzoom_read", {})
    assert "error" in result

    # Non-existent file
    result = server.handle_tool_call("auzoom_read", {
        "path": "nonexistent.py"
    })
    assert "error" in result

    # Unknown tool
    result = server.handle_tool_call("unknown_tool", {})
    assert "error" in result


def test_progressive_disclosure_python(server):
    """Test that levels provide progressive detail for Python files."""
    skeleton = server.handle_tool_call("auzoom_read", {
        "path": "src/auzoom/models.py",
        "level": "skeleton"
    })

    summary = server.handle_tool_call("auzoom_read", {
        "path": "src/auzoom/models.py",
        "level": "summary"
    })

    full = server.handle_tool_call("auzoom_read", {
        "path": "src/auzoom/models.py",
        "level": "full"
    })

    # Should have increasing detail
    skeleton_size = len(json.dumps(skeleton))
    summary_size = len(json.dumps(summary))
    full_size = len(json.dumps(full))

    assert skeleton_size < summary_size < full_size
    print(f"Sizes - Skeleton: {skeleton_size}, Summary: {summary_size}, Full: {full_size}")


def test_lazy_indexing_all_files(server):
    """Test that all files are indexed lazily."""
    # Python file
    py_result = server.handle_tool_call("auzoom_read", {
        "path": "src/auzoom/models.py",
        "level": "skeleton"
    })
    assert py_result["type"] == "python"

    # Non-Python file (first access)
    test_file = Path("test_config.json")
    test_file.write_text('{"key": "value"}')

    try:
        json_result = server.handle_tool_call("auzoom_read", {
            "path": str(test_file),
            "level": "skeleton"
        })

        # First access should return full (not yet cached)
        assert json_result["type"] == "full_content_first_access"
        assert json_result["cached"] == False

        # Wait for summarization
        time.sleep(0.5)

        # Check stats - summary should be cached
        stats = server.handle_tool_call("auzoom_stats", {})
        assert stats["non_python_summaries_cached"] >= 1

    finally:
        test_file.unlink()


def test_cache_invalidation_non_python(server):
    """Test that modified non-Python files are re-indexed."""
    test_file = Path("test_modified.txt")
    test_file.write_text("Original content")

    try:
        # First read
        result1 = server.handle_tool_call("auzoom_read", {
            "path": str(test_file),
            "level": "full"
        })
        assert "Original content" in result1["content"]

        # Wait for summarization
        time.sleep(0.5)

        # Modify file
        test_file.write_text("Modified content")

        # Second read - should detect change (new hash)
        result2 = server.handle_tool_call("auzoom_read", {
            "path": str(test_file),
            "level": "skeleton"
        })

        # Should return full because cache hash doesn't match
        assert result2["type"] == "full_content_first_access"

    finally:
        test_file.unlink()
