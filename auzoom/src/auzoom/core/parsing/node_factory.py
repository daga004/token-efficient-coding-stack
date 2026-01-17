"""Factory for creating CodeNode objects from tree-sitter nodes."""

from typing import Optional
from tree_sitter import Node as TSNode
from ...models import CodeNode, NodeType


class NodeFactory:
    """Create CodeNode objects from tree-sitter AST nodes."""

    def __init__(self, get_text_func):
        """Initialize with text extraction function."""
        self.get_text = get_text_func

    def create_function_node(
        self,
        node: TSNode,
        file_path: str,
        node_type: NodeType,
        class_name: Optional[str] = None
    ) -> Optional[CodeNode]:
        """Create CodeNode from function definition."""
        name, params, body = self._extract_node_parts(node)
        if not name:
            return None

        # Build node ID with optional class prefix
        node_id = self._build_node_id(file_path, class_name, name) if class_name else self._build_node_id(file_path, name)

        # Extract signature and docstring
        signature = f"{name}{self.get_text(params)}" if params else None
        docstring = self._extract_docstring(body)

        # Get line range and source
        line_start, line_end = self._get_line_range(node)
        source = self.get_text(node)

        return CodeNode(
            id=node_id,
            name=name,
            node_type=node_type,
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            dependents=[],  # Reverse deps only
            children=[],
            docstring=docstring,
            signature=signature,
            source=source
        )

    def create_class_node(self, node: TSNode, file_path: str) -> Optional[CodeNode]:
        """Create CodeNode from class definition."""
        name, _, body = self._extract_node_parts(node)
        if not name:
            return None

        # Build node ID and extract metadata
        node_id = self._build_node_id(file_path, name)
        docstring = self._extract_docstring(body)
        line_start, line_end = self._get_line_range(node)
        source = self.get_text(node)
        children = self._collect_method_children(body, file_path, name)

        return CodeNode(
            id=node_id,
            name=name,
            node_type=NodeType.CLASS,
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            dependents=[],  # Reverse deps only
            children=children,
            docstring=docstring,
            signature=None,
            source=source
        )

    def create_import_node(self, node: TSNode, file_path: str) -> Optional[CodeNode]:
        """Create CodeNode from import statement."""
        # Extract import details
        module_name = None
        import_items = []

        if node.type == 'import_statement':
            for child in node.children:
                if child.type == 'dotted_name':
                    module_name = self.get_text(child)
        elif node.type == 'import_from_statement':
            for child in node.children:
                if child.type == 'dotted_name':
                    module_name = self.get_text(child)

        if not module_name:
            return None

        node_id = f"{file_path}::import::{module_name}"
        line_start, line_end = self._get_line_range(node)
        source = self.get_text(node)

        return CodeNode(
            id=node_id,
            name=f"import {module_name}",
            node_type=NodeType.IMPORT,
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            dependents=[],  # Reverse deps only
            children=[],
            docstring=None,
            signature=None,
            source=source
        )

    def _extract_node_parts(self, node: TSNode):
        """Extract name, params, and body from node children."""
        name = None
        params = None
        body = None
        for child in node.children:
            if child.type == 'identifier' and not name:
                name = self.get_text(child)
            elif child.type == 'parameters':
                params = child
            elif child.type == 'block':
                body = child
        return name, params, body

    def _build_node_id(self, file_path: str, *parts: str) -> str:
        """Build node ID from file path and name parts."""
        qualified_name = ".".join(parts)
        return f"{file_path}::{qualified_name}"

    def _get_line_range(self, node: TSNode) -> tuple:
        """Get 1-indexed line range from node."""
        return node.start_point[0] + 1, node.end_point[0] + 1

    def _collect_method_children(self, body: TSNode, file_path: str, class_name: str) -> list:
        """Collect method names from class body."""
        children = []
        if body:
            for child in body.children:
                if child.type == 'function_definition':
                    for subchild in child.children:
                        if subchild.type == 'identifier':
                            method_name = self.get_text(subchild)
                            children.append(self._build_node_id(file_path, class_name, method_name))
                            break
        return children

    def _extract_docstring(self, body: Optional[TSNode]) -> Optional[str]:
        """Extract docstring from function/class body."""
        if not body:
            return None

        # Look for first expression statement containing a string
        for child in body.children:
            if child.type == 'expression_statement':
                for subchild in child.children:
                    if subchild.type == 'string':
                        docstring_text = self.get_text(subchild)
                        # Remove quotes and clean up
                        docstring_text = docstring_text.strip('"\'')
                        return docstring_text

        return None
