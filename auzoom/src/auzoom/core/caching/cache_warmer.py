"""Cache warming and entry point discovery for lazy code graph."""

import threading
import time
from pathlib import Path
from ...models import FetchLevel


class CacheWarmer:
    """Handle cache warming and entry point discovery."""

    def __init__(self, project_root: Path, graph):
        self.project_root = project_root
        self.graph = graph

    def discover_entry_points(self) -> list[str]:
        """Find likely entry points in project.

        Priority order:
        1. Files with if __name__ == "__main__"
        2. Common entry point names (main.py, app.py, etc.)
        3. Files in project root
        """
        candidates = []

        # Check common names in root
        common_names = [
            "main.py", "app.py", "__main__.py",
            "manage.py", "run.py", "server.py", "cli.py"
        ]

        for name in common_names:
            path = self.project_root / name
            if path.exists():
                candidates.append(str(path.resolve()))

        # Scan for __main__ blocks (limit to avoid slow startup)
        scan_count = 0
        for py_file in self.project_root.rglob("*.py"):
            if scan_count >= 50:  # Limit scan
                break

            # Skip venv, node_modules, etc.
            if any(part.startswith(".") or part in ["venv", "node_modules", "__pycache__"]
                   for part in py_file.parts):
                continue

            try:
                content = py_file.read_text()
                if '__name__ == "__main__"' in content or "__name__ == '__main__'" in content:
                    candidates.append(str(py_file.resolve()))
                scan_count += 1
            except:
                pass

        return candidates[:5]  # Limit to top 5

    def warm_cache(self, file_paths: list[str], level: FetchLevel = FetchLevel.SKELETON):
        """Pre-parse files to warm cache (non-blocking).

        Args:
            file_paths: List of files to pre-parse
            level: Fetch level to cache
        """
        def warm_thread():
            for path in file_paths:
                try:
                    self.graph.get_file(path, level)
                except Exception as e:
                    print(f"Warning: Failed to warm {path}: {e}")

        thread = threading.Thread(target=warm_thread, daemon=True)
        thread.start()
        return thread

    def warm_entry_points(self):
        """Discover and pre-parse entry points in background."""
        entry_points = self.discover_entry_points()

        if not entry_points:
            return

        print(f"Info: Warming cache for {len(entry_points)} entry points...")
        self.warm_cache(entry_points)

    def preload_discovered(self, limit: int = 10):
        """Parse discovered but not-yet-indexed files.

        Args:
            limit: Max number of files to preload
        """
        discovered = self.graph.get_discovered_files()[:limit]
        paths = [f["path"] for f in discovered]

        if paths:
            print(f"Info: Preloading {len(paths)} discovered imports...")
            self.warm_cache(paths)

    def auto_warm_sequence(self):
        """Background warming strategy."""
        # Give main thread a head start
        time.sleep(0.1)

        # 1. Warm entry points
        self.warm_entry_points()

        # 2. Wait for entry points to finish discovering imports
        time.sleep(0.5)

        # 3. Warm discovered imports
        self.preload_discovered(limit=10)
