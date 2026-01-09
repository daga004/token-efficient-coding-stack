"""Cache management for lazy code graph."""

import json
import hashlib
from pathlib import Path
from typing import Optional, Union
from datetime import datetime


class CacheManager:
    """Manage file caching for LazyCodeGraph."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.metadata_dir = cache_dir / "metadata"
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = cache_dir / "index.json"
        self.file_index = self._load_index()

    def _load_index(self) -> dict:
        """Load file index from cache."""
        if self.index_file.exists():
            try:
                return json.loads(self.index_file.read_text())
            except Exception:
                return {}
        return {}

    def save_index(self):
        """Save file index to cache."""
        self.index_file.write_text(json.dumps(self.file_index, indent=2))

    def compute_hash(self, file_path: Union[str, Path]) -> str:
        """Compute SHA256 hash of file contents."""
        return hashlib.sha256(Path(file_path).read_bytes()).hexdigest()[:8]

    def timestamp(self) -> str:
        """Get current ISO timestamp."""
        return datetime.utcnow().isoformat() + "Z"

    def is_loaded(self, file_path: str) -> bool:
        """Check if file is loaded in cache."""
        return file_path in self.file_index

    def load_from_cache(self, file_path: str) -> Optional[dict]:
        """Load cached file data."""
        if file_path not in self.file_index:
            return None

        entry = self.file_index[file_path]
        cache_file = self.metadata_dir / f"{entry['cache_key']}.json"

        if not cache_file.exists():
            return None

        try:
            current_hash = self.compute_hash(file_path)
            if current_hash != entry['hash']:
                return None  # File changed

            return json.loads(cache_file.read_text())
        except Exception:
            return None

    def should_update_summary(self, file_path: str, old_entry: dict) -> bool:
        """Check if file needs summary update."""
        try:
            current_hash = self.compute_hash(file_path)
            return current_hash != old_entry.get('hash')
        except Exception:
            return True

    def save_to_cache(self, file_path: str, cache_data: dict):
        """Save file data to cache."""
        file_hash = self.compute_hash(file_path)
        cache_key = Path(file_path).stem + "_" + file_hash

        # Update index
        self.file_index[file_path] = {
            "hash": file_hash,
            "cache_key": cache_key,
            "last_parsed": self.timestamp()
        }

        # Write cache file
        cache_file = self.metadata_dir / f"{cache_key}.json"
        cache_file.write_text(json.dumps(cache_data, indent=2))

        # Save index
        self.save_index()

    def get_cache_path(self, file_path: str) -> Optional[Path]:
        """Get cache file path for a file."""
        if file_path not in self.file_index:
            return None

        entry = self.file_index[file_path]
        return self.metadata_dir / f"{entry['cache_key']}.json"
