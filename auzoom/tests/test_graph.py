import pytest
from auzoom import PythonParser
from auzoom.graph import CodeGraph
from auzoom.models import FetchLevel

def test_graph_navigation():
    """Test building and navigating a code graph."""
    test_code = '''
def helper():
    """A helper function."""
    return 42

class Calculator:
    def add(self, a, b):
        """Add two numbers using helper."""
        return helper() + a + b

    def multiply(self, a, b):
        return a * b
'''
    with open('/tmp/test_nav.py', 'w') as f:
        f.write(test_code)

    parser = PythonParser()
    graph = CodeGraph()

    nodes = parser.parse_file('/tmp/test_nav.py')
    for node in nodes:
        graph.add_node(node)

    # Test file-level fetch
    skeleton_view = graph.get_file('/tmp/test_nav.py', FetchLevel.SKELETON)
    assert len(skeleton_view) >= 3  # helper, Calculator, methods

    # Test individual node fetch at different levels
    calc_id = [n.id for n in nodes if n.name == 'Calculator'][0]
    skeleton = graph.get_node(calc_id, FetchLevel.SKELETON)
    summary = graph.get_node(calc_id, FetchLevel.SUMMARY)
    full = graph.get_node(calc_id, FetchLevel.FULL)

    assert 'id' in skeleton
    assert 'name' in skeleton
    assert len(str(summary)) > len(str(skeleton))
    assert len(str(full)) > len(str(summary))

def test_dependency_traversal():
    """Test traversing dependencies."""
    test_code = '''
def leaf():
    return 1

def middle():
    return leaf()

def top():
    return middle()
'''
    with open('/tmp/test_deps.py', 'w') as f:
        f.write(test_code)

    parser = PythonParser()
    graph = CodeGraph()

    nodes = parser.parse_file('/tmp/test_deps.py')
    for node in nodes:
        graph.add_node(node)

    top_id = [n.id for n in nodes if n.name == 'top'][0]
    deps = graph.get_dependencies(top_id, depth=2)

    # Should find middle (depth 1) and leaf (depth 2)
    dep_names = [d['name'] for d in deps]
    assert 'middle' in dep_names
    assert 'leaf' in dep_names

def test_token_reduction():
    """Verify skeleton provides significant token reduction."""
    import os
    parser = PythonParser()
    graph = CodeGraph()

    # Parse a real file from the codebase
    test_dir = os.path.dirname(os.path.abspath(__file__))
    models_path = os.path.join(test_dir, '..', 'src', 'auzoom', 'models.py')
    nodes = parser.parse_file(models_path)
    for node in nodes:
        graph.add_node(node)

    stats = graph.get_token_stats(models_path)

    print(f"Token stats: {stats}")

    # Verify reduction
    assert stats['reduction_ratio'] >= 4.0  # At least 4x reduction
    assert stats['tokens_skeleton'] < stats['tokens_summary'] < stats['tokens_full']
