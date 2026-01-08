"""Python parser using Tree-sitter for extracting code elements."""

from pathlib import Path
from typing import Optional
from tree_sitter import Language, Parser, Node as TSNode, Tree
import tree_sitter_python as tspython

from .models import CodeNode, NodeType


class PythonParser:
    """Parser for extracting Python code elements using Tree-sitter."""

    def __init__(self):
        """Initialize tree-sitter with Python grammar."""
        PY_LANGUAGE = Language(tspython.language())
        self.parser = Parser(PY_LANGUAGE)

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
            List of CodeNode objects for functions
        """
        functions = []
        query = """
        (function_definition
            name: (identifier) @name
            parameters: (parameters) @params
            body: (block) @body) @function
        """

        root = tree.root_node

        # Find all function definitions at module level (not inside classes)
        for node in self._walk_tree(root):
            if node.type == 'function_definition':
                # Check if it's a top-level function (not a method)
                if not self._is_inside_class(node):
                    func_node = self._create_function_node(node, file_path, NodeType.FUNCTION)
                    if func_node:
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
                class_node = self._create_class_node(node, file_path)
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
            List of CodeNode objects for methods
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
                method_node = self._create_function_node(
                    node, file_path, NodeType.METHOD, class_name
                )
                if method_node:
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
                import_node = self._create_import_node(node, file_path)
                if import_node:
                    imports.append(import_node)

        return imports

    def _create_function_node(
        self,
        node: TSNode,
        file_path: str,
        node_type: NodeType,
        class_name: Optional[str] = None
    ) -> Optional[CodeNode]:
        """Create a CodeNode from a function definition node.

        Args:
            node: Tree-sitter function node
            file_path: Path to the source file
            node_type: FUNCTION or METHOD
            class_name: Name of containing class if this is a method

        Returns:
            CodeNode object or None if parsing fails
        """
        # Extract function name
        name = None
        params = None
        body = None

        for child in node.children:
            if child.type == 'identifier':
                name = self._get_node_text(child)
            elif child.type == 'parameters':
                params = child
            elif child.type == 'block':
                body = child

        if not name:
            return None

        # Build qualified name
        if class_name:
            qualified_name = f"{class_name}.{name}"
        else:
            qualified_name = name

        # Create node ID
        node_id = f"{file_path}::{qualified_name}"

        # Extract signature
        signature = None
        if params:
            signature = f"{name}{self._get_node_text(params)}"

        # Extract docstring
        docstring = self._extract_docstring(body)

        # Get line range
        line_start = node.start_point[0] + 1  # Convert to 1-indexed
        line_end = node.end_point[0] + 1

        # Get source code
        source = self._get_node_text(node)

        return CodeNode(
            id=node_id,
            name=name,
            node_type=node_type,
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            dependencies=[],
            children=[],
            docstring=docstring,
            signature=signature,
            source=source
        )

    def _create_class_node(self, node: TSNode, file_path: str) -> Optional[CodeNode]:
        """Create a CodeNode from a class definition node.

        Args:
            node: Tree-sitter class node
            file_path: Path to the source file

        Returns:
            CodeNode object or None if parsing fails
        """
        # Extract class name
        name = None
        body = None

        for child in node.children:
            if child.type == 'identifier':
                name = self._get_node_text(child)
            elif child.type == 'block':
                body = child

        if not name:
            return None

        # Create node ID
        node_id = f"{file_path}::{name}"

        # Extract docstring
        docstring = self._extract_docstring(body)

        # Get line range
        line_start = node.start_point[0] + 1
        line_end = node.end_point[0] + 1

        # Get source code
        source = self._get_node_text(node)

        # Collect method names as children
        children = []
        if body:
            for child in body.children:
                if child.type == 'function_definition':
                    for subchild in child.children:
                        if subchild.type == 'identifier':
                            method_name = self._get_node_text(subchild)
                            children.append(f"{file_path}::{name}.{method_name}")
                            break

        return CodeNode(
            id=node_id,
            name=name,
            node_type=NodeType.CLASS,
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            dependencies=[],
            children=children,
            docstring=docstring,
            signature=None,
            source=source
        )

    def _create_import_node(self, node: TSNode, file_path: str) -> Optional[CodeNode]:
        """Create a CodeNode from an import statement node.

        Args:
            node: Tree-sitter import node
            file_path: Path to the source file

        Returns:
            CodeNode object or None if parsing fails
        """
        import_text = self._get_node_text(node)

        # Create a simple identifier for the import
        import_id = f"{file_path}::import_{node.start_point[0]}"

        line_start = node.start_point[0] + 1
        line_end = node.end_point[0] + 1

        return CodeNode(
            id=import_id,
            name=import_text,
            node_type=NodeType.IMPORT,
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            dependencies=[],
            children=[],
            docstring=None,
            signature=None,
            source=import_text
        )

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

        Args:
            nodes: List of CodeNode objects to analyze
        """
        # Create a mapping of function/method names to node IDs
        name_to_id = {}
        for node in nodes:
            if node.node_type in (NodeType.FUNCTION, NodeType.METHOD):
                name_to_id[node.name] = node.id

        # Analyze each function/method for calls
        for node in nodes:
            if node.node_type in (NodeType.FUNCTION, NodeType.METHOD) and node.source:
                # Look for function calls in the source
                for name, node_id in name_to_id.items():
                    if node_id != node.id and f"{name}(" in node.source:
                        if node_id not in node.dependencies:
                            node.dependencies.append(node_id)

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
