"""Integration tests for the Python parser."""

import pytest
from auzoom import PythonParser
from auzoom.models import FetchLevel, NodeType


def test_parse_real_file():
    """Test parsing a file with mixed functions and classes."""
    # Create a test file with functions, class with methods, imports
    test_code = '''
import os
from typing import Optional

def helper(x: int) -> int:
    """Helper function."""
    return x * 2

class Calculator:
    """A calculator class."""

    def add(self, a: int, b: int) -> int:
        """Add two numbers."""
        return helper(a) + helper(b)

    def subtract(self, a: int, b: int) -> int:
        return a - b
'''

    with open('/tmp/test_calc.py', 'w') as f:
        f.write(test_code)

    parser = PythonParser()
    nodes = parser.parse_file('/tmp/test_calc.py')

    # Should find: 2 imports, 1 function, 1 class, 2 methods
    assert len(nodes) >= 5

    # Verify node types
    types = [n.node_type for n in nodes]
    assert NodeType.IMPORT in types
    assert NodeType.FUNCTION in types
    assert NodeType.CLASS in types
    assert NodeType.METHOD in types

    # Verify serialization
    for node in nodes:
        skeleton = node.to_skeleton()
        assert 'id' in skeleton
        assert 'name' in skeleton

        summary = node.to_summary()
        assert len(str(summary)) > len(str(skeleton))

        full = node.to_full()
        assert 'source' in full


def test_dependency_resolution():
    """Test that function calls are detected as dependencies."""
    test_code = '''
def caller():
    return callee()

def callee():
    return 42
'''
    with open('/tmp/test_deps.py', 'w') as f:
        f.write(test_code)

    parser = PythonParser()
    nodes = parser.parse_file('/tmp/test_deps.py')

    caller_node = [n for n in nodes if n.name == 'caller'][0]
    # Should have dependency on callee
    assert len(caller_node.dependencies) > 0
