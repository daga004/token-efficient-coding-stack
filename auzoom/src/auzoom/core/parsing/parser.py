"""Python parser using Tree-sitter for extracting code elements."""

from pathlib import Path
from typing import Optional
from tree_sitter import Language, Parser, Node as TSNode, Tree
import tree_sitter_python as tspython

from ...models import CodeNode, NodeType
from .node_factory import NodeFactory


class PythonParser:
    """Parser for extracting Python code elements using Tree-sitter."""

    def __init__(self):
        """Initialize tree-sitter with Python grammar."""
        PY_LANGUAGE = Language(tspython.language())
        self.parser = Parser(PY_LANGUAGE)
        self.factory = NodeFactory(self._get_node_text)

    def parse_file(self, file_path: str) -> list[CodeNode]:
        """Parse a Python file and extract all code nodes.

        Args:
            file_path: Path to the Python file to parse

        Returns:
            List of CodeNode objects representing functions, classes, methods, and imports
        """
        with open(file_path, 'rb') as f:
            source_code = f.read()

        tree = self.parser.parse(source_code)
        self.source_code = source_code
        self.source_lines = source_code.decode('utf-8').split('\n')

        nodes = []
        nodes.extend(self._extract_imports(tree, file_path))
        nodes.extend(self._extract_functions(tree, file_path))
        nodes.extend(self._extract_classes(tree, file_path))

        self._resolve_dependencies(nodes)
        return nodes

    def _extract_functions(self, tree: Tree, file_path: str) -> list[CodeNode]:
        """Extract function definitions from the parse tree.

        Args:
            tree: Tree-sitter parse tree
            file_path: Path to the source file

        Returns:
            List of CodeNode objects for functions with TSNode attached
        """
        functions = []
        root = tree.root_node

        # Find all function definitions at module level (not inside classes)
        for node in self._walk_tree(root):
            if node.type == 'function_definition':
                # Check if it's a top-level function (not a method)
                if not self._is_inside_class(node):
                    func_node = self.factory.create_function_node(node, file_path, NodeType.FUNCTION)
                    if func_node:
                        # Attach the TSNode for later dependency extraction
                        func_node.ts_node = node
                        functions.append(func_node)

        return functions

    def _extract_classes(self, tree: Tree, file_path: str) -> list[CodeNode]:
        """Extract class definitions and their methods from the parse tree.

        Args:
            tree: Tree-sitter parse tree
            file_path: Path to the source file

        Returns:
            List of CodeNode objects for classes and methods
        """
        classes = []
        root = tree.root_node

        for node in self._walk_tree(root):
            if node.type == 'class_definition':
                class_node = self.factory.create_class_node(node, file_path)
                if class_node:
                    classes.append(class_node)

                    # Extract methods
                    methods = self._extract_methods(node, file_path, class_node.name)
                    classes.extend(methods)

        return classes

    def _extract_methods(self, class_node: TSNode, file_path: str, class_name: str) -> list[CodeNode]:
        """Extract method definitions from a class node.

        Args:
            class_node: Tree-sitter class node
            file_path: Path to the source file
            class_name: Name of the containing class

        Returns:
            List of CodeNode objects for methods with TSNode attached
        """
        methods = []

        # Find the class body
        body = None
        for child in class_node.children:
            if child.type == 'block':
                body = child
                break

        if not body:
            return methods

        # Look for function definitions in the class body
        for node in body.children:
            if node.type == 'function_definition':
                method_node = self.factory.create_function_node(
                    node, file_path, NodeType.METHOD, class_name
                )
                if method_node:
                    # Attach the TSNode for later dependency extraction
                    method_node.ts_node = node
                    methods.append(method_node)

        return methods

    def _extract_imports(self, tree: Tree, file_path: str) -> list[CodeNode]:
        """Extract import statements from the parse tree.

        Args:
            tree: Tree-sitter parse tree
            file_path: Path to the source file

        Returns:
            List of CodeNode objects for imports
        """
        imports = []
        root = tree.root_node

        for node in self._walk_tree(root):
            if node.type in ('import_statement', 'import_from_statement'):
                import_node = self.factory.create_import_node(node, file_path)
                if import_node:
                    imports.append(import_node)

        return imports

    def _extract_docstring(self, body: Optional[TSNode]) -> Optional[str]:
        """Extract docstring from a function or class body.

        Args:
            body: Tree-sitter body node

        Returns:
            Docstring text or None
        """
        if not body:
            return None

        # Look for the first expression statement that contains a string
        for child in body.children:
            if child.type == 'expression_statement':
                for subchild in child.children:
                    if subchild.type == 'string':
                        docstring = self._get_node_text(subchild)
                        # Remove quotes
                        if docstring.startswith('"""') or docstring.startswith("'''"):
                            docstring = docstring[3:-3]
                        elif docstring.startswith('"') or docstring.startswith("'"):
                            docstring = docstring[1:-1]
                        return docstring.strip()

        return None

    def _resolve_dependencies(self, nodes: list[CodeNode]):
        """Analyze function/method bodies for function calls and populate dependencies.

        Uses tree-sitter AST nodes (attached during parsing) to accurately extract
        function calls.

        Args:
            nodes: List of CodeNode objects with ts_node attributes
        """
        # Create a mapping of function/method names to node IDs
        name_to_id = {}
        for node in nodes:
            if node.node_type in (NodeType.FUNCTION, NodeType.METHOD):
                name_to_id[node.name] = node.id

        # Analyze each function/method for calls using their TSNode
        for node in nodes:
            if node.node_type in (NodeType.FUNCTION, NodeType.METHOD):
                # Extract function calls from the TSNode
                if hasattr(node, 'ts_node') and node.ts_node:
                    calls = self._extract_function_calls_from_node(node.ts_node)

                    # Map calls to node IDs
                    for call_name in calls:
                        if call_name in name_to_id and name_to_id[call_name] != node.id:
                            node_id = name_to_id[call_name]
                            if node_id not in node.dependencies:
                                node.dependencies.append(node_id)

                # Clean up: remove ts_node to avoid serialization issues
                if hasattr(node, 'ts_node'):
                    delattr(node, 'ts_node')

    def _extract_function_calls_from_node(self, ts_node: TSNode) -> set[str]:
        """Extract function calls from a tree-sitter node.

        Args:
            ts_node: Tree-sitter node (function/method definition)

        Returns:
            Set of function names called within this node
        """
        calls = set()
        self._extract_calls_recursive(ts_node, calls)
        return calls

    def _extract_calls_recursive(self, node: TSNode, calls: set[str]) -> None:
        """Recursively extract function call names from an AST node.

        Args:
            node: Tree-sitter node to analyze
            calls: Set to populate with function names
        """
        if node.type == 'call':
            # Get the function being called
            function_node = node.child_by_field_name('function')
            if function_node:
                # Handle simple function calls: func()
                if function_node.type == 'identifier':
                    calls.add(self._get_node_text(function_node))
                # Handle method calls: self.method() or obj.method()
                elif function_node.type == 'attribute':
                    attr_node = function_node.child_by_field_name('attribute')
                    if attr_node:
                        calls.add(self._get_node_text(attr_node))

        # Recurse into children
        for child in node.children:
            self._extract_calls_recursive(child, calls)

    def _is_inside_class(self, node: TSNode) -> bool:
        """Check if a node is inside a class definition.

        Args:
            node: Tree-sitter node to check

        Returns:
            True if the node is inside a class
        """
        current = node.parent
        while current:
            if current.type == 'class_definition':
                return True
            current = current.parent
        return False

    def _walk_tree(self, node: TSNode) -> list[TSNode]:
        """Walk the parse tree and return all nodes in depth-first order.

        Args:
            node: Root node to start walking from

        Returns:
            List of all nodes in the tree
        """
        result = [node]
        for child in node.children:
            result.extend(self._walk_tree(child))
        return result

    def _get_node_text(self, node: TSNode) -> str:
        """Get the text content of a node.

        Args:
            node: Tree-sitter node

        Returns:
            Text content of the node
        """
        return self.source_code[node.start_byte:node.end_byte].decode('utf-8')
