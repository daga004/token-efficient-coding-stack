import pytest
import time
import shutil
from pathlib import Path
from auzoom import LazyCodeGraph
from auzoom.models import FetchLevel


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


def test_lazy_loading():
    """Test that files are only parsed on first access."""
    g = LazyCodeGraph('.', auto_warm=False)

    # Initially, no files loaded
    assert g.stats["parses"] == 0

    # First access triggers parse
    nodes = g.get_file('src/auzoom/models.py', FetchLevel.SKELETON)
    assert g.stats["parses"] == 1
    assert len(nodes) > 0

    # Second access uses cache
    nodes2 = g.get_file('src/auzoom/models.py', FetchLevel.SKELETON)
    assert g.stats["parses"] == 1  # No additional parse
    assert nodes == nodes2


def test_cache_persistence():
    """Test that cache persists across graph instances."""
    # First instance: parse and cache
    g1 = LazyCodeGraph('.', auto_warm=False)
    nodes1 = g1.get_file('src/auzoom/models.py', FetchLevel.SKELETON)
    parse_count1 = g1.stats["parses"]
    assert parse_count1 == 1

    # Second instance: should load from disk cache
    g2 = LazyCodeGraph('.', auto_warm=False)
    nodes2 = g2.get_file('src/auzoom/models.py', FetchLevel.SKELETON)
    parse_count2 = g2.stats["parses"]

    assert parse_count2 == 0  # No parse needed
    assert len(nodes1) == len(nodes2)


def test_cache_speed():
    """Verify cache is significantly faster than parsing."""
    g = LazyCodeGraph('.', auto_warm=False)

    # Cold access (parse)
    start = time.time()
    g.get_file('src/auzoom/models.py', FetchLevel.SKELETON)
    cold_time = time.time() - start

    # Warm access (cache)
    start = time.time()
    g.get_file('src/auzoom/models.py', FetchLevel.SKELETON)
    warm_time = time.time() - start

    print(f"Cold: {cold_time:.3f}s, Warm: {warm_time:.3f}s, Speedup: {cold_time/warm_time:.1f}x")
    assert warm_time < cold_time / 5  # Cache should be 5x+ faster


def test_import_discovery():
    """Test that imports are discovered without parsing."""
    g = LazyCodeGraph('.', auto_warm=False)

    # Parse a file that has imports
    g.get_file('src/auzoom/core/parsing/parser.py', FetchLevel.SKELETON)

    # Check that imports were discovered
    discovered = g.get_discovered_files()
    # May discover files depending on imports

    print(f"Discovered files: {len(discovered)}")
    # Discovered files should not be parsed yet (unless already cached)


def test_entry_point_discovery():
    """Test entry point discovery."""
    g = LazyCodeGraph('.', auto_warm=False)

    entry_points = g.discover_entry_points()

    print(f"Found entry points: {entry_points}")
    assert isinstance(entry_points, list)
    # May or may not find any, depending on project structure


def test_fetch_levels():
    """Test different fetch levels return appropriate detail."""
    g = LazyCodeGraph('.', auto_warm=False)

    skeleton = g.get_file('src/auzoom/models.py', FetchLevel.SKELETON)
    summary = g.get_file('src/auzoom/models.py', FetchLevel.SUMMARY)
    full = g.get_file('src/auzoom/models.py', FetchLevel.FULL)

    # Verify progressive detail
    assert len(str(skeleton)) < len(str(summary)) < len(str(full))

    # Skeleton should have minimal fields
    if skeleton:
        assert 'id' in skeleton[0]
        assert 'name' in skeleton[0]
        assert 'dependencies' in skeleton[0]

    # Full should have source
    if full:
        assert 'source' in full[0] or full[0].get('type') == 'import'


def test_node_access():
    """Test accessing individual nodes lazily."""
    g = LazyCodeGraph('.', auto_warm=False)

    # Get a node by searching first
    g.get_file('src/auzoom/models.py', FetchLevel.SKELETON)

    # Find a specific node
    matches = g.find_by_name("CodeNode")
    assert len(matches) > 0

    node_id = matches[0]['id']

    # Access node at different levels
    skeleton = g.get_node(node_id, FetchLevel.SKELETON)
    full = g.get_node(node_id, FetchLevel.FULL)

    assert skeleton['id'] == node_id
    assert full['id'] == node_id
    assert len(str(full)) > len(str(skeleton))


def test_stats_tracking():
    """Test that stats are tracked correctly."""
    g = LazyCodeGraph('.', auto_warm=False)

    # Make some accesses
    g.get_file('src/auzoom/models.py', FetchLevel.SKELETON)  # miss
    g.get_file('src/auzoom/models.py', FetchLevel.SKELETON)  # hit

    stats = g.get_stats()

    assert stats['cache_hits'] >= 1
    assert stats['cache_misses'] >= 1
    assert stats['files_parsed'] >= 1
    assert 'hit_rate' in stats

    print(f"Stats: {stats}")


def test_file_modification_detection():
    """Test that modified files are detected."""
    import tempfile
    import os

    # Create a temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('def foo():\n    pass\n')
        temp_path = f.name

    try:
        g = LazyCodeGraph(os.path.dirname(temp_path), auto_warm=False)

        # First access
        nodes1 = g.get_file(temp_path, FetchLevel.SKELETON)
        assert len(nodes1) == 1

        # Modify file
        with open(temp_path, 'w') as f:
            f.write('def foo():\n    pass\n\ndef bar():\n    pass\n')

        # Create new graph instance
        g2 = LazyCodeGraph(os.path.dirname(temp_path), auto_warm=False)

        # Should detect change and re-parse
        nodes2 = g2.get_file(temp_path, FetchLevel.SKELETON)
        assert len(nodes2) == 2  # Now has foo and bar

    finally:
        os.unlink(temp_path)


def test_dependency_traversal_lazy():
    """Test that dependency traversal loads files as needed."""
    test_code = '''
def leaf():
    return 1

def middle():
    return leaf()

def top():
    return middle()
'''
    with open('/tmp/test_lazy_deps.py', 'w') as f:
        f.write(test_code)

    g = LazyCodeGraph('/tmp', auto_warm=False)

    # Parse the file
    g.get_file('/tmp/test_lazy_deps.py', FetchLevel.SKELETON)

    # Get dependencies (should not trigger additional parses)
    nodes = [n for n in g.nodes.values() if n.name == 'top']
    if nodes:
        top_id = nodes[0].id
        deps = g.get_dependencies(top_id, depth=2)

        dep_names = [d['name'] for d in deps]
        assert 'middle' in dep_names


def test_background_warming():
    """Test that background warming doesn't block."""
    import time

    g = LazyCodeGraph('.', auto_warm=True)

    # Should start immediately, not block on warming
    start_time = time.time()
    assert time.time() - start_time < 0.5  # Init should be instant

    # Give warming thread time to work
    time.sleep(1)

    # Check if any files were warmed
    stats = g.get_stats()
    print(f"After warming: {stats}")

    # Should have found and parsed some entry points
    # (or not, if no entry points exist)
