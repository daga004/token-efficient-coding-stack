"""Import resolution for lazy code graph."""

from pathlib import Path
from typing import Optional
from ...models import CodeNode, NodeType


class ImportResolver:
    """Resolve Python imports to file paths."""

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def extract_imports(self, nodes: list[CodeNode]) -> list[str]:
        """Get list of imported file paths from nodes."""
        imports = []
        for node in nodes:
            if node.node_type == NodeType.IMPORT:
                resolved = self.resolve_import(node.name, node.file_path)
                if resolved:
                    imports.append(resolved)
        return imports

    def resolve_import(self, import_name: str, from_file: str) -> Optional[str]:
        """Convert import name to file path.

        Simple resolution for V1:
        - Relative imports: resolve relative to from_file
        - Absolute imports: resolve from project root
        """
        # Remove "from" and "import" keywords if present
        import_name = import_name.replace("from ", "").replace("import ", "").split()[0]

        # Handle relative imports
        if import_name.startswith("."):
            base_dir = Path(from_file).parent
            import_path = import_name.lstrip(".")
            potential = base_dir / f"{import_path}.py"
        else:
            # Absolute from project root
            import_path = import_name.replace(".", "/")
            potential = self.project_root / "src" / f"{import_path}.py"
            if not potential.exists():
                potential = self.project_root / f"{import_path}.py"

        if potential.exists():
            return str(potential.resolve())

        return None
