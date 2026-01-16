from pathlib import Path
import json
from typing import Optional, Union
from ...models import CodeNode, FetchLevel, NodeType
from ..parsing.parser import PythonParser
from ..caching.cache_manager import CacheManager
from ..node_serializer import NodeSerializer
from .import_resolver import ImportResolver
from ..caching.cache_warmer import CacheWarmer
from .graph_queries import GraphQueries


class LazyCodeGraph:
    """Graph that indexes files on-demand with persistent caching."""

    def __init__(self, project_root: str, auto_warm: bool = True):
        self.project_root = Path(project_root).resolve()
        cache_dir = self.project_root / ".auzoom"
        cache_dir.mkdir(parents=True, exist_ok=True)

        self.cache = CacheManager(cache_dir)
        self.parser = PythonParser()
        self.serializer = NodeSerializer()
        self.import_resolver = ImportResolver(self.project_root)
        self.cache_warmer = CacheWarmer(self.project_root, self)
        self.queries = GraphQueries(self)
        self.nodes = {}
        self.file_index = {}  # Maps file_path -> [node_ids]
        self.index = self.cache.file_index  # Cache index with metadata
        self.metadata_dir = cache_dir / "metadata"
        self.stats = {"cache_hits": 0, "cache_misses": 0, "parses": 0}

        if auto_warm:
            import threading
            threading.Thread(
                target=self.cache_warmer.auto_warm_sequence,
                daemon=True
            ).start()

    def get_file(
        self,
        file_path: str,
        level: FetchLevel,
        format: str = "standard",
        fields: list[str] | None = None
    ) -> tuple[list[str], list[dict]]:
        """Get file nodes, parsing lazily if needed.

        Flow:
        1. Check memory cache
        2. Check disk cache (validate hash)
        3. Parse and cache if needed

        Args:
            file_path: Path to file
            level: Detail level (skeleton/summary/full)
            format: Serialization format ("standard" or "compact")
            fields: Optional list of fields to include

        Returns:
            Tuple of (import_names, serialized_nodes)
        """
        file_path = str(Path(file_path).resolve())

        # 1. Already in memory?
        if self._is_loaded(file_path):
            self.stats["cache_hits"] += 1
            return self._get_serialized_nodes(file_path, level, format, fields)

        # 2. On disk with valid hash?
        cached = self._load_from_cache(file_path)
        if cached:
            self.stats["cache_hits"] += 1
            self._load_nodes_into_memory(cached)
            return self._get_serialized_nodes(file_path, level, format, fields)

        # 3. Parse now (first access or stale)
        self.stats["cache_misses"] += 1
        self._parse_and_cache(file_path)
        return self._get_serialized_nodes(file_path, level, format, fields)

    def _is_loaded(self, file_path: str) -> bool:
        """Check if file's nodes are in memory."""
        return file_path in self.file_index

    def _load_from_cache(self, file_path: str) -> Optional[dict]:
        """Try to load from disk cache if hash matches."""
        if file_path not in self.index:
            return None

        entry = self.index[file_path]
        if not entry.get("indexed"):
            return None

        # Validate content hasn't changed
        try:
            current_hash = self.cache.compute_hash(file_path)
        except FileNotFoundError:
            return None

        if current_hash != entry["hash"]:
            # File changed, check if summary needs update
            if self._should_update_summary(file_path, entry):
                return None  # Force re-parse
            # Content changed but summary still valid
            entry["hash"] = current_hash
            self.cache.save_index()

        # Load metadata
        cache_file = self.metadata_dir / f"{file_path.replace('/', '_')}_{entry['hash']}.json"
        if cache_file.exists():
            return json.loads(cache_file.read_text())

        return None

    def _should_update_summary(self, file_path: str, old_entry: dict) -> bool:
        """Determine if file changes require re-parsing.

        Simple strategy: content hash changed = re-parse.
        Claude Code (the orchestrator LLM) makes higher-level decisions
        about when to fetch fresh data vs use cached results.

        Args:
            file_path: Path to changed file
            old_entry: Previous index entry

        Returns:
            True if should re-parse (always True for hash mismatch)
        """
        # File content changed → re-parse
        # This is correct and simple: parse is cheap (~5ms), correctness is critical
        return True

    def _parse_and_cache(self, file_path: str):
        """Parse file and cache metadata to disk."""
        self.stats["parses"] += 1
        nodes = self.parser.parse_file(file_path)
        # Store in memory
        node_ids = []
        for node in nodes:
            self.nodes[node.id] = node
            node_ids.append(node.id)
        self.file_index[file_path] = node_ids
        # Extract imports and cache to disk
        imports = self.import_resolver.extract_imports(nodes)
        content_hash = self.cache.compute_hash(file_path)
        cache_data = {
            "file_path": file_path,
            "hash": content_hash,
            "indexed_at": self.cache.timestamp(),
            "nodes": [self.serializer.serialize_node_for_cache(n) for n in nodes],
            "imports": imports
        }
        cache_file = self.metadata_dir / f"{file_path.replace('/', '_')}_{content_hash}.json"
        cache_file.write_text(json.dumps(cache_data, indent=2))
        # Update index
        self.index[file_path] = {
            "hash": content_hash,
            "indexed": True,
            "indexed_at": self.cache.timestamp(),
            "imports": imports,
            "node_count": len(nodes)
        }
        # Discover imports (but don't parse them)
        for imp in imports:
            if imp not in self.index:
                self.index[imp] = {
                    "hash": None,
                    "indexed": False,
                    "discovered_at": self.cache.timestamp()
                }
        self.cache.save_index()

    def _load_nodes_into_memory(self, cache_data: dict):
        """Hydrate nodes from cache and load into memory."""
        nodes = self.serializer.hydrate_nodes(cache_data)
        file_path = cache_data["file_path"]
        node_ids = []
        for node in nodes:
            self.nodes[node.id] = node
            node_ids.append(node.id)
        self.file_index[file_path] = node_ids

    def _get_serialized_nodes(
        self,
        file_path: str,
        level: FetchLevel,
        format: str = "standard",
        fields: list[str] | None = None
    ) -> tuple[list[str], list[dict]]:
        """Get and serialize nodes for a file at requested level with optimization support.

        Separates import nodes from code nodes for token efficiency (imports = 43% of skeleton).

        Args:
            file_path: Path to file
            level: Detail level
            format: Serialization format ("standard" or "compact")
            fields: Optional list of fields to include

        Returns:
            Tuple of (import_names, serialized_nodes)
            - import_names: Simple string list of imported modules
            - serialized_nodes: Serialized non-import nodes (functions, classes, methods)
        """
        from ..models import NodeType

        node_ids = self.file_index.get(file_path, [])
        all_nodes = [self.nodes[nid] for nid in node_ids]

        # Separate imports from code nodes
        import_nodes = [n for n in all_nodes if n.node_type == NodeType.IMPORT]
        code_nodes = [n for n in all_nodes if n.node_type != NodeType.IMPORT]

        # Extract import names (simple strings)
        import_names = [n.name for n in import_nodes]

        # Serialize code nodes (not imports)
        if format == "compact":
            serialized = self.serializer.serialize_file_compact(
                code_nodes,
                level,
                relative_to=str(self.project_root),
                fields=fields
            )
        else:
            serialized = self.serializer.serialize_file(code_nodes, level, fields=fields)

        return import_names, serialized

    def get_node(self, node_id: str, level: FetchLevel) -> dict:
        """Delegate to graph queries."""
        return self.queries.get_node(node_id, level)

    def get_children(self, node_id: str, level: FetchLevel) -> list[dict]:
        """Delegate to graph queries."""
        return self.queries.get_children(node_id, level)

    def get_dependencies(self, node_id: str, depth: int = 1) -> list[dict]:
        """Delegate to graph queries."""
        return self.queries.get_dependencies(node_id, depth)

    def find_by_name(self, name_pattern: str) -> list[dict]:
        """Delegate to graph queries."""
        return self.queries.find_by_name(name_pattern)

    def get_discovered_files(self) -> list[dict]:
        """List files discovered via imports but not yet indexed."""
        return [
            {"path": path, "discovered_at": entry["discovered_at"]}
            for path, entry in self.index.items()
            if not entry.get("indexed")
        ]

    def get_stats(self) -> dict:
        """Return cache performance stats."""
        total = self.stats["cache_hits"] + self.stats["cache_misses"]
        hit_rate = self.stats["cache_hits"] / total if total > 0 else 0

        return {
            "cache_hits": self.stats["cache_hits"],
            "cache_misses": self.stats["cache_misses"],
            "hit_rate": f"{hit_rate:.1%}",
            "files_parsed": self.stats["parses"],
            "files_indexed": len([e for e in self.index.values() if e.get("indexed")]),
            "files_discovered": len([e for e in self.index.values() if not e.get("indexed")]),
            "nodes_in_memory": len(self.nodes)
        }

    def discover_entry_points(self) -> list[str]:
        """Delegate to cache warmer."""
        return self.cache_warmer.discover_entry_points()

    def warm_cache(self, file_paths: list[str], level: FetchLevel = FetchLevel.SKELETON):
        """Delegate to cache warmer."""
        return self.cache_warmer.warm_cache(file_paths, level)

    def warm_entry_points(self):
        """Delegate to cache warmer."""
        return self.cache_warmer.warm_entry_points()

    def preload_discovered(self, limit: int = 10):
        """Delegate to cache warmer."""
        return self.cache_warmer.preload_discovered(limit)
