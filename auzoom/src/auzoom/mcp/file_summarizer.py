"""Non-Python file summarization for AuZoom."""

import json
import sys
import threading
import hashlib
from pathlib import Path
from typing import Optional
from datetime import datetime


class FileSummarizer:
    """Handle summarization and caching of non-Python files."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def load_cached_summary(self, file_path: Path) -> Optional[dict]:
        """Load cached summary for a file."""
        try:
            content_hash = self._compute_hash(file_path)
            cache_file = self.cache_dir / f"{file_path.name}_{content_hash}.json"

            if cache_file.exists():
                return json.loads(cache_file.read_text())
        except Exception:
            pass

        return None

    def schedule_summarization(self, file_path: Path, content: str):
        """Schedule background summarization for a file."""
        thread = threading.Thread(
            target=self._summarize_in_background,
            args=(file_path, content),
            daemon=True
        )
        thread.start()

    def _summarize_in_background(self, file_path: Path, content: str):
        """Background thread to generate and cache summary."""
        try:
            lines = content.splitlines()

            summary = {
                "summary": self._generate_summary_text(file_path, lines, content),
                "file_type": file_path.suffix,
                "line_count": len(lines),
                "size_bytes": len(content.encode('utf-8')),
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "version": "metadata_v1"
            }

            content_hash = self._compute_hash(file_path)
            cache_file = self.cache_dir / f"{file_path.name}_{content_hash}.json"
            cache_file.write_text(json.dumps(summary, indent=2))

        except Exception as e:
            print(f"Warning: Failed to generate summary for {file_path}: {e}", file=sys.stderr)

    def _generate_summary_text(self, file_path: Path, lines: list, content: str) -> str:
        """Generate basic metadata summary."""
        file_type = file_path.suffix

        if file_type in ['.md', '.txt', '.rst']:
            return self._summarize_text_file(file_path, lines)
        elif file_type in ['.json', '.yaml', '.yml', '.toml']:
            return self._summarize_config_file(file_path, lines, content)
        elif file_type in ['.js', '.ts', '.jsx', '.tsx', '.go', '.rs', '.java']:
            return self._summarize_code_file(file_path, lines)
        else:
            return self._summarize_generic_file(file_path, lines, content)

    def _summarize_text_file(self, file_path: Path, lines: list) -> str:
        """Summarize text/markdown files."""
        headers = [line.strip() for line in lines[:20] if line.strip().startswith('#')]
        header_summary = ", ".join(headers[:3]) if headers else "No headers"
        return f"Document: {file_path.name}\nType: {file_path.suffix}\nLines: {len(lines)}\nHeaders: {header_summary}"

    def _summarize_config_file(self, file_path: Path, lines: list, content: str) -> str:
        """Summarize configuration files."""
        return f"Configuration: {file_path.name}\nType: {file_path.suffix}\nLines: {len(lines)}\nSize: {len(content)} bytes"

    def _summarize_code_file(self, file_path: Path, lines: list) -> str:
        """Summarize non-Python code files."""
        lang_map = {'.js': 'JavaScript', '.ts': 'TypeScript', '.go': 'Go', '.rs': 'Rust', '.java': 'Java'}
        lang = lang_map.get(file_path.suffix, file_path.suffix)
        return f"Code file: {file_path.name}\nLanguage: {lang}\nLines: {len(lines)}\nNote: V2 will provide parsed structure"

    def _summarize_generic_file(self, file_path: Path, lines: list, content: str) -> str:
        """Summarize generic files."""
        return f"File: {file_path.name}\nType: {file_path.suffix}\nLines: {len(lines)}\nSize: {len(content)} bytes"

    def _compute_hash(self, file_path: Path) -> str:
        """Compute content hash for cache key."""
        return hashlib.sha256(file_path.read_bytes()).hexdigest()[:8]
