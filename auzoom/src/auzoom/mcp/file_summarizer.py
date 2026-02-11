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
        # Extract ALL headers (not just first 3 from first 20 lines)
        headers = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#'):
                # Preserve indentation level (# vs ## vs ###)
                headers.append(stripped)

        if headers:
            header_summary = "\n".join(headers)
        else:
            header_summary = "No headers"

        return f"""Document: {file_path.name}
Type: {file_path.suffix}
Lines: {len(lines)}
Headers:
{header_summary}"""

    def _summarize_config_file(self, file_path: Path, lines: list, content: str) -> str:
        """Summarize configuration files."""
        basic_info = f"Configuration: {file_path.name}\nType: {file_path.suffix}\nLines: {len(lines)}\nSize: {len(content)} bytes"

        # Try to parse and extract structure
        structure = self._extract_config_structure(file_path, content)
        if structure:
            basic_info += f"\n\nStructure:\n{structure}"

        return basic_info

    def _extract_config_structure(self, file_path: Path, content: str) -> str:
        """Extract structural info from config files."""
        import re

        try:
            if file_path.suffix == '.json':
                data = json.loads(content)
                if isinstance(data, dict):
                    keys = list(data.keys())[:10]  # Limit to first 10 keys
                    return "Top-level keys: " + ", ".join(keys)

            elif file_path.suffix in ['.yaml', '.yml']:
                # Basic regex extraction (no pyyaml dependency needed)
                keys = re.findall(r'^(\w+):', content, re.MULTILINE)[:10]
                if keys:
                    return "Top-level keys: " + ", ".join(keys)

            elif file_path.suffix == '.toml':
                # Extract section headers
                sections = re.findall(r'^\[([^\]]+)\]', content, re.MULTILINE)
                if sections:
                    return "Sections: " + ", ".join(sections)

        except Exception:
            pass  # Fallback to basic info if parsing fails

        return ""

    def _summarize_code_file(self, file_path: Path, lines: list) -> str:
        """Summarize non-Python code files."""
        lang_map = {
            '.js': 'JavaScript',
            '.jsx': 'JavaScript',
            '.ts': 'TypeScript',
            '.tsx': 'TypeScript',
            '.go': 'Go',
            '.rs': 'Rust',
            '.java': 'Java'
        }
        lang = lang_map.get(file_path.suffix, file_path.suffix)

        basic_info = f"Code file: {file_path.name}\nLanguage: {lang}\nLines: {len(lines)}"

        # Extract imports/exports
        structure = self._extract_code_structure(file_path, lines, lang)
        if structure:
            basic_info += f"\n\n{structure}"

        return basic_info

    def _extract_code_structure(self, file_path: Path, lines: list, lang: str) -> str:
        """Extract imports/exports from code files."""
        import re
        content = "\n".join(lines)

        imports = []
        exports = []

        if lang in ['JavaScript', 'TypeScript']:
            # ES6 imports: import X from 'Y'
            imports = re.findall(r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]', content)
            # ES6 exports: export function/class/const
            exports = re.findall(r'export\s+(?:function|class|const|interface|type|enum)\s+(\w+)', content)
            # Also: export default
            if re.search(r'export\s+default', content):
                exports.append('default')

        elif lang == 'Go':
            # Go imports: import "package"
            imports = re.findall(r'import\s+[\'"]([^\'"]+)[\'"]', content)
            # Go exports: func NameStartsWithCapital
            exports = re.findall(r'func\s+([A-Z]\w+)', content)

        elif lang == 'Rust':
            # Rust imports: use crate::module
            imports = re.findall(r'use\s+([^;]+);', content)
            # Rust public items: pub fn/struct/enum
            exports = re.findall(r'pub\s+(?:fn|struct|enum|trait)\s+(\w+)', content)

        elif lang == 'Java':
            # Java imports: import package.Class
            imports = re.findall(r'import\s+([^;]+);', content)
            # Java public classes/interfaces
            exports = re.findall(r'public\s+(?:class|interface|enum)\s+(\w+)', content)

        result = []
        if imports:
            result.append(f"Imports: {', '.join(imports[:10])}")  # Limit to 10
        if exports:
            result.append(f"Exports: {', '.join(exports[:10])}")

        return "\n".join(result) if result else ""

    def _summarize_generic_file(self, file_path: Path, lines: list, content: str) -> str:
        """Summarize generic files."""
        return f"File: {file_path.name}\nType: {file_path.suffix}\nLines: {len(lines)}\nSize: {len(content)} bytes"

    def _compute_hash(self, file_path: Path) -> str:
        """Compute content hash for cache key."""
        return hashlib.sha256(file_path.read_bytes()).hexdigest()[:8]
